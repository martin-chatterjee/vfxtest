# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# Licensed under MIT License (--> LICENSE.txt)
# -----------------------------------------------------------------------------

"""'vfxtest' is a thin wrapper around unittest, coverage and mock.

Its purpose is to manage and run multiple test suites against a python
codebase that gets used inside multiple different contexts commonly found
in a VFX production environment.

Such common contexts in a VFX production environment include:
    - standalone Python 2.7.x
    - standalone Python 3.7.x
    - mayapy/maya
    - hython/houdini
    - nuke
    - ...

'vfxtest' lets you write and run test suites for all those contexts and then
provides you with combined code coverage metrics for all of them.

"""

"""
*** - rename output folder
*** - derive 'ignore' from executable
*** - remove colorama dependency
- come up with workflow that works with a pip-installed vfxtest installation!
- what's up with requirements.txt in mayapy/maya/hython/houdini/...?
        --> create a pure-python lib folder ?!?
            (coverage, mock, virtualenv)
        --> use lib/site-packages from python virtualenv?!?
- keep it simple!
- auto-generate wrapper scripts in subfolders(?!?)
-
"""

import argparse
import copy
from fnmatch import fnmatch
import glob
import inspect
import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
import unittest

try:
    import unittest.mock as mock
except: # pragma: no cover_3
    import mock

import coverage

main = unittest.main


# -----------------------------------------------------------------------------
def runMain(args=[]):
    """Main function that gets executed when ``vfxtest`` gets run.

    Collects and validates **settings** from both the passed in arguments as
    well as the config file.
    Then runs the test suite found directly in the 'target' folder specified
    in 'settings', followed by all other test suites found in subfolders of
    'target'.
    Finally combines all coverage reports into one, and reports it both to
    STDOUT and to HTML.

    Args:
        args (list)     :   list of command line arguments. (optional)

    Returns:
        (int)           :   statistics encoded into an 'exitcode' integer

    Raises:
        (SystemExit)    :   on missing or incompatible settings or arguments

    """
    settings = collectSettings(args)
    runTestSuite(settings)

    if settings['subprocess'] is False:
        runChildTestSuites(settings)
        combineCoverages(settings)

    return getStats(settings)


# -----------------------------------------------------------------------------
def collectSettings(args=[]):
    """Collects and validates 'settings' from both the passed in arguments
    as well as the config file.

    Args:
        args (list)     :   list of command line arguments. (optional)

    Returns:
        (dict)          :   dictionary holding all settings

    Raises:
        (SystemExit)    :   on missing or incompatible settings or arguments

    """
    arg_parser = _defineArguments()
    settings = _getSettings(arg_parser, args)

    return settings


# -----------------------------------------------------------------------------
def runTestSuite(settings, report=True):
    """Runs the test suite found inside the 'target' folder specified in
    'settings'.

    If runTestSuite gets called in 'native' context or inside a
    child subprocess then this will execute the test suite natively, meaning
    inside this current process and thereby using the current
    Python interpreter.
    Otherwise it will attempt to spawn an appropriate subprocess for
    this context that will then execute the test suite.

    Args:
        settings (dict)     :  dictionary holding all our settings
        report (bool)       :  will print a coverage report to STDOUT, if True
                               (default: True)
    Raises:
        (Exception)         : any internal exception will be re-raised

    """
    if settings['context'] == 'native' or settings['subprocess'] == True:
        runNative(settings, report=report)
        return

    for context in _resolveContextsToRun(settings):
        try:
            # start with copy of settings, update context
            ctxt_settings = copy.deepcopy(settings)
            ctxt_settings['context'] = context

            _storeSettingsInEnv(ctxt_settings)

            wrapper = _getWrapperPath(ctxt_settings)
            executable = _getExecutable(ctxt_settings)
            vfxtest_root = os.path.dirname(_getPathToMyself())
            dcc_settings_root = _createTestRootFolder(settings,
                                                      name='_dcc_settings',
                                                      reuse_existing=True)
            _ensureVirtualEnvs(settings, dcc_settings_root)

            args = [wrapper,
                    executable,
                    vfxtest_root,
                    dcc_settings_root,
                    str(settings['debug_mode'])]

            # deal with target_wrapper
            target_wrapper = _getTargetWrapper(ctxt_settings)
            if os.path.exists(target_wrapper):
                args.append(target_wrapper)

            # deal with virtualenv activation and deactivation
            if executable.find('virtualenv_{}'.format(context)) != -1:
                activate = os.sep.join([os.path.dirname(executable), 'activate'])
                deactivate = os.sep.join([os.path.dirname(executable), 'deactivate'])
                args.insert(0, activate)
                args.insert(1, '&&')
                args.append('&&')
                args.append(deactivate)

            print('')
            print('/'*80)
            status_line = ("// Running tests in './{}' as a subprocess (context '{}'): "
                           .format(os.path.basename(settings['target']), context))
            status_line += '/'*(80-len(status_line))
            print (status_line)
            print('')
            sys.stdout.flush()

            if settings['debug_mode']:
                print('')
                print('[DBG] Wrapper call:')
                print('      -------------')
                print('      ' + ' '.join(args))
                print('')
                print('[DBG] target folder:')
                print('      -------------')
                print('      ' + ctxt_settings['target'])
                print('')
                print('[DBG] target context:')
                print('      --------------')
                print('      ' + ctxt_settings['context'])
                print('')
                print('[DBG] dcc settings root:')
                print('      -----------------')
                print('      ' + dcc_settings_root)
                print('')
                print('')
                sys.stdout.flush()

            Popen = _resolvePopenClass()
            with Popen(args=args,
                       bufsize=0,
                       shell=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT) as proc:
                sys.stdout.flush()
                while True:
                    line = proc.stdout.readline().decode('utf-8')
                    if not line:
                        break
                    if not _updateStatsFromStdout(settings, line):
                        sys.stdout.write(line)
                        sys.stdout.flush()
                returncode = proc.wait()

            if settings['debug_mode']:
                print('')
                print('[DBG] --> Process Return Code: {}'
                       .format(returncode))
                print('')
                print('')
                print ('/'*80)
                print('')
                sys.stdout.flush()

            # stop here on internal child process error
            if returncode != 0:
                print("vfxtest ERROR: '{}' returned with error code {}. Stopping here..."
                       .format(settings['context'], returncode))
                raise(SystemExit)

        except Exception as e:
            traceback.print_exc()
            raise(e)
        finally:
            _clearSettingsInEnv()


# -----------------------------------------------------------------------------
def runChildTestSuites(settings):
    """Runs every child test suite found in 'target' in it's appropriate
    context.

    Every subfolder of 'target' that is named like a known context gets
    run.

    Args:
        settings (dict)     :  dictionary holding all our settings

    Raises:
        (Exception)         : any internal exception will be re-raised

    """
    child_settings = settings.copy()
    target = child_settings['target']

    # run child test suites in alphabetical order, but do 'Python' first
    def sort_python_first(item):
        if item.lower().startswith('python'):
            return 0
        return 1
    children = sorted(os.listdir(target))
    children = sorted(children, key=sort_python_first)

    for item in children:
        if item in child_settings['context_details']:
            item_path = '{}{}{}'.format(target, os.sep, item)
            if os.path.isdir(item_path):
                child_settings['target'] = item_path
                child_settings['context'] = item
                print(child_settings['context'])
                runTestSuite(child_settings)

    settings['files_run'] = child_settings['files_run']
    settings['tests_run'] = child_settings['tests_run']
    settings['errors'] = child_settings['errors']


# -----------------------------------------------------------------------------
def runNative(settings, report=True, use_coverage=True):
    """Runs the test suite found in 'target' natively in this current process.

    Locates all valid test files, filters them down by filter tokens and by
    limit, then runs them.
    Tracks coverage, and updates statistics in 'settings'.

    Args:
        settings (dict)     :  dictionary holding all our settings
        report (bool)       :  will print a coverage report to STDOUT, if True
                               (default: True)
        use_coverage (bool) :  will track coverage if True.
                               (default: True)
    Raises:
        (Exception)         : any internal exception will be re-raised

    """
    initContext(settings)

    if use_coverage:
        cov = _startCoverage(settings)

    suite = _discoverTests(settings)

    runner = TextTestRunner(failfast=settings['failfast'],
                            buffer=False)
    # run tests file by file
    for item in suite:
        if (settings['limit'] > 0 and
                settings['files_run'] >= settings['limit']):
            print('Reached file limit... Stopping here...')
            break

        result = runner.run(item, settings=settings)
        sys.stdout.flush()

        settings['files_run'] += 1
        settings['tests_run'] += result.testsRun
        settings['errors'] += len(result.errors) + len(result.failures)

    if use_coverage:
        # --> can't be covered:
        #     coverage does not work inside of another coverage run
        _stopCoverage(settings, cov, report=report) # pragma: no cover

    if settings['context'] != 'native':
        encodeStatsIntoStdout(settings)


# -----------------------------------------------------------------------------
def combineCoverages(settings):
    """Combines all .coverage files found into on overall coverage data set.

    Reports this coverage both to STDOUT as well as to HTML.

    Args:
        settings (dict)     :  dictionary holding all our settings

    """
    test_output = settings['output_folder']
    data_file='{}/.coverage'.format(test_output)
    cov = coverage.Coverage(data_file=data_file)
    cov.combine()
    cov.save()
    try:
        print('')
        cov.report()
        cov.html_report(directory='{}/_coverage_html'.format(test_output))
    except coverage.misc.CoverageException as e:
        print('Coverage: no data to report')


# -----------------------------------------------------------------------------
def encodeStatsIntoStdout(settings):
    """Encode serialized stats into a parsable string and write that to STDOUT.

    Using this mechanism we pass back the current stats to a potential parent
    process.

    Args:
        settings (dict)     :  dictionary holding all our settings

    """
    stats = getStats(settings)
    encoded = '<vfxtest-stats>{}</vfxtest-stats>'.format(json.dumps(stats))

    stdout = sys.stdout
    # let Maya print the stats to the _external_ stdout
    # (console, not script editor)
    if settings['context'].lower() == 'maya':
        stdout = sys.__stdout__ # pragma: no cover

    stdout.write('')
    stdout.write(encoded)
    stdout.write('')
    stdout.flush()


# -----------------------------------------------------------------------------
def getStats(settings):
    """Extract and return our stats from settings.

    Args:
        settings (dict)     :  dictionary holding all our settings

    Returns:
        (dict)              : dictionary holding stats

    """
    stats = {}
    stats['files_run'] = settings.get('files_run', 0)
    stats['tests_run'] = settings.get('tests_run', 0)
    stats['errors'] = settings.get('errors', 0)

    return stats


# -----------------------------------------------------------------------------
def resolveContext(settings):
    """Resolves the current content by comparing the name of the current
    'target' folder to all known contexts in 'settings'.

    If the context is know, it is returned. Otherwise 'native' gets returned
    as default context.

    Args:
        settings (dict)     :  dictionary holding all our settings

    Returns:
        (string)            :  resolved context

    """
    context = os.path.basename(os.path.abspath(settings['target']))
    if not context in settings['context_details']:
        context = 'native'
    return context


# -----------------------------------------------------------------------------
def initContext(settings):
    """Perform any context-specific inits.

    Right now we are only dealing with 'mayapy' inits in here.

    Args:
        settings (dict)     :  dictionary holding all our settings

    """
    try:
        if settings['context'] == 'mayapy':
            import maya.standalone
            maya.standalone.initialize()

    except Exception as e:
        print("initContext(): {}".format(e))
        traceback.print_exc()


# -----------------------------------------------------------------------------
def _defineArguments():
    """Defines and documents the valid command line arguments.

    Returns:
        (ArgumentParser)  : ArgumentParser object

    """
    parser = argparse.ArgumentParser(description='Run test suite(s):')

    parser.add_argument('-t', '--target', metavar='', type=str, default='.',
                        help='target folder path (defaults to current working directory)')
    parser.add_argument('-f', '--failfast', type=__stringToBool, default=True,
                        help='Stops execution of test suite on first error.')
    parser.add_argument('-c', '--cfg', metavar='', type=str, default=None,
                        help="path of the .cfg file to use. "
                             ""
                             "Defaults to 'vfxtest.cfg' in:"
                             "    - the current working directory"
                             "    - the one root dir of the current working directory")
    parser.add_argument('-l', '--limit', metavar='', type=int, default=0,
                        help='limits the number of test files that get executed.')
    parser.add_argument('filter_tokens', nargs='*', type=str,
                        help='specify tokens that filter down the test files by name.')

    return parser


# -----------------------------------------------------------------------------
def __stringToBool(value):
    """Attempts to interpret value as a boolean value.

    Args:
        value (string)               : string to interpret as a boolean

    Returns:
        (bool)                       : extracted boolean value

    Raises:
        (argparse.ArgumentTypeError) : If value could not be interpreted
                                       as a boolean value

    """
    if value.lower() in ('true', '1', 'y', 'yes'):
        return True
    if value.lower() in ('false', '0', 'n', 'no'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')


# -----------------------------------------------------------------------------
def _updateStatsFromStdout(settings, line):
    """Parses 'line' and tries to extract encoded 'vfxtest-stats' that the
    subprocess might have logged.

    If any 'vfxtest-stats' were found the corresponding settings get updated.

    Args:
        settings (dict) : settings dictionary
        line (string)   : current STDOUT line to parse

    Returns:
        (bool)          : True if stats got found, False if not

    """
    status = False

    try:
        tokens = line.split('<vfxtest-stats>')
        stats = tokens[1].split('</vfxtest-stats>')[0]
        decoded = json.loads(stats)

        settings['files_run'] = decoded['files_run']
        settings['tests_run'] = decoded['tests_run']
        settings['errors'] = decoded['errors']

        print('')
        print('Updated Stats -------------------------')
        print(' {} test files run'.format(settings['files_run']))
        print(' {} tests run'.format(settings['tests_run']))
        print(' {} errors'.format(settings['errors']))
        print('---------------------------------------')
        print('')
        sys.stdout.flush()

        status = True

    except (IndexError, TypeError) as e:
        pass

    return status


# -----------------------------------------------------------------------------
def _storeSettingsInEnv(settings):
    """Serializes the settings dictionary and stores it in the environment
    variable 'vfxtest_settings'.

    These stored settings then get extracted and used inside a subprocess.

    Args:
        settings (dict) : settings dictionary

    """
    # serialize and store in environment variable
    json_settings = json.dumps(settings)
    os.environ['vfxtest_settings'] = json_settings


# -----------------------------------------------------------------------------
def _clearSettingsInEnv():
    """Clears the environment variable 'vfxtest_settings' if it is set.

    """
    if 'vfxtest_settings' in os.environ:
        os.environ.pop('vfxtest_settings')


# -----------------------------------------------------------------------------
def _resolveContextsToRun(settings):
    """Returns a list of contexts that we need to run.

    Args:
        settings (dict) : settings dictionary

    Returns:
        (list)          : list of contexts to run.

    """
    context = settings['context']
    context_details = settings['context_details'][context]
    if 'nested_contexts' in context_details:
        return context_details['nested_contexts']

    return [context,]


# -----------------------------------------------------------------------------
def _getExecutable(settings):
    """Resolves and returns the executable for the current context.

    Args:
        settings (dict) : settings dictionary

    Returns:
        (string)        : path to the executable

    """
    context = settings['context']
    context_details = settings['context_details'][context]
    executable = context_details['executable']

    # if this is standalone python then prefer the correct virtualenv
    if context.lower().find('python') != -1:
        dcc_settings = _createTestRootFolder(settings,
                                             name='_dcc_settings',
                                             reuse_existing=True)
        venv_root = os.sep.join([dcc_settings, 'virtualenv_{}'.format(context)])
        if os.path.exists(venv_root):
            subfolder = 'bin'
            if sys.platform == 'win32':
                subfolder = 'Scripts'
            if os.path.exists('{}/{}'.format(venv_root, subfolder)):
                executable = os.sep.join([venv_root, subfolder, 'python'])

    return executable


# -----------------------------------------------------------------------------
def _getPathToMyself():
    """Return absolute path of this file.

    """
    # for Python 2 and 3 compatibility we need to ensure a .py suffix
    path_tokens = __file__.split('.')
    path_tokens[-1] = 'py'
    path_to_myself = '.'.join(path_tokens)

    return os.path.abspath(path_to_myself)


# -----------------------------------------------------------------------------
def _getTargetWrapper(settings):
    """
    """
    context = settings['context']
    context_details = settings['context_details'][context]
    target_wrapper = context_details.get('target_wrapper', '')
    if target_wrapper != '':
        target_wrapper = _getWrapperPath(settings,
                                         name=target_wrapper,
                                         suffix='')
    return target_wrapper


# -----------------------------------------------------------------------------
def _getWrapperPath(settings, name=None, suffix=None):
    """
    """
    # use bash for every os execpt Windows
    if suffix is None:
        suffix = '.sh'
        if platform.system() == 'Windows':
            suffix = '.cmd'
    if name is None:
        name = settings['context']
    wrapper_name = '{}{}'.format(name, suffix)
    wrapper_path = '{}{}{}'.format(settings['wrapper_scripts'],
                                   os.sep,
                                   wrapper_name)

    if not os.path.exists(wrapper_path):
        raise OSError('Could not find wrapper script:'
                                '\n{}'.format(wrapper_path))

    return wrapper_path


# -----------------------------------------------------------------------------
def _discoverTests(settings):
    """Discover all relevant Test Cases.

    Args:
        settings (dict) : settings dictionary

    Returns:
        (TestSuite) : test suite to run

    """
    patterns = [settings['test_file_pattern'],]
    for item in settings['filter_tokens']:
        patterns.append('*{}*'.format(item))

    loader = FilteredTestLoader()
    suite = loader.discover(settings['target'], pattern=patterns)

    return suite


# -----------------------------------------------------------------------------
def _startCoverage(settings):
    """Start the code coverage.

    Args:
        settings (dict) : settings dictionary

    """
    omit = []
    # omit myself
    omit.append('*vfxtest.py')
    # omit everythin in 'output_folder'
    omit.append('{}/*'.format(settings['output_folder']))
    # add omit_coverage tokens from config
    context = settings['context']
    context_details = settings.get('context_details', {}).get(context, {})
    omit_coverage = context_details.get('omit_coverage', [])
    # omit root folder of executable
    executable = context_details.get('executable', '')

    # --> can't be covered:
    #     coverage does not work inside of another coverage run
    if os.path.exists(executable): # pragma: no cover
        basename = os.path.basename(executable).lower()
        omit_root_folder = os.path.dirname(executable)
        if (basename.find('maya') != -1 or
            basename.find('hython') != -1 or
            basename.find('houdini') != -1
        ):
            omit_root_folder = os.path.dirname(omit_root_folder)
        omit_root_folder = omit_root_folder.replace('\\', '/')
        omit_coverage.append('{}/*'.format(omit_root_folder))
    if isinstance(omit_coverage, list) or isinstance(omit_coverage, tuple):
        omit.extend(omit_coverage)
    # omit all test files
    if not settings['include_test_files']:
        # prepare test file pattern
        prefix = settings['target'].replace(settings['cwd'], '')
        if len(prefix) > 0:
            prefix = '{}{}'.format(prefix[1:], prefix[0])
        test_file_pattern = prefix + settings['test_file_pattern']
        omit.append(test_file_pattern)

    data_file='{}/.coverage'.format(settings['output_folder'])
    cov = coverage.Coverage(omit=omit,
                            data_file=data_file,
                            data_suffix=settings['context'])
    cov.start()
    # --> can't be covered:
    #     coverage does not work inside of another coverage run
    return cov # pragma: no cover


# -----------------------------------------------------------------------------
def _stopCoverage(settings, cov, report=True):
    """Stops the code coverage.

    Args:
        settings (dict) : settings dictionary
        cov (coverage)  : coverage object
        report (bool)   : True if coverage should be reported.
                          (Optional, defaults to True)

    """
    # --> 'cov.stop()' can't be covered:
    #     coverage does not work inside of another coverage run
    cov.stop() # pragma: no cover

    cov.save()
    if report:
        try:
            print('')
            cov.report()
        except coverage.misc.CoverageException as e:
            print('Coverage: no data to report')


# -----------------------------------------------------------------------------
def _getSettings(arg_parser, args):
    """Collects and combines all valid settings.

    Also ensures that the 'output_folder' folder exists (but will never create
    its parent folder).

    Settings get collected from:
        - parsing the command line arguments
        - settings in the 'vfxtest_settings' environment variable
        - a config file

    Args:
        arg_parser (ArgParser)  : ArgumentParser object
        args (list)             : list of command line arguments

    Returns:
        (dict)                  : dictionary of combined settings

    Raises:
        (SystemExit)            : on failure while reading/conforming
                                  config file

    """
    settings = {}

    try:
        # start with arguments
        settings = vars(arg_parser.parse_args(args=args))
        # use settings in environment if present, fall back to cfg file
        if 'vfxtest_settings' in os.environ:
            _recoverSettingsFromEnv(settings)
        else:
            _readConfig(settings)

    except Exception as e:
        if not isinstance(e, ValueError):
            print('Failed to read and conform config:\n{}\n{}'
                   .format(e, traceback.format_exc()))
        raise SystemExit

    # create a fresh output folder, but never create its parent folder
    test_output = settings['output_folder']
    parent_folder = os.path.dirname(test_output)
    if not os.path.exists(parent_folder):
        raise SystemExit("Folder does not exist: '{}'"
                          .format(parent_folder))
    if not os.path.exists(test_output):
        os.makedirs(test_output)

    return settings


# -----------------------------------------------------------------------------
def _recoverSettingsFromEnv(settings):
    """Recovers settings from the environment variable 'vfxtest_settings'
    and replaces the contents of the settings dictionary accordingly.

    This environment variable gets used to pass down settings into a
    vfxtest subprocess.

    Args:
        settings (dict) : settings dictionary

    """
    serialized = os.environ['vfxtest_settings']
    recovered_settings = json.loads(serialized)
    settings.clear()
    settings.update(recovered_settings)

    settings['subprocess'] = True


# -----------------------------------------------------------------------------
def _readConfig(settings):
    """Reads a vfxtest config file and updates the settings dictionary
    accordingly.
    Also ensures default values for a bunch of settings in case they are
    not explicitely specified.

    Respects the path to a config file stored in the 'cfg' value of
    the settings dictionary.
    Otherwise falls back to expecting 'vfxtest.cfg' in the current
    working directory, or its parent directory.

    The config file must contain valid JSON, but can also contain lines
    commented out with the # sign.

    Args:
        settings (dict)     :  dictionary holding all our settings

    Raises:
        (Exception)         : on Problems decoding JSON

    """
    # prefer 'vfxtest.cfg' in current folder, fallback to parent folder
    explicit_cfg = True
    if settings['cfg'] is None:
        explicit_cfg = False
        if os.path.exists('./vfxtest.cfg'):
            settings['cfg'] = './vfxtest.cfg'
        else:
            settings['cfg'] = '../vfxtest.cfg'
    # deal with explicit config that can not be read
    if explicit_cfg is True and not os.path.exists(settings['cfg']):
        raise IOError('Config file does not exist: {}'.format(settings['cfg']))
    # read out cfg and strip comments
    content = ''
    if os.path.exists(settings['cfg']):
        with open(settings['cfg'], 'r') as f:
            content = f.read()
        # strip comments and empty lines
        lines = []
        for line in content.split('\n'):
            tokens = line.split('#')
            relevant = tokens[0]
            if len(relevant.strip()) > 0:
                lines.append(relevant)
        try:
            # interpret as json and add to settings
            json_string = '\n'.join(lines)
            cfg = json.loads(json_string)
        except Exception as e:
        # except ValueError as e:  --> Python 2.7
        # except json.decoder.JSONDecodeError as e:  --> Python 3.7
            _logJsonError(settings['cfg'], e, lines)
            raise

        settings.update(cfg)

    # initialize a few settings
    if not 'include_test_files' in settings:
        settings['include_test_files'] = False
    if not 'test_file_pattern' in settings:
        settings['test_file_pattern'] = 'test*.py'
    if not 'output_folder' in settings:
        settings['output_folder'] = './vfxtest_output'
    if not 'context_details' in settings:
        settings['context_details'] = {}
    if not 'wrapper_scripts' in settings:
        wrapper_scripts = ('{}{}wrapper_scripts'
                            .format(os.path.dirname(__file__), os.sep))
        settings['wrapper_scripts'] = wrapper_scripts

    if not 'files_run' in settings:
        settings['files_run'] = 0
    if not 'tests_run' in settings:
        settings['tests_run'] = 0
    if not 'errors' in settings:
        settings['errors'] = 0

    if not 'debug_mode' in settings:
        settings['debug_mode'] = False
    # sanitize debug_mode
    if '{}'.format(settings['debug_mode']).lower() == 'true':
        settings['debug_mode'] = True
    if not settings['debug_mode'] == True:
        settings['debug_mode'] = False

    settings['cwd'] = os.getcwd()

    # make all paths absolute
    for key in ['cfg', 'target']:
        settings[key] = os.path.abspath(settings[key])
    # make test_output absolute in relation to config location
    stored_wd = os.getcwd()
    try:
        os.chdir(os.path.dirname(settings['cfg']))
        settings['output_folder'] = os.path.abspath(settings['output_folder'])
    finally:
        os.chdir(stored_wd)

    settings['context'] = resolveContext(settings)

    settings['subprocess'] = False


# -----------------------------------------------------------------------------
def _logJsonError(cfg_path, e, lines):
    """Prints out a meaningful JSON error with correct line numbers and the
    correct line-numbered part of the offending JSON.

    Args:
        cfg_path (string)   :   path to the config file
        e (Exception)       :   thrown Exception object
        lines (list)        :   json source lines (with stripped comments)

    """
    offending_line_nbr = _extractLineNumber(e)

    print('')
    print('')
    print('='*80)
    print('= cfg Error ' + ('='*66))
    print('')
    print('This cfg file does not contain valid JSON:')
    print("       '{}'".format(cfg_path))
    print('')
    print("Error in line {}: '{}'".format(offending_line_nbr, e))
    print('')
    print('Faulty JSON (after stripping comments):')
    print('---------------------------------------')
    print('')
    for index, line in enumerate(lines):
        lineno = index+1
        source_line = '{}  {}'.format(str(lineno).rjust(3), line)
        print(source_line)
    print('')
    print('='*80)
    print('')


# -----------------------------------------------------------------------------
def _extractLineNumber(e):
    """Attempts to extract the offending line number from the thrown exception.

    Args:
        e (Exception) : Exception object

    Returns:
        (int)   : offending line number, or -1

    """
    line_nbr = -1
    try:
        right_side = str(e).split('line ')[1]
        number = right_side.split(' ')[0]
        line_nbr = int(number)
    except Exception as e:
        pass
    return line_nbr


# -------------------------------------------------------------------------
def _createTestRootFolder(settings, name, reuse_existing=False):
    """Creates a sandboxed test_root folder inside the 'output_folder'
    folder specified in 'settings'. The name of the test_root folder
    will match the name of the TestCase.

    If the test_root folder already exists, it will get deleted
    and recreated.

    However if the output folder does not exist it will raise an OSError.

    Args:
        settings (dict)      :  dictionary holding all our settings
        name (string)        :  name of the test root folder to create.

    Returns:
        (string)        :  absolute path of test_root

    Raises:
        (OSError)       :  if the output folder does not exist

    """
    test_output = settings.get('output_folder', None)
    if not os.path.exists(test_output):
        raise OSError("Invalid test_output: {}".format(test_output))

    testsuite_root = '{}{}{}'.format(test_output,
                                     os.sep,
                                     name)
    if os.path.exists(testsuite_root) and not reuse_existing:
       shutil.rmtree(testsuite_root)
    if not os.path.exists(testsuite_root):
        os.makedirs(testsuite_root)

    return testsuite_root


# -----------------------------------------------------------------------------
def _collectVirtualEnvDetails(settings, root_folder):
    """
    """
    result = {}

    for context in settings['context_details']:
        if context.lower().find('python') != -1:
            details = settings['context_details'][context]
            executable = details.get('executable', '')
            if os.path.exists(executable):
                venv_name = 'virtualenv_{}'.format(context)
                venv_path = '{}{}{}'.format(root_folder, os.sep, venv_name)
                result[venv_path] = executable

    return result


# -----------------------------------------------------------------------------
def _ensureVirtualEnvs(settings, root_folder):
    """
    """
    virtualenvs = _collectVirtualEnvDetails(settings, root_folder)

    for venv_path in virtualenvs:
        if not os.path.exists(venv_path):
            executable = virtualenvs[venv_path]
            _initializeVirtualEnv(settings, venv_path, executable)


# -----------------------------------------------------------------------------
def _initializeVirtualEnv(settings, venv_path, executable):
    """
    """
    venv_name = os.path.basename(venv_path)
    venv_root = os.path.dirname(venv_path)
    wrapper = _getWrapperPath(settings,
                              name='setup_python_virtualenv')

    args = [wrapper,
            executable,
            venv_name,
            venv_root,
            os.path.dirname(_getPathToMyself())]

    Popen = _resolvePopenClass()
    with Popen(args=args,
               bufsize=0,
               shell=True,
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT) as proc:
        print('')
        print('/'*80)
        print("Initializing virtualenv '{}'".format(venv_name))
        sys.stdout.flush()
        while True:
            line = proc.stdout.readline().decode('utf-8')
            if not line:
                break
            sys.stdout.write(line)
        proc.wait()
        print('/'*80)
        print('')


# -----------------------------------------------------------------------------
def _resolvePopenClass():
    """Returns the correct Popen class to use.

    In Python 3.x we use the native subprocess.Popen class, as this can already
    be used as a Context Manager natively.

    For Python 2.x contexts we return our own wrapped PopenWithContextManager
    class.

    Returns:
        (class)     : Popen class to use

    """
    Popen = subprocess.Popen
    if not hasattr(Popen, '__enter__'):
        Popen = PopenWithContextManager  # pragma: no cover_3
    return Popen


# -----------------------------------------------------------------------------
class PopenWithContextManager(subprocess.Popen): # pragma: no cover_3
    """A wrapper around subproces.Popen that also is a Context Manager.

    Python 3.x already supports this out of the box.
    Therefore we use this in Python 2.x contexts.

    """

    # -------------------------------------------------------------------------
    def __enter__(self):
        return self

    # -------------------------------------------------------------------------
    def __exit__(self, exc_type, value, traceback):
        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()
        try:  # Flushing a BufferedWriter may raise an error
            if self.stdin:
                self.stdin.close()
        finally:
            # Wait for the process to terminate, to avoid zombies.
            self.wait()

# -----------------------------------------------------------------------------
class FilteredTestLoader(unittest.TestLoader):
    """Test Loader that accepts a list of patterns as value for 'pattern'.

    The first pattern MUST be matched for a Test File to be included.
    (This is the equivalent of the standard unittest.TestLoader 'pattern')

    All other patterns are optional. For a file to be included it must
    match at least one of those optional patterns (--> an OR operation)

    """

    # -------------------------------------------------------------------------
    def _match_path(self, path, full_path, pattern, *args, **kwargs):
        """Test Loader that accepts a list of patterns as value for 'pattern'.

        The first pattern MUST be matched for a Test File to be included.
        (This is the equivalent of the standard unittest.TestLoader 'pattern')

        All other patterns are optional. For a file to be included it must
        match at least one of those optional patterns (--> an OR operation)

        Args:
            pattern (list)   : list of at least one string pattern

        """
        # first pattern must be matched
        result = False
        if fnmatch(path, pattern[0]):
            result = True
            # at least one of the optional patterns must be matched
            optionals = pattern[1:]
            if len(optionals) > 0:
                result = False
                for item in optionals:
                    if fnmatch(path, item):
                        result = True
                        break

        return result


# -----------------------------------------------------------------------------
class TextTestRunner(unittest.TextTestRunner):
    """TestRunner that also injects 'settings' into each test case and
    prepares a sandboxed test root folder.

    This you can query the settings and test_root from inside your test case
    implementation.

    """

    # -------------------------------------------------------------------------
    def run(self, test, settings={}, *args, **kwargs):
        """
        """
        self._prepTestCases(test, settings)
        return super(TextTestRunner, self).run(test, *args, **kwargs)

    # -------------------------------------------------------------------------
    def _prepTestCases(self, test, settings):
        """
        """
        if isinstance(test, unittest.TestSuite):
            for item in test._tests:
                if isinstance(item, unittest.TestCase):
                    # We can't just do 'isinstance(item, TestCase)' in here
                    # because this fails for TestTextRunners in child processes.
                    # Instead we fall back to text comparision of the parent classes.
                    # Feels a bit dodgy, but works...
                    base_classes = inspect.getmro(item.__class__)
                    for bc in base_classes:
                        if str(bc) == "<class 'vfxtest.TestCase'>":
                            item.settings = settings
                            test_case_name = item.__class__.__name__
                            item.test_root = _createTestRootFolder(settings,
                                                                   test_case_name)
                            return
                elif isinstance(item, unittest.TestSuite):
                    self._prepTestCases(item, settings)


# -----------------------------------------------------------------------------
class TestCase(unittest.TestCase):
    """TestCase that also provides easy access to associated data such
    as 'test_root',  'setttings' or 'context'.

    """

    __test_root = None

    # -------------------------------------------------------------------------
    def __init__(self, methodName='runTest', test_run=False,  *args, **kwargs):
        """
        """
        self.__settings = {}

        if not test_run:
            super(TestCase, self).__init__(methodName, *args, **kwargs)

    # -------------------------------------------------------------------------
    @property
    def test_root(self):
        """Gives access to the current test_root folder path inside
        the TestCase.

        """
        return TestCase.__test_root
    # -------------------------------------------------------------------------
    @test_root.setter
    def test_root(self, value):
        TestCase.__test_root = value

    # -------------------------------------------------------------------------
    @property
    def settings(self):
        """Gives access to the settings dictionary inside the TestCase.

        """
        return self.__settings
    # -------------------------------------------------------------------------
    @settings.setter
    def settings(self, value):
        if isinstance(value, dict):
            self.__settings = value
            TestCase.test_output = self.settings.get('output_folder', None)

    # -------------------------------------------------------------------------
    @property
    def context(self):
        """Returns current context.
        """
        return self.settings.get('context', 'unknown')

    # -------------------------------------------------------------------------
    @property
    def context_settings(self):
        """Returns current context settings.
        """
        all_details = self.settings.get('context_details', {})
        return all_details.get(self.context, {})

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Executes TestCase.setupClass, and also prints our test header.
        """
        super(TestCase, cls).setUpClass(*args, **kwargs)
        cls.logHeader()

    # -------------------------------------------------------------------------
    @classmethod
    def logHeader(cls):
        """Prints the test header.
        """
        print('')
        print('-' * 70)
        print("    Running tests in '{}'".format(cls.__name__))
        print('-' * 70)
        sys.stdout.flush()


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    runMain(sys.argv[1:]) # pragma: no cover


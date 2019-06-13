#!/usr/bin/env python
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

import argparse
import copy
from fnmatch import fnmatch
import glob
import importlib
import inspect
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import traceback
import unittest

try:
    import unittest.mock as mock
except ImportError: # pragma: no cover_3
    import mock

import coverage

main = unittest.main

logger = logging.getLogger('vfxtest')
"""vfxtest logger"""

# -----------------------------------------------------------------------------
def initLogging(level=logging.INFO,
                format='%(name)s | %(levelname)s : %(message)s'):
    """Initializes the vfxtest logger.

    """
    logger = logging.getLogger('vfxtest')
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    console = logging.StreamHandler()
    formatter = logging.Formatter(format)
    console.setFormatter(formatter)
    console.setLevel(level)
    logger.addHandler(console)

    # return logger

initLogging()

# -----------------------------------------------------------------------------
def runMain(args=[]):
    """Main function that gets executed when ``vfxtest`` gets run.

    Collects and validates **settings** from both the passed in arguments as
    well as the config file.
    Then runs the test suite found directly in the 'target' folder specified
    in 'settings', followed by all other test suites specified in the config
    file.
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
    prepareTestEnvironment(settings)
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
    settings = _compileSettings(arg_parser, args)

    return settings


# -----------------------------------------------------------------------------
def prepareTestEnvironment(settings):
    """Prepares the testing environment.

    First ensures that our output folder exists.
    Makes sure that all needed Python virtual environments are prepared.
    Also prepares a PYTHONPATH folder holding copies of all our pure-python
    requirement modules.

    Args:
        settings (dict) : settings dictionary

    """
    _ensureOutputFolder(settings)
    settings['dcc_settings_path'] = _createTestRootFolder(settings,
                                                          name='_dcc_settings',
                                                          reuse_existing=True)
    _prepareHelpers(settings)
    _ensureVirtualEnvs(settings)
    _preparePythonPath(settings)


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
        report (bool)       :  will log the coverage report to STDOUT, if True
                               (default: True)
    Raises:
        (Exception)         : any internal exception will be re-raised

    """
    if settings['context'] == 'native' or settings['subprocess'] == True:
        runNative(settings, report=report)
        return

    for context in _resolveContextsToRun(settings):
        runInSubprocess(settings, context)


# -----------------------------------------------------------------------------
def runNative(settings, report=True, use_coverage=True):
    """Runs the test suite found in 'target' natively in this current process.

    Locates all valid test files, filters them down by filter tokens and by
    limit, then runs them.
    Tracks coverage, and updates statistics in 'settings'.

    Args:
        settings (dict)     :  dictionary holding all our settings
        report (bool)       :  will log the coverage report to STDOUT, if True
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
            logger.info('Reached file limit... Stopping here...')
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
def runInSubprocess(settings, context):
    """Runs the test suite for context in a spawned subprocess using the
    correct Python executable.

    Args:
        settings (dict)     :  dictionary holding all our settings
        settings (string)   :  name of the context to run
    Raises:
        (SystemExit)        : if subprocess return an errorcode != 0

    """
    # start with copy of settings, update context
    ctxt_settings = copy.deepcopy(settings)
    ctxt_settings['context'] = context

    env = _preparePatchedEnvironment(ctxt_settings, context)
    executable = _getExecutable(ctxt_settings)
    vfxtest_py = _getPathToMyself()
    args = [executable, ]
    is_maya = False
    if context.lower().find('mayapy') != -1:
        args.append(vfxtest_py)

    elif context.lower().find('maya') != -1:
        is_maya = True
        args.append('-command')
        args.append('source vfxtest_maya; vfxtestSchedule();')

    elif context.lower().find('hython') != -1:
        args.append(vfxtest_py)

    elif context.lower().find('houdini') != -1:
        dcc_settings = settings['dcc_settings_path']
        hou_helper = '{}/helpers/vfxtest_houdini.py'.format(dcc_settings)
        args.append(hou_helper)

    else:
        args.append(vfxtest_py)

    # deal with virtualenv activation and deactivation
    if executable.find('virtualenv_{}'.format(context)) != -1:
        activate = os.sep.join([os.path.dirname(executable), 'activate'])
        deactivate = os.sep.join([os.path.dirname(executable), 'deactivate'])
        args.insert(0, activate)
        args.insert(1, '&&')
        args.append('&&')
        args.append(deactivate)

    logger.info('')
    logger.info('/'*80)
    status_line = ("// Running tests in './{}' as a subprocess (context '{}'): "
                   .format(os.path.basename(settings['target']), context))
    status_line += '/'*(80-len(status_line))
    logger.info(status_line)
    logger.info('')
    sys.stdout.flush()

    if settings['debug_mode']:
        logger.info('')
        logger.info('[DBG] target folder:')
        logger.info('      -------------')
        logger.info('      ' + ctxt_settings['target'])
        logger.info('')
        logger.info('[DBG] target context:')
        logger.info('      --------------')
        logger.info('      ' + ctxt_settings['context'])
        logger.info('')
        logger.info('')
        sys.stdout.flush()

    Popen = _resolvePopenClass()
    with Popen(args=args,
               bufsize=0,
               shell=True,
               stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT,
               env=env) as proc:
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
        logger.info('')
        logger.info('[DBG] --> Process Return Code: {}'
                     .format(returncode))
        logger.info('')
        logger.info('')
        logger.info ('/'*80)
        logger.info('')
        sys.stdout.flush()


    # Maya _always_ seems to be returning an errorcode of 1.
    # Soooo we ignore it...
    if is_maya:
        return

    # stop here on internal child process error
    if returncode != 0:
            logger.error("'{}' returned with error code {}. Stopping here..."
                          .format(settings['context'], returncode))
            raise(SystemExit)


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
                runTestSuite(child_settings)

    settings['files_run'] = child_settings['files_run']
    settings['tests_run'] = child_settings['tests_run']
    settings['errors'] = child_settings['errors']


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
        cov.report()
        cov.html_report(directory='{}/_coverage_html'.format(test_output))
    except coverage.misc.CoverageException as e:
        logger.info('Coverage: no data to report')


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
    # let Maya write the stats to the _external_ stdout
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

    If the context is known, it is returned. Otherwise 'native' gets returned
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
        if settings['context'].find('mayapy') != -1:
            import maya.standalone
            maya.standalone.initialize()

    except Exception as e:
        logger.error("initContext(): {}".format(e))
        logger.exception(e)
        # logger.exception(traceback.format_exc())


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
                             "    - the parent folder of the current working directory")
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
def _compileSettings(arg_parser, args):
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
            _ensureDefaultSettings(settings)

    except Exception as e:
        if not isinstance(e, ValueError):
            logger.error('Failed to read and conform config')
            logger.error('{}\n{}'.format(e, traceback.format_exc()))
        raise SystemExit

    return settings


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

        logger.info('')
        logger.info('Updated Stats -------------------------')
        logger.info(' {} test files run'.format(settings['files_run']))
        logger.info(' {} tests run'.format(settings['tests_run']))
        logger.info(' {} errors'.format(settings['errors']))
        logger.info('---------------------------------------')
        logger.info('')
        sys.stdout.flush()

        status = True

    except (IndexError, TypeError) as e:
        pass

    return status



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
def _preparePatchedEnvironment(settings, context):
    """Creates a duplicate of the current environment and patches all
    relevant environment variables for this context.

    Args:
        settings (dict)      : dictionary holding all our settings
        context (string)     : context to prepare the env for

    Returns:
        (dict)               : dictionary holding the context

    """
    env = dict(os.environ)

    # store updated copy fo settings in environment variable
    json_settings = json.dumps(settings)
    env['vfxtest_settings'] = json_settings
    dcc_settings = settings['dcc_settings_path']
    cwd = os.path.abspath(settings['cwd']).replace('\\', '/')

    # patch PYTHONPATH
    tokens = []
    env_var_value = env.get('PYTHONPATH', '')
    if env_var_value != '':
        tokens = env_var_value.split(os.pathsep)
    tokens.insert(0, cwd.replace('\\', '/'))
    env['PYTHONPATH'] = os.pathsep.join(tokens)

    dcc_pythonpath = '{}/PYTHONPATH'.format(dcc_settings)

    # deal with maya contexts
    context = settings.get('context', '')
    if context.lower().find('maya') != -1:
        maya_version = settings['context_details'][context].get('version', '')
        env['PYTHONPATH'] = '{}{}{}'.format(dcc_pythonpath,
                                            os.pathsep,
                                            env['PYTHONPATH'])
        env['MAYA_APP_DIR'] = '{}/{}.vfxtest.{}'.format(dcc_settings,
                                                        context,
                                                        maya_version)
        env['MAYA_SCRIPT_PATH'] = '{}{}{}/helpers'.format(cwd,
                                                          os.pathsep,
                                                          dcc_settings)
        env.pop('MAYA_PLUG_IN_PATH', None)
        env.pop('MAYA_MODULE_PATH', None)

    # deal with houdini/hython context
    if (context.lower().find('hython') != -1 or context.lower().find('houdini') != -1):
        env['PYTHONPATH'] = '{}{}{}'.format(dcc_pythonpath,
                                            os.pathsep,
                                            env['PYTHONPATH'])
        env['HOUDINI_USER_PREF_DIR'] = '{}/houdini.vfxtest.__HVER__'.format(dcc_settings)
        env.pop('HSITE', None)

    return env


# -----------------------------------------------------------------------------
def _getExecutable(settings):
    """Resolves and returns the executable for the current context.

    If this is a standalone Python executable it tries to resolve the correct
    prepared virtual environment for it.

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
        dcc_settings = settings['dcc_settings_path']
        venv_root = os.sep.join([dcc_settings, 'virtualenv_{}'.format(context)])
        if os.path.exists(venv_root):
            subfolder = 'bin'
            if sys.platform == 'win32':
                subfolder = 'Scripts'
            if os.path.exists('{}/{}'.format(venv_root, subfolder)):
                executable = '{}/{}/{}'.format(venv_root, subfolder, 'python')

    return executable


# -----------------------------------------------------------------------------
def _getPathToMyself():
    """Return absolute path of this file.

    """
    # for Python 2 and 3 compatibility we need to ensure a .py suffix
    my_path = __file__.replace('\\', '/')
    my_path = my_path.replace('.pyc', '.py')
    return my_path


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
            cov.report()
        except coverage.misc.CoverageException as e:
            logger.error('Coverage: no data to report')


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

    else:
        # deal with explicit config that can not be read
        if explicit_cfg is True:
            raise IOError('Config file does not exist: {}'.format(settings['cfg']))


# -----------------------------------------------------------------------------
def _ensureDefaultSettings(settings):
    """Ensures sensible default settings.

    Args:
        settings (dict)     :  dictionary holding all our settings

    """
    # user-facing settings
    if not 'include_test_files' in settings:
        settings['include_test_files'] = False
    if not 'test_file_pattern' in settings:
        settings['test_file_pattern'] = 'test*.py'
    if not 'output_folder' in settings:
        settings['output_folder'] = './vfxtest_output'

    if not 'debug_mode' in settings:
        settings['debug_mode'] = False
    if '{}'.format(settings['debug_mode']).lower() == 'true':
        settings['debug_mode'] = True
    if not settings['debug_mode'] == True:
        settings['debug_mode'] = False

    # internal settings
    if not 'context_details' in settings:
        settings['context_details'] = {}
    if not 'files_run' in settings:
        settings['files_run'] = 0
    if not 'tests_run' in settings:
        settings['tests_run'] = 0
    if not 'errors' in settings:
        settings['errors'] = 0

    settings['cwd'] = os.getcwd()
    settings['context'] = resolveContext(settings)
    settings['subprocess'] = False

    # make all paths absolute
    for key in ['cfg', 'target']:
        settings[key] = os.path.abspath(settings[key])
    # make test_output absolute in relation to config location
    stored_wd = os.getcwd()
    try:
        os.chdir(os.path.dirname(settings['cfg']))
        settings['output_folder'] = os.path.abspath(settings['output_folder'])
        settings['output_folder'] = settings['output_folder'].replace('\\', '/')
    finally:
        os.chdir(stored_wd)


# -----------------------------------------------------------------------------
def _logJsonError(cfg_path, e, lines):
    """Logs a meaningful JSON error with correct line numbers and the
    correct line-numbered part of the offending JSON.

    Args:
        cfg_path (string)   :   path to the config file
        e (Exception)       :   thrown Exception object
        lines (list)        :   json source lines (with stripped comments)

    """
    offending_line_nbr = _extractLineNumber(e)

    logger.error('')
    logger.error('')
    logger.error('='*80)
    logger.error('= cfg Error ' + ('='*68))
    logger.error('')
    logger.error('This cfg file does not contain valid JSON:')
    logger.error("       '{}'".format(cfg_path))
    logger.error('')
    logger.error("Error in line {}: '{}'".format(offending_line_nbr, e))
    logger.error('')
    logger.error('Faulty JSON (after stripping comments):')
    logger.error('---------------------------------------')
    logger.error('')
    for index, line in enumerate(lines):
        lineno = index+1
        source_line = '{}  {}'.format(str(lineno).rjust(3), line)
        logger.error(source_line)
    logger.error('')
    logger.error('='*80)
    logger.error('')


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

    return testsuite_root.replace('\\', '/')


# -----------------------------------------------------------------------------
def _ensureOutputFolder(settings):
    """Ensures that the output folder exists.

    Will create a the output folder, but will never create its parent folder.

    Args:
        settings (dict) : settings dictionary

    """
    test_output = settings['output_folder']
    parent_folder = os.path.dirname(test_output)
    if not os.path.exists(parent_folder):
        raise SystemExit("Folder does not exist: '{}'"
                          .format(parent_folder))
    if not os.path.exists(test_output):
        os.makedirs(test_output)


# -----------------------------------------------------------------------------
def _prepareHelpers(settings):
    """Ensures that all needed helpers start scripts do exist.

    Args:
        settings (dict) : settings dictionary

    """
    helpers = '{}/helpers'.format(settings['dcc_settings_path'])
    if not os.path.exists(helpers):
        os.makedirs(helpers)

    _ensureRequirements(helpers)
    _ensureHoudiniHelper(helpers)
    _ensureMayaHelper(helpers)


# -----------------------------------------------------------------------------
def _preparePythonPath(settings):
    """Creates a PYTHONPATH folder in dcc_settings_path and copies all
    our pure-python requirements in there.

    If the folder already exists it will not be recreated.

    Right now copies over these modules:
        coverage
        mock
        six
        vfxtest

    Later on we will point the PYTHONPATH environment variable to this
    folder for our child processes.
    This way all embedded Python interpreters inside a DCC will be able
    run vfxtest and its required modules.

    Args:
        settings (dict) : settings dictionary

    """
    test_no_pythonpath = settings.get('test_no_pythonpath', False)
    if test_no_pythonpath is True:
        return

    pythonpath = '{}/PYTHONPATH'.format(settings['dcc_settings_path'])
    if os.path.exists(pythonpath):
        return

    os.makedirs(pythonpath)

    # copy over vfxtest
    vfxtest_py = _getPathToMyself()
    dest_path = '{}/vfxtest.py'.format(pythonpath)
    shutil.copy2(vfxtest_py, dest_path)

    # is there a Python 2.x virtualenv that we can harvest?
    virtualenvs = _collectPythonExecutableDetails(settings)
    for env in virtualenvs:
        executable = virtualenvs[env]
        if _getPythonVersion(executable).startswith('2.'):
            source = '{}/Lib/site-packages'.format(env)
            _copyFolderContentToFolder(source, pythonpath)
            return

    # Fallback: If my current Python is 2.x then we can use that
    if sys.version.startswith('2.'): # pragma: no cover_2
        module_names = ['coverage', 'mock', 'six', 'funcsigs']
        _copyModulesToFolder(module_names, pythonpath)
        return

    else: # pragma: no cover_2

        error = ["",
                 "'vfxtest' needs access to a Python 2.x environment.",
                 "",
                 "You have two options:",
                 "",
                 "    - run vfxtest from a Python 2.x interpreter",
                 "    - define a 'Python 2.x' context in your config",
                 "      (even if you don't use it)"]
        raise EnvironmentError('\n'.join(error))


# -----------------------------------------------------------------------------
def _copyModulesToFolder(module_names, dest):
    """Copies the Python modules specified by their names to the destination
    folder.

    Args:
        module_names (list) : list of module names to copy
        dest (string)       : destination folder path

    """
    for name in module_names:
        module = importlib.import_module(name)

        if hasattr(module, '__path__') and len(module.__path__) > 0:
            module_path = module.__path__[0].replace('\\', '/')
        else:
            module_path = module.__file__.replace('\\', '/')
        module_path = module_path.replace('.pyc', '.py')
        module_name = os.path.basename(module_path)
        dest_path = '{}/{}'.format(dest, module_name)

        if os.path.isdir(module_path):
            shutil.copytree(module_path, dest_path)
        else:
            shutil.copyfile(module_path, dest_path)


# -----------------------------------------------------------------------------
def _copyFolderContentToFolder(source, dest):
    """Copies content of source folder into dest folder.

    Args:
        source (string) : source folder path
        dest (string)   : destination folder path

    """
    for item in os.listdir(source):
        source_path = '{}/{}'.format(source, item)
        target_path = '{}/{}'.format(dest, item)
        if os.path.isdir(source_path):
            shutil.copytree(source_path, target_path)
        else:
            shutil.copy2(source_path, target_path)


# -----------------------------------------------------------------------------
def _ensureRequirements(target_path, name='requirements.txt'):
    """Prepares a requirements file that will be used in the virtual
    environment setup.

    Args:
        target_path (string) : path to target folder
        name (string)        : target file name
                               (Optional, defaults to requirements.txt)

    """
    file_path = '{}/{}'.format(target_path, name)

    with open(file_path, 'w') as f:
        f.write('coverage >= 4.5\n')
        f.write('mock >= 3.0; python_version < "3.3"\n')


# -----------------------------------------------------------------------------
def _ensureMayaHelper(target_path):
    """Ensures the Maya Helper MEL script necessary to run tests inside
    an interactive Maya session.

    Args:
        target_path (string)   : target folder path

    """
    maya_helper = '{}/vfxtest_maya.mel'.format(target_path)

    if not os.path.exists(maya_helper):

        code = [
            'global proc vfxtestSchedule() {',
            '    string $python = "import vfxtest; vfxtest.mayaScheduleDelayed()";',
            '    evalDeferred `python $python`;',
            '}',
        ]

        with open(maya_helper, 'w') as f:
            f.write('\n'.join(code))


# -----------------------------------------------------------------------------
def _ensureHoudiniHelper(target_path):
    """Ensures the Houdini Helper Python module necessary to run tests inside
    an interactive Houdini session.

    Args:
        target_path (string)   : target folder path

    """
    hou_helper = '{}/vfxtest_houdini.py'.format(target_path)

    if not os.path.exists(hou_helper):

        code = [
            "import vfxtest",
            "",
            "if __name__ == '__main__':",
            "    vfxtest.houdiniScheduleDelayed()",
        ]

        with open(hou_helper, 'w') as f:
            f.write('\n'.join(code))


# -----------------------------------------------------------------------------
def _ensureVirtualEnvs(settings):
    """Makes sure that we have a prepared Python virtual environment
    prepared for every Python executable specified in context_details.

    If a python executable is not able to create a virtualenv then we ignore
    this fact for the time being. Later on the actual executable will get
    used instead of the virtual environment.

    Args:
        settings (dict)          : dictionary holding all our settings

    """
    virtualenvs = _collectPythonExecutableDetails(settings)

    for venv_path in virtualenvs:
        if not os.path.exists(venv_path):
            executable = virtualenvs[venv_path]
            _initializeVirtualEnv(settings, venv_path, executable)


# -----------------------------------------------------------------------------
def _getPythonVersion(executable):
    """
    """
    proc = subprocess.Popen([executable, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    proc.wait()
    out = proc.communicate()[0]
    version = out.decode('utf-8').replace('Python', '').split()[0]
    return version

# -----------------------------------------------------------------------------
def _collectPythonExecutableDetails(settings):
    """Extracts details of all  python executables specified in
    context_details.

    Verifies that those executables exist. Prepares the corresponding
    virtualenv names and returns all those details.

    Args:
        settings (dict)          : dictionary holding all our settings

    Returns:
        (dict)               :  dictionary of details

    """
    dcc_settings_path = settings['dcc_settings_path']

    result = {}

    for context in settings['context_details']:
        if context.lower().find('python') != -1:
            details = settings['context_details'][context]
            executable = details.get('executable', '')
            if os.path.exists(executable):
                venv_name = 'virtualenv_{}'.format(context)
                venv_path = '{}/{}'.format(dcc_settings_path, venv_name)
                result[venv_path] = executable

    return result


# -----------------------------------------------------------------------------
def _initializeVirtualEnv(settings, venv_path, executable):
    """Tries to initialize a Python virtual environment using this specific
    Python executable.

    If this Python executable is not able to create a virtualenv then we
    ignore this fact for the time being.
    Later on the actual executable will get used instead of the
    virtual environment.

    Args:
        settings (dict)      : dictionary holding all our settings
        venv_path (string)   : absolute path to the virtual environment
        executable (string)  : absolute path of the Python executable to use

    """
    requirements = '{}/helpers/requirements.txt'.format(settings['dcc_settings_path'])

    venv_name = os.path.basename(venv_path)
    subfolder = 'bin'
    keyword = 'source'
    if sys.platform == 'win32':
        subfolder = 'Scripts'
        keyword = 'call'

    args = [executable,
            '-m',
            'virtualenv',
            venv_path,
            '&&',
            keyword,
            '{}/{}/activate'.format(venv_path, subfolder),
            '&&',
            'pip',
            'install',
            '-r',
            requirements,
            '&&',
            keyword,
            '{}/{}/deactivate'.format(venv_path, subfolder),
           ]

    Popen = _resolvePopenClass()
    logger.info('')
    logger.info('/'*80)
    logger.info("Initializing virtualenv '{}'".format(venv_name))

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
            sys.stdout.write(line)
        proc.wait()

    logger.info('/'*80)
    logger.info('')


# -----------------------------------------------------------------------------
# DCC Schedule and Run methods
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def mayaScheduleDelayed(): # pragma: no cover
    """Schedule a delayed test suite run inside an interactive Maya session.

    """
    import maya.cmds as cmds

    logger.info('-----------------------------')
    logger.info('vfxtest: scheduleDelayed()')
    logger.info('-----------------------------')

    myself = __file__.replace('\\', '/').replace('.pyc', '.py')

    run_delayed = 'import maya.cmds as cmds;' \
                  'import vfxtest;' \
                  "cmds.evalDeferred('vfxtest.mayaRunDelayed()')".format(myself)

    cmds.scriptJob(runOnce=True, event=['NewSceneOpened', run_delayed])
    cmds.file(new=True, f=True)


# -----------------------------------------------------------------------------
def mayaRunDelayed(): # pragma: no cover
    """Run test suite inside an interactive Maya session.

    """
    import maya.cmds as cmds

    logger.info('-----------------------------')
    logger.info('vfxtest: runTestsDelayed()')
    logger.info('-----------------------------')
    stats = runMain()
    # don't quit if errors occured
    if stats['errors'] == 0:
        cmds.quit(f=True)


# -----------------------------------------------------------------------------
def houdiniScheduleDelayed(): # pragma: no cover
    """Schedule a delayed test suite run inside an interactive Houdini session.

    """
    import hdefereval

    context = os.path.basename(sys.executable)
    if context.lower().find('houdini') != -1:
        hdefereval.executeDeferred(houdiniRunDelayed)


# -----------------------------------------------------------------------------
def houdiniRunDelayed(): # pragma  no cover
    """Run test suite inside an interactive Houdini session.

    """
    import hou

    try:
        runMain()
        hou.exit(suppress_save_prompt=True)
    except Exception as e:
        hou.exit(error_code=1, suppress_save_prompt=True)






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
        """Executes TestCase.setupClass, and also logs our test header.
        """
        super(TestCase, cls).setUpClass(*args, **kwargs)
        cls.logHeader()

    # -------------------------------------------------------------------------
    @classmethod
    def logHeader(cls):
        """logs the test header.
        """
        logger.info('')
        logger.info('-' * 70)
        logger.info("    Running tests in '{}'".format(cls.__name__))
        logger.info('-' * 70)
        sys.stdout.flush()


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    runMain(sys.argv[1:]) # pragma: no cover


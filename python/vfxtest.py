# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# Licensed under MIT License (--> LICENSE.txt)
# -----------------------------------------------------------------------------

import argparse
import copy
from fnmatch import fnmatch
import glob
import inspect
import json
import os
import platform
import subprocess
import shutil
import sys
import traceback
import unittest

try: # pragma: no cover
    import unittest.mock as mock
except: # pragma: no cover
    import mock

import coverage
import colorama

colorama.init()
main = unittest.main


"""'vfxtest' is a thin wrapper around unittest, coverage and mock.

It's purpose is to manage and run multiple test suites testing a python
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


# -----------------------------------------------------------------------------
def runMain(args=[]):
    """Main function that gets executed when 'vfxtest' gets run.

    Collects and validates 'settings' from both the passed in arguments as
    well as the config file.
    Then runs the test suite found directly in the 'target' folder specified
    in 'settings', followee by all other test suites found in subfolders of
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

    exit_status = _encodeStatsIntoReturnCode(settings)
    return exit_status


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
    # define arguments
    arg_parser = _defineArguments()
    # validate preferences and add to settings
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
            path_to_myself = _getPathToMyself()

            args = [wrapper,
                    executable,
                    path_to_myself,
                    str(settings['debug_mode'])]

            print('')
            print('/'*80)
            status_line = ("// Running tests in './{}' as a subprocess (context '{}'): "
                           .format(os.path.basename(settings['target']), context))
            status_line += '/'*(80-len(status_line))
            print (status_line)
            print('')

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
                print('      -------------')
                print('      ' + ctxt_settings['context'])
                print('')
                print('')


            proc = subprocess.Popen(args=args,
                                    bufsize=0,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)

            sys.stdout.flush()
            while True:
                line = proc.stdout.readline().decode('utf-8')
                if not line:
                    break
                sys.stdout.write(line)
            proc.wait()

            if settings['debug_mode']:
                print('')
                print('[DBG] --> Process Return Code: {}'
                       .format(proc.returncode))
                print('')

            print('')
            print ('/'*80)
            print('')
            sys.stdout.flush()

            _recoverStatsFromReturnCode(settings, proc.returncode)

        except Exception as e:
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
    for item in os.listdir(target):
        if item in child_settings['context_details']:
            item_path = '{}{}{}'.format(target, os.sep, item)
            if os.path.isdir(item_path):
                child_settings['target'] = item_path
                child_settings['context'] = item
                print(child_settings['context'])
                runTestSuite(child_settings)

    settings['count_files_run'] = child_settings['count_files_run']
    settings['count_tests_run'] = child_settings['count_tests_run']
    settings['count_errors'] = child_settings['count_errors']


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
    if use_coverage:
        cov = _startCoverage(settings)

    suite = _discoverTests(settings)

    runner = TextTestRunner(failfast=settings['failfast'],
                            buffer=False)
    # run tests file by file
    for item in suite:
        if (settings['limit'] > 0 and
                settings['count_files_run'] >= settings['limit']):
            print('Reached file limit... Stopping here...')
            break

        result = runner.run(item, settings=settings)

        settings['count_files_run'] += 1
        settings['count_tests_run'] += result.testsRun
        settings['count_errors'] += len(result.errors) + len(result.failures)

    if use_coverage:
        # --> can't be covered:
        #     coverage does not work inside of another coverage run
        _stopCoverage(settings, cov, report=report) # pragma: no cover


# -----------------------------------------------------------------------------
def combineCoverages(settings):
    """Combines all .coverage files found into on overall coverage data set.

    Reports this coverage both to STDOUT as well as to HTML.

    Args:
        settings (dict)     :  dictionary holding all our settings

    """
    test_output = settings['test_output']
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
    context = os.path.basename(settings['target'])
    if not context in settings['context_details']:
        context = 'native'
    return context


# -----------------------------------------------------------------------------
def _defineArguments():
    """
    """
    parser = argparse.ArgumentParser(description='Run test suite(s):')

    parser.add_argument('-t', '--target', metavar='', type=str, default='.',
                        help='target folder path (defaults to current working directory)')
    parser.add_argument('-f', '--failfast', type=__stringToBool, default=True,
                        help='Stops execution of test suite on first error.')
    parser.add_argument('-p', '--cfg', metavar='', type=str, default=None,
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
def _encodeStatsIntoReturnCode(settings):
    """
    """
    # cap all count stats into range 0 - 999
    for item in ['count_files_run', 'count_tests_run', 'count_errors']:
        if settings[item] > 999:
            print("Warning: '{}' run was {} - capping to 999"
                   .format(item, settings[item]))
            settings[item] = 999
        elif settings[item] < 0:
            print("Warning: '{}' run was {} - capping to 0"
                   .format(item, settings[item]))
            settings[item] = 0

    result = 0
    result += (settings['count_files_run'] * 1000000)
    result += (settings['count_tests_run'] * 1000)
    result += (settings['count_errors'] * 1)

    return result

# -----------------------------------------------------------------------------
def _recoverStatsFromReturnCode(settings, returncode):
    """
    """
    count_files_run = returncode // 1000000
    returncode -= (count_files_run * 1000000)
    count_tests_run = returncode // 1000
    returncode -= (count_tests_run * 1000)
    count_errors = returncode

    settings['count_files_run'] = count_files_run
    settings['count_tests_run'] = count_tests_run
    settings['count_errors'] = count_errors

# -----------------------------------------------------------------------------
def _storeSettingsInEnv(settings):
    """
    """
    # serialize and store in environment variable
    json_settings = json.dumps(settings)
    os.environ['vfxtest_settings'] = json_settings

# -----------------------------------------------------------------------------
def _clearSettingsInEnv():
    """
    """
    if 'vfxtest_settings' in os.environ:
        os.environ.pop('vfxtest_settings')

# -----------------------------------------------------------------------------
def _resolveContextsToRun(settings):
    """
    """
    context = settings['context']
    context_details = settings['context_details'][context]
    if 'nested_contexts' in context_details:
        return context_details['nested_contexts']

    return [context,]

# -----------------------------------------------------------------------------
def _getExecutable(settings):
    """
    """
    context = settings['context']
    context_details = settings['context_details'][context]
    return context_details['executable']

# -----------------------------------------------------------------------------
def _getPathToMyself():
    """
    """
    # for Python 2 and 3 compatibility we need to ensure a .py suffix
    path_tokens = __file__.split('.')
    path_tokens[-1] = 'py'
    path_to_myself = '.'.join(path_tokens)

    return path_to_myself

# -----------------------------------------------------------------------------
def _getWrapperPath(settings):
    """
    """
    # use bash for every os execpt Windows
    suffix = '.sh'
    if platform.system() == 'Windows':
        suffix = '.cmd'

    wrapper_name = '{}{}'.format(settings['context'], suffix)
    wrapper_path = '{}{}{}'.format(settings['wrapper_scripts'],
                                   os.sep,
                                   wrapper_name)

    if not os.path.exists(wrapper_path):
        raise OSError('Could not find wrapper script:'
                                '\n{}'.format(wrapper_path))

    return wrapper_path

# -----------------------------------------------------------------------------
def _startCoverage(settings):

    omit = []
    # omit myself
    omit.append('*vfxtest.py')
    # omit all test files
    if not settings['include_test_files']:
        # prepare test file pattern
        prefix = settings['target'].replace(settings['cwd'], '')
        if len(prefix) > 0:
            prefix = '{}{}'.format(prefix[1:], prefix[0])
        test_file_pattern = prefix + settings['test_file_pattern']
        omit.append(test_file_pattern)

    data_file='{}/.coverage'.format(settings['test_output'])
    cov = coverage.Coverage(omit=omit,
                            data_file=data_file,
                            data_suffix=settings['context'])
    cov.start()
    # --> can't be covered:
    #     coverage does not work inside of another coverage run
    return cov # pragma: no cover

# -----------------------------------------------------------------------------
def _discoverTests(settings):
    """
    """
    patterns = [settings['test_file_pattern'],]
    for item in settings['filter_tokens']:
        patterns.append('*{}*'.format(item))

    loader = FilteredTestLoader()
    suite = loader.discover(settings['target'], pattern=patterns)

    return suite

# -----------------------------------------------------------------------------
def _stopCoverage(settings, cov, report=True):
    """
    """
    # --> can't be covered:
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
    """
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

        # make all paths absolute
        for key in ['cfg', 'target', 'test_output']:
            settings[key] = os.path.abspath(settings[key])

        # create 'test_output' if needed, but never create it's parent folder
        test_output = settings['test_output']
        parent_folder = os.path.dirname(test_output)
        if not os.path.exists(parent_folder):
            raise OSError("Folder does not exist: '{}'"
                           .format(parent_folder))
        if not os.path.exists(test_output):
            os.makedirs(test_output)

    except Exception as e:
        if not isinstance(e, ValueError):
            print('Failed to read and conform config:\n{}\n{}'
                   .format(e, traceback.format_exc()))
        raise(SystemExit)

    return settings

# -----------------------------------------------------------------------------
def _recoverSettingsFromEnv(settings):
    """
    """
    serialized = os.environ['vfxtest_settings']
    recovered_settings = json.loads(serialized)
    settings.clear()
    settings.update(recovered_settings)

    settings['subprocess'] = True

# -----------------------------------------------------------------------------
def _readConfig(settings):
    """
    """
    # prefer 'vfxtest.cfg' in current folder, fallback to parent folder
    if settings['cfg'] is None:
        if os.path.exists('./vfxtest.cfg'):
            settings['cfg'] = './vfxtest.cfg'
        else:
            settings['cfg'] = '../vfxtest.cfg'
    # read out cfg and strip comments
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
    # except ValueError as e:
    # except json.decoder.JSONDecodeError as e:
        _logJsonError(settings['cfg'], e, lines)
        raise

    settings.update(cfg)
    # initialize a few settings
    if not 'include_test_files' in settings:
        settings['include_test_files'] = False
    if not 'test_file_pattern' in settings:
        settings['test_file_pattern'] = 'test*.py'
    if not 'test_output' in settings:
        settings['test_output'] = './test_output'
    if not 'context_details' in settings:
        settings['context_details'] = {}
    if not 'wrapper_scripts' in settings:
        wrapper_scripts = ('{}{}wrapper_scripts'
                            .format(os.path.dirname(__file__), os.sep))
        settings['wrapper_scripts'] = wrapper_scripts

    if not 'count_files_run' in settings:
        settings['count_files_run'] = 0
    if not 'count_tests_run' in settings:
        settings['count_tests_run'] = 0
    if not 'count_errors' in settings:
        settings['count_errors'] = 0

    if not 'debug_mode' in settings:
        settings['debug_mode'] = False
    # sanitize debug_mode
    if '{}'.format(settings['debug_mode']).lower() == 'true':
        settings['debug_mode'] = True
    if not settings['debug_mode'] == True:
        settings['debug_mode'] = False

    settings['cwd'] = os.getcwd()
    settings['context'] = resolveContext(settings)

    settings['subprocess'] = False

# -----------------------------------------------------------------------------
def _extractLineNumber(e):
    """
    """
    lineno = -1
    try:
        right_side = str(e).split('line ')[1]
        number = right_side.split(' ')[0]
        lineno = int(number)
    except Exception as e:
        pass
    return lineno

# -----------------------------------------------------------------------------
def _logJsonError(cfg_path, e, lines):
    """
    """
    offending_lineno = _extractLineNumber(e)

    print('')
    print('')
    print('='*80)
    print('= cfg Error ' + ('='*66))
    print('')
    print('This cfg file does not contain valid JSON:')
    print("       '{}'".format(cfg_path))
    print('')
    print("Error: '{}'".format(e))
    print('')
    print('Faulty JSON (after stripping comments):')
    print('---------------------------------------')
    print('')
    for index, line in enumerate(lines):
        lineno = index+1
        source_line = '{}  {}'.format(str(lineno).rjust(3), line)
        if lineno == offending_lineno:
            _printHighlighted(source_line)
        else:
            print(source_line)
    print('')
    print('='*80)
    print('')

# -----------------------------------------------------------------------------
def _printHighlighted(line):

    # uses the awesome colorama package
    styled = '{}{}{}{}'.format(colorama.Fore.WHITE,
                               colorama.Back.RED,
                               line,
                               colorama.Style.RESET_ALL)
    print(styled)


# -----------------------------------------------------------------------------
def __stringToBool(value):
    """
    """
    if value.lower() in ('true', '1', 'y', 'yes'):
        return True
    if value.lower() in ('false', '0', 'n', 'no'):
        return False
    raise argparse.ArgumentTypeError('Boolean value expected.')



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
    def _createTestRootFolder(self, settings, test_case):
        """Creates a sandboxed test_root folder inside the 'test_output'
        folder specified in 'settings'. The name of the test_root folder
        will match the name of the TestCase.

        If the test_root folder already exists, it will get deleted
        and recreated.

        However if 'test_output' does not exist it will raise an OSError.

        Args:
            settings (dict)      :  dictionary holding all our settings
            test_case (TestCase) :  TestCase for which to create the test_root
                                    folder.
                                    (default: True)

        Returns:
            (string)        :  absolute path of test_root

        Raises:
            (OSError)       :  if 'test_output' does not exist

        """
        test_output = settings.get('test_output', None)
        if not os.path.exists(test_output):
            raise OSError("Invalid test_output: {}".format(test_output))

        testsuite_root = '{}{}{}'.format(test_output,
                                         os.sep,
                                         test_case.__class__.__name__)
        if os.path.exists(testsuite_root):
           shutil.rmtree(testsuite_root)
        os.makedirs(testsuite_root)
        return testsuite_root

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
                            item.test_root = self._createTestRootFolder(settings, item)
                            return
                elif isinstance(item, unittest.TestSuite):
                    self._prepTestCases(item, settings)


# -----------------------------------------------------------------------------
class TestCase(unittest.TestCase):
    """TestCase that also provides easy access to associated data such
    as 'test_root',  'setttings' or 'context'.

    """
    __test_root = None

    # --------------------------------------------------------------------------
    def __init__(self, methodName='runTest', test_run=False,  *args, **kwargs):
        """
        """
        self.__settings = {}

        if not test_run:
            super(TestCase, self).__init__(methodName, *args, **kwargs)

    # --------------------------------------------------------------------------
    @property
    def test_root(self):
        return TestCase.__test_root
    # --------------------------------------------------------------------------
    @test_root.setter
    def test_root(self, value):
        TestCase.__test_root = value

    # --------------------------------------------------------------------------
    @property
    def settings(self):
        return self.__settings
    # --------------------------------------------------------------------------
    @settings.setter
    def settings(self, value):
        if isinstance(value, dict):
            self.__settings = value
            TestCase.test_output = self.settings.get('test_output', None)

    # --------------------------------------------------------------------------
    @property
    def context(self):
        return self.settings.get('context', 'unknown')

    # --------------------------------------------------------------------------
    @property
    def context_settings(self):
        all_details = self.settings.get('context_details', {})
        return all_details.get(self.context, {})

    # --------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestCase, cls).setUpClass(*args, **kwargs)
        cls.logHeader()

    # --------------------------------------------------------------------------
    @classmethod
    def logHeader(cls):
        """Prints the test header."""
        print('')
        print('-' * 70)
        print("    Running tests in '{}'".format(cls.__name__))
        print('-' * 70)
        sys.stdout.flush()


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    sys.exit(runMain(sys.argv[1:])) # pragma: no cover


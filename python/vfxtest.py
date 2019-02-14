# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import argparse
import json
import os
import copy
import platform
import glob
import subprocess
import sys
import traceback
import unittest
from fnmatch import fnmatch

import coverage

"""

NEXT STEPS
----------

- build and test all our wrapper scripts:
    mayapy
    maya
    hython
    houdini


- move --settings into environment variable
- make sure encode/decode plays nice
- refactor main() once more


*** - serialize full settings dict and pass it in as a command line argument

- append executable index to coverage suffix --> .coverage.python.0
- full test case with two separate child context_details



USAGE
-----

- run 'vfxtest' in any folder:
    - all tests directly inside this folder will be run with the current
      python interpreter
    - all subfolders that contain tests will be found:
        - based on the name of the subfolder and the settings all those
          tests will be run in spawned test run
    - at the end all coverage information will get combined and reported.


- defaults for main 'vfxtest' process:
    clear=True, failfast=True

- defaults for child processes:
    clear=True, failfast=True

- prefs file is assumed in the current folder

- test_output is assumed to be './test_output' (can be set in prefs file)


EXAMPLE USAGES
--------------

    vfxtest.py

    vfxtest.py --target ./subfolder

    vfxtest.py --failfast false --limit 12

    vfxtest.py -t ./python 03

"""


# -----------------------------------------------------------------------------
def main(args=[]):
    """
    """
    # collect and validate settings from arguments and preferences
    settings = collectSettings(args)

    # run test suite in current folder
    runTestSuite(settings)

    if settings['subprocess'] is False:
        # run all child context test suites
        runChildTestSuites(settings)
        # combine coverages
        combineCoverages(settings)

    exit_status = _encodeStatsIntoReturnCode(settings)
    return exit_status

# -----------------------------------------------------------------------------
def _encodeStatsIntoReturnCode(settings):
    """
    """
    # cap all count stats into range 0 - 999
    for item in ['count_files_run', 'count_tests_run', 'count_errors']:
        if settings[item] > 999:
            print("Warning: '{}' run was {} - capping to 999".format(item, settings[item]))
            settings[item] = 999
        elif settings[item] < 0:
            print("Warning: '{}' run was {} - capping to 0".format(item, settings[item]))
            settings[item] = 0

    result = 0
    result += (settings['count_files_run'] * 1000000)
    result += (settings['count_tests_run'] * 1000)
    result += (settings['count_errors'] * 1)

    return result

# -----------------------------------------------------------------------------
def runTestSuite(settings):
    """
    """
    if settings['context'] == 'native' or settings['subprocess'] == True:
        runNative(settings)
        return

    for context in _resolveContextsToRun(settings):

        try:
            # start with copy of settings, update context
            ctxt_settings = copy.deepcopy(settings)
            ctxt_settings['context'] = context

            _storeSettingsInEnv(ctxt_settings)
            wrapper = _getWrapperPath(ctxt_settings)
            executable = _getExecutable(ctxt_settings)

            args = [wrapper,
                    executable,
                    __file__]

            print('')
            print('Wrapper call:')
            print('-------------')
            print('        ' + ' '.join(args))
            print('target folder:')
            print('-------------')
            print('        ' + ctxt_settings['target'])
            print('target context:')
            print('-------------')
            print('        ' + ctxt_settings['context'])
            print('')


            proc = subprocess.Popen(args=args,
                                    bufsize=0,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)

            print ('/'*80)
            while True:
                line = proc.stdout.readline().decode('utf-8')
                if not line:
                    break
                sys.stdout.write(line)
            print ('/'*80)

            proc.wait()
            print('')
            print('Process Return Code: {}'.format(proc.returncode))
            print('')

            _recoverStatsFromReturnCode(settings, proc.returncode)

        except Exception as e:
            raise(e)
        finally:
            _clearSettingsInEnv()


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
        raise FileNotFoundError('Could not find wrapper script:'
                                '\n{}'.format(wrapper_path))

    return wrapper_path

# -----------------------------------------------------------------------------
def runChildTestSuites(settings):
    """
    """
    child_settings = settings.copy()

    target = child_settings['target']
    for item in os.listdir(target):
        if item in child_settings['context_details']:
            item_path = '{}{}{}'.format(target, os.sep, item)
            if os.path.isdir(item_path):
                child_settings['target'] = item_path
                child_settings['context'] = item
                runTestSuite(child_settings)

    settings['count_files_run'] = child_settings['count_files_run']
    settings['count_tests_run'] = child_settings['count_tests_run']
    settings['count_errors'] = child_settings['count_errors']

# -----------------------------------------------------------------------------
def runNative(settings, use_coverage=True):
    """
    """
    if use_coverage:
        cov = _startCoverage(settings)

    suite = _discoverTests(settings)

    runner = unittest.TextTestRunner(failfast=settings['failfast'],
                                     buffer=False)
    # run tests file by file
    for item in suite:
        if (settings['limit'] > 0 and
                settings['count_files_run'] >= settings['limit']):
            print('Reached file limit... Stopping here...')
            break

        print('-'*70)
        # TODO
        # print name of file
        result = runner.run(item)
        settings['count_files_run'] += 1
        settings['count_tests_run'] += result.testsRun
        settings['count_errors'] += len(result.errors) + len(result.failures)

    if use_coverage:
        # --> can't be covered:
        #     coverage does not work inside of another coverage run
        _stopCoverage(settings, cov) # pragma: no cover

# -----------------------------------------------------------------------------
def collectSettings(args=[]):
    """
    """
    # define arguments
    arg_parser = _defineArguments()
    # validate preferences and add to settings
    settings = _getSettings(arg_parser, args)

    return settings


# -----------------------------------------------------------------------------
def resolveContext(settings):
    """
    """
    context = os.path.basename(settings['target'])
    if not context in settings['context_details']:
        context = 'native'
    return context

# -----------------------------------------------------------------------------
def combineCoverages(settings):
    """
    """
    test_output = settings['test_output']
    data_file='{}/.coverage'.format(test_output)
    cov = coverage.Coverage(data_file=data_file)
    cov.combine()
    cov.save()
    try:
        cov.report()
        cov.html_report(directory='{}/_coverage_html'.format(test_output))
    except coverage.misc.CoverageException as e:
        print('Coverage: no data to report')

# -----------------------------------------------------------------------------
def _defineArguments():
    """
    """
    parser = argparse.ArgumentParser(description='Run test suite(s):')

    parser.add_argument('-t', '--target', metavar='', type=str, default='.',
                        help='target folder path (defaults to current working directory)')
    parser.add_argument('-f', '--failfast', type=__stringToBool, default=True,
                        help='Stops execution of test suite on first error.')
    parser.add_argument('-p', '--prefs', metavar='', type=str, default=None,
                        help="path of the .prefs file to use. "
                             ""
                             "Defaults to 'test.prefs' in:"
                             "    - the current working directory"
                             "    - the one root dir of the current working directory")
    parser.add_argument('-l', '--limit', metavar='', type=int, default=0,
                        help='limits the number of test files that get executed.')
    parser.add_argument('filter_tokens', nargs='*', type=str,
                        help='specify tokens that filter down the test files by name.')

    return parser

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

        # use settings in environment if present, fall back to prefs file
        if 'vfxtest_settings' in os.environ:
            _recoverSettingsFromEnv(settings)
        else:
            _readPrefs(settings)

        # make all paths absolute
        for key in ['prefs', 'target', 'test_output']:
            settings[key] = os.path.abspath(settings[key])

        # create 'test_output' if needed, but never create it's parent folder
        test_output = settings['test_output']
        parent_folder = os.path.dirname(test_output)
        if not os.path.exists(parent_folder):
            raise FileNotFoundError('Folder does not exist:\n'
                                    '{}'.format(parent_folder))
        if not os.path.exists(test_output):
            os.makedirs(test_output)

    except Exception as e:
        print('Failed to read and conform preferences:\n{}\n{}'.format(e, traceback.format_exc()))
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
def _readPrefs(settings):
    """
    """
    # prefer 'test.prefs' in current folder, fallback to parent folder
    if settings['prefs'] is None:
        if os.path.exists('./test.prefs'):
            settings['prefs'] = './test.prefs'
        else:
            settings['prefs'] = '../test.prefs'

    # read out prefs and strip comments
    with open(settings['prefs'], 'r') as f:
        lines = []
        for line in f.readlines():
            tokens = line.split('#')
            lines.append(tokens[0])
    # interpret as json and add to settings
    prefs = json.loads('\n'.join(lines))
    settings.update(prefs)
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
        wrapper_scripts = '{}{}wrapper_scripts'.format(os.path.dirname(__file__), os.sep)
        settings['wrapper_scripts'] = wrapper_scripts

    if not 'count_files_run' in settings:
        settings['count_files_run'] = 0
    if not 'count_tests_run' in settings:
        settings['count_tests_run'] = 0
    if not 'count_errors' in settings:
        settings['count_errors'] = 0

    settings['cwd'] = os.getcwd()
    settings['context'] = resolveContext(settings)

    settings['subprocess'] = False




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
    """
    """

    # -------------------------------------------------------------------------
    def _match_path(self, path, full_path, pattern):
        """
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
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:])) # pragma: no cover


# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import argparse
import json
import os
import sys
import traceback

"""

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

- test_root is assumed to be './test_root' (can be set in prefs file)


EXAMPLE USAGES
--------------

    vfxtest.py

    vfxtest.py --target ./subfolder

    vfxtest.py --failfast false --limit 12

    vfxtest.py -t ./python 03

"""


# -----------------------------------------------------------------------------
def main(args):
    """
    """
    # collect and validate settings from arguments and preferences
    settings = collectSettings(args)

    # DBG
    for key in settings:
        print('{} :    {}'.format(key.ljust(15), settings[key]))


# -----------------------------------------------------------------------------
def collectSettings(args=[]):
    """
    """
    # define arguments
    parser = argparse.ArgumentParser(description='Run test suite(s):')

    parser.add_argument('-t', '--target', metavar='', type=str, default='.',
                        help='target folder path (defaults to current working directory)')
    parser.add_argument('-f', '--failfast', type=__stringToBool, default=True,
                        help='Stops execution of test suite on first error.')
    parser.add_argument('-p', '--prefs', metavar='', type=str, default='./test.prefs',
                        help="path of the .prefs file to use. "
                             ""
                             "Defaults to 'test.prefs' in:"
                             "    - the current working directory"
                             "    - the one root dir of the current working directory")
    parser.add_argument('-l', '--limit', metavar='', type=int, default=0,
                        help='limits the number of test files that get executed.')
    parser.add_argument('filter_tokens', nargs='*', type=str,
                        help='specify tokens that filter down the test files by name.')

    # receive valid arguments as dictionary
    settings = vars(parser.parse_args(args))

    # validate preferences and add to settings
    _addValidatedPrefsToSettings(settings)

    return settings

# -----------------------------------------------------------------------------
def _addValidatedPrefsToSettings(settings):
    """
    """
    try:
        # read out prefs and strip comments
        with open(settings['prefs'], 'r') as f:
            lines = []
            for line in f.readlines():
                tokens = line.split('#')
                lines.append(tokens[0])
        # interpret as json and add to settings
        prefs = json.loads('\n'.join(lines))
        settings.update(prefs)

        settings['cwd'] = os.getcwd()
        if not 'test_root' in settings:
            settings['test_root'] = './test_root'

        # make all paths absolute
        for key in ['prefs', 'target', 'test_root']:
            settings[key] = os.path.abspath(settings[key])

        # create 'test_root' if needed, but never create it's parent folder
        test_root = settings['test_root']
        parent_folder = os.path.dirname(test_root)
        if not os.path.exists(parent_folder):
            raise FileNotFoundError('Folder does not exist:\n'
                                    '{}'.format(parent_folder))
        if not os.path.exists(test_root):
            os.makedirs(test_root)

    except Exception as e:
        print('Failed to read and conform preferences:'
               '\n\n{}'
               '\n\n{}'.format(e, traceback.format_exc()))
        raise(SystemExit)

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
if __name__ == '__main__':
    main(sys.argv[1:]) # pragma: no cover


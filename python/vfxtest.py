# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import sys
import os
import argparse


# -----------------------------------------------------------------------------
def main(args):
    """
    """
    settings = _parseArgs(args)

    # DBG
    for key in settings:
        print('{} :    {}'.format(key.ljust(15), settings[key]))


# -----------------------------------------------------------------------------
def _parseArgs(args):
    """
    """

    # TODO
    #       root folder name tests and run-all=None: --> run-all=True
    #       root folder name anything else and run-all=None: --> run-all=False

    #       explicit prefs is None
    #           try to find prefs file in cwd: --> use it
    #           try to find prefs file in parent folder: --> use it


    parser = argparse.ArgumentParser(description='Run test suite(s):')

    parser.add_argument('filter_tokens', nargs='*', type=str,
                        help='specify tokens that filter down the test files by name.')
    parser.add_argument('-ra', '--run-all', type=__stringToBool, default=None,
                        help='Runs all test suites in all subfolders of '
                             'the current working directory.')
    parser.add_argument('-c', '--clear', type=__stringToBool, default=None,
                        help='Clears old coverage reports.')
    parser.add_argument('-f', '--failfast', type=__stringToBool, default=None,
                        help='Stops execution of test suite on first error.')
    parser.add_argument('-t', '--target', metavar='', type=str, default='.',
                        help='target folder path (defaults to current working directory)')
    parser.add_argument('-p', '--prefs', metavar='', type=str, default='./vfxtest.prefs',
                        help="path of the .prefs file to use. "
                             ""
                             "Defaults to 'vfxtest.prefs' in:"
                             "    - the current working directory"
                             "    - the one root dir of the current working directory")
    parser.add_argument('-l', '--limit', metavar='', type=int, default=0,
                        help='limits the number of test files that get executed.')

    settings = vars(parser.parse_args(args))

    # set sensible defaults based the 'run-all' state
    # (respects explicit user argument values)
    if settings['failfast'] is None:
        settings['failfast'] = True

    if settings['clear'] is None:
        if settings['run_all']:
            settings['clear'] = True
        else:
            settings['clear'] = False


    settings['cwd'] = os.getcwd()
    settings['prefs'] = os.path.abspath(settings['prefs'])
    settings['target'] = os.path.abspath(settings['target'])

    # read out prefs file
    try:
        _readPrefs(settings)
    except Exception as e:
        parser.error('Invalid .prefs file: {}'.format(settings['prefs']))


    return settings

# -----------------------------------------------------------------------------
def _readPrefs(settings):
    """
    """
    # TODO: read out prefs
    #       store everything in settings
    #       raise exception on error
    settings['proof'] = 'yeah'
    # raise Exception()

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
    main(sys.argv[1:])


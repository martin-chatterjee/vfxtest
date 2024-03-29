#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2022, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import os
import sys
import platform
import unittest
import shutil
import argparse

import coverage


# -----------------------------------------------------------------------------
def main(folder_path, test_dccs, fail_fast, log_output, cover_testfiles):
    """"""
    test_sandbox = os.path.abspath(os.path.join(folder_path, 'test_sandbox'))
    python = os.path.abspath(os.path.join(folder_path, '..'))
    sys.path.append(test_sandbox)
    sys.path.append(python)
    os.environ['PYTHONPATH'] = os.pathsep.join([test_sandbox, python])

    # Cleanup.
    dot_output = os.path.abspath(os.path.join(folder_path, '.output'))
    if os.path.exists(dot_output):
        shutil.rmtree(dot_output)
    omit = []
    if not cover_testfiles:
        omit.append('test*.py')
        omit.append('dcc_test*.py')
    # add support for Python major version 'no-cover' support:
    # --> no coverage on python 2.x:
    #                                # pragma: no cover_2
    # --> no coverage on python 3.x:
    #                                # pragma: no cover_3
    cov = coverage.Coverage(omit=omit)
    major = platform.python_version_tuple()[0]
    versioned_exclude = (
        r'#\s*(pragma|PRAGMA)[:\s]?\s*' r'(no|NO)\s*(cover_{}|COVER_{})'
    ).format(major, major)
    cov.exclude(versioned_exclude, which='exclude')
    cov.start()

    # Disable all OutputTraps, if necessary.
    if log_output:
        import output_trap
        output_trap.BYPASS = log_output

    # Prepare and configure.
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(failfast=fail_fast, buffer=(not log_output))

    # Discover and run main test suite.
    suite = loader.discover(folder_path, pattern='test*.py')
    runner.run(suite)

    # Discover and tests requiring DCC licenses.
    if test_dccs is True:
        dcc_suite = loader.discover(folder_path, pattern='dcc_test*.py')
        runner.run(dcc_suite)
    cov.stop()
    cov.save()
    cov.report()
    cov.html_report(directory='_html_coverage')


# -----------------------------------------------------------------------------
def constructParser():
    """Return argument parser."""
    parser = argparse.ArgumentParser(
        prog='run_all_tests',
        description=('Run test suite for vfxtest.'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        '-dccs',
        '--test-dccs',
        help='Also test dcc related code. '
        '(Needs a valid Maya and Houdini license, '
        'and an interactive graphical environment.)',
        action='store_true',
    )

    parser.add_argument(
        '-lo',
        '--log-output',
        help='Log all internal output to console.',
        action='store_true',
    )

    parser.add_argument(
        '-coe',
        '--continue-on-error',
        help='Continue test suite on error.',
        action='store_true',
    )

    parser.add_argument(
        '-ctf',
        '--cover-testfiles',
        help='Include Coverage of test files.',
        action='store_true',
    )

    return parser


# -----------------------------------------------------------------------------
def commandLine(arguments):
    """Handle Command line argument parsing."""
    parser = constructParser()
    namespace = parser.parse_args(arguments)

    main(
        folder_path='.',
        test_dccs=namespace.test_dccs,
        fail_fast=(not namespace.continue_on_error),
        log_output=namespace.log_output,
        cover_testfiles=namespace.cover_testfiles,
    )


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    commandLine(sys.argv[1:])

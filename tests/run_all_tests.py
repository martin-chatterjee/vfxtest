#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import os
import sys
import platform
import glob
import unittest
import shutil

import coverage

# -----------------------------------------------------------------------------
def main(folder_path, failfast, print_to_stdout, include_test_files):
    """
    """
    test_sandbox = os.path.abspath('./test_sandbox')
    python = os.path.abspath('..')
    sys.path.append(test_sandbox)
    sys.path.append(python)
    os.environ['PYTHONPATH'] = os.pathsep.join([test_sandbox, python])

    # cleanup
    if os.path.exists('./.output'):
        shutil.rmtree('./.output')

    omit = []
    if include_test_files is False:
        omit.append('test*.py')
    # add support for Python major version 'no-cover' support:
    # --> no coverage on python 2.x:
    #                                # pragma: no cover_2
    # --> no coverage on python 3.x:
    #                                # pragma: no cover_3
    cov = coverage.Coverage(omit=omit)
    major = platform.python_version_tuple()[0]
    versioned_exclude = (r'#\s*(pragma|PRAGMA)[:\s]?\s*'
                         r'(no|NO)\s*(cover_{}|COVER_{})').format(major, major)
    cov.exclude(versioned_exclude, which='exclude')
    cov.start()

    # discover all tests and run them
    loader = unittest.TestLoader()
    suite = loader.discover(folder_path)

    runner = unittest.TextTestRunner(failfast=failfast,
                                     buffer=(not print_to_stdout))

    result = runner.run(suite)

    cov.stop()
    cov.save()
    cov.report()
    cov.html_report(directory='_html_coverage')



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    # pass in any argument to enable 'print to stdout'
    print_to_stdout = False
    if len(sys.argv) > 1:
        print_to_stdout = True

    main(folder_path='.',
         failfast=True,
         print_to_stdout=print_to_stdout,
         include_test_files=False)

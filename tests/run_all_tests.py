# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import os
import sys
import glob
import unittest

import coverage

# -----------------------------------------------------------------------------
def main(folder_path, failfast, print_to_stdout, include_test_files):
    """
    """
    sys.path.append(os.path.abspath('./test_setting'))
    print('>>> ' + sys.path[-1])
    omit = []
    if not include_test_files:
        omit.append('test*.py')

    cov = coverage.Coverage(omit=omit)
    cov.start()

    # discover all tests and run them
    loader = unittest.TestLoader()
    suite = loader.discover(folder_path)

    runner = unittest.TextTestRunner(failfast=failfast,
                                     stream=sys.stdout,
                                     buffer=(not print_to_stdout))

    result = runner.run(suite)

    cov.stop()
    cov.save()
    cov.report()
    cov.html_report(directory='_html_coverage')



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main(folder_path='.',
         failfast=True,
         print_to_stdout=False,
         include_test_files=False)

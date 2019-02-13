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

    # # clean up all data files if clear == True
    # for data_file in glob.glob('./.coverage*'):
    #     os.remove(data_file)


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

    # stats = [0, 0, 0]
    # for item in suite:
    #     print('-'*70)
    #     result = runner.run(item)
    #     stats[0] += result.testsRun
    #     stats[1] += len(result.errors)
    #     stats[2] += len(result.failures)

    cov.stop()
    cov.save()

    # print('')
    # print('-'*70)
    # print('STATISTICS')
    # print('')
    # print('test run: {}   errors: {}   failures: {}'.format(result.testsRun,
    #                                                         len(result.errors),
    #                                                         len(result.failures)))
    # print('-'*70)

    cov.report()
    cov.html_report(directory='_html_coverage')



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main(folder_path='.',
         failfast=True,
         print_to_stdout=False,
         include_test_files=False)

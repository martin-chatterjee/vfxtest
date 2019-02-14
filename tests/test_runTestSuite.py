# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import json

import vfxtest


# -----------------------------------------------------------------------------
class RunTestSuiteTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpOnce(cls):
        """
        """
    # -------------------------------------------------------------------------
    @classmethod
    def tearDownOnce(cls):
        """
        """
    # -------------------------------------------------------------------------
    def setUp(self):
        """
        """
        self.cwd = os.getcwd()
        os.chdir('./test_sandbox')
    # -------------------------------------------------------------------------
    def tearDown(self):
        """
        """
        os.chdir(self.cwd)


    # -------------------------------------------------------------------------
    def test01_runTestSuite_native_runs_successfully(self):

        settings = vfxtest.collectSettings()
        vfxtest.runTestSuite(settings=settings)

        self.assertEqual(settings['count_files_run'], 2)
        self.assertEqual(settings['count_tests_run'], 6)
        self.assertEqual(settings['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test02_runTestSuite_single_context_runs_successfully(self):

        settings = vfxtest.collectSettings()

        cov_file = os.path.abspath('{}/.coverage.python3.x'.format(settings['test_output']))
        if os.path.exists(cov_file):
            os.remove(cov_file)

        settings['context'] = 'python3.x'

        vfxtest.runTestSuite(settings=settings)
        self.assertEqual(settings['count_files_run'], 2)
        self.assertEqual(settings['count_tests_run'], 6)
        self.assertEqual(settings['count_errors'], 0)
        self.assertTrue(os.path.exists(cov_file))

    # -------------------------------------------------------------------------
    def test03_runTestSuite_nested_context_runs_successfully(self):

        settings = vfxtest.collectSettings()

        cov_file_3 = os.path.abspath('{}/.coverage.python3.x'.format(settings['test_output']))
        if os.path.exists(cov_file_3):
            os.remove(cov_file_3)
        cov_file_2 = os.path.abspath('{}/.coverage.python2.x'.format(settings['test_output']))
        if os.path.exists(cov_file_2):
            os.remove(cov_file_2)

        settings['context'] = 'python'

        vfxtest.runTestSuite(settings=settings)

        self.assertEqual(settings['count_files_run'], 4)
        self.assertEqual(settings['count_tests_run'], 12)
        self.assertEqual(settings['count_errors'], 0)
        self.assertTrue(os.path.exists(cov_file_3))
        self.assertTrue(os.path.exists(cov_file_2))

    # -------------------------------------------------------------------------
    def test04_runTestSuite_wrapper_script_not_found_throws_FileNotFoundError(self):

        settings = vfxtest.collectSettings()
        settings['context'] = 'context_without_wrapper_script'

        with self.assertRaises(FileNotFoundError):
            vfxtest.runTestSuite(settings=settings)


    # -------------------------------------------------------------------------
    def test05_encodeStatsIntoReturnCode_works_as_expected(self):

        empty = {}
        empty['count_files_run'] = 0
        empty['count_tests_run'] = 0
        empty['count_errors'] = 0
        settings = empty.copy()
        settings['count_files_run'] = 13
        settings['count_tests_run'] = 26
        settings['count_errors'] = 39

        exitcode = vfxtest._encodeStatsIntoReturnCode(settings)

        proof = empty.copy()
        vfxtest._recoverStatsFromReturnCode(proof, exitcode)
        self.assertEqual(settings, proof)

        settings['count_files_run'] = 0
        settings['count_tests_run'] = 0
        settings['count_errors'] = 0

        exitcode = vfxtest._encodeStatsIntoReturnCode(settings)

        proof = empty.copy()
        vfxtest._recoverStatsFromReturnCode(proof, exitcode)
        self.assertEqual(settings, proof)

        settings['count_files_run'] = 999
        settings['count_tests_run'] = 998
        settings['count_errors'] = 997

        exitcode = vfxtest._encodeStatsIntoReturnCode(settings)

        proof = empty.copy()
        vfxtest._recoverStatsFromReturnCode(proof, exitcode)
        self.assertEqual(settings, proof)

    # -------------------------------------------------------------------------
    def test06_encodeStatsIntoReturnCode_caps_illegal_stats_to_range_0_to_999(self):

        empty = {}
        empty['count_files_run'] = 0
        empty['count_tests_run'] = 0
        empty['count_errors'] = 0
        settings = empty.copy()
        settings['count_files_run'] = 1000
        settings['count_tests_run'] = 999
        settings['count_errors'] = 202020

        exitcode = vfxtest._encodeStatsIntoReturnCode(settings)

        proof = empty.copy()
        vfxtest._recoverStatsFromReturnCode(proof, exitcode)
        self.assertEqual(proof['count_files_run'], 999)
        self.assertEqual(proof['count_tests_run'], 999)
        self.assertEqual(proof['count_errors'], 999)

        settings['count_files_run'] = -13
        settings['count_tests_run'] = -26
        settings['count_errors'] = -27

        exitcode = vfxtest._encodeStatsIntoReturnCode(settings)

        proof = empty.copy()
        vfxtest._recoverStatsFromReturnCode(proof, exitcode)
        self.assertEqual(proof['count_files_run'], 0)
        self.assertEqual(proof['count_tests_run'], 0)
        self.assertEqual(proof['count_errors'], 0)

# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import json

import vfxtest


# -----------------------------------------------------------------------------
class RunStandaloneTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        """
        """
    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):
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
    def test01_runStandalone_filtered_works_as_expected(self):

        returnvalue = vfxtest.runStandalone(['01', '03'])

        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 3)
        self.assertEqual(proof['count_tests_run'], 9)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test02_runStandalone_limit_works_as_expected(self):

        returnvalue = vfxtest.runStandalone(['--limit', '2'])
        print(returnvalue)
        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 2)
        self.assertEqual(proof['count_tests_run'], 6)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test03_runStandalone_with_empty_filtered_result_works_as_expected(self):

        returnvalue = vfxtest.runStandalone(['asdfg',])
        print(returnvalue)
        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 0)
        self.assertEqual(proof['count_tests_run'], 0)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test04_runStandalone_works_as_expected(self):

        returnvalue = vfxtest.runStandalone()

        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 4)
        self.assertEqual(proof['count_tests_run'], 12)
        self.assertEqual(proof['count_errors'], 0)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

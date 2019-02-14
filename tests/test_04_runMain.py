# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import json

import vfxtest


# -----------------------------------------------------------------------------
class RunMainTestCase(unittest.TestCase):

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
    def test01_runMain_filtered_works_as_expected(self):

        returnvalue = vfxtest.main(['01', '03'])

        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 3)
        self.assertEqual(proof['count_tests_run'], 9)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test02_runMain_limit_works_as_expected(self):

        returnvalue = vfxtest.main(['--limit', '2'])
        print(returnvalue)
        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 2)
        self.assertEqual(proof['count_tests_run'], 6)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test03_runMain_with_empty_filtered_result_works_as_expected(self):

        returnvalue = vfxtest.main(['asdfg',])
        print(returnvalue)
        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 0)
        self.assertEqual(proof['count_tests_run'], 0)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test04_runMain_works_as_expected(self):

        returnvalue = vfxtest.main()

        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 4)
        self.assertEqual(proof['count_tests_run'], 12)
        self.assertEqual(proof['count_errors'], 0)



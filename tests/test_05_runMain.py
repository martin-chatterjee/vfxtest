# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import sys
import json
# try:
#     import unittest.mock as mock
# except ImportError:
#     import mock

import vfxtest
mock = vfxtest.mock

# -----------------------------------------------------------------------------
class RunMainTestCase(unittest.TestCase):

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
    def test01_runMain_filtered_works_as_expected(self):

        returnvalue = vfxtest.runMain(['01', '03'])

        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 3)
        self.assertEqual(proof['count_tests_run'], 9)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test02_runMain_limit_works_as_expected(self):

        returnvalue = vfxtest.runMain(['--limit', '2'])
        print(returnvalue)
        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 2)
        self.assertEqual(proof['count_tests_run'], 6)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test03_runMain_with_empty_filtered_result_works_as_expected(self):

        returnvalue = vfxtest.runMain(['asdfg',])
        print(returnvalue)
        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 0)
        self.assertEqual(proof['count_tests_run'], 0)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test04_runMain_works_as_expected(self):

        returnvalue = vfxtest.runMain()

        proof = vfxtest.collectSettings()
        vfxtest._recoverStatsFromReturnCode(proof, returnvalue)
        self.assertEqual(proof['count_files_run'], 5)
        self.assertEqual(proof['count_tests_run'], 15)
        self.assertEqual(proof['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test05_initContext_recognizes_and_initializes_mayapy_session(self):

        settings = vfxtest.collectSettings()
        settings['context'] = 'mayapy'

        with mock.patch.dict(sys.modules, {'maya': mock.Mock()}):
            with mock.patch.dict(sys.modules, {'maya.standalone': mock.Mock()}):
                vfxtest.initContext(settings)

    # -------------------------------------------------------------------------
    def test06_initContext_logs_ands_swallows_any_exception(self):

        settings = vfxtest.collectSettings()
        settings['context'] = 'mayapy'

        vfxtest.initContext(settings)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

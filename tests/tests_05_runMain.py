# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import sys
import json

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

        proof = vfxtest.runMain(['01', '03'])

        self.assertEqual(proof['files_run'], 3)
        self.assertEqual(proof['tests_run'], 9)
        self.assertEqual(proof['errors'], 0)

    # -------------------------------------------------------------------------
    def test02_runMain_globallimit_works_as_expected(self):

        proof = vfxtest.runMain(['--globallimit', '2'])
        self.assertEqual(proof['files_run'], 2)
        self.assertEqual(proof['tests_run'], 6)
        self.assertEqual(proof['errors'], 0)

    # -------------------------------------------------------------------------
    def test03_runMain_with_empty_filtered_result_works_as_expected(self):

        proof = vfxtest.runMain(['asdfg',])
        self.assertEqual(proof['files_run'], 0)
        self.assertEqual(proof['tests_run'], 0)
        self.assertEqual(proof['errors'], 0)

    # -------------------------------------------------------------------------
    def test04_runMain_works_as_expected(self):

        proof = vfxtest.runMain()
        self.assertEqual(proof['files_run'], 7)
        self.assertEqual(proof['tests_run'], 21)
        self.assertEqual(proof['errors'], 0)

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

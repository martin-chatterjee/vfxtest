# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import json

import vfxtest
mock = vfxtest.mock


# -----------------------------------------------------------------------------
class RunTestSuiteTestCase(unittest.TestCase):

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
    def test01_runTestSuite_native_runs_successfully(self):

        settings = vfxtest.collectSettings()
        vfxtest.runTestSuite(settings=settings)

        self.assertEqual(settings['files_run'], 2)
        self.assertEqual(settings['tests_run'], 6)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test02_runTestSuite_single_context_runs_successfully(self):

        settings = vfxtest.collectSettings()

        cov_file = os.path.abspath('{}/.coverage.python3.x'.format(settings['test_output']))
        if os.path.exists(cov_file):
            os.remove(cov_file)

        settings['context'] = 'python3.x'
        settings['debug_mode'] = True

        vfxtest.runTestSuite(settings=settings)
        self.assertEqual(settings['files_run'], 2)
        self.assertEqual(settings['tests_run'], 6)
        self.assertEqual(settings['errors'], 0)
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

        self.assertEqual(settings['files_run'], 4)
        self.assertEqual(settings['tests_run'], 12)
        self.assertEqual(settings['errors'], 0)
        self.assertTrue(os.path.exists(cov_file_3))
        self.assertTrue(os.path.exists(cov_file_2))

    # -------------------------------------------------------------------------
    def test04_runTestSuite_wrapper_script_not_found_raises_OSError(self):

        settings = vfxtest.collectSettings()
        settings['context'] = 'context_without_wrapper_script'

        with self.assertRaises(OSError):
            vfxtest.runTestSuite(settings=settings)


    # -------------------------------------------------------------------------
    def test05_runTestSuite_raises_SystemExit_on_child_proc_exit_code_bigger_than_zero(self):

        settings = vfxtest.collectSettings()

        settings['context'] = 'python3.x'
        settings['debug_mode'] = True

        with self.assertRaises(SystemExit):
            with mock.patch('subprocess.Popen.wait', return_value=13):
                vfxtest.runTestSuite(settings=settings)

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

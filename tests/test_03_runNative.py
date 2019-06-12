# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import shutil

import vfxtest


# -----------------------------------------------------------------------------
class RunNativeTestCase(unittest.TestCase):

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
    def test01_runNative_runs_successfully(self):

        settings = vfxtest.collectSettings()
        vfxtest.prepareEnvironment(settings)

        cov_file = os.path.abspath('{}/.coverage.native'.format(settings['output_folder']))
        if os.path.exists(cov_file):
            os.remove(cov_file)
        vfxtest.runNative(settings=settings, use_coverage=True)

        self.assertEqual(settings['files_run'], 2)
        self.assertEqual(settings['tests_run'], 6)
        self.assertEqual(settings['errors'], 0)
        self.assertTrue(os.path.exists(cov_file))

    # -------------------------------------------------------------------------
    def test02_runNative_with_filter_tokens_runs_successfully(self):

        settings = vfxtest.collectSettings(['--target', '.', '_01',])
        vfxtest.prepareEnvironment(settings)

        vfxtest.runNative(settings=settings, use_coverage=False)
        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test03_combineCoverages_works_as_expected(self):

        settings = vfxtest.collectSettings(['_02',])
        vfxtest.prepareEnvironment(settings)

        settings['context'] = 'differentContext'
        vfxtest.runNative(settings=settings)
        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertTrue(os.path.exists('{}/.coverage.differentContext'.format(settings['output_folder'])))

        settings = vfxtest.collectSettings()
        vfxtest.combineCoverages(settings)

        self.assertFalse(os.path.exists('{}/.coverage.differentContext'.format(settings['output_folder'])))
        self.assertTrue(os.path.exists('{}/.coverage'.format(settings['output_folder'])))

    # -------------------------------------------------------------------------
    def test04_resolveContext_defaults_to_native(self):

        settings = vfxtest.collectSettings()
        vfxtest.prepareEnvironment(settings)

        self.assertEqual(settings['context'], 'native')

    # -------------------------------------------------------------------------
    def test05_resolveContext_defaults_to_native(self):

        settings = vfxtest.collectSettings(['--target','./python2.x'])
        vfxtest.prepareEnvironment(settings)

        self.assertEqual(settings['context'], 'python2.x')

    # -------------------------------------------------------------------------
    def test06_runNative_with_limit_works_as_expected(self):

        settings = vfxtest.collectSettings(['--limit', '1'])
        vfxtest.prepareEnvironment(settings)

        vfxtest.runNative(settings=settings, use_coverage=False)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test07_runNative_in_subfolder_works_as_expected(self):

        settings = vfxtest.collectSettings(['--target', './python'])
        vfxtest.prepareEnvironment(settings)

        vfxtest.runNative(settings=settings)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertEqual(settings['errors'], 0)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

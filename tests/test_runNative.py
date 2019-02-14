# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

import vfxtest


# -----------------------------------------------------------------------------
class RunNativeTestCase(unittest.TestCase):

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
    def test01_runNative_runs_successfully(self):

        # if 'vfxtest_settings' in os.environ:
        #     os.environ.pop('vfxtest_settings')
        settings = vfxtest.collectSettings()

        cov_file = os.path.abspath('{}/.coverage.native'.format(settings['test_output']))
        if os.path.exists(cov_file):
            os.remove(cov_file)
        print('WRD  {}'.format(cov_file))
        print('xxx {}'.format(settings['context']))
        vfxtest.runNative(settings=settings, use_coverage=True)

        self.assertEqual(settings['count_files_run'], 2)
        self.assertEqual(settings['count_tests_run'], 6)
        self.assertEqual(settings['count_errors'], 0)
        self.assertTrue(os.path.exists(cov_file))

    # -------------------------------------------------------------------------
    def test02_runNative_with_filter_tokens_runs_successfully(self):

        settings = vfxtest.collectSettings(['--target', '.', '_01',])
        vfxtest.runNative(settings=settings, use_coverage=False)
        self.assertEqual(settings['count_files_run'], 1)
        self.assertEqual(settings['count_tests_run'], 3)
        self.assertEqual(settings['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test03_combineCoverages_works_as_expected(self):

        settings = vfxtest.collectSettings(['_02',])
        settings['context'] = 'differentContext'
        vfxtest.runNative(settings=settings)
        self.assertEqual(settings['count_files_run'], 1)
        self.assertEqual(settings['count_tests_run'], 3)
        self.assertTrue(os.path.exists('{}/.coverage.differentContext'.format(settings['test_output'])))

        settings = vfxtest.collectSettings()
        vfxtest.combineCoverages(settings)

        self.assertFalse(os.path.exists('{}/.coverage.differentContext'.format(settings['test_output'])))
        self.assertTrue(os.path.exists('{}/.coverage'.format(settings['test_output'])))

    # -------------------------------------------------------------------------
    def test04_resolveContext_defaults_to_native(self):
        settings = vfxtest.collectSettings()
        self.assertEqual(settings['context'], 'native')

    # -------------------------------------------------------------------------
    def test05_resolveContext_defaults_to_native(self):
        settings = vfxtest.collectSettings(['--target','./python2.x'])
        self.assertEqual(settings['context'], 'python2.x')

    # -------------------------------------------------------------------------
    def test06_runNative_with_limit_works_as_expected(self):

        settings = vfxtest.collectSettings(['--limit', '1'])

        vfxtest.runNative(settings=settings, use_coverage=False)

        self.assertEqual(settings['count_files_run'], 1)
        self.assertEqual(settings['count_tests_run'], 3)
        self.assertEqual(settings['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test07_runNative_in_subfolder_works_as_expected(self):

        settings = vfxtest.collectSettings(['--target', './python2.x'])

        vfxtest.runNative(settings=settings)

        self.assertEqual(settings['count_files_run'], 1)
        self.assertEqual(settings['count_tests_run'], 3)
        self.assertEqual(settings['count_errors'], 0)

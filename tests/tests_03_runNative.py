# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2022, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import shutil

import vfxtest

from vfxtest import mock

from output_trap import OutputTrap


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
        vfxtest.prepareTestEnvironment(settings)

        cov_file = os.path.abspath('{}/.coverage.native'.format(settings['output_folder']))
        if os.path.exists(cov_file):
            os.remove(cov_file)

        with OutputTrap():
            vfxtest.runNative(settings=settings, use_coverage=True)

        self.assertEqual(settings['files_run'], 2)
        self.assertEqual(settings['tests_run'], 6)
        self.assertEqual(settings['errors'], 0)
        self.assertTrue(os.path.exists(cov_file))

    # -------------------------------------------------------------------------
    def test02_runNative_with_filter_tokens_runs_successfully(self):

        settings = vfxtest.collectSettings(['--target', '.', '_01',])
        vfxtest.prepareTestEnvironment(settings)

        with OutputTrap():
            vfxtest.runNative(settings=settings, use_coverage=False)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test03_combineCoverages_works_as_expected(self):

        settings = vfxtest.collectSettings(['_02',])
        vfxtest.prepareTestEnvironment(settings)

        settings['context'] = 'differentContext'

        with OutputTrap():
            vfxtest.runNative(settings=settings)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertTrue(os.path.exists('{}/.coverage.differentContext'.format(settings['output_folder'])))

        with OutputTrap():
            settings = vfxtest.collectSettings()
            vfxtest.combineCoverages(settings)

        self.assertFalse(os.path.exists('{}/.coverage.differentContext'.format(settings['output_folder'])))
        self.assertTrue(os.path.exists('{}/.coverage'.format(settings['output_folder'])))

    # -------------------------------------------------------------------------
    def test04_resolveContext_defaults_to_native(self):

        settings = vfxtest.collectSettings()
        vfxtest.prepareTestEnvironment(settings)

        self.assertEqual(settings['context'], 'native')

    # -------------------------------------------------------------------------
    def test05_resolveContext_defaults_to_native(self):

        settings = vfxtest.collectSettings(['--target','./python2.x'])
        vfxtest.prepareTestEnvironment(settings)

        self.assertEqual(settings['context'], 'python2.x')

    # -------------------------------------------------------------------------
    def test06_runNative_with_globallimit_works_as_expected(self):

        settings = vfxtest.collectSettings(['--globallimit', '1'])
        vfxtest.prepareTestEnvironment(settings)

        with OutputTrap():
            vfxtest.runNative(settings=settings, use_coverage=False)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test07_runNative_with_limit_works_as_expected(self):

        settings = vfxtest.collectSettings(['--limit', '1'])
        vfxtest.prepareTestEnvironment(settings)

        with OutputTrap():
            vfxtest.runNative(settings=settings, use_coverage=False)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test08_runNative_in_subfolder_works_as_expected(self):

        settings = vfxtest.collectSettings(['--target', './python'])
        vfxtest.prepareTestEnvironment(settings)

        with OutputTrap():
            vfxtest.runNative(settings=settings)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 3)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test09_runNative_no_tests_at_all_does_not_try_to_report_coverage(self):

        settings = vfxtest.collectSettings(['--target', './python'])
        settings['filter_tokens'].append('does-not-get-matched')
        vfxtest.prepareTestEnvironment(settings)

        with OutputTrap():
            vfxtest.runNative(settings=settings)

        self.assertEqual(settings['files_run'], 0)
        self.assertEqual(settings['tests_run'], 0)
        self.assertEqual(settings['errors'], 0)

    # -------------------------------------------------------------------------
    def test10_runNative_with_failfast_stops_on_first_error(self):

        settings = vfxtest.collectSettings(['--failfast', 'true'])

        vfxtest.prepareTestEnvironment(settings)
        with OutputTrap():
            with mock.patch('awesome_module.buzz', return_value=1):
                vfxtest.runNative(settings=settings, use_coverage=False)

        self.assertEqual(settings['files_run'], 1)
        self.assertEqual(settings['tests_run'], 2)
        self.assertEqual(settings['errors'], 1)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

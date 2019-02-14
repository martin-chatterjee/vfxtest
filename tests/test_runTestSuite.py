# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

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
        os.chdir('./test_setting')
    # -------------------------------------------------------------------------
    def tearDown(self):
        """
        """
        os.chdir(self.cwd)


    # -------------------------------------------------------------------------
    def test01_runTestSuite_native_runs_successfully(self):

        settings = vfxtest.collectSettings()
        vfxtest.runTestSuite(settings=settings)

        self.assertEqual(settings['count_run'], 6)
        self.assertEqual(settings['count_failures'], 0)
        self.assertEqual(settings['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test00002_runTestSuite_single_context_runs_successfully(self):

        settings = vfxtest.collectSettings()
        settings['context'] = 'python3.x'
        vfxtest.runTestSuite(settings=settings)
        # assert(1 == 3)
        # self.assertEqual(settings['count_run'], 6)
        # self.assertEqual(settings['count_failures'], 0)
        # self.assertEqual(settings['count_errors'], 0)
        # self.assertTrue(os.path.exists(cov_file))

    # # -------------------------------------------------------------------------
    # def test02_runTestSuite_with_filter_tokens_runs_successfully(self):

    #     settings = vfxtest.collectSettings(['--target', '.', '_01',])
    #     vfxtest.runTestSuite(settings=settings, use_coverage=False)
    #     self.assertEqual(settings['count_run'], 3)
    #     self.assertEqual(settings['count_failures'], 0)
    #     self.assertEqual(settings['count_errors'], 0)

    # # -------------------------------------------------------------------------
    # def test03_combineCoverages_works_as_expected(self):

    #     settings = vfxtest.collectSettings(['_02',])
    #     settings['context'] = 'differentContext'
    #     vfxtest.runTestSuite(settings=settings)
    #     self.assertEqual(settings['count_run'], 3)
    #     self.assertTrue(os.path.exists('{}/.coverage.differentContext'.format(settings['test_output'])))

    #     settings = vfxtest.collectSettings()
    #     vfxtest.combineCoverages(settings)

    #     self.assertFalse(os.path.exists('{}/.coverage.differentContext'.format(settings['test_output'])))
    #     self.assertTrue(os.path.exists('{}/.coverage'.format(settings['test_output'])))

    # # -------------------------------------------------------------------------
    # def test04_resolveContext_defaults_to_native(self):
    #     settings = vfxtest.collectSettings()
    #     self.assertEqual(settings['context'], 'native')

    # # -------------------------------------------------------------------------
    # def test05_resolveContext_defaults_to_native(self):
    #     settings = vfxtest.collectSettings(['--target','./python2.x'])
    #     self.assertEqual(settings['context'], 'python2.x')

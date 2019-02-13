# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

import vfxtest


# -----------------------------------------------------------------------------
class RunTestsTestCase(unittest.TestCase):

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
    def test01_runTests_runs_successfully(self):

        cov_file = os.path.abspath('./test_output/.coverage.native')
        if os.path.exists(cov_file):
            os.remove(cov_file)

        settings = vfxtest.collectSettings()
        vfxtest.runTests(target='.', settings=settings, context='native', use_coverage=True)

        self.assertEqual(settings['count_run'], 6)
        self.assertEqual(settings['count_failures'], 0)
        self.assertEqual(settings['count_errors'], 0)
        self.assertTrue(os.path.exists(cov_file))

    # -------------------------------------------------------------------------
    def test02_runTests_with_filter_tokens_runs_successfully(self):

        settings = vfxtest.collectSettings(['_01',])
        vfxtest.runTests(target='.', settings=settings, context='native', use_coverage=False)
        self.assertEqual(settings['count_run'], 3)
        self.assertEqual(settings['count_failures'], 0)
        self.assertEqual(settings['count_errors'], 0)

    # -------------------------------------------------------------------------
    def test03_combineCoverages_works_as_expected(self):

        settings = vfxtest.collectSettings(['_02',])
        vfxtest.runTests(target='.', settings=settings, context='differentContext')
        self.assertEqual(settings['count_run'], 3)
        self.assertTrue(os.path.exists('{}/.coverage.differentContext'.format(settings['test_output'])))

        settings = vfxtest.collectSettings()
        vfxtest.combineCoverages(settings)

        self.assertFalse(os.path.exists('{}/.coverage.differentContext'.format(settings['test_output'])))
        self.assertTrue(os.path.exists('{}/.coverage'.format(settings['test_output'])))

    # -------------------------------------------------------------------------
    def test04_resolveContext_defaults_to_native(self):
        settings = vfxtest.collectSettings()
        context = vfxtest.resolveContext(settings)
        self.assertEqual(context, 'native')

    # -------------------------------------------------------------------------
    def test05_resolveContext_defaults_to_native(self):
        settings = vfxtest.collectSettings(['--target','./python2.x'])
        context = vfxtest.resolveContext(settings)
        self.assertEqual(context, 'python2.x')

    # -------------------------------------------------------------------------
    def test06_runChildContextTests(self):
        settings = vfxtest.collectSettings()
        vfxtest.runChildContextTests(target=settings['cwd'], settings=settings)
        # context = vfxtest.resolveContext(settings)
        # self.assertEqual(context, 'python2.x')

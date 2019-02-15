# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

import vfxtest

# -----------------------------------------------------------------------------
class TestCaseTestCase(unittest.TestCase):

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
    def test01_TestCase_object_is_valid_unittest_TestCase(self):

        foo = vfxtest.TestCase(test_run=True)
        self.assertTrue(isinstance(foo, unittest.TestCase))

    # -------------------------------------------------------------------------
    def test02_settings_can_be_get_and_set(self):

        foo = vfxtest.TestCase(test_run=True)
        settings = vfxtest.collectSettings()
        foo.settings = settings
        self.assertEqual(foo.settings, settings)

    # -------------------------------------------------------------------------
    def test03_settings_set_to_invalid_content_results_in_empty_dict(self):

        foo = vfxtest.TestCase(test_run=True)
        foo.settings = ['invalid', 'settings']
        self.assertEqual(foo.settings, {})

    # -------------------------------------------------------------------------
    def test04_context_matches_context_in_settings(self):

        foo = vfxtest.TestCase(test_run=True)
        settings = vfxtest.collectSettings()
        settings['context'] = 'awesomeContext'
        foo.settings = settings
        self.assertEqual(foo.context, 'awesomeContext')

    # -------------------------------------------------------------------------
    def test05_context_settings_matches_settings(self):

        foo = vfxtest.TestCase(test_run=True)
        settings = vfxtest.collectSettings()
        settings['context'] = 'python3.x'
        foo.settings = settings
        self.assertEqual(foo.context_settings, settings['context_details']['python3.x'])

    # -------------------------------------------------------------------------
    def test06_createTestFolder_works_as_expected(self):

        settings = vfxtest.collectSettings()
        self.assertTrue(os.path.exists(settings['test_output']))
        foo = vfxtest.TestCase(test_run=True)
        foo.settings = settings

        proof = foo.createTestFolder('MyName')
        self.assertEqual(proof, '{}{}{}'.format(settings['test_output'], os.sep, 'MyName'))

# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

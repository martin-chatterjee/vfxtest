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
    def test06__createTestRootFolder_invalid_test_output_raises_OSError(self):

        invalid_test_output = os.path.abspath('./does/not/exist')
        self.assertFalse(os.path.exists(invalid_test_output))

        runner = vfxtest.TextTestRunner()
        settings = vfxtest.collectSettings()
        settings['test_output'] = invalid_test_output

        with self.assertRaises(OSError):
            vfxtest._createTestRootFolder(settings=settings, name=['invalid'])

    # -------------------------------------------------------------------------
    def test07_test_root_sets_and_gets_class_variable(self):

        a = vfxtest.TestCase(test_run=True)
        b = vfxtest.TestCase(test_run=True)

        a.test_root = './foo/bar'
        self.assertEqual(a.test_root, './foo/bar')
        self.assertEqual(a.test_root, b.test_root)

        b.test_root = './fizz/buzz'
        self.assertEqual(b.test_root, './fizz/buzz')
        self.assertEqual(a.test_root, b.test_root)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

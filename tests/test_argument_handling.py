# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import json

import vfxtest


# -----------------------------------------------------------------------------
class ArgumentHandlingTestCase(unittest.TestCase):

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
    def test01_collectSettings_help_raises_SystemError(self):

        with self.assertRaises(SystemExit):
            result = vfxtest.collectSettings(['--help'])

    # -------------------------------------------------------------------------
    def test02_collectSettings_unknown_argument_raises_SystemError(self):

        with self.assertRaises(SystemExit):
            result = vfxtest.collectSettings(['--doesnotexist'])

    # -------------------------------------------------------------------------
    def test03_collectSettings_returns_default_args(self):

        result = vfxtest.collectSettings()

        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result['target'], os.getcwd())
        self.assertEqual(result['failfast'], True)
        self.assertEqual(result['prefs'], os.sep.join([result['target'],
                                                       'test.prefs']))
        self.assertEqual(result['limit'], 0)
        self.assertEqual(result['filter_tokens'], [])
        self.assertEqual(result['cwd'], os.getcwd())

    # -------------------------------------------------------------------------
    def test04_collectSettings_explicit_values_for_clear_and_failfast_get_respected(self):

        result_a = vfxtest.collectSettings(['--target', './subfolder',
                                       '--failfast', 'False',
                                       '--prefs', './other.prefs',
                                       '--limit', '13',
                                       'foo', 'bar', 'baz'])

        result_b = vfxtest.collectSettings(['-t', './subfolder',
                                       '-f', 'False',
                                       '-p', './other.prefs',
                                       '-l', '13',
                                       'foo', 'bar', 'baz'])

        self.assertEqual(result_a['target'], '{}{}{}'.format(os.getcwd(),
                                                           os.sep,
                                                           'subfolder'))
        self.assertEqual(result_a['failfast'], False)
        self.assertEqual(result_a['prefs'], '{}{}{}'.format(os.getcwd(),
                                                          os.sep,
                                                          'other.prefs'))
        self.assertEqual(result_a['limit'], 13)
        self.assertEqual(result_a['filter_tokens'], ['foo', 'bar', 'baz'])

        self.assertEqual(result_a, result_b)

    # -------------------------------------------------------------------------
    def test05_collectSettings_invalid_boolean_string_raises_SystemExit(self):

        true_boolean_strings = ['true', 'True', 'yes', 'y', '1']
        for item in true_boolean_strings:
            result = vfxtest.collectSettings(['--failfast', item])
            self.assertEqual(result['failfast'], True)

        false_boolean_strings = ['false', 'False', 'no', 'n', '0']
        for item in false_boolean_strings:
            result = vfxtest.collectSettings(['--failfast', item])
            self.assertEqual(result['failfast'], False)

        with self.assertRaises(SystemExit):
            result = vfxtest.collectSettings(['--failfast', 'Nope'])

    # -------------------------------------------------------------------------
    def test06_collectSettings_invalid_or_nonexistent_prefs_file_raises_SystemExit(self):

        with self.assertRaises(SystemExit):
            result = vfxtest.collectSettings(['--prefs', 'does_not_exist.prefs'])


    # -------------------------------------------------------------------------
    def test07_collectSettings_nonexistent_test_output_parent_folder_raises_SystemExit(self):

        with self.assertRaises(SystemExit):
            result = vfxtest.collectSettings(['--prefs',
                                              './test_output-non-existent-parent-folder.prefs'])

    # -------------------------------------------------------------------------
    def test08_collectSettings_nonexistent_test_output_folder_gets_created(self):

        if os.path.exists('./remove_me'):
            os.rmdir('./remove_me')

        result = vfxtest.collectSettings(['--prefs',
                                          './test_output-create-folder.prefs'])

        self.assertTrue(os.path.exists('./remove_me'))
        os.rmdir('./remove_me')

    # -------------------------------------------------------------------------
    def test09_collectSettings_falls_back_to_prefs_in_parent_folder(self):

        cwd = os.getcwd()
        os.chdir('./python')
        result = vfxtest.collectSettings([])
        self.assertEqual(result['prefs'], '{}{}{}'.format(cwd,
                                                          os.sep,
                                                          'test.prefs'))
        os.chdir('..')

    # -------------------------------------------------------------------------
    def test10_collectSettings_settings_in_environment_get_recovered(self):

        result_a = vfxtest.collectSettings(['--target', './subfolder',
                                            '--failfast', 'False',
                                            '--prefs', './other.prefs',
                                            '--limit', '13',
                                            'foo', 'bar', 'baz'])

        self.assertEqual(result_a['target'], '{}{}{}'.format(os.getcwd(),
                                                           os.sep,
                                                           'subfolder'))
        self.assertEqual(result_a['failfast'], False)
        self.assertEqual(result_a['prefs'], '{}{}{}'.format(os.getcwd(),
                                                          os.sep,
                                                          'other.prefs'))
        self.assertEqual(result_a['limit'], 13)
        self.assertEqual(result_a['filter_tokens'], ['foo', 'bar', 'baz'])

        self.assertEqual(result_a['subprocess'], False)

        serialized = json.dumps(result_a)
        os.environ['vfxtest_settings'] = serialized
        result_b = vfxtest.collectSettings()
        os.environ.pop('vfxtest_settings')

        self.assertEqual(result_b['subprocess'], True)

        result_a['subprocess'] = None
        result_b['subprocess'] = None
        self.assertEqual(result_a, result_b)

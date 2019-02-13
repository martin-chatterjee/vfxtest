# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

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
    # -------------------------------------------------------------------------
    def tearDown(self):
        """
        """


    # -------------------------------------------------------------------------
    def test01__parseArgs_help_raises_SystemError(self):

        with self.assertRaises(SystemExit):
            result = vfxtest._parseArgs(['--help'])

    # -------------------------------------------------------------------------
    def test02__parseArgs_unknown_argument_raises_SystemError(self):

        with self.assertRaises(SystemExit):
            result = vfxtest._parseArgs(['--doesnotexist'])

    # -------------------------------------------------------------------------
    def test03__parseArgs_returns_default_args(self):

        result = vfxtest._parseArgs()

        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result['filter_tokens'], [])
        self.assertEqual(result['run_all'], None)
        self.assertEqual(result['clear'], False)
        self.assertEqual(result['failfast'], True)
        self.assertEqual(result['target'], os.getcwd())
        self.assertEqual(result['prefs'], os.sep.join([result['target'],
                                                       'vfxtest.prefs']))
        self.assertEqual(result['target'], result['cwd'])
        self.assertEqual(result['limit'], 0)
        self.assertEqual(result['cwd'], os.getcwd())

    # -------------------------------------------------------------------------
    def test04__parseArgs_explicit_values_for_clear_and_failfast_get_respected(self):

        result_a = vfxtest._parseArgs(['--run-all', 'True',
                                       '--clear', 'True',
                                       '--failfast', 'False',
                                       '--target', './subfolder',
                                       '--prefs', './other.prefs',
                                       '--limit', '13'])

        result_b = vfxtest._parseArgs(['-ra', 'True',
                                       '-c', 'True',
                                       '-f', 'False',
                                       '-t', './subfolder',
                                       '-p', './other.prefs',
                                       '-l', '13'])

        self.assertEqual(result_a['run_all'], True)
        self.assertEqual(result_a['clear'], True)
        self.assertEqual(result_a['failfast'], False)
        self.assertEqual(result_a['target'], '{}{}{}'.format(os.getcwd(),
                                                           os.sep,
                                                           'subfolder'))
        self.assertEqual(result_a['prefs'], '{}{}{}'.format(os.getcwd(),
                                                          os.sep,
                                                          'other.prefs'))
        self.assertEqual(result_a['limit'], 13)

        self.assertEqual(result_a, result_b)

    # -------------------------------------------------------------------------
    def test05__parseArgs_clear_is_False_if_not_set_explictely(self):

        result = vfxtest._parseArgs()
        self.assertEqual(result['clear'], False)

    # -------------------------------------------------------------------------
    def test06__parseArgs_clear_is_True_if_not_set_explictely_and_run_all_is_True(self):

        result = vfxtest._parseArgs(['--run-all', 'True'])
        self.assertEqual(result['clear'], True)

        result = vfxtest._parseArgs(['--run-all', 'True', '--clear', 'False'])
        self.assertEqual(result['clear'], False)

    # -------------------------------------------------------------------------
    def test07__parseArgs_invalid_boolean_string_raises_SystemExit(self):

        true_boolean_strings = ['true', 'True', 'yes', 'y', '1']
        for item in true_boolean_strings:
            result = vfxtest._parseArgs(['--clear', item])
            self.assertEqual(result['clear'], True)

        false_boolean_strings = ['false', 'False', 'no', 'n', '0']
        for item in false_boolean_strings:
            result = vfxtest._parseArgs(['--clear', item])
            self.assertEqual(result['clear'], False)

        with self.assertRaises(SystemExit):
            result = vfxtest._parseArgs(['--clear', 'Nope'])

    # -------------------------------------------------------------------------
    def test08__parseArgs_invalid_or_nonexistent_prefs_file_raises_SystemExit(self):

        with self.assertRaises(SystemExit):
            result = vfxtest._parseArgs(['--prefs', 'does_not_exist.prefs'])



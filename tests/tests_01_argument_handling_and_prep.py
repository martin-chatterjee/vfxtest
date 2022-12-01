# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2022, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import json
try:
    import unittest.mock as mock
except:
    import mock

import logging
import os
import shutil
import sys
import unittest

import vfxtest

from output_trap import OutputTrap


# -----------------------------------------------------------------------------
class ArgumentHandlingAndPrepTestCase(unittest.TestCase):

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

        with OutputTrap():
            with self.assertRaises(SystemExit):
                result = vfxtest.collectSettings(['--help'])

    # -------------------------------------------------------------------------
    def test02_collectSettings_unknown_argument_raises_SystemError(self):

        with OutputTrap():
            with self.assertRaises(SystemExit):
                result = vfxtest.collectSettings(['--doesnotexist'])

    # -------------------------------------------------------------------------
    def test03_collectSettings_returns_default_args(self):

        result = vfxtest.collectSettings()

        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result['target'], os.getcwd())
        self.assertEqual(result['failfast'], True)
        self.assertEqual(result['cfg'], os.sep.join([result['target'],
                                                       '.config']))
        self.assertEqual(result['limit'], 0)
        self.assertEqual(result['filter_tokens'], [])
        self.assertEqual(result['cwd'], os.getcwd())

    # -------------------------------------------------------------------------
    def test04_collectSettings_explicit_values_for_clear_and_failfast_get_respected(self):

        result_a = vfxtest.collectSettings(['--target', './subfolder',
                                       '--failfast', 'False',
                                       '--cfg', './other.cfg',
                                       '--limit', '13',
                                       'foo', 'bar', 'baz'])

        result_b = vfxtest.collectSettings(['-t', './subfolder',
                                       '-f', 'False',
                                       '-c', './other.cfg',
                                       '-l', '13',
                                       'foo', 'bar', 'baz'])

        self.assertEqual(result_a['target'], '{}{}{}'.format(os.getcwd(),
                                                           os.sep,
                                                           'subfolder'))
        self.assertEqual(result_a['failfast'], False)
        self.assertEqual(result_a['cfg'], '{}{}{}'.format(os.getcwd(),
                                                          os.sep,
                                                          'other.cfg'))
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

        with OutputTrap():
            with self.assertRaises(SystemExit):
                result = vfxtest.collectSettings(['--failfast', 'Nope'])

    # -------------------------------------------------------------------------
    def test06_collectSettings_nonexistent_cfg_file_raises_SystemExit(self):

        with self.assertRaises(SystemExit):
            result = vfxtest.collectSettings(['--cfg', 'does_not_exist.cfg'])


    # -------------------------------------------------------------------------
    def test07_prepareTestEnvironment_nonexistent_test_output_parent_folder_raises_SystemExit(self):

        with self.assertRaises(SystemExit):
            settings = vfxtest.collectSettings(['--cfg',
                                                './test_output-non-existent-parent-folder.cfg'])
            settings['test_no_pythonpath'] = True
            vfxtest.prepareTestEnvironment(settings)

    # -------------------------------------------------------------------------
    def test08_prepareTestEnvironment_nonexistent_test_output_folder_gets_created(self):

        if os.path.exists('./remove_me'):
            shutil.rmtree('./remove_me')

        settings = vfxtest.collectSettings(['--cfg',
                                            './test_output-create-folder.cfg'])
        settings['test_no_pythonpath'] = True
        vfxtest.prepareTestEnvironment(settings,)

        self.assertTrue(os.path.exists('./remove_me'))
        shutil.rmtree('./remove_me')

    # -------------------------------------------------------------------------
    def test09_collectSettings_falls_back_to_cfg_in_parent_folder(self):

        cwd = os.getcwd()
        os.chdir('./python')
        result = vfxtest.collectSettings([])
        self.assertEqual(result['cfg'], '{}{}{}'.format(cwd,
                                                          os.sep,
                                                          '.config'))
        os.chdir('..')

    # -------------------------------------------------------------------------
    def test10_collectSettings_settings_in_environment_get_recovered(self):

        result_a = vfxtest.collectSettings(['--target', './subfolder',
                                            '--failfast', 'False',
                                            '--cfg', './other.cfg',
                                            '--limit', '13',
                                            'foo', 'bar', 'baz'])

        self.assertEqual(result_a['target'], '{}{}{}'.format(os.getcwd(),
                                                           os.sep,
                                                           'subfolder'))
        self.assertEqual(result_a['failfast'], False)
        self.assertEqual(result_a['cfg'], '{}{}{}'.format(os.getcwd(),
                                                          os.sep,
                                                          'other.cfg'))
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


    # -------------------------------------------------------------------------
    def test11_collectSettings_invalid_cfg_file_prints_useful_error_and_raises_SystemExit(self):
        with mock.patch.object(vfxtest,
                               '_extractLineNumber',
                               return_value=3):
            with self.assertRaises(SystemExit):
                result = vfxtest.collectSettings(['--cfg', 'invalid_json.cfg'])

    # -------------------------------------------------------------------------
    def test12_collectSettings_cfg_bool_values_defined_as_strings_get_converted(self):

        result = vfxtest.collectSettings(['--cfg', 'boolean_as_string.cfg'])
        self.assertTrue(result['debug_mode'])

    # -------------------------------------------------------------------------
    def test13__extractLineNumber_defaults_to_minus_one_on_internal_exception(self):

        result = vfxtest._extractLineNumber('Expecting value: line 13 column 20 (char 59)')
        self.assertEqual(result, 13)

        result = vfxtest._extractLineNumber('Not a single line number in here...')
        self.assertEqual(result, -1)

    # -------------------------------------------------------------------------
    def test14_prepareTestEnvironment_without_python_contexts_still_preps_pythonpath_or_throws_EnvironmentError(self):

        if os.path.exists('./no_python_contexts'):
            shutil.rmtree('./no_python_contexts')

        settings = vfxtest.collectSettings(['--cfg',
                                            './test_no-python-contexts.cfg'])
        # Python 2.x
        if sys.version.startswith('2.'):
            vfxtest.prepareTestEnvironment(settings)
            proof = './no_python_contexts/_dcc_settings/PYTHONPATH/mock/mock.py'
            self.assertTrue(os.path.exists(proof))

        elif sys.version.startswith('3.'):
            with self.assertRaises(EnvironmentError):
                vfxtest.prepareTestEnvironment(settings)
        else:
            raise EnvironmentError('Python version not tested: {}'.format(sys.version))

        shutil.rmtree('./no_python_contexts')

    # -------------------------------------------------------------------------
    def test15_copyModulesToFolder_works_as_expected(self):
        if os.path.exists('./copy_modules'):
            shutil.rmtree('./copy_modules')

        os.makedirs('./copy_modules')
        module_names = ['os', 'sqlite3',]

        vfxtest._copyModulesToFolder(module_names, './copy_modules')

        self.assertTrue(os.path.exists('./copy_modules/os.py'))
        self.assertTrue(os.path.exists('./copy_modules/sqlite3/__init__.py'))

        shutil.rmtree('./copy_modules')

    # -------------------------------------------------------------------------
    def test16_initLogging(self):

        logger = logging.getLogger('vfxtest')
        vfxtest.initLogging(level=logging.DEBUG, format='PROOF: %(message)s')
        self.assertEqual(vfxtest.logger.level, logging.DEBUG)
        vfxtest.initLogging()
        self.assertEqual(vfxtest.logger.level, logging.INFO)



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    vfxtest.main()

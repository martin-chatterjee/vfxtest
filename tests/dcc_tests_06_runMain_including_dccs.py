    # -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2022, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
import sys
import json

import vfxtest
mock = vfxtest.mock

from output_trap import OutputTrap


# -----------------------------------------------------------------------------
class RunMainTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        """
        """
        cls.init_target = '{}/test_sandbox/init'.format(os.getcwd().replace('\\', '/'))
        if not os.path.exists(cls.init_target):
            os.makedirs(cls.init_target)

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
    def test01_runMain_including_DCCs_works_as_expected(self):

        with OutputTrap():
            proof = vfxtest.runMain(['--cfg','.config-including-dccs'])
        self.assertEqual(proof['files_run'], 8)
        self.assertEqual(proof['tests_run'], 24)
        self.assertEqual(proof['errors'], 0)



# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()

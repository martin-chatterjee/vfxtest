# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import os
import sys

import vfxtest

import awesome_module

# -----------------------------------------------------------------------------
class TestCase03(vfxtest.TestCase):

    @classmethod
    def setUpClass(cls):
        print('')
        print("    [TestCase03]  accessed test_root in 'setUpClass': {}".format(cls.test_root))
        sys.stdout.flush()

    # -------------------------------------------------------------------------
    def test01_(self):
        tr = self.test_root
        self.assertTrue(os.path.exists(tr))

        # retrieve settings in here
        current_context = self.context
        print('    [TestCase03]  current context: {}'.format(current_context))
        executable = self.context_settings.get('executable', None)
        print('    [TestCase03]  executable:      {}'.format(executable))

        foo = awesome_module.lorem(3, 5)
        self.assertEqual(foo, 8)

    # -------------------------------------------------------------------------
    def test02_(self):
        foo = awesome_module.lorem(6, 4)
        self.assertEqual(foo, 10)

    # -------------------------------------------------------------------------
    def test03_(self):
        foo = awesome_module.lorem(1, 2)
        self.assertEqual(foo, 3)

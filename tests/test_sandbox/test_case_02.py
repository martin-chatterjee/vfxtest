# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import vfxtest
import os

import awesome_module

# -----------------------------------------------------------------------------
class TestCase02(vfxtest.TestCase):

    # -------------------------------------------------------------------------
    def test01_(self):
        foo = awesome_module.bar(3, 5)
        self.assertEqual(foo, 8)

    # -------------------------------------------------------------------------
    def test02_(self):
        foo = awesome_module.bar(6, 4)
        self.assertEqual(foo, 10)

    # -------------------------------------------------------------------------
    def test03_(self):
        foo = awesome_module.bar(1, 2)
        self.assertEqual(foo, 3)

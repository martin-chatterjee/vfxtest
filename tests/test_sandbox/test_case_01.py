# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

import awesome_module

# -----------------------------------------------------------------------------
class TestCase01(unittest.TestCase):

    # -------------------------------------------------------------------------
    def test01_(self):
        foo = awesome_module.fizz(3, 5)
        self.assertEqual(foo, 8)

    # -------------------------------------------------------------------------
    def test02_(self):
        foo = awesome_module.buzz(3, 5)
        self.assertEqual(foo, 8)

    # -------------------------------------------------------------------------
    def test03_(self):
        foo = awesome_module.foo(3, 5)
        self.assertEqual(foo, 8)

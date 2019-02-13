# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

import module_to_test

# -----------------------------------------------------------------------------
class TestCase01(unittest.TestCase):

    # -------------------------------------------------------------------------
    def test01_(self):
        foo = module_to_test.fizz(3, 5)
        self.assertEqual(foo, 8)

    # -------------------------------------------------------------------------
    def test02_(self):
        foo = module_to_test.buzz(3, 5)
        self.assertEqual(foo, 8)

    # -------------------------------------------------------------------------
    def test03_(self):
        foo = module_to_test.foo(3, 5)
        self.assertEqual(foo, 8)

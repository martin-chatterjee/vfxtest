# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os

import module_to_test

# -----------------------------------------------------------------------------
class FooTest(unittest.TestCase):

    # -------------------------------------------------------------------------
    def test01_(self):
        foo = module_to_test.bar(3, 5)
        self.assertEqual(foo, 8)

    # -------------------------------------------------------------------------
    def test02_(self):
        foo = module_to_test.bar(6, 4)
        self.assertEqual(foo, 10)

    # -------------------------------------------------------------------------
    def test03_(self):
        foo = module_to_test.bar(1, 2)
        self.assertEqual(foo, 3)

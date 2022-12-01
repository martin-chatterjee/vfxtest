# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2022, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import sys
import logging

try:  # pragma: no cover_3
    from cStringIO import StringIO
except ImportError:  # pragma: no cover_2
    from io import StringIO

import vfxtest
mock = vfxtest.mock


# Global constant to completely bypass the functionality.
BYPASS = False


# -----------------------------------------------------------------------------
class OutputTrap():
    """Context Manager for trapping any output.

    Swallows all vfxtest and unittest logging, as well as STDOUT and STDERR.
    This way the console output of the test suite will not polluted by the
    internal output of the called methods.

    Usage:

        print("This gets logged.")
        vfxtest.logger.info("This gets logged as well.")

        with OutputTrap():
            print("This does not appear.")
            vfxtest.logger.info("This does not appear well.")

        print("This gets logged again.")
        vfxtest.logger.info("Visible again.")

    """

    # -------------------------------------------------------------------------
    def __init__(self):
        self.stored_stdout = sys.stdout
        self.stored_stderr = sys.stderr
        self.stored_loglevel = vfxtest.logger.level
        self.stored_writelndecorator = unittest.runner._WritelnDecorator
        self.mocked_stdout = StringIO()
        self.mocked_stderr = StringIO()

        self.mocked_writelndecorator = mock.Mock()

    # -------------------------------------------------------------------------
    def __enter__(self):
        if BYPASS:  # pragma: no cover
            return
        sys.stdout = self.mocked_stdout
        sys.stderr = self.mocked_stderr
        vfxtest.initLogging(level=logging.NOTSET)
        unittest.runner._WritelnDecorator = self.mocked_writelndecorator

    # -------------------------------------------------------------------------
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if BYPASS:  # pragma: no cover
            return
        vfxtest.initLogging(level=self.stored_loglevel)
        sys.stdout = self.stored_stdout
        sys.stderr = self.stored_stderr
        unittest.runner._WritelnDecorator = self.stored_writelndecorator

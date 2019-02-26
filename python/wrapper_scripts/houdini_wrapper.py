# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------

import os
import sys

import vfxtest
import hou
import hdefereval

# ------------------------------------------------------------------------------
def run_tests():
    """
    """
    try:
        vfxtest.runMain()
        hou.exit(suppress_save_prompt=True)
    except Exception as e:
        hou.exit(error_code=1, suppress_save_prompt=True)

# ------------------------------------------------------------------------------
def main():
    context = os.path.basename(sys.executable)
    if context.lower().find('houdini') != -1:
        hdefereval.executeDeferred(run_tests)

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    main()

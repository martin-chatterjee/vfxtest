# -*- coding: utf-8 -*-
#
# Copyright (c) 2019, Martin Chatterjee. All rights reserved.
# -----------------------------------------------------------------------------

import unittest
import os
from fnmatch import fnmatch

# -----------------------------------------------------------------------------
class FilteredTestLoader(unittest.TestLoader):
    """
    """

    # -------------------------------------------------------------------------
    def _match_path(self, path, full_path, pattern):
        """
        """
        # ensure that pattern is iterable
        if not isinstance(pattern, list) and not isinstance(pattern, tuple):
            pattern = [pattern,]

        # first pattern must be matched
        result = False
        if fnmatch(path, pattern[0]):
            result = True

            # at least one of the optional patterns must be matched
            optionals = pattern[1:]
            if len(optionals) > 0:
                result = False
                for item in optionals:
                    if fnmatch(path, item):
                        result = True
                        break

        return result


# -----------------------------------------------------------------------------
def main(folder_path):

    loader = FilteredTestLoader()

    file_pattern = 'test*.py'
    filter_tokens = []

    patterns = [file_pattern,]
    for item in filter_tokens:
        patterns.append('*{}*'.format(item))

    # discover all tests and run them
    suite = loader.discover(folder_path, pattern=patterns)
    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    # print('-'*80)
    # print(result)

if __name__ == '__main__':
    main(os.getcwd())

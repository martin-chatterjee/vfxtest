# `vfxtest` Release Notes


## `Next` (Date)

- **Refactored test suite**: _(→ [Issue #3](https://github.com/martin-chatterjee/vfxtest/issues/3))_
    - Added **command line argument** handling.
    - Separated tests that require interactive DCC licenses.
    - Cleaned up console output by hiding internal logging.
    - Made `run_all_tests.py` fully Python 3.x compatible.

<br>

## `0.2.1` (09-Sep-2022)

- **Improved virtualenv management**:
    - Added support for `requirements.txt` files per context.
    - Added support for `PYTHONPATH` entries per context.
- **Housekeeping**:
    - Fixed Python 2/3 compatibility issue.
    - Added missing `six` requirement in `setup.py`.

<br>

## `0.2.0` (22-Jul-2019)

- Prototypical implementation.


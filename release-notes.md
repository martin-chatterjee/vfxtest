# `vfxtest` Release Notes


## `Next` (Date)

- **Refactored test suite**: _(→ [Issue #3](https://github.com/martin-chatterjee/vfxtest/issues/3))_
    - Added **command line argument** handling.
    - Separated tests that require interactive DCC licenses.
    - Cleaned up console output by hiding internal logging.
    - Made `run_all_tests.py` fully Python 3.x compatible.

- **Refactored virtualenv management**: _(→ [Issue #2](https://github.com/martin-chatterjee/vfxtest/issues/2))_
    - Added introspectable version.
    - Now `pip install`'s specific `vfxtest` version into every virtualenv, to get set of matching dependencies.
    - Now copies current `vfxtest.py` file to separate `PYTHONPATH` folder in dcc_settings.
    - Now executes all subprocesses with the `-m vfxtest` args, instead of the absolute path to `vfxtest.py`.
    - Introduced `use-environment` context setting for DCC contexts, specifying which Python environment they should use.
      > **Warning**\
      > This is a **breaking change** for DCC contexts. `use-environment` **must** be specified for all DCC contexts.
    - Now uses `console_scripts` mechanism in `setup.py`.

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


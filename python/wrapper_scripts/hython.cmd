@echo off
setlocal

set EXECUTABLE=%1
set VFXTEST_ROOT=%2
set SETTINGS_ROOT=%3
set DEBUG_MODE=%4

set COMMAND=%EXECUTABLE% %VFXTEST_ROOT%\vfxtest.py

IF "%DEBUG_MODE%"=="True" (
    echo.
    echo [DBG] Resulting Command:
    echo       ------------------
    echo       %COMMAND%
    echo.
    echo.
    echo.
)

set HOUDINI_USER_PREF_DIR=%SETTINGS_ROOT%/hython.vfxtest.__HVER__
set HSITE=
set PYTHONPATH=%~dp0;%SETTINGS_ROOT%\virtualenv_python2.x\Lib\site-packages;%PYTHONPATH%

%COMMAND%

endlocal

exit /B %ERRORLEVEL%

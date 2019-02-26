@echo off
setlocal

set EXECUTABLE=%1
set VFXTEST_ROOT=%2
set SETTINGS_ROOT=%3
set DEBUG_MODE=%4
set TARGET_WRAPPER=%5

set COMMAND=%EXECUTABLE% %TARGET_WRAPPER%

IF "%DEBUG_MODE%"=="True" (
    echo.
    echo [DBG] Resulting Command:
    echo       ------------------
    echo       %COMMAND%
    echo.
    echo.
    echo.
)

set HOUDINI_USER_PREF_DIR=%SETTINGS_ROOT%/houdini.vfxtest.__HVER__
set HSITE=
set PYTHONPATH=%~dp0;%VFXTEST_ROOT%;%SETTINGS_ROOT%\virtualenv_python2.x\Lib\site-packages;%PYTHONPATH%

%COMMAND%

endlocal

exit /B %ERRORLEVEL%

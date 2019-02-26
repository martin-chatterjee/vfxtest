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

%COMMAND%

endlocal

exit /B %ERRORLEVEL%

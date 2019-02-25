@echo off
setlocal

set EXECUTABLE=%1
set VFXTEST=%2
set SETTINGS_ROOT=%3
set DEBUG_MODE=%4

set COMMAND=%EXECUTABLE% %VFXTEST%

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

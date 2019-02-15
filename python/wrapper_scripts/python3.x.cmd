@echo off
setlocal

set EXECUTABLE=%1
set VFXTEST=%2
set DEBUG_MODE=%3

set COMMAND=%EXECUTABLE% %VFXTEST%

IF "%DEBUG_MODE%"=="True" (
    echo.
    echo Resulting Command:
    echo ------------------
    echo         %COMMAND%
    echo.
    echo.
    echo.
)

%COMMAND%

endlocal

exit /B %ERRORLEVEL%

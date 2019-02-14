@echo off
setlocal

set EXECUTABLE=%1
set VFXTEST=%2
set COMMAND=%EXECUTABLE% %VFXTEST%

echo Resulting Command:
echo ------------------
echo         %COMMAND%
echo.
echo.
echo.

%COMMAND%

endlocal

exit /B %ERRORLEVEL%

@echo off
setlocal

set EXECUTABLE=%1
set VFXTEST=%2
set SETTINGS=%3


set CMD=%EXECUTABLE% %VFXTEST% --settings "%SETTINGS%"

%CMD%

endlocal

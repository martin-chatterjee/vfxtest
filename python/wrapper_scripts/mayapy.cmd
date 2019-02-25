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

set MAYA_APP_DIR=%SETTINGS_ROOT%/mayapy.vfxtest
set MAYA_SCRIPT_PATH=%~dp0
set PYTHONPATH=%~dp0;%SETTINGS_ROOT%\virtualenv_python2.x\Lib\site-packages;%PYTHONPATH%
set MAYA_PLUG_IN_PATH=
set MAYA_MODULE_PATH=

%COMMAND%

endlocal

exit /B %ERRORLEVEL%

@echo off
setlocal

set CWD=%~dp0

set PYTHON=%1
set VENV_NAME=%2
set VENV_ROOT=%3
set VFXTEST_ROOT=%4

cd %VENV_ROOT%
%PYTHON% -m virtualenv %VENV_NAME%
CALL %VENV_NAME%\Scripts\activate.bat
echo pip install -r %VFXTEST_ROOT%\..\requirements.txt
pip install -r %VFXTEST_ROOT%\..\requirements.txt
CALL %VENV_NAME%\Scripts\deactivate.bat
cd %CWD%

endlocal
exit /B %ERRORLEVEL%

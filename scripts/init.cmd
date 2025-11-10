@echo off
setlocal
goto :start
rem Function to update deps, install python3-venv and ensure pip is installed
:install_venv
echo Updating dependencies and installing Python 3 and pip...
REM Ensure Python is installed; you can adjust the paths based on your setup
WHERE python >nul 2>nul
IF ERRORLEVEL 1 (
    echo Python is not installed. Please install Python from https://www.python.org/downloads/
    exit /b
)

rem Check if pip is installed
WHERE pip >nul 2>nul
IF ERRORLEVEL 1 (
    echo Pip is not installed. Installing pip...
    python -m ensurepip --upgrade
)

rem Check if venv is available
python -m venv --help >nul 2>nul
IF ERRORLEVEL 1 (
    echo Installing venv module...
    pip install virtualenv
)

exit /b

:main
set "env_name=.venv"

call :install_venv

rem Create the virtual environment
echo Creating the virtual environment...
python -m venv "%env_name%"
echo Virtual environment "%env_name%" created successfully.

rem Mark the newly created virtual enviroment as a hidden directory
attrib +h .venv

rem Activate the virtual environment
echo Activating the virtual environment...
call "%env_name%\Scripts\activate.bat"
echo Virtual environment "%env_name%" activated successfully.

rem Install dependencies
echo Installing dependencies from dependencies/requirements.txt...
if exist "dependencies\requirements.txt" (
    pip install -r "dependencies\requirements.txt"
    echo Dependencies installed into the environment "%env_name%" successfully.
) else (
    echo requirements.txt not found in dependencies directory.
)

endlocal
exit /b

:start
rem Call the main function
call :main

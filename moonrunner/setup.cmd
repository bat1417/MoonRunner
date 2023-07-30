@echo off
REM Check if Python is installed
where python > nul 2>&1

IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed on this system.
    echo Please install Python from https://www.python.org/downloads/
    exit /b 1
) else (
    echo 'found Python:'
    python --version
)
echo "create virtual environment ..."
py -m venv env
echo "activate the virtual environment ..."
.\env\Scripts\activate
echo "install the requirements ..."
py -m pip install -r requirements.txt
echo "finished! You can start MoonRunner by double-click on moonrunner_gui.py or 'py moonrunner_gui.py' in a cmd line"

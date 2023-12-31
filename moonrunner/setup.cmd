@echo off
REM Check if Python is installed
python --version 2>nul | findstr /i "Python 3" >nul

IF %ERRORLEVEL% NEQ 0 (
    echo Python 3 is not installed on this system.
    echo Please install Python 3 from the Windows App Store or download from https://www.python.org/downloads/
    REM start the Windows Appstore installer dummy
    start python.exe
    exit /b 1
) else (
    echo 'found Python:'
    python --version
)
echo "create virtual environment ..."
python -m venv venv
echo "activate the virtual environment ..."
call .\env\Scripts\activate
echo "install the requirements ..."
python -m pip install -r requirements.txt
echo "finished! You can start MoonRunner by double-click on moonrunner_gui.py or 'python moonrunner_gui.py' in a cmd line"

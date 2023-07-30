@echo off
echo "create virtual environment ..."
py -m venv env
echo "activate the virtual environment ..."
.\env\Scripts\activate
echo "install the requirements ..."
py -m pip install -r requirements.txt
echo "finished! You can start MoonRunner by double-click on moonrunner_gui.py or 'py moonrunner_gui.py' in a cmd line"

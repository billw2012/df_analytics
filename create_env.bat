@echo off
py -3 -m venv env
env\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

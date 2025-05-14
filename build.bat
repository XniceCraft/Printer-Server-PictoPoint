@echo off
pyinstaller --onefile --add-data "venv\Lib\site-packages\escpos\capabilities.json;escpos" main.py
pause
@echo off
pyinstaller --name "Printer Server" --icon "assets/icon.ico" --onefile --collect-data escpos main.py
pause
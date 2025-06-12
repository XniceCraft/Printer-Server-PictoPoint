@echo off
pyinstaller --name "Printer Server" --icon "assets/icon.ico" --add-data "assets/Picto 7.png;assets" --add-data "assets/AR QR.png;assets"  --onefile --collect-data escpos main.py
pause
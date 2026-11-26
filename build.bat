@echo off
cd /d "%~dp0"
py -3 -m PyInstaller --noconfirm --clean --windowed --name PolymerModes app.py
pause

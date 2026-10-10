@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m venv .build-env
if errorlevel 1 goto fail
call .build-env\Scripts\activate.bat
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --clean --onefile --windowed --name ScriptStudio --icon app.ico --add-data "app.ico;." --add-data "fonts;fonts" --add-data "licenses;licenses" --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets scriptstudio.py
if errorlevel 1 goto fail
echo Ready: dist\ScriptStudio.exe
pause
exit /b 0
:fail
echo Build failed. Read the error above.
pause
exit /b 1

@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt "pyinstaller>=6.16,<7"
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" tools\make_icon.py
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" tools\build.py
exit /b %errorlevel%

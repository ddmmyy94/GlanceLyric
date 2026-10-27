@echo off
REM Menonaktifkan autostart GlanceLyric.
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=%CD%\.venv"
set "EXE=%CD%\GlanceLyric.exe"
if not exist "%EXE%" set "EXE=%CD%\dist\GlanceLyric\GlanceLyric.exe"
if exist "%EXE%" (
  start "" /wait "%EXE%" --uninstall
  if errorlevel 1 exit /b 1
  exit /b 0
)

if not exist "%VENV%\Scripts\pythonw.exe" (
  echo Autostart GlanceLyric tidak aktif atau belum dipasang.
  pause
  exit /b 0
)

"%VENV%\Scripts\python.exe" "%CD%\glance_watcher.pyw" --uninstall
if errorlevel 1 exit /b 1
echo Autostart dimatikan. Folder aplikasi tetap terpasang.
pause

@echo off
REM Mengaktifkan widget GlanceLyric otomatis saat Windows mulai.
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=%CD%\.venv"
set "EXE=%CD%\GlanceLyric.exe"
if not exist "%EXE%" set "EXE=%CD%\dist\GlanceLyric\GlanceLyric.exe"
if exist "%EXE%" (
  start "" /wait "%EXE%" --install
  if errorlevel 1 exit /b 1
  start "" "%EXE%" --watch
  echo Autostart GlanceLyric aktif.
  exit /b 0
)

if not exist "%VENV%\Scripts\pythonw.exe" (
  echo GlanceLyric belum dipasang. Jalankan Install.bat terlebih dahulu.
  pause
  exit /b 1
)

"%VENV%\Scripts\python.exe" "%CD%\glance_watcher.pyw" --install
if errorlevel 1 exit /b 1
start "" "%VENV%\Scripts\pythonw.exe" "%CD%\glance_watcher.pyw"
echo Autostart aktif. Widget muncul otomatis setiap Spotify dibuka.
pause

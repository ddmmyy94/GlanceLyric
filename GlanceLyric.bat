@echo off
REM GlanceLyric v1.0 - jalankan widget (klik 2x atau lewat shortcut).
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=%CD%\.venv"
if exist "%CD%\GlanceLyric.exe" (
  start "" "%CD%\GlanceLyric.exe"
  exit /b 0
)
if exist "%CD%\dist\GlanceLyric\GlanceLyric.exe" (
  start "" "%CD%\dist\GlanceLyric\GlanceLyric.exe"
  exit /b 0
)

if not exist "%VENV%\Scripts\pythonw.exe" (
  echo GlanceLyric belum dipasang. Jalankan Install.bat terlebih dahulu.
  pause
  exit /b 1
)

start "" "%VENV%\Scripts\pythonw.exe" "%CD%\glancelyric.pyw"
exit /b 0

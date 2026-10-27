@echo off
REM Menghapus shortcut, autostart, dan virtual environment GlanceLyric.
setlocal EnableExtensions
title GlanceLyric Uninstaller
cd /d "%~dp0"
set "ROOT=%CD%"

echo.
echo  Menghapus shortcut Desktop dan Start Menu ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\install-shortcuts.ps1" -Remove
if errorlevel 1 exit /b 1

REM HKCU entry removal also works when the executable/runtime is unavailable.
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $key='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'; Remove-ItemProperty -LiteralPath $key -Name 'GlanceLyric' -ErrorAction SilentlyContinue; Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'GlanceLyric.exe' -and $_.ExecutablePath -and $_.ExecutablePath.StartsWith($env:ROOT + '\', [StringComparison]::OrdinalIgnoreCase)) -or ($_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and $_.CommandLine.Contains($env:ROOT) -and ($_.CommandLine.Contains('glancelyric.pyw') -or $_.CommandLine.Contains('glance_watcher.pyw'))) } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop }"
if errorlevel 1 exit /b 1

if exist "%ROOT%\.venv\Scripts\pythonw.exe" (
  echo  Menghapus autostart ...
  "%ROOT%\.venv\Scripts\python.exe" "%ROOT%\glance_watcher.pyw" --uninstall
  if errorlevel 1 exit /b 1
  echo  Menghapus virtual environment ...
  rmdir /s /q "%ROOT%\.venv"
)

echo  Data pengaturan tetap ada di %USERPROFILE%\.glancelyric (hapus manual bila perlu).
echo.
set /p "FULL=Juga hapus seluruh folder GlanceLyric? (Y/N): "
if /i not "%FULL%"=="Y" goto keep
REM A batch file cannot delete its own folder; hand the job to a temp script.
set "REMOVER=%TEMP%\glancelyric-remove.cmd"
echo @echo off> "%REMOVER%"
echo cd /d "%%TEMP%%">> "%REMOVER%"
echo timeout /t 3 /nobreak ^>nul>> "%REMOVER%"
echo rmdir /s /q "%ROOT%">> "%REMOVER%"
echo del "%%~f0">> "%REMOVER%"
echo  Folder akan dihapus dalam 3 detik.
start "" "%REMOVER%"
exit /b 0

:keep
echo  Selesai.
pause
exit /b 0

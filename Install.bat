@echo off
REM ==========================================================================
REM  GlanceLyric v1.0 - pemasang. Jalankan dari CMD admin:
REM      D:\Software\GlanceLyric\Install.bat
REM ==========================================================================
setlocal EnableExtensions
title GlanceLyric Installer
cd /d "%~dp0"
set "ROOT=%CD%"
set "VENV=%ROOT%\.venv"

echo.
echo  ==========================================================
echo    GlanceLyric v1.0  ^|  pemasang
echo  ==========================================================
echo.

REM --- 1. Admin? UAC akan menappear sekali -----------------------------------
powershell -NoProfile -Command "exit ([int](-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)))" >nul 2>&1
if errorlevel 1 goto need_admin

REM Paket executable membawa runtime sendiri; Python hanya untuk sumber.
set "EXE=%ROOT%\GlanceLyric.exe"
if not exist "%EXE%" set "EXE=%ROOT%\dist\GlanceLyric\GlanceLyric.exe"
if exist "%EXE%" goto executable

REM --- 2. Cari Python 64-bit 3.10+ ------------------------------------------
set "PY="
call :try_python "py -3"
call :try_python "python"
call :try_python "python3"
if not defined PY goto no_python
echo  [1/4] Python ditemukan: %PY%

REM --- 3. Virtual environment + dependensi ----------------------------------
if exist "%VENV%\Scripts\pythonw.exe" goto deps
echo  [2/4] Membuat virtual environment .venv ...
%PY% -m venv "%VENV%"
if errorlevel 1 goto venv_failed
:deps
echo  [3/4] Memasang dependensi (PySide6, requests, winrt) ...
"%VENV%\Scripts\python.exe" -m pip install --quiet --upgrade pip
"%VENV%\Scripts\python.exe" -m pip install --quiet -r "%ROOT%\requirements.txt"
if errorlevel 1 goto deps_failed
"%VENV%\Scripts\python.exe" -c "import PySide6, requests, winrt.windows.media.control"
if errorlevel 1 goto deps_failed

REM --- 4. Shortcut + autostart ----------------------------------------------
echo  [4/4] Membuat shortcut Desktop dan Start Menu ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\install-shortcuts.ps1"
if errorlevel 1 goto links_failed

set /p "AUTO=Pasang autostart saat Windows mulai? (Y/N): "
if /i not "%AUTO%"=="Y" goto done

"%VENV%\Scripts\python.exe" "%ROOT%\glance_watcher.pyw" --install
if errorlevel 1 goto failed
start "" "%VENV%\Scripts\pythonw.exe" "%ROOT%\glance_watcher.pyw"
echo  Autostart aktif: GlanceLyric muncul otomatis saat Spotify dibuka.

:done
echo.
echo  ==========================================================
echo   GlanceLyric v1.0 terpasang.
echo   Mulai sekarang  : "%ROOT%\GlanceLyric.bat"
echo   Buka pengaturan  : klik kanan widget ^> Settings
echo  ==========================================================
echo.
start "" "%VENV%\Scripts\pythonw.exe" "%ROOT%\glancelyric.pyw"
pause
exit /b 0

:executable
echo  Runtime mandiri ditemukan. Tidak perlu memasang Python.
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\install-shortcuts.ps1"
if errorlevel 1 goto links_failed
choice /c YN /n /m "Aktifkan autostart saat Spotify dibuka? (Y/N): "
if errorlevel 2 goto executable_done
start "" /wait "%EXE%" --install
if errorlevel 1 goto failed
start "" "%EXE%" --watch
:executable_done
echo  GlanceLyric v1.0 terpasang.
start "" "%EXE%"
pause
exit /b 0

REM --- Subrutin & pesan galat ------------------------------------------------
:try_python
REM %~1 keeps "py -3" unquoted, otherwise cmd looks for a program literally named "py -3".
%~1 -c "import sys;raise SystemExit(0 if sys.version_info >= (3, 10) and sys.maxsize > 2 ** 32 else 1)" >nul 2>&1
if not errorlevel 1 if not defined PY set "PY=%~1"
exit /b 0

:need_admin
echo.
echo  Membuka jendela baru dengan hak Administrator (UAC) ...
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b 0

:no_python
echo  [X] Python 64-bit versi 3.10+ tidak ditemukan.
echo      Pasang dari https://www.python.org/downloads/windows/
echo      centang "Add python.exe to PATH", lalu jalankan Install.bat lagi.
goto failed

:venv_failed
echo  [X] Gagal membuat virtual environment di %VENV%
echo      Hapus folder .venv yang tersisa lalu ulangi.
goto failed

:deps_failed
echo  [X] Gagal memasang dependensi. Periksa koneksi internet dan versi Python.
goto failed

:links_failed
echo  [X] Gagal membuat shortcut. Periksa izin tulis folder profil.
goto failed

:failed
echo.
pause
exit /b 1

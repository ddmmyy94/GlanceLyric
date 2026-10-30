"""Build a portable Windows package, including Python and Qt runtime."""
from pathlib import Path
from importlib.metadata import distribution
import hashlib
import os
import shutil
import subprocess
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from glance_backend import APP_VERSION


def main():
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--onedir', '--windowed', '--name', 'GlanceLyric',
        '--icon', str(ROOT / 'assets' / 'glancelyric.ico'),
        '--version-file', str(ROOT / 'tools' / 'version_info.txt'),
        '--add-data', f'{ROOT / "assets"};assets',
        '--collect-submodules', 'winrt',
        '--distpath', str(ROOT / 'dist'), '--workpath', str(ROOT / 'build'),
        '--specpath', str(ROOT / 'build'), str(ROOT / 'glancelyric.pyw'),
    ], cwd=ROOT, check=True)
    destination = ROOT / 'dist' / 'GlanceLyric'
    for name in ('Install.bat', 'Uninstall.bat', 'GlanceLyric.bat',
                 'Aktifkan-Autostart.bat', 'Matikan-Autostart.bat', 'README.md', 'LICENSE',
                  'THIRD-PARTY.md', 'PRIVACY.md', 'RELEASING.md'):
        shutil.copy2(ROOT / name, destination / name)
    shutil.copytree(ROOT / 'assets', destination / 'assets', dirs_exist_ok=True)
    (destination / 'tools').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'tools' / 'install-shortcuts.ps1', destination / 'tools')
    for package in ('PySide6', 'PySide6_Essentials', 'shiboken6', 'requests',
                    'urllib3', 'charset-normalizer', 'idna', 'certifi',
                    'winrt-runtime', 'winrt-Windows.Media.Control',
                    'winrt-Windows.Foundation', 'winrt-Windows.Foundation.Collections',
                    'pyinstaller'):
        dist = distribution(package)
        for file in dist.files or []:
            if file.name.lower().startswith(('license', 'copying', 'notice')):
                folder = destination / 'licenses' / package
                folder.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dist.locate_file(file), folder / file.name)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if python_license.exists():
        shutil.copy2(python_license, destination / 'licenses' / 'Python-LICENSE.txt')
    # Some wheels ship only a commercial notice, or omit their license text.
    qt_version = distribution('PySide6').version
    extra_licenses = {
        'Qt-LGPL-3.0-only.txt': f'https://raw.githubusercontent.com/qt/qtbase/v{qt_version}/LICENSES/LGPL-3.0-only.txt',
        'Qt-GPL-3.0-only.txt': f'https://raw.githubusercontent.com/qt/qtbase/v{qt_version}/LICENSES/GPL-3.0-only.txt',
        'PyWinRT-MIT.txt': 'https://raw.githubusercontent.com/pywinrt/pywinrt/main/LICENSE',
    }
    for name, url in extra_licenses.items():
        with urlopen(url, timeout=30) as response:
            (destination / 'licenses' / name).write_bytes(response.read())
    archive = shutil.make_archive(str(ROOT / 'dist' / f'GlanceLyric-v{APP_VERSION}-windows-x64'),
                                  'zip', ROOT / 'dist', 'GlanceLyric')
    print(f'Portable package: {destination}\nArchive: {archive}')
    compiler = shutil.which('ISCC.exe')
    for variable in ('ProgramFiles(x86)', 'ProgramFiles', 'LOCALAPPDATA'):
        base = os.environ.get(variable)
        if not base:
            continue
        for folder in ('Inno Setup 6', 'Programs/Inno Setup 6'):
            candidate = Path(base) / folder / 'ISCC.exe'
            if not compiler and candidate.is_file():
                compiler = str(candidate)
    if compiler:
        subprocess.run([compiler, str(ROOT / 'tools' / 'installer.iss')],
                       cwd=ROOT, check=True)
    else:
        print('Setup.exe not built: install Inno Setup 6, then run Build.bat again.')
    artifacts = [Path(archive)]
    if compiler:
        artifacts.append(ROOT / 'dist' / f'GlanceLyric-Setup-{APP_VERSION}-x64.exe')
    checksums = ''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n'
                        for path in artifacts)
    (ROOT / 'dist' / 'SHA256SUMS.txt').write_text(checksums, encoding='utf-8')


if __name__ == '__main__':
    main()

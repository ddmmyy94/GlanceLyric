"""Check local release assets after Build.bat. Uses only the Python standard library."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import re
import zipfile

ROOT = Path(__file__).resolve().parent
ASSETS = {'GlanceLyric-Setup-1.0.0-x64.exe', 'GlanceLyric-v1.0-windows-x64.zip'}


def main():
    dist = ROOT / 'dist'
    hashes = {}
    for line in (dist / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64})  ([A-Za-z0-9._-]+)', line)
        assert match, 'Invalid checksum entry'
        digest, name = match.groups()
        assert name not in hashes, 'Duplicate checksum: ' + name
        hashes[name] = digest.lower()
    assert set(hashes) == ASSETS, 'Release must include installer and portable ZIP checksums'
    for name, expected in hashes.items():
        with (dist / name).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected, name

    with zipfile.ZipFile(dist / 'GlanceLyric-v1.0-windows-x64.zip') as archive:
        assert archive.testzip() is None, 'Corrupt ZIP member'
        members = set(archive.namelist())
        for name in ('GlanceLyric.exe', 'README.md', 'LICENSE', 'THIRD-PARTY.md', 'PRIVACY.md'):
            assert 'GlanceLyric/' + name in members, 'Missing package file: ' + name
        assert any(name.startswith('GlanceLyric/licenses/') for name in members)
        forbidden = {'.git', '.venv', 'venv', 'env', 'output', 'tmp', 'secret', 'secrets'}
        assert not any(forbidden.intersection(part.lower() for part in Path(name).parts)
                       for name in members), 'Local data in ZIP'
        assert not any(part.lower().startswith('.env') or part.lower().endswith('.env')
                       or '.env.' in part.lower()
                       for name in members for part in Path(name).parts), '.env file in ZIP'
        readme = archive.read('GlanceLyric/README.md').decode('utf-8')
        links = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', readme)
        links += re.findall(r'(?:src|href)=["\']([^"\']+)["\']', readme)
        for link in links:
            url = urlsplit(link)
            if not url.scheme and url.path:
                name = 'GlanceLyric/' + unquote(url.path)
                assert name in members, 'Missing README asset: ' + name
                assert archive.read(name) == (ROOT / unquote(url.path)).read_bytes(), name
    print('PASS: installer/ZIP SHA-256, ZIP integrity, licenses, no local data, packaged README links and screenshots.')


if __name__ == '__main__':
    main()

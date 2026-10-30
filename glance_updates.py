"""Release notifications only: never download or execute an installer."""
import json
import logging
from pathlib import Path
import re
import threading
import time
from urllib.parse import quote

import requests

from glance_backend import APP_NAME, APP_VERSION, APP_PRERELEASE, DATA_DIR

RELEASES_URL = 'https://github.com/ddmmyy94/GlanceLyric/releases'
API_URL = 'https://api.github.com/repos/ddmmyy94/GlanceLyric/releases'
CHECK_INTERVAL = 24 * 60 * 60


def version_tuple(value):
    """Project tags use vMAJOR.MINOR.PATCH; accept the old two-part UI version too."""
    match = re.fullmatch(r'v?(\d+)\.(\d+)(?:\.(\d+))?', value) if isinstance(value, str) and len(value) <= 64 else None
    return tuple(int(part or 0) for part in match.groups()) if match else None


def select_update(releases, current=APP_VERSION, prereleases=APP_PRERELEASE):
    if not isinstance(releases, list):
        raise ValueError('Invalid GitHub release response')
    installed = version_tuple(current)
    if installed is None:
        raise ValueError('Invalid application version')
    newest, result = installed, None
    for release in releases:
        if not isinstance(release, dict) or release.get('draft') or (release.get('prerelease') and not prereleases):
            continue
        version = version_tuple(release.get('tag_name'))
        if version is None or version <= newest:
            continue
        number = '.'.join(map(str, version))
        assets = release.get('assets')
        packages = {f'GlanceLyric-Setup-{number}-x64.exe', f'GlanceLyric-v{number}-windows-x64.zip'}
        if not isinstance(assets, list) or not any(isinstance(asset, dict) and asset.get('name') in packages
                                                 and asset.get('state') == 'uploaded' for asset in assets):
            continue
        notes = release.get('body')
        result = dict(version=number, prerelease=bool(release.get('prerelease')),
                      url=RELEASES_URL + '/tag/' + quote(release['tag_name'], safe=''),
                      notes=notes[:12000] if isinstance(notes, str) and notes.strip() else
                      'Catatan pembaruan tersedia di halaman rilis.')
        newest = version
    return result


class UpdateChecker:
    def __init__(self, inbox, state_path=None):
        self.inbox = inbox
        self.path = Path(state_path) if state_path is not None else DATA_DIR / 'update-check.json'
        self.busy = False
        try:
            state = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            state = {}
        self.state = state if isinstance(state, dict) else {}

    def ensure(self, manual=False):
        checked = self.state.get('checked_at')
        if self.busy:
            return False
        if not manual and type(checked) in (int, float) and 0 <= checked < 1e12 and \
                0 <= time.time() - checked < CHECK_INTERVAL:
            return False
        self.busy = True
        threading.Thread(target=self._fetch, args=(manual,), daemon=True, name='UpdateChecker').start()
        return True

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(self.state, indent=2), encoding='utf-8')
            temporary.replace(self.path)
        except OSError:
            logging.warning('Cannot save update-check state')

    def mark_notified(self, version):
        self.state['notified_version'] = version
        self._save()

    def _fetch(self, manual):
        message = dict(update_check=True, manual=manual)
        try:
            # ponytail: inspect the newest 100 releases; paginate if this project outgrows that.
            response = requests.get(API_URL, params={'per_page': 100}, timeout=10, headers={
                'Accept': 'application/vnd.github+json', 'User-Agent': f'{APP_NAME}/{APP_VERSION}'})
            response.raise_for_status()
            release = select_update(response.json())
            self.state['checked_at'] = time.time()
            self._save()
            if not manual and release and release['version'] == self.state.get('notified_version'):
                release = None
            message['release'] = release
        except (requests.RequestException, ValueError, TypeError):
            message['error'] = True
        finally:
            self.busy = False
        self.inbox.put(message)

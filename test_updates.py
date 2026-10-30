"""Run: python test_updates.py. No network, Spotify, or installed app changes."""
import json
from pathlib import Path
import queue
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests

from glance_backend import APP_VERSION
from glance_updates import UpdateChecker, CHECK_INTERVAL, RELEASES_URL, select_update, version_tuple


def release(tag, **fields):
    number = tag.removeprefix('v')
    return dict(tag_name=tag, draft=False, prerelease=False, body='Perbaikan taskbar small.',
                assets=[{'name': f'GlanceLyric-Setup-{number}-x64.exe', 'state': 'uploaded'}]) | fields


def main():
    assert version_tuple('1.0') == version_tuple('v1.0.0') == (1, 0, 0)
    assert version_tuple('v1.10.0') > version_tuple('v1.9.0')
    for value in (None, [], 'bad', '1.0.0.exe', 'v1.2.3-beta.1', '1.' + '9' * 100):
        assert version_tuple(value) is None
    releases = [release('v1.0.0'), release('v1.1.0'), release('v1.10.0'),
                release('v2.0.0', draft=True), release('v3.0.0', prerelease=True),
                release('v4.0.0', assets=[]), release('v5.0.0', assets=[{'name': 'SHA256SUMS.txt'}]),
                release('v6.0.0', assets=[{'name': 'GlanceLyric-Setup-6.0.0-x64.exe', 'state': 'new'}]),
                {'tag_name': 'invalid'}, None]
    assert select_update(releases, current='1.0', prereleases=False)['version'] == '1.10.0'
    assert select_update(releases, current='1.0', prereleases=True)['version'] == '3.0.0'
    assert select_update(releases, current='9.0.0') is None
    safe = select_update([release('v1.2.0', html_url='file:///bad.exe', body='<img src=x onerror=bad()>')], current='1.1.0')
    assert safe['url'] == RELEASES_URL + '/tag/v1.2.0'
    assert safe['notes'] == '<img src=x onerror=bad()>'  # Displayed as plain text in the UI.
    assert select_update([release('v1.2.0', body=None)], current='1.1.0')['notes']
    try:
        select_update({'message': 'rate limited'})
        raise AssertionError('Malformed response accepted')
    except ValueError:
        pass

    with TemporaryDirectory() as directory:
        state = Path(directory) / 'update-check.json'
        state.write_text('[]', encoding='utf-8')
        inbox = queue.Queue()
        checker = UpdateChecker(inbox, state)
        assert not checker.state
        response = Mock()
        response.json.return_value = [release('v9.0.0')]
        with patch('glance_updates.requests.get', return_value=response) as get, \
                patch('glance_updates.time.time', return_value=100000):
            checker._fetch(False)
            message = inbox.get_nowait()
            assert message['release']['version'] == '9.0.0' and not message['manual']
            assert get.call_args.kwargs['timeout'] == 10
            assert set(get.call_args.kwargs['params']) == {'per_page'}
            checker.mark_notified('9.0.0')
            loaded = UpdateChecker(inbox, state)
            assert loaded.state['notified_version'] == '9.0.0'
            assert not loaded.ensure()  # Persisted once-a-day throttle across app restarts.
            loaded._fetch(False)
            assert inbox.get_nowait()['release'] is None
            loaded._fetch(True)
            assert inbox.get_nowait()['release']['version'] == '9.0.0'
            with patch('glance_updates.threading.Thread') as thread:
                assert loaded.ensure(manual=True)
                assert not loaded.ensure(manual=True)  # No concurrent check.
                thread.assert_called_once()
                loaded.busy = False
                loaded.state['checked_at'] = 100000 - CHECK_INTERVAL
                assert loaded.ensure()
                loaded.busy = False
                for invalid in (None, 'bad', [], 10 ** 400, float('inf'), float('nan')):
                    loaded.state['checked_at'] = invalid
                    assert loaded.ensure()
                    loaded.busy = False
            # Exercise the real daemon worker with a mocked HTTP boundary.
            assert loaded.ensure(manual=True)
            assert inbox.get(timeout=3)['release']['version'] == '9.0.0'
            assert not loaded.busy
        saved = json.loads(state.read_text())
        with patch('glance_updates.requests.get', side_effect=requests.ConnectionError('offline')):
            checker._fetch(True)
            assert inbox.get_nowait()['error'] and not checker.busy
            assert json.loads(state.read_text())['checked_at'] == saved['checked_at']
        response.json.return_value = {'message': 'bad response'}
        with patch('glance_updates.requests.get', return_value=response):
            checker._fetch(False)
            assert inbox.get_nowait()['error']
            response.raise_for_status.side_effect = requests.HTTPError('rate limited')
            checker._fetch(True)
            assert inbox.get_nowait()['error'] and not checker.busy
        state.write_text('{bad json', encoding='utf-8')
        assert not UpdateChecker(inbox, state).state

    root = Path(__file__).resolve().parent
    assert f'#define AppVersion "{APP_VERSION}"' in (root / 'tools/installer.iss').read_text()
    metadata = (root / 'tools/version_info.txt').read_text()
    assert f"StringStruct('ProductVersion', '{APP_VERSION}')" in metadata
    assert f"StringStruct('FileVersion', '{APP_VERSION}.0')" in metadata
    assert 'filevers=' + str((*version_tuple(APP_VERSION), 0)) in metadata
    print('PASS: version ordering, release channels/assets, safe release URL, notes, daily throttle,')
    print('      manual checks, duplicate suppression, offline/malformed data, consistent version metadata.')


if __name__ == '__main__':
    main()

"""Run: python test_timing.py. Deterministic playback and recording-match regressions."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import queue
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from glance_backend import TimelineClock, LyricsFetcher, matching_lyrics


def main():
    utc = datetime(2026, 11, 6, tzinfo=timezone.utc)
    clock = TimelineClock()
    def sample(pos, updated=utc, playing=True, now=100, wall=utc, key='song', rate=1):
        return clock.sample(key, pos, updated, playing, 200, rate, now=now, utc=wall)

    assert sample(10, utc - timedelta(seconds=2)) == 12
    # Wall-clock corrections must not move an unchanged SMTC snapshot.
    assert sample(10, utc - timedelta(seconds=2), now=101, wall=utc + timedelta(hours=1)) == 13
    assert sample(10, utc - timedelta(seconds=2), playing=False, now=102) == 14
    assert sample(10, utc - timedelta(seconds=2), playing=False, now=160) == 14
    assert sample(10, utc - timedelta(seconds=2), now=161) == 14
    assert sample(10, utc - timedelta(seconds=2), now=162) == 15
    assert sample(50, utc + timedelta(seconds=63), now=163, wall=utc + timedelta(seconds=63)) == 50
    assert sample(5, utc + timedelta(seconds=64), now=164, wall=utc + timedelta(seconds=64)) == 5
    assert sample(1, utc, now=165, key='next') == 1
    assert sample(20, utc - timedelta(days=5000), now=166) == 20
    assert sample(30, utc + timedelta(days=1), now=167) == 30
    assert sample(10, utc.replace(tzinfo=None), now=168, rate=2) == 10
    assert sample(10, utc.replace(tzinfo=None), now=169, rate=2) == 12

    good = dict(trackName='Title', artistName='Artist', albumName='Album', duration=100,
                syncedLyrics='[00:01]correct recording')
    wrong = good | dict(duration=130, syncedLyrics='[00:01]wrong recording')
    assert matching_lyrics(good, 'artist', 'title', 100)
    assert not matching_lyrics(wrong, 'artist', 'title', 100)
    for bad in (None, [], {}, good | dict(duration='100'), good | dict(trackName=None)):
        assert not matching_lyrics(bad, 'artist', 'title', 100)
    with TemporaryDirectory() as folder:
        inbox = queue.Queue()
        direct, search = Mock(status_code=200), Mock(status_code=200)
        direct.json.return_value = wrong
        search.json.return_value = [wrong, good]
        with patch('glance_backend.DATA_DIR', Path(folder)), \
                patch('glance_backend.requests.get', side_effect=[direct, search]) as get:
            fetcher = LyricsFetcher(inbox)
            fetcher._fetch(('song',), 'artist', 'title', 'Album', 100)
            assert inbox.get_nowait()['lines'] == [(1, 'correct recording')]
            assert get.call_count == 2
            fetcher._fetch(('song',), 'artist', 'title', 'Album', 100)
            assert inbox.get_nowait()['lines'] == [(1, 'correct recording')]
            assert get.call_count == 2  # Valid cache avoids network requests.
    print('PASS: stale/future timestamps, clock changes, pause/resume, seeks, track changes, playback rate, recording match/cache.')


if __name__ == '__main__':
    main()

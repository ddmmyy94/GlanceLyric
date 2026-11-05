"""Spotify SMTC clock and LRCLIB lookup; no GUI dependencies."""
import asyncio
import hashlib
import json
import logging
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

APP_NAME = 'GlanceLyric'
APP_VERSION = '1.1.1'
APP_PRERELEASE = True  # Early-testing builds also check published pre-releases.
APP_TITLE = f'{APP_NAME} v{APP_VERSION}'
SUPPORT_URL = 'https://sociabuzz.com/ddmmyy94/tribe'
ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR / 'assets'
DATA_DIR = Path.home() / '.glancelyric'


def parse_lrc(text):
    lines = []
    offset = re.search(r'\[offset:([+-]?\d+)\]', text or '', re.I)
    shift = int(offset[1]) / 1000 if offset else 0
    for row in (text or '').splitlines():
        stamps = re.findall(r'\[(\d+):(\d{2})(?:[.:](\d{1,3}))?\]', row)
        lyric = re.sub(r'\[[^\]]*\]', '', row).strip()
        for minutes, seconds, fraction in stamps:
            stamp = int(minutes) * 60 + int(seconds)
            stamp += int((fraction or '0').ljust(3, '0')) / 1000
            lines.append((max(0, stamp - shift), lyric))
    return sorted(lines, key=lambda item: item[0])


class PlaybackClock:
    def __init__(self):
        self.position = 0.0
        self.stamp = time.monotonic()
        self.playing = False
        self.duration = 0.0
        self.rate = 1.0

    def update(self, position, stamp, playing, duration, rate=1.0):
        self.position, self.stamp = position, stamp
        self.playing, self.duration = playing, duration
        self.rate = rate

    def at(self, now=None):
        now = time.monotonic() if now is None else now
        pos = self.position + (max(0, now - self.stamp) * self.rate if self.playing else 0)
        return max(0, min(pos, self.duration) if self.duration else pos)


class TimelineClock(PlaybackClock):
    """Anchor unchanged SMTC snapshots to monotonic time, including pause/resume."""
    def __init__(self):
        super().__init__()
        self.snapshot = None

    def sample(self, key, position, updated, playing, duration, rate=1.0, *, now=None, utc=None):
        now = time.monotonic() if now is None else now
        utc = datetime.now(timezone.utc) if utc is None else utc
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        snapshot = (key, position, updated)
        if snapshot != self.snapshot:
            age = (utc - updated).total_seconds()
            # Invalid/default/future timestamps must not jump lyrics to the end.
            if playing and 0 <= age <= 86400 and (not duration or position + age * rate <= duration + 2):
                position += age * rate
            self.snapshot = snapshot
        else:
            # Reusing an old timestamp after resume would include the paused time.
            position = self.at(now)
        self.update(position, now, playing, duration, rate)
        return self.at(now)


class SpotifyMonitor(threading.Thread):
    def __init__(self, inbox):
        super().__init__(daemon=True, name='SpotifyMonitor')
        self.inbox = inbox
        self.stop_event = threading.Event()

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        manager = None
        clock = TimelineClock()
        while not self.stop_event.is_set():
            try:
                from winrt.windows.media.control import (
                    GlobalSystemMediaTransportControlsSessionManager as Manager,
                )
                if manager is None:
                    manager = await Manager.request_async()
                sessions = [s for s in manager.get_sessions()
                            if 'spotify' in s.source_app_user_model_id.lower()]
                session = next((s for s in sessions if int(s.get_playback_info().playback_status) == 4),
                               sessions[0] if sessions else None)
                if session is None:
                    clock = TimelineClock()
                    self.inbox.put({'available': False})
                else:
                    props = await session.try_get_media_properties_async()
                    pb = session.get_playback_info()
                    tl = session.get_timeline_properties()
                    stamp = time.monotonic()
                    playing = int(pb.playback_status) == 4
                    position = tl.position.total_seconds()
                    rate = pb.playback_rate
                    rate = float(rate) if rate is not None and 0 < rate <= 4 else 1.0
                    key = (session.source_app_user_model_id, props.artist, props.title, props.album_title)
                    position = clock.sample(key, position, tl.last_updated_time, playing,
                                            tl.end_time.total_seconds(), rate, now=stamp)
                    self.inbox.put(dict(
                        available=True, artist=(props.artist or '').strip(),
                        title=(props.title or '').strip(),
                        album=(props.album_title or '').strip(),
                        position=position, stamp=stamp, playing=playing,
                        duration=tl.end_time.total_seconds(),
                        rate=rate,
                    ))
            except Exception:
                logging.exception('Spotify timeline unavailable')
                self.inbox.put({'available': False, 'error': True})
                manager = None
                clock = TimelineClock()
            await asyncio.sleep(0.2)


class LyricsFetcher:
    def __init__(self, inbox):
        self.inbox = inbox

    def ensure(self, key, artist, title, album, duration):
        threading.Thread(target=self._fetch,
                         args=(key, artist, title, album, duration), daemon=True).start()

    def _fetch(self, key, artist, title, album, duration):
        cache = DATA_DIR / 'cache-v3' / (hashlib.sha256(repr(key).encode()).hexdigest() + '.json')
        try:
            try:
                data = json.loads(cache.read_text(encoding='utf-8'))
                if not matching_lyrics(data, artist, title, duration):
                    raise ValueError('Cached lyrics do not match this recording')
            except (OSError, ValueError):
                params = {'artist_name': artist, 'track_name': title}
                if album:
                    params['album_name'] = album
                if duration:
                    params['duration'] = round(duration)
                headers = {'User-Agent': f'{APP_NAME}/{APP_VERSION}'}
                response = requests.get('https://lrclib.net/api/get', params=params,
                                        headers=headers, timeout=12)
                if response.status_code != 404:
                    response.raise_for_status()
                    data = response.json()
                else:
                    data = {}
                if not matching_lyrics(data, artist, title, duration):
                    response = requests.get('https://lrclib.net/api/search',
                                            params={'q': f'{artist} {title}'},
                                            headers=headers, timeout=12)
                    response.raise_for_status()
                    candidates = [c for c in response.json() if matching_lyrics(c, artist, title, duration)]
                    data = min(candidates, key=lambda c: (
                        (c.get('albumName') or '').casefold() != album.casefold() if album else False,
                        abs((c.get('duration') or 0) - duration)),
                               default={})
                if data.get('syncedLyrics') or data.get('instrumental'):
                    try:
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        cache.write_text(json.dumps(data), encoding='utf-8')
                    except OSError:
                        logging.exception('Cannot save lyric cache')
            self.inbox.put({'lyrics_key': key, 'lines': parse_lrc(data.get('syncedLyrics')),
                            'instrumental': bool(data.get('instrumental'))})
        except Exception:
            logging.exception('Lyrics lookup failed')
            self.inbox.put({'lyrics_key': key, 'lines': [], 'error': True})


def matching_lyrics(data, artist, title, duration):
    return (isinstance(data, dict)
            and isinstance(data.get('trackName'), str) and data['trackName'].casefold() == title.casefold()
            and isinstance(data.get('artistName'), str) and data['artistName'].casefold() == artist.casefold()
            and (not duration or (type(data.get('duration')) in (int, float)
                                  and abs(data['duration'] - duration) < 3))
            and bool(data.get('syncedLyrics') or data.get('instrumental')))

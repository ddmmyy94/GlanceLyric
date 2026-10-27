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
APP_VERSION = '1.0'
APP_TITLE = f'{APP_NAME} v{APP_VERSION}'
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

    def update(self, position, stamp, playing, duration):
        self.position, self.stamp = position, stamp
        self.playing, self.duration = playing, duration

    def at(self, now=None):
        now = time.monotonic() if now is None else now
        pos = self.position + (max(0, now - self.stamp) if self.playing else 0)
        return max(0, min(pos, self.duration) if self.duration else pos)


class SpotifyMonitor(threading.Thread):
    def __init__(self, inbox):
        super().__init__(daemon=True, name='SpotifyMonitor')
        self.inbox = inbox
        self.stop_event = threading.Event()

    def run(self):
        asyncio.run(self._run())

    async def _run(self):
        manager = None
        while not self.stop_event.is_set():
            try:
                from winrt.windows.media.control import (
                    GlobalSystemMediaTransportControlsSessionManager as Manager,
                )
                if manager is None:
                    manager = await Manager.request_async()
                session = next((s for s in manager.get_sessions()
                                if 'spotify' in s.source_app_user_model_id.lower()), None)
                if session is None:
                    self.inbox.put({'available': False})
                else:
                    props = await session.try_get_media_properties_async()
                    pb = session.get_playback_info()
                    tl = session.get_timeline_properties()
                    stamp = time.monotonic()
                    playing = int(pb.playback_status) == 4
                    position = tl.position.total_seconds()
                    # SMTC position belongs to LastUpdatedTime, not poll time.
                    # Repeated snapshots must not rewind the locally running clock.
                    updated = tl.last_updated_time
                    if updated.tzinfo is None:
                        updated = updated.replace(tzinfo=timezone.utc)
                    age = max(0.0, (datetime.now(timezone.utc) - updated).total_seconds())
                    if playing:
                        position += age
                    self.inbox.put(dict(
                        available=True, artist=(props.artist or '').strip(),
                        title=(props.title or '').strip(),
                        album=(props.album_title or '').strip(),
                        position=position, stamp=stamp, playing=playing,
                        duration=tl.end_time.total_seconds(),
                    ))
            except Exception:
                logging.exception('Spotify timeline unavailable')
                self.inbox.put({'available': False, 'error': True})
                manager = None
            await asyncio.sleep(0.2)


class LyricsFetcher:
    def __init__(self, inbox):
        self.inbox = inbox

    def ensure(self, key, artist, title, album, duration):
        threading.Thread(target=self._fetch,
                         args=(key, artist, title, album, duration), daemon=True).start()

    def _fetch(self, key, artist, title, album, duration):
        cache = DATA_DIR / 'cache-v2' / (hashlib.sha256(repr(key).encode()).hexdigest() + '.json')
        try:
            try:
                data = json.loads(cache.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                params = {'artist_name': artist, 'track_name': title}
                if album:
                    params['album_name'] = album
                if duration:
                    params['duration'] = round(duration)
                headers = {'User-Agent': f'{APP_NAME}/{APP_VERSION}'}
                response = requests.get('https://lrclib.net/api/get', params=params,
                                        headers=headers, timeout=12)
                if response.status_code == 404:
                    response = requests.get('https://lrclib.net/api/search',
                                            params={'q': f'{artist} {title}'},
                                            headers=headers, timeout=12)
                    response.raise_for_status()
                    candidates = [c for c in response.json()
                                  if c.get('trackName', '').casefold() == title.casefold()
                                  and c.get('artistName', '').casefold() == artist.casefold()
                                   and (not duration or abs((c.get('duration') or 0) - duration) < 3)
                                  and (c.get('syncedLyrics') or c.get('instrumental'))]
                    data = min(candidates, key=lambda c: abs((c.get('duration') or 0) - duration),
                               default={})
                else:
                    response.raise_for_status()
                    data = response.json()
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

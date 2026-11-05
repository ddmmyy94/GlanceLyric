# Privacy notes

GlanceLyric reads the Spotify desktop app's media session through Windows SMTC
to obtain track metadata, playback status, and the playback timeline.

For lyric lookup, the application sends song metadata to
[LRCLIB](https://lrclib.net), including the title, artist, and, depending on the
lookup, album and duration. LRCLIB receives these requests and the connection's
public IP address as part of normal network communication.

Starting with v1.1.0, GlanceLyric also requests public
release information from GitHub to check for updates. GitHub receives the
connection's public IP address and a User-Agent containing the application name
and version. These requests contain no song metadata or browser identifier.
You can turn off automatic checks in Settings and use **Check for updates…**
when you choose. v1.0 does not make these update-check requests.

The checker stores its last successful check time, last notified version, and
any skipped version in `%USERPROFILE%\.glancelyric\update-check.json`.
From v1.1.1, the watcher checks at Windows login even without Spotify, if you
enable autostart and automatic checks. The widget also checks after opening.
Automatic requests run at most once per hour after success, plus a fresh check
at login; offline failures retry every five minutes while running. A shared
local lock prevents simultaneous watcher/widget checks and duplicate windows.
v1.1.0 checks only from the open widget, at most once per day after success.
Clicking **Download** opens GitHub in your browser. GlanceLyric does not download
or execute updates on your behalf.

GlanceLyric stores settings, cached lyrics, and diagnostic logs under
`%USERPROFILE%\.glancelyric`. The v1.1.1 installer selects autostart by default
for new installations; you can deselect it or change it in Settings. Autostart creates a `GlanceLyric` value
in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` for your Windows account.

The application does not require a Spotify account password or Spotify API key.
The current source does not include analytics or a donation payment processor.
If you follow a donation link, the payment provider will handle the
payment under its own privacy policy.

Uninstalling the application keeps the local data folder. You can delete that
folder yourself to remove settings, cache, and logs.

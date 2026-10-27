# Privacy notes

GlanceLyric reads the Spotify desktop app's media session through Windows SMTC
to obtain track metadata, playback status, and the playback timeline.

For lyric lookup, the application sends song metadata to
[LRCLIB](https://lrclib.net), including the title, artist, and, depending on the
lookup, album and duration. LRCLIB receives these requests and the connection's
public IP address as part of normal network communication.

GlanceLyric stores settings, cached lyrics, and diagnostic logs under
`%USERPROFILE%\.glancelyric`. Optional autostart creates a `GlanceLyric` value
in `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` for your Windows account.

The application does not require a Spotify account password or Spotify API key.
The current source does not include analytics or a donation payment processor.
If you follow a donation link, the payment provider will handle the
payment under its own privacy policy.

Uninstalling the application keeps the local data folder. You can delete that
folder yourself to remove settings, cache, and logs.

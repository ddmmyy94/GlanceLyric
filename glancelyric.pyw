"""GlanceLyric executable and source entry point."""
import sys


def check(report_path):
    """Check the packaged runtime without Spotify or network access."""
    import json
    import traceback
    from pathlib import Path

    report = {'ok': False}
    try:
        from PySide6.QtWidgets import QApplication
        from glance_backend import APP_TITLE, parse_lrc
        from glance_settings import DEFAULTS, SettingsDialog
        from glance_widget import LyricWidget
        from glance_win32 import app_command
        from glance_watcher import Watcher
        from glance_update_ui import UpdateDialog
        import winrt.windows.media.control
        import winrt.windows.foundation
        import winrt.windows.foundation.collections
        import asyncio

        async def media_check():
            manager = await winrt.windows.media.control.GlobalSystemMediaTransportControlsSessionManager.request_async()
            for session in manager.get_sessions():
                if 'spotify' in session.source_app_user_model_id.lower():
                    await session.try_get_media_properties_async()
                    session.get_timeline_properties()
                    session.get_playback_info().playback_rate
            return True

        media_ready = asyncio.run(media_check())

        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
        dialog = SettingsDialog(DEFAULTS)
        widget = LyricWidget(start_monitor=False, config=DEFAULTS)
        assert dialog.windowTitle() == APP_TITLE
        assert not dialog.windowIcon().pixmap(16, 16).isNull()
        assert parse_lrc('[00:01]GlanceLyric') == [(1.0, 'GlanceLyric')]
        assert len(widget.labels) == 2
        assert any(action.text() == 'Support this Project' for action in widget.menu.actions())
        update_dialog = UpdateDialog(dict(version='9.0.0', prerelease=True, notes='Runtime check',
                                          url='https://github.com/ddmmyy94/GlanceLyric/releases'),
                                     widget.updater, 'Dark')
        assert update_dialog.notes.toPlainText() == 'Runtime check'
        assert update_dialog.download.text() == 'Download'
        update_dialog.close()
        launches = []
        watcher = Watcher(detect=lambda: {1}, launch=lambda: launches.append(True))
        watcher.poll()
        watcher.poll()
        assert launches == [True]
        report.update(ok=True, title=APP_TITLE, icon=True, smtc_imports=True,
                      update_dialog=True, support_menu=True,
                      smtc_connection=media_ready,
                      watch_command=app_command('--watch'))
        widget.close()
        dialog.close()
    except Exception:
        report['error'] = traceback.format_exc()
    Path(report_path).write_text(json.dumps(report, indent=2), encoding='utf-8')
    return 0 if report['ok'] else 1


def main():
    if '--check' in sys.argv:
        return check(sys.argv[sys.argv.index('--check') + 1])
    if any(flag in sys.argv for flag in ('--watch', '--install', '--uninstall')):
        from glance_watcher import main as watch
        watch()
    else:
        from glance_widget import main as widget
        widget()
    return 0

if __name__ == '__main__':
    sys.exit(main())

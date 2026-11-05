"""Run: python test_update_ui.py. Login notices without Spotify; no network/registry changes."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from glance_settings import DEFAULTS
from glance_update_ui import UpdatePresenter


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with TemporaryDirectory() as folder:
        state = Path(folder) / 'updates.json'
        first = UpdatePresenter(settings=lambda: DEFAULTS, state_path=state)
        other = UpdatePresenter(settings=lambda: DEFAULTS, state_path=state)
        first.start(login=True)
        assert first.startup_pending and first.timer.isActive() and first.results.isActive()
        with patch.object(first.checker, 'ensure', return_value=True) as request:
            first.check()
            request.assert_called_once_with(manual=False, startup=True)
        with patch.object(other.checker, 'ensure') as request:
            other.check()
            request.assert_not_called()  # Cross-process lock also covers the in-flight request.
        first.show_result(dict(manual=False, error=True))
        assert first.startup_pending and not first.lock.isLocked() and first.dialog is None
        with patch.object(first.checker, 'ensure', return_value=True) as request:
            first.check()
            request.assert_called_once_with(manual=False, startup=True)
        release = dict(version='9.0.0', prerelease=False, notes='<b>Plain text</b>\n' * 200,
                       url='https://github.com/ddmmyy94/GlanceLyric/releases/tag/v9.0.0')
        first.show_result(dict(manual=False, release=release))
        app.processEvents()
        assert not first.startup_pending and first.dialog.isVisible()
        assert first.dialog.notes.toPlainText() == release['notes']
        assert first.dialog.screen().availableGeometry().contains(first.dialog.frameGeometry())
        if len(sys.argv) > 1:
            assert first.dialog.grab().save(str(Path(sys.argv[1]) / 'glancelyric-update.png'))
        with patch.object(other.checker, 'ensure') as request:
            other.check()
            request.assert_not_called()  # No duplicate popup while the login notice is visible.
        first.dialog.later.click()
        assert not first.lock.isLocked()
        with patch.object(other.checker, 'ensure', return_value=False) as request:
            other.check()
            request.assert_called_once_with(manual=False)
            assert other.checker.state['notified_version'] == '9.0.0'
        first.show_result(dict(manual=True, release=release))
        first.dialog.skip.click()
        other.checker.reload()
        assert other.checker.state['skipped_version'] == '9.0.0'
        disabled = UpdatePresenter(settings=lambda: DEFAULTS | dict(check_updates=False), state_path=state)
        with patch.object(disabled.checker, 'ensure') as request:
            disabled.check()
            request.assert_not_called()
        disabled.stop()
        first.stop()
        other.stop()
    print('PASS: login update check without Spotify, offline retry, scrollable plain-text notes, duplicate lock, skip/later, preferences.')


if __name__ == '__main__':
    main()

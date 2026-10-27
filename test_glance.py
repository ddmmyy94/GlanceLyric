"""Run: python test_glance.py [screenshot-directory]. No network/Spotify required."""
from pathlib import Path
import math
import queue
import runpy
import sys
import tempfile
from unittest.mock import Mock, patch

from PySide6.QtCore import QRect, Qt, QPointF, QEvent
from PySide6.QtGui import QEnterEvent, QCursor
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

import glance_backend
import glance_win32
import glance_watcher
import glance_settings as settings
from glance_widget import LyricWidget
from glance_win32 import dock_rect, taskbar_geometry, spotify_pids


def main():
    # Shared backend checks retained from the retired desktop-overlay tests.
    lines = glance_backend.parse_lrc('[offset:100]\n[00:01.20][00:03.20]Hello\n[00:04.00]')
    assert [text for _, text in lines] == ['Hello', 'Hello', '']
    assert all(math.isclose(actual[0], expected)
               for actual, expected in zip(lines, [1.1, 3.1, 3.9]))
    clock = glance_backend.PlaybackClock()
    clock.update(10, 100, True, 200)
    assert clock.at(102) == 12
    clock.update(12, 102, False, 200)
    assert clock.at(105) == 12
    clock.update(3, 105, True, 200)
    assert clock.at(105) == 3

    # Frozen launch/Run registration must point to the executable, not a .pyw.
    with patch.object(sys, 'frozen', True, create=True), \
            patch.object(sys, 'executable', r'D:\Software\GlanceLyric\GlanceLyric.exe'):
        expected = [sys.executable, '--watch']
        assert glance_win32.app_command('--watch') == expected
        with patch.object(glance_win32.subprocess, 'Popen') as launch:
            glance_win32.start_widget()
            assert launch.call_args.args[0] == [sys.executable]
            assert launch.call_args.kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'] == '1'
        with patch.object(glance_watcher.winreg, 'CreateKey') as registry, \
                patch.object(glance_watcher.winreg, 'SetValueEx') as save_run:
            glance_watcher.install_autostart()
            assert save_run.call_args.args[1] == 'GlanceLyric'
            assert save_run.call_args.args[4] == glance_watcher.subprocess.list2cmdline(expected)

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    # Geometry includes negative monitor origins, vertical/top bars, and auto-hide.
    screen = QRect(0, 0, 1920, 1080)
    bar, tray = QRect(0, 1032, 1920, 48), QRect(1680, 1032, 240, 48)
    rect = dock_rect(screen, bar, tray, 320, 42)
    assert rect.right() < tray.left() and bar.contains(rect)
    assert dock_rect(screen, bar, tray, 320, 70).bottom() < bar.top()
    top = dock_rect(screen, QRect(0, 0, 1920, 48), QRect(1680, 0, 240, 48), 320, 70)
    assert top.top() >= 48
    left = dock_rect(screen, QRect(0, 0, 48, 1080), QRect(0, 900, 48, 180), 320, 42)
    assert left.left() >= 48
    negative = QRect(-1920, -200, 1920, 1080)
    assert negative.contains(dock_rect(negative, QRect(-1920, 832, 1920, 48),
                                      QRect(-240, 832, 240, 48), 320, 42))
    assert screen.contains(dock_rect(screen, QRect(0, 1078, 1920, 48), QRect(), 320, 42))
    assert screen.contains(dock_rect(screen, QRect(), QRect(), 320, 42))
    # Actual Windows 11 layout: 72px shell surface, 48px NetSpeedTray row.
    shell = QRect(0, 1008, 1920, 72)
    speed = QRect(1563, 1032, 85, 48)
    notification = QRect(1656, 1008, 264, 72)
    docked = dock_rect(screen, shell, notification, 260, 42, speed)
    assert docked == QRect(1295, 1035, 260, 42)
    assert speed.left() - (docked.right() + 1) == 8
    assert docked.center().y() == speed.center().y()
    assert not docked.intersects(speed) and shell.contains(docked)
    # Follow a changed network-widget width without overlap; ignore free-floating windows.
    wider = QRect(1460, 1032, 188, 48)
    assert dock_rect(screen, shell, notification, 260, 42, wider).right() == 1451
    assert dock_rect(screen, shell, notification, 260, 42, QRect(500, 500, 85, 48)) == \
        dock_rect(screen, shell, notification, 260, 42)
    assert isinstance(spotify_pids(), set)
    assert any(s.geometry().contains(taskbar_geometry(320, 42)) for s in app.screens())

    # Exiting the child must NOT reopen it until the Spotify process session changes.
    Watcher = runpy.run_path(str(Path(__file__).with_name('glance_watcher.pyw')))['Watcher']
    launches = []
    processes = iter([set(), {1, 2}, {1, 2}, {1, 3}, set(), {4}, {5}])
    watcher = Watcher(detect=lambda: next(processes), launch=lambda: launches.append(True))
    for expected in [0, 1, 1, 1, 1, 2, 3]:
        watcher.poll()
        assert len(launches) == expected

    with tempfile.TemporaryDirectory() as directory:
        inbox = queue.Queue()
        missing = Mock(status_code=404)
        search = Mock()
        search.json.return_value = [
            dict(trackName='title', artistName='artist', duration=None, syncedLyrics='[00:01]bad'),
            dict(trackName='title', artistName='artist', duration=100, syncedLyrics='[00:01]good')]
        with patch.object(glance_backend, 'DATA_DIR', Path(directory)), \
                patch.object(glance_backend.requests, 'get', side_effect=[missing, search]):
            glance_backend.LyricsFetcher(inbox)._fetch(('test',), 'artist', 'title', '', 100)
        assert inbox.get_nowait()['lines'] == [(1, 'good')]
        settings.CONFIG_PATH = Path(directory) / 'config.json'
        settings.CONFIG_PATH.write_text('[]', encoding='utf-8')
        assert settings.load_settings() == settings.DEFAULTS
        bad = settings.normalize(dict(font_size='bad', transparency=999, offset=float('nan'),
                                      theme='wrong', text_color='not a color'))
        assert bad['font_size'] == 9 and bad['transparency'] == 100 and bad['offset'] == 0
        widget = LyricWidget(start_monitor=False, config=settings.DEFAULTS)
        widget.show()
        app.processEvents()
        assert len(widget.labels) == 2
        anchor = widget.geometry()
        long_line = 'If you wanted, you could make it all worth it, worth it, worth it, worth it, oh'
        original_fonts = [label.font() for label in widget.labels]
        widget.set_text(long_line, 'Next lyric')
        app.processEvents()
        assert widget.labels[0].text() == long_line
        assert all(label.alignment() & Qt.AlignmentFlag.AlignRight for label in widget.labels)
        assert widget.full_text[0] == long_line
        assert widget.labels[0].geometry().bottom() < widget.labels[1].geometry().top()
        assert widget.width() > 260 and widget.x() < anchor.x()
        assert widget.geometry().right() == anchor.right()
        assert widget.labels[0].fontMetrics().horizontalAdvance(long_line) <= widget.labels[0].width()
        assert not widget.toolTip()  # Long lyrics must not spawn a taskbar-covering popup.
        for text in ['W' * 1000, 'line one\nline two\nline three', '♪ 歌詞 ' * 100]:
            widget.set_text(text, text)
            app.processEvents()
            assert widget.geometry().right() == anchor.right()
            assert widget.y() == anchor.y() and widget.height() == anchor.height()
            assert any(s.geometry().contains(widget.geometry()) for s in app.screens())
            for label, font in zip(widget.labels, original_fonts):
                assert label.font() == font
                assert '\n' not in label.text()
                assert label.text() == ' '.join(text.split())
                assert widget.rect().contains(label.geometry())
        widget.set_text('Short lyric', 'Next')
        app.processEvents()
        assert widget.geometry() == anchor
        widget.set_text('Short lyric', long_line)
        app.processEvents()
        assert widget.width() > 260 and widget.geometry().right() == anchor.right()
        assert widget.labels[1].fontMetrics().horizontalAdvance(long_line) <= widget.labels[1].width()
        assert [a.text() for a in widget.menu.actions() if not a.isSeparator()] == [
            'Settings', 'Show Spotify', 'About GlanceLyric', 'Exit']
        lyric_geometry = widget.geometry()
        label_geometry = [label.geometry() for label in widget.labels]
        point = QPointF(widget.rect().center())
        QApplication.sendEvent(widget, QEnterEvent(point, point, QPointF(widget.mapToGlobal(point.toPoint()))))
        app.processEvents()
        assert all(button.isVisible() for button in widget.buttons)
        assert widget.controls.isWindow()
        assert widget.controls.geometry().bottom() < widget.geometry().top()
        assert widget.geometry() == lyric_geometry
        assert [label.geometry() for label in widget.labels] == label_geometry
        QCursor.setPos(widget.controls.geometry().center())
        QApplication.sendEvent(widget, QEvent(QEvent.Type.Leave))
        QTest.qWait(160)
        assert widget.controls.isVisible()
        widget.set_text('Short', 'Next')
        app.processEvents()
        assert abs(widget.controls.geometry().center().x() - widget.geometry().center().x()) <= 1
        assert not widget.controls.geometry().intersects(widget.geometry())
        QTest.mouseClick(widget.buttons[0], Qt.MouseButton.LeftButton)
        assert widget.offset == 0.1 and settings.load_settings()['offset'] == 0.1
        QTest.mouseClick(widget.buttons[1], Qt.MouseButton.LeftButton)
        assert widget.offset == 0
        QCursor.setPos(widget.screen().availableGeometry().center())
        QApplication.sendEvent(widget.controls, QEvent(QEvent.Type.Leave))
        QTest.qWait(160)
        assert not any(button.isVisible() for button in widget.buttons)
        widget.key = ('artist', 'title', 'album', 100)
        widget.inbox.put({'lyrics_key': ('old',), 'lines': [(0, 'stale')]})
        widget.tick()
        assert widget.lines == []
        widget.inbox.put({'lyrics_key': widget.key, 'lines': [
            (1, 'first'), (2, 'second'), (3, 'third'), (4, 'fourth'), (5, 'fifth')]})
        widget.clock.update(0, 0, False, 100)
        widget.tick()
        assert widget.full_text == ('♪', 'first')
        widget.clock.update(1, 0, False, 100)
        widget.tick()
        assert widget.full_text == ('first', 'second')
        # Neither row nor geometry is refreshed during the second line or pause.
        with patch.object(widget, 'set_text', wraps=widget.set_text) as render:
            for position in (2, 2.5, 2.999, 2.999):
                widget.clock.update(position, 0, False, 100)
                widget.tick()
                assert widget.full_text == ('first', 'second')
            render.assert_not_called()
        widget.clock.update(3, 0, False, 100)
        widget.tick()
        assert widget.full_text == ('third', 'fourth')
        widget.clock.update(5, 0, False, 100)
        widget.tick()
        assert widget.full_text == ('fifth', '')
        widget.clock.update(2, 0, False, 100)
        widget.tick()
        assert widget.full_text == ('first', 'second')
        widget.clock.update(2.95, 0, False, 100)
        widget.nudge_offset(0.1)
        widget.tick()
        assert widget.full_text == ('third', 'fourth')
        widget.nudge_offset(-0.1)
        widget.tick()
        assert widget.full_text == ('first', 'second')
        # Blank timed entries retain their slots; an odd final chunk has no duplicate.
        widget.inbox.put({'lyrics_key': widget.key, 'lines': [(1, ''), (2, 'second')]})
        widget.tick()
        assert widget.full_text == ('♪', 'second')
        widget.inbox.put({'available': False})
        widget.tick()
        assert widget.lines == [] and widget.key is None

        widget.open_settings()
        app.processEvents()
        # Title bar must carry the app mark and name, like NetSpeedTray's dialog.
        assert widget.settings.windowTitle() == 'GlanceLyric v1.0'
        assert widget.windowTitle() == 'GlanceLyric v1.0'
        for icon in (widget.windowIcon(), widget.settings.windowIcon()):
            assert not icon.isNull() and not icon.pixmap(16, 16).isNull()
        widget.settings.size_slider.setValue(12)
        widget.settings.theme.setCurrentText('Light')
        widget.settings.reject()
        assert widget.config['font_size'] == 9 and widget.config['theme'] == 'Dark'
        widget.open_settings()
        widget.settings.size_slider.setValue(11)
        widget.settings.transparency.setValue(25)
        widget.settings.save()
        assert widget.config['font_size'] == 11 and widget.config['transparency'] == 25
        assert settings.load_settings()['font_size'] == 11
        for theme in ('Dark', 'Light', 'System'):
            widget.config['theme'] = theme
            widget.apply_settings()
            app.processEvents()
        widget.config.update(settings.DEFAULTS)
        widget.apply_settings()
        widget.set_text('Lirik yang sedang diputar', 'Baris lirik berikutnya')
        widget.open_settings()
        app.processEvents()
        if len(sys.argv) > 1:
            destination = Path(sys.argv[1])
            assert destination.is_dir()
            assert widget.grab().save(str(destination / 'glancelyric-widget.png'))
            assert widget.settings.grab().save(str(destination / 'glancelyric-settings.png'))
        widget.settings.close()
        if len(sys.argv) > 1:
            widget.menu.popup(widget.geometry().topLeft())
            app.processEvents()
            assert widget.menu.grab().save(str(destination / 'glancelyric-menu.png'))
            widget.menu.close()
        widget.close()
        assert not widget.controls.isVisible() and not widget.hover_timer.isActive()
    print('PASS: LRC parsing, playback clock, docking, native process detection, session autostart, settings Save/Cancel,')
    print('      floating hover controls, timing persistence, static lyric pages, seek, stale results, themes.')
    print('      executable launch, isolated child runtime, executable autostart, title bar and icon.')


if __name__ == '__main__':
    main()

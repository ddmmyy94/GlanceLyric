"""Native Qt resize regression; fake Win32 measurements, never resize the Windows taskbar.

Run: python test_taskbar.py [evidence-directory]
Test DPI without changing Windows: set QT_SCALE_FACTOR to 1, 1.25, or 1.5.
"""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QRect
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import glance_settings
import glance_win32
from glance_updates import UpdateChecker
from glance_widget import LyricWidget


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    screen = app.primaryScreen()
    area, ratio = screen.geometry(), screen.devicePixelRatio()
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if output:
        output.mkdir(parents=True, exist_ok=True)
    rectangles, scenario, results = {}, {'neighbor': None, 'shell': True}, []

    def physical(rect):
        return QRect(area.x() + round((rect.x() - area.x()) * ratio),
                     area.y() + round((rect.y() - area.y()) * ratio),
                     round(rect.width() * ratio), round(rect.height() * ratio))

    def find_window(class_name, title):
        if class_name == 'Shell_TrayWnd':
            return 1 if scenario['shell'] else 0
        return 3 if scenario['neighbor'] and title == scenario['neighbor'] else 0

    def measure(size, edge):
        extra = 24 if scenario['neighbor'] else 0
        row_y = area.top() if edge == 'top' else area.bottom() - size + 1
        shell_y = area.top() if edge == 'top' else area.bottom() - size - extra + 1
        row = QRect(area.left(), row_y, area.width(), size)
        shell = QRect(area.left(), shell_y, area.width(), size + extra)
        tray = QRect(area.right() - 239, shell_y, 240, size + extra)
        neighbor = QRect(tray.left() - 93, row_y, 85, size)
        rectangles.update({1: physical(shell), 2: physical(tray), 3: physical(neighbor)})
        return row, neighbor if scenario['neighbor'] else tray

    with TemporaryDirectory() as directory, \
            patch.object(glance_win32.user32, 'FindWindowW', side_effect=find_window), \
            patch.object(glance_win32.user32, 'FindWindowExW', return_value=2), \
            patch.object(glance_win32.user32, 'IsWindowVisible', return_value=True), \
            patch.object(glance_win32, 'native_rect', side_effect=lambda hwnd: rectangles.get(hwnd, QRect())):
        measure(72, 'bottom')
        widget = LyricWidget(start_monitor=False, config=glance_settings.DEFAULTS)
        widget.updater = UpdateChecker(widget.inbox, Path(directory) / 'updates.json')
        try:
            widget.set_text('Pengujian taskbar GlanceLyric', 'Dua baris tetap di dalam taskbar')
            widget.show()
            app.processEvents()
            for neighbor in (None, 'NetSpeedTray', 'TrafficMonitor'):
                scenario['neighbor'] = neighbor
                for edge in ('bottom', 'top'):
                    for preferred in (7, 9, 20):
                        widget.config['font_size'] = preferred
                        configured = QFont(widget.config['font_family'], preferred)
                        normal_size = max(72, QFontMetrics(configured, widget.labels[0]).height() * 2 + 6)
                        restored = None
                        for index, size in enumerate((normal_size, 48, 40, 32, 24, 32, 48, normal_size)):
                            row, anchor = measure(size, edge)
                            widget.dock()
                            app.processEvents()
                            geometry = widget.geometry()
                            assert row.contains(geometry), (ratio, neighbor, edge, preferred, size, geometry, row)
                            assert anchor.left() - geometry.right() - 1 == 8
                            assert not geometry.intersects(anchor)
                            assert geometry.center().y() in (row.center().y(), row.center().y() + 1)
                            assert widget.labels[0].geometry().bottom() < widget.labels[1].geometry().top()
                            assert widget.config['font_size'] == preferred
                            for label in widget.labels:
                                assert label.fontMetrics().height() <= label.height()
                                assert widget.rect().contains(label.geometry())
                            if restored is None:
                                restored = widget.labels[0].font()
                            if index == 7:
                                assert widget.labels[0].font() == restored
                                assert restored == configured
                            results.append(dict(neighbor=neighbor, edge=edge, preferred=preferred, row=size,
                                                font=widget.labels[0].font().pointSizeF(),
                                                geometry=[geometry.x(), geometry.y(), geometry.width(), geometry.height()]))
                            if output and edge == 'bottom' and preferred == 9 and index in (0, 3, 4, 7):
                                name = f"{'neighbor' if neighbor else 'plain'}-{neighbor or 'none'}-{index}-{size}.png"
                                assert widget.grab().save(str(output / name))

            # A paused song does not change text: the docking timer must still detect a resize.
            scenario['neighbor'] = 'NetSpeedTray'
            widget.config['font_size'] = 9
            measure(72, 'bottom')
            widget.dock()
            normal_font = widget.labels[0].font()
            saved_text = widget.full_text
            widget.dock_timer.setInterval(20)
            widget.dock_timer.start()
            row, _ = measure(24, 'bottom')
            QTest.qWait(150)
            assert row.contains(widget.geometry()) and widget.labels[0].font() != normal_font
            row, _ = measure(72, 'bottom')
            QTest.qWait(150)
            assert row.contains(widget.geometry()) and widget.labels[0].font() == normal_font
            assert widget.full_text == saved_text
            widget.dock_timer.stop()

            # Explorer disappears/reappears, and auto-hide exposes a thin edge.
            scenario['shell'] = False
            widget.dock()
            app.processEvents()
            assert area.contains(widget.geometry())
            scenario.update(shell=True, neighbor=None)
            hidden, _ = measure(2, 'bottom')
            widget.dock()
            app.processEvents()
            assert widget.height() >= 42 and widget.geometry().bottom() < hidden.top()
            row, _ = measure(48, 'bottom')
            widget.dock()
            app.processEvents()
            assert row.contains(widget.geometry())
        finally:
            widget.close()
    report = dict(scale=ratio, platform=app.platformName(), cases=len(results),
                  timer_resize_restore=True, explorer_recovery=True, auto_hide=True,
                  windows_taskbar_settings_changed=False, results=results)
    if output:
        (output / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'PASS: {len(results)} native Qt layout cases at scale {ratio}; timer resize/restore, Explorer recovery, auto-hide.')


if __name__ == '__main__':
    main()

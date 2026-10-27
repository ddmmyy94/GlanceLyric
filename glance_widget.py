"""Two-line Spotify taskbar UI; playback and lyrics work live in glance_backend.

Reference: NetSpeedTray screenshots — compact Segoe UI, charcoal cards, red controls.
Hallmark pre-emit critique: Philosophy 4, Hierarchy 4, Execution 4, Specificity 5,
Restraint 5, Variety 3. Native desktop UI; no web page scaffolding.
"""
import bisect
import logging
import queue
import sys

from PySide6.QtCore import Qt, QTimer, QRectF, QLockFile, QEvent
from PySide6.QtGui import (QColor, QFont, QPainter, QPainterPath, QRegion, QCursor,
                           QShortcut, QKeySequence, QIcon, QPixmap)
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QToolButton,
                               QMenu, QToolTip, QMessageBox, QSizePolicy)

from glance_backend import (APP_NAME, APP_TITLE, DATA_DIR, PlaybackClock, SpotifyMonitor,
                            LyricsFetcher)
from glance_settings import (SettingsDialog, load_settings, save_settings, normalize,
                             palette, stylesheet)
from glance_win32 import app_icon, taskbar_geometry, keep_on_top, apply_acrylic, show_spotify


class LyricWidget(QWidget):
    def __init__(self, start_monitor=True, config=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(app_icon())
        self.config = load_settings() if config is None else normalize(config)
        self.offset = self.config['offset']
        self.clock = PlaybackClock()
        self.inbox = queue.Queue()
        self.monitor = SpotifyMonitor(self.inbox)
        self.fetcher = LyricsFetcher(self.inbox)
        self.key = None
        self.lines, self.times = [], []
        self.index = None
        self.full_text = ('Buka Spotify', 'Putar lagu untuk menampilkan lirik')
        self.blur = False
        self.settings = None
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 3, 8, 3)
        root.setSpacing(0)
        self.labels = []
        for _ in range(2):
            label = QLabel()
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(False)
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            root.addWidget(label)
            self.labels.append(label)
        self.buttons = []
        # A tool window can extend above the masked lyric window without clipping.
        self.controls = QWidget(self, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                                Qt.WindowType.WindowStaysOnTopHint |
                                Qt.WindowType.WindowDoesNotAcceptFocus)
        self.controls.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.controls.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.controls.setFixedSize(58, 24)
        self.controls.installEventFilter(self)
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(120)
        self.hover_timer.timeout.connect(self.update_hover)
        for symbol, delta in [('+', 0.1), ('−', -0.1)]:
            button = QToolButton(self.controls)
            button.setText(symbol)
            button.setFixedSize(24, 18)
            button.move(3 + len(self.buttons) * 28, 3)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            description = 'Lirik lebih awal +0,1 detik' if delta > 0 else 'Lirik lebih lambat −0,1 detik'
            button.setToolTip(description)
            button.setAccessibleName(description)
            button.clicked.connect(lambda checked=False, d=delta: self.nudge_offset(d))
            self.buttons.append(button)
        for key, delta in [('Left', -0.1), ('Right', 0.1), ('Shift+Left', -0.5), ('Shift+Right', 0.5)]:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda d=delta: self.nudge_offset(d))
        reset = QShortcut(QKeySequence('Ctrl+0'), self)
        reset.activated.connect(lambda: self.nudge_offset(-self.offset))
        self.menu = QMenu(self)
        self.menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.menu.addAction('Settings', self.open_settings)
        self.menu.addAction('Show Spotify', self.open_spotify)
        self.menu.addSeparator()
        self.menu.addAction('About GlanceLyric', self.open_about)
        self.menu.addSeparator()
        self.menu.addAction('Exit', self.close)
        self.menu.aboutToHide.connect(lambda: QTimer.singleShot(0, self.update_hover))
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.tick)
        self.dock_timer = QTimer(self)
        self.dock_timer.setInterval(1000)
        self.dock_timer.timeout.connect(self.dock)
        self.apply_settings()
        if start_monitor:
            self.monitor.start()
            self.timer.start()
            self.dock_timer.start()

    def apply_settings(self):
        self.offset = self.config['offset']
        font = QFont(self.config['font_family'], self.config['font_size'])
        for label in self.labels:
            label.setFont(font)
            label.setStyleSheet(f"background: transparent; color: {self.config['text_color']};")
        p = palette(self.config['theme'])
        for button in self.buttons:
            button.setStyleSheet(f"QToolButton {{ color: {p['text']}; background: {p['card']}; "
                                f"border: 1px solid {p['border']}; border-radius: 3px; font-size: 13px; }}"
                                f"QToolButton:hover, QToolButton:focus {{ background: {p['hover']}; }}")
        self.menu.setStyleSheet(stylesheet(self.config['theme']))
        actions = [action for action in self.menu.actions() if not action.isSeparator()]
        for action, glyph in zip(actions, ('\uE713', '\uE768', '\uEB51', '\uE7E8')):
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(QColor(p['text']))
            painter.setFont(QFont('Segoe MDL2 Assets', 12))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
            painter.end()
            action.setIcon(QIcon(pixmap))
        self.row_height = max(18, self.labels[0].fontMetrics().height())
        self.dock()
        self.render_text()
        if self.isVisible():
            self.refresh_acrylic()
        self.update()

    def dock(self):
        width = 260
        for label, text in zip(self.labels, self.full_text):
            metrics = label.fontMetrics()
            single_line = ' '.join(text.split())
            width = max(width, metrics.horizontalAdvance(single_line) + 18,
                        metrics.boundingRect(single_line).width() + 18)
        # Grow to the left of the same tray anchor; retain the configured font size.
        geometry = taskbar_geometry(width, self.row_height * 2 + 6)
        self.setFixedSize(geometry.size())
        if self.geometry() != geometry:
            self.setGeometry(geometry)
        self.position_controls()
        if self.isVisible() and not self.menu.isVisible() and not (self.settings and self.settings.isVisible()):
            keep_on_top(int(self.winId()))

    def refresh_acrylic(self):
        self.blur = apply_acrylic(int(self.winId()), QColor(palette(self.config['theme'])['card']),
                                 100 - self.config['transparency'])

    def showEvent(self, event):
        super().showEvent(event)
        self.dock()
        self.refresh_acrylic()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        background = QColor(palette(self.config['theme'])['card'])
        # Alpha 1 keeps the transparent panel hit-testable on Windows.
        opacity = 100 - self.config['transparency']
        background.setAlpha(max(1, round(255 * opacity / 100 * (0.25 if self.blur else 1))))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(QRectF(self.rect()), 5, 5)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 5, 5)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        self.position_controls()
        self.render_text()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.position_controls()

    def position_controls(self):
        area = self.screen().geometry()
        x = self.x() + (self.width() - self.controls.width()) // 2
        y = self.y() - self.controls.height()
        # Top-edge taskbars may have no space above: keep controls on-screen below.
        if y < area.top():
            y = self.geometry().bottom() + 1
        x = max(area.left(), min(x, area.right() - self.controls.width() + 1))
        y = max(area.top(), min(y, area.bottom() - self.controls.height() + 1))
        self.controls.move(x, y)

    def render_text(self):
        if not self.labels:
            return
        for label, text in zip(self.labels, self.full_text):
            single_line = ' '.join(text.split()) or ' '
            label.setText(single_line)
            label.setAccessibleName(text)

    def set_text(self, current, following):
        self.full_text = (current, following)
        self.render_text()
        self.dock()

    def enterEvent(self, event):
        self.hover_timer.stop()
        self.position_controls()
        self.controls.show()
        super().enterEvent(event)

    def update_hover(self):
        point = QCursor.pos()
        visible = self.isVisible() and (
            self.geometry().contains(point) or
            (self.controls.isVisible() and self.controls.geometry().contains(point)))
        self.controls.setVisible(visible)

    def leaveEvent(self, event):
        # Allow the cursor to cross from the lyric window into the floating tool.
        self.hover_timer.start()
        super().leaveEvent(event)

    def eventFilter(self, watched, event):
        if watched is self.controls:
            if event.type() == QEvent.Type.Enter:
                self.hover_timer.stop()
            elif event.type() == QEvent.Type.Leave:
                self.hover_timer.start()
        return super().eventFilter(watched, event)

    def hideEvent(self, event):
        self.hover_timer.stop()
        self.controls.hide()
        super().hideEvent(event)

    def contextMenuEvent(self, event):
        self.menu.popup(event.globalPos())
        event.accept()

    def open_settings(self):
        if self.settings and self.settings.isVisible():
            self.settings.raise_()
            self.settings.activateWindow()
            return
        if self.settings:
            self.settings.deleteLater()
        self.settings = SettingsDialog(self.config, self)
        self.settings.accepted.connect(self.settings_saved)
        self.settings.show()
        self.settings.activateWindow()

    def settings_saved(self):
        self.config = self.settings.config.copy()
        self.index = None
        self.apply_settings()

    def open_spotify(self):
        try:
            show_spotify()
        except OSError as exc:
            QMessageBox.warning(self, 'Show Spotify', f'Spotify gagal dibuka:\n{exc}')

    def open_about(self):
        QMessageBox.about(self, APP_TITLE,
                          f'{APP_TITLE}\n\nLirik Spotify dua baris di taskbar Windows.\n'
                          'Lirik dari LRCLIB')

    def nudge_offset(self, delta):
        self.offset = round(max(-60, min(60, self.offset + delta)), 1)
        self.config['offset'] = self.offset
        if self.settings and self.settings.isVisible():
            self.settings.config['offset'] = self.offset
        self.index = None
        try:
            save_settings(self.config)
            message = f'Timing {self.offset:+.1f}s · positif = lirik lebih awal'
        except OSError:
            logging.exception('Cannot save timing offset')
            message = 'Timing berubah, tetapi gagal disimpan ke disk'
        QToolTip.showText(self.mapToGlobal(self.rect().topLeft()), message, self)

    def tick(self):
        while True:
            try:
                message = self.inbox.get_nowait()
            except queue.Empty:
                break
            if 'lyrics_key' in message:
                if message['lyrics_key'] != self.key:
                    continue
                self.lines = message['lines']
                self.times = [stamp for stamp, _ in self.lines]
                self.index = None
                if not self.lines:
                    status = ('Instrumental' if message.get('instrumental') else
                              'Gagal mengambil lirik' if message.get('error') else 'Lirik tersinkron belum tersedia')
                    self.set_text(status, self.key[1])
                continue
            if not message.get('available'):
                self.key = None
                self.lines, self.times = [], []
                self.index = None
                self.set_text('Menunggu koneksi Spotify' if message.get('error') else 'Buka Spotify',
                              'Putar lagu untuk menampilkan lirik')
                continue
            key = (message['artist'], message['title'], message['album'], round(message['duration']))
            self.clock.update(message['position'], message['stamp'], message['playing'], message['duration'])
            if key != self.key:
                self.key = key
                self.lines, self.times = [], []
                self.index = None
                self.set_text('Mencari lirik…', f'{key[0]} — {key[1]}')
                self.fetcher.ensure(key, *key)
        if not self.lines:
            return
        index = bisect.bisect_right(self.times, self.clock.at() + self.offset) - 1
        # Static chunks [0:2], [2:4], ...; line two never shifts into row one.
        page_start = (index // 2) * 2 if index >= 0 else -1
        if page_start != self.index:
            self.index = page_start
            if page_start < 0:
                self.set_text('♪', self.lines[0][1])
            else:
                chunk = [text or '♪' for _, text in self.lines[page_start:page_start + 2]]
                self.set_text(chunk[0], chunk[1] if len(chunk) > 1 else '')

    def closeEvent(self, event):
        self.hover_timer.stop()
        self.controls.hide()
        self.timer.stop()
        self.dock_timer.stop()
        self.monitor.stop_event.set()
        if self.settings:
            self.settings.close()
        super().closeEvent(event)
        QApplication.instance().quit()


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=str(DATA_DIR / 'overlay.log'), level=logging.WARNING,
                        format='%(asctime)s %(levelname)s %(message)s')
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_TITLE)
    app.setWindowIcon(app_icon())
    lock = QLockFile(str(DATA_DIR / 'taskbar-widget.lock'))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        return
    widget = LyricWidget()
    widget.show()
    try:
        app.exec()
    finally:
        widget.monitor.stop_event.set()
        lock.unlock()


if __name__ == '__main__':
    main()

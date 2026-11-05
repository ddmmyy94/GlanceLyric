"""Shared update window for the widget and the Windows-login watcher."""
import queue
import logging

from PySide6.QtCore import QObject, QLockFile, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPlainTextEdit, QPushButton, QMessageBox)

from glance_backend import APP_NAME, APP_VERSION
from glance_settings import load_settings, stylesheet, palette
from glance_updates import UpdateChecker
from glance_win32 import app_icon


class UpdateDialog(QDialog):
    def __init__(self, release, checker, theme, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Update Available — ' + APP_NAME)
        self.setWindowIcon(app_icon())
        self.setStyleSheet(stylesheet(theme))
        self.setWindowModality(Qt.WindowModality.NonModal)
        area = self.screen().availableGeometry()
        self.resize(min(540, area.width() - 24), min(490, area.height() - 64))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(12)
        heading = QLabel('A new version of GlanceLyric is available!')
        heading.setWordWrap(True)
        layout.addWidget(heading)
        versions = QLabel(f"Current: v{APP_VERSION}\nLatest: v{release['version']}" +
                          (' (pre-release)' if release['prerelease'] else ''))
        layout.addWidget(versions)
        layout.addWidget(QLabel(f"What's new in v{release['version']}?"))
        self.notes = QPlainTextEdit()
        self.notes.setReadOnly(True)
        self.notes.setPlainText(release['notes'])
        self.notes.setAccessibleName('Release notes')
        self.notes.setStyleSheet('QPlainTextEdit { background: transparent; color: ' +
                                palette(theme)['text'] + '; }')
        layout.addWidget(self.notes, 1)
        row = QHBoxLayout()
        self.skip = QPushButton('Skip This Version')
        self.later = QPushButton('Not Now')
        self.download = QPushButton('Download')
        self.later.setDefault(True)
        self.download.setToolTip('Open the official GitHub release in your browser')
        self.skip.clicked.connect(lambda: (checker.skip_version(release['version']), self.reject()))
        self.later.clicked.connect(self.reject)
        self.download.clicked.connect(lambda: self.open_download(release['url']))
        row.addWidget(self.skip)
        row.addStretch()
        row.addWidget(self.later)
        row.addWidget(self.download)
        layout.addLayout(row)
        self.move(area.center() - self.rect().center())

    def open_download(self, url):
        if QDesktopServices.openUrl(QUrl(url)):
            self.accept()
        else:
            QMessageBox.warning(self, 'Download', 'Browser gagal dibuka. Buka halaman ini:\n' + url)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.center_on_screen)

    def center_on_screen(self):
        area, frame = self.screen().availableGeometry(), self.frameGeometry()
        self.move(area.center() - (frame.center() - frame.topLeft()))


class UpdatePresenter(QObject):
    busy_changed = Signal(bool)

    def __init__(self, parent=None, inbox=None, settings=load_settings, state_path=None):
        super().__init__(parent)
        self.owner = parent
        self.settings = settings
        self.inbox = inbox if inbox is not None else queue.Queue()
        self.checker = UpdateChecker(self.inbox, state_path)
        self.dialog = None
        self.startup_pending = False
        self.lock = QLockFile(str(self.checker.path.with_suffix('.lock')))
        self.lock.setStaleLockTime(0)
        self.timer = QTimer(self)
        self.timer.setInterval(5 * 60 * 1000)
        self.timer.timeout.connect(self.check)
        self.results = QTimer(self)
        self.results.setInterval(100)
        self.results.timeout.connect(self.poll)
        self.owns_inbox = inbox is None

    def start(self, login=False):
        self.startup_pending = login
        self.timer.start()
        if self.owns_inbox:
            self.results.start()
        QTimer.singleShot(15000 if login else 5000, self.check)

    def check(self, manual=False):
        if self.dialog and self.dialog.isVisible():
            if manual:
                self.dialog.raise_()
                self.dialog.activateWindow()
            return
        if not manual and not self.settings()['check_updates']:
            return
        if self.checker.busy or self.lock.isLocked():
            return
        try:
            self.checker.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            logging.warning('Cannot create update state directory')
            return
        if not self.lock.tryLock(0):
            # Another widget/watcher owns this session's check or visible notice.
            self.startup_pending = False
            return
        self.checker.reload()
        kwargs = dict(manual=manual)
        if self.startup_pending:
            kwargs['startup'] = True
        if self.checker.ensure(**kwargs):
            self.busy_changed.emit(True)
        else:
            self.lock.unlock()

    def poll(self):
        while True:
            try:
                message = self.inbox.get_nowait()
            except queue.Empty:
                return
            self.show_result(message)

    def show_result(self, message):
        self.busy_changed.emit(False)
        if not message.get('error'):
            self.startup_pending = False
        if not message['manual'] and not self.settings()['check_updates']:
            self.lock.unlock()
            return
        release = message.get('release')
        if not release:
            self.lock.unlock()
            if message['manual']:
                if self.dialog:
                    self.dialog.close()
                    self.dialog.deleteLater()
                self.dialog = QMessageBox(self.owner)
                self.dialog.setWindowTitle(APP_NAME + ' — Pembaruan')
                self.dialog.setWindowIcon(app_icon())
                self.dialog.setText('Pembaruan belum dapat diperiksa. Periksa koneksi internet dan coba lagi.'
                                    if message.get('error') else
                                    f'Anda sudah menggunakan versi terbaru yang tersedia: {APP_VERSION}.')
                self.dialog.show()
            return
        if self.dialog:
            self.dialog.close()
            self.dialog.deleteLater()
        if not self.lock.isLocked() and not self.lock.tryLock(0):
            return
        self.dialog = UpdateDialog(release, self.checker, self.settings()['theme'], self.owner)
        self.dialog.finished.connect(lambda _: self.lock.unlock())
        self.checker.mark_notified(release['version'])
        self.dialog.show()
        self.dialog.raise_()

    def stop(self):
        self.timer.stop()
        self.results.stop()
        if self.dialog:
            self.dialog.close()
        # A worker in flight still owns the state file until this process exits.
        if not self.checker.busy:
            self.lock.unlock()

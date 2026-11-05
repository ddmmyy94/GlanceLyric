"""Per-user Spotify autostart watcher. Exit in the widget is respected per session."""
import logging
from pathlib import Path
import subprocess
import sys
import winreg

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication

from glance_backend import APP_NAME, DATA_DIR
from glance_win32 import app_command, spotify_pids, start_widget, start_app

RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
RUN_NAME = APP_NAME


def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            command, _ = winreg.QueryValueEx(key, RUN_NAME)
            return command == subprocess.list2cmdline(app_command('--watch'))
    except OSError:
        return False


def install_autostart(remove=False):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
        if remove:
            try:
                winreg.DeleteValue(key, RUN_NAME)
            except FileNotFoundError:
                pass
        else:
            command = subprocess.list2cmdline(app_command('--watch'))
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, command)


class Watcher:
    def __init__(self, detect=spotify_pids, launch=start_widget):
        self.detect, self.launch = detect, launch
        self.previous = set()
        self.child = None

    def poll(self):
        try:
            current = self.detect()
            # A fresh PID set also catches a restart between two polls.
            if current and not current.intersection(self.previous):
                self.child = self.launch()
            self.previous = current
            if self.child is not None and self.child.poll() is not None:
                if self.child.returncode:
                    # Retry a failed executable launch, but respect a normal Exit.
                    self.previous = set()
                self.child = None
        except OSError:
            logging.exception('Spotify watcher failed')


def main():
    if '--install' in sys.argv or '--uninstall' in sys.argv:
        install_autostart('--uninstall' in sys.argv)
        if '--install' in sys.argv:
            start_app('--watch')
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=str(DATA_DIR / 'watcher.log'), level=logging.WARNING,
                        format='%(asctime)s %(levelname)s %(message)s')
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    lock = QLockFile(str(DATA_DIR / 'spotify-watcher.lock'))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        return
    watcher = Watcher()
    from glance_update_ui import UpdatePresenter
    updates = UpdatePresenter()
    updates.start(login=True)
    timer = QTimer()
    timer.timeout.connect(watcher.poll)
    timer.start(1000)
    watcher.poll()
    try:
        app.exec()
    finally:
        updates.stop()
        lock.unlock()


if __name__ == '__main__':
    main()

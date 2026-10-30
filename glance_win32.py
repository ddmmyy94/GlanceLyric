"""Small Win32 bridge: taskbar geometry, acrylic, app icon, and Spotify detection."""
import ctypes
from ctypes import wintypes as wt
import os
from pathlib import Path
import subprocess
import sys

from PySide6.QtCore import QRect
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from glance_backend import ASSETS_DIR

# Other taskbar tools that already own the tray strip; dock to their left instead.
NEIGHBOR_CLASSES = ('NetSpeedTray', 'TrafficMonitor')


def app_icon():
    """Window and shortcut icon; the bundled mark is the single source of truth."""
    path = ASSETS_DIR / 'glancelyric.ico'
    return QIcon(str(path)) if path.exists() else QIcon()

if sys.platform == 'win32':
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
    user32.FindWindowW.restype = wt.HWND
    user32.FindWindowExW.argtypes = [wt.HWND, wt.HWND, wt.LPCWSTR, wt.LPCWSTR]
    user32.FindWindowExW.restype = wt.HWND
    user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
    user32.IsWindowVisible.argtypes = [wt.HWND]
    user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, wt.UINT]


def spotify_pids():
    """Toolhelp avoids launching tasklist.exe every second."""
    class ProcessEntry(ctypes.Structure):
        _fields_ = [('size', wt.DWORD), ('usage', wt.DWORD), ('pid', wt.DWORD),
                    ('heap', ctypes.c_size_t), ('module', wt.DWORD), ('threads', wt.DWORD),
                    ('parent', wt.DWORD), ('priority', wt.LONG), ('flags', wt.DWORD),
                    ('exe', wt.WCHAR * 260)]

    kernel32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wt.HANDLE
    kernel32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel32.CloseHandle.argtypes = [wt.HANDLE]
    handle = kernel32.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        found = set()
        more = kernel32.Process32FirstW(handle, ctypes.byref(entry))
        while more:
            if entry.exe.casefold() == 'spotify.exe':
                found.add(entry.pid)
            more = kernel32.Process32NextW(handle, ctypes.byref(entry))
        return found
    finally:
        kernel32.CloseHandle(handle)


def native_rect(hwnd):
    rect = wt.RECT()
    if hwnd and user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return QRect(rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
    return QRect()


def dock_rect(screen, bar, tray, width, height, neighbor=None):
    """Logical-pixel layout; fit horizontal taskbar rows, including small mode."""
    width, height = min(width, screen.width()), min(height, screen.height())
    if bar.isEmpty() or not bar.intersects(screen):
        x, y = screen.right() - width - 12, screen.bottom() - height - 12
    elif bar.width() >= bar.height():
        edge = tray.left() if not tray.isEmpty() else bar.right() - 180
        alignment = bar
        if neighbor is not None and not neighbor.isEmpty() and bar.intersects(neighbor):
            edge = min(edge, neighbor.left())
            # Shell_TrayWnd may include extra padding above the actual taskbar row.
            alignment = bar.intersected(neighbor)
        alignment = alignment.intersected(screen)
        # Auto-hide can leave only a thin edge: don't squeeze two lyrics into it.
        if alignment.height() >= 16:
            height = min(height, alignment.height())
        # Match the measured 8-DIP gap between NetSpeedTray and TrayNotifyWnd.
        width = min(width, max(1, edge - 8 - screen.left()))
        x = edge - width - 8
        if height <= alignment.height():
            y = alignment.top() + (alignment.height() - height) // 2
        elif bar.center().y() > screen.center().y():
            y = bar.top() - height - 4
        else:
            y = bar.bottom() + 5
    else:
        # Vertical taskbars are too narrow for a lyric line: dock beside them.
        x = bar.right() + 5 if bar.center().x() < screen.center().x() else bar.left() - width - 4
        y = (tray.top() if not tray.isEmpty() else bar.bottom()) - height - 8
    x = max(screen.left(), min(x, screen.right() - width + 1))
    y = max(screen.top(), min(y, screen.bottom() - height + 1))
    return QRect(x, y, width, height)


def taskbar_geometry(width, height):
    screen = QApplication.primaryScreen()
    if sys.platform != 'win32':
        return dock_rect(screen.availableGeometry(), QRect(), QRect(), width, height)
    bar_hwnd = user32.FindWindowW('Shell_TrayWnd', None)
    bar = native_rect(bar_hwnd)
    tray = native_rect(user32.FindWindowExW(bar_hwnd, None, 'TrayNotifyWnd', None)) if bar_hwnd else QRect()
    neighbors = [hwnd for hwnd in (user32.FindWindowW(None, name) for name in NEIGHBOR_CLASSES)
                 if hwnd and user32.IsWindowVisible(hwnd)]
    neighbor = min((native_rect(hwnd) for hwnd in neighbors), key=lambda rect: rect.left(),
                   default=QRect())
    # Windows keeps monitor origins in physical coordinates; scale relative to origin.
    for candidate in QApplication.screens():
        origin = candidate.geometry().topLeft()
        physical = QRect(origin, candidate.geometry().size() * candidate.devicePixelRatio())
        if physical.contains(bar.center()):
            screen = candidate
            break
    origin, ratio = screen.geometry().topLeft(), screen.devicePixelRatio()

    def logical(rect):
        if rect.isEmpty():
            return QRect()
        return QRect(origin.x() + round((rect.x() - origin.x()) / ratio),
                     origin.y() + round((rect.y() - origin.y()) / ratio),
                     round(rect.width() / ratio), round(rect.height() / ratio))

    return dock_rect(screen.geometry(), logical(bar), logical(tray), width, height, logical(neighbor))


def keep_on_top(hwnd):
    if sys.platform == 'win32':
        user32.SetWindowPos(hwnd, wt.HWND(-1), 0, 0, 0, 0, 0x0013)  # no activate/move/size


def apply_acrylic(hwnd, color, opacity):
    """Optional Windows acrylic with a painted translucent fallback in the UI."""
    if sys.platform != 'win32':
        return False

    class Accent(ctypes.Structure):
        _fields_ = [('state', ctypes.c_int), ('flags', ctypes.c_int),
                    ('color', wt.DWORD), ('animation', ctypes.c_int)]

    class Data(ctypes.Structure):
        _fields_ = [('attribute', ctypes.c_int), ('data', ctypes.c_void_p), ('size', ctypes.c_size_t)]

    try:
        apply = user32.SetWindowCompositionAttribute
        apply.argtypes = [wt.HWND, ctypes.POINTER(Data)]
        apply.restype = wt.BOOL
        tint = (round(255 * opacity / 100) << 24) | (color.blue() << 16) | (color.green() << 8) | color.red()
        accent = Accent(4 if opacity else 0, 0, tint, 0)
        data = Data(19, ctypes.addressof(accent), ctypes.sizeof(accent))
        return bool(apply(hwnd, ctypes.byref(data))) and opacity > 0
    except (AttributeError, OSError):
        return False


def show_spotify():
    # Spotify's own protocol restores its existing window, including Store installs.
    os.startfile('spotify:')


def pythonw():
    executable = Path(sys.executable)
    candidate = executable.with_name('pythonw.exe')
    return str(candidate if candidate.exists() else executable)


def app_command(*arguments):
    if getattr(sys, 'frozen', False):
        return [sys.executable, *arguments]
    return [pythonw(), str(Path(__file__).with_name('glancelyric.pyw')), *arguments]


def start_widget():
    return subprocess.Popen(app_command(), env={**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1'})

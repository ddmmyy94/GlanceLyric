"""Build a multi-size ICO from the user's PNG without modifying the original."""
import struct
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRect, Qt
from PySide6.QtGui import QImage, QPainter

SIZES = (16, 24, 32, 48, 64, 128, 256)
OUTPUT = Path(__file__).resolve().parent.parent / 'assets' / 'glancelyric.ico'


def main():
    source = QImage(str(OUTPUT.with_suffix('.png')))
    if source.isNull():
        raise ValueError('assets/glancelyric.png is missing or unreadable')
    entries, blobs = b'', []
    offset = 6 + 16 * len(SIZES)
    for size in SIZES:
        scaled = source.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.drawImage(QRect((size - scaled.width()) // 2,
                                (size - scaled.height()) // 2,
                                scaled.width(), scaled.height()), scaled)
        painter.end()
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not image.save(buffer, 'PNG'):
            raise OSError(f'Cannot encode {size}px icon')
        buffer.close()
        blobs.append(bytes(data))
        entries += struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32,
                               len(blobs[-1]), offset)
        offset += len(blobs[-1])
    OUTPUT.write_bytes(struct.pack('<HHH', 0, 1, len(SIZES)) + entries + b''.join(blobs))
    print(f'{OUTPUT} ({OUTPUT.stat().st_size} bytes, sizes {SIZES})')


if __name__ == '__main__':
    main()

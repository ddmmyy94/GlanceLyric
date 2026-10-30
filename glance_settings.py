"""Appearance editor and persisted taskbar-widget preferences."""
import json
import logging
import math
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QSlider, QComboBox, QFrame, QFontDialog,
                               QColorDialog, QScrollArea, QWidget, QMessageBox, QCheckBox)

from glance_backend import APP_TITLE, DATA_DIR
from glance_win32 import app_icon

CONFIG_PATH = DATA_DIR / 'taskbar-settings.json'
DEFAULTS = dict(font_family='Segoe UI', font_size=9, text_color='#FFFFFF',
                theme='Dark', transparency=100, offset=0.0, check_updates=True)
PALETTES = {
    'Dark': dict(window='#202020', card='#2B2B2B', border='#3B3B3B', text='#FFFFFF',
                 muted='#B8B8B8', hover='#383838', track='#606060'),
    'Light': dict(window='#F3F3F3', card='#FFFFFF', border='#D5D5D5', text='#202020',
                  muted='#666666', hover='#E5E5E5', track='#BBBBBB'),
}
ACCENT = '#D60016'
FONT = 'Segoe UI'


def palette(theme):
    if theme == 'System':
        theme = 'Dark' if QApplication.palette().window().color().lightness() < 128 else 'Light'
    return PALETTES.get(theme, PALETTES['Dark'])


def normalize(config):
    result = DEFAULTS.copy()
    if not isinstance(config, dict):
        return result
    if isinstance(config.get('font_family'), str) and config['font_family'].strip():
        result['font_family'] = config['font_family']
    for key, low, high in [('font_size', 7, 20), ('transparency', 0, 100), ('offset', -60, 60)]:
        try:
            value = float(config.get(key, result[key]))
            if math.isfinite(value):
                result[key] = max(low, min(high, value if key == 'offset' else int(value)))
        except (TypeError, ValueError, OverflowError):
            pass
    if config.get('theme') in ('Dark', 'Light', 'System'):
        result['theme'] = config['theme']
    if isinstance(config.get('check_updates'), bool):
        result['check_updates'] = config['check_updates']
    color = config.get('text_color')
    if isinstance(color, str) and QColor(color).isValid():
        result['text_color'] = QColor(color).name().upper()
    return result


def load_settings():
    try:
        return normalize(json.loads(CONFIG_PATH.read_text(encoding='utf-8')))
    except (OSError, ValueError):
        return DEFAULTS.copy()


def save_settings(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = CONFIG_PATH.with_suffix('.tmp')
    temporary.write_text(json.dumps(normalize(config), indent=2), encoding='utf-8')
    os.replace(temporary, CONFIG_PATH)


def stylesheet(theme):
    p = palette(theme)
    return f'''
        QDialog, QScrollArea, QWidget#content {{ background: {p['window']}; color: {p['text']}; }}
        QWidget {{ font-family: "{FONT}"; font-size: 12px; }}
        QLabel, QCheckBox {{ color: {p['text']}; background: transparent; }}
        QLabel#muted {{ color: {p['muted']}; }}
        QFrame#card {{ background: {p['card']}; border: 1px solid {p['border']}; border-radius: 8px; }}
        QPushButton, QComboBox {{ color: {p['text']}; background: {p['card']};
            border: 1px solid {p['border']}; border-radius: 4px; padding: 6px 14px; }}
        QPushButton:hover, QComboBox:hover {{ background: {p['hover']}; }}
        QPushButton:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
        QPushButton:pressed {{ background: {p['track']}; }}
        QPushButton#save {{ background: {ACCENT}; color: #FFFFFF; border-color: {ACCENT}; }}
        QComboBox QAbstractItemView {{ background: {p['card']}; color: {p['text']}; selection-background-color: {ACCENT}; }}
        QSlider {{ border: none; background: transparent; }}
        QSlider::groove:horizontal {{ height: 4px; background: {p['track']}; border: none; border-radius: 2px; }}
        QSlider::add-page:horizontal {{ background: {p['track']}; border: none; border-radius: 2px; }}
        QSlider::sub-page:horizontal {{ background: {ACCENT}; border: none; border-radius: 2px; }}
        QSlider::handle:horizontal {{ background: {ACCENT}; border: none; width: 17px; margin: -7px 0; border-radius: 8px; }}
        QSlider::handle:horizontal:focus {{ border: 2px solid {p['text']}; }}
        QScrollArea {{ border: none; }}
        QMenu {{ background: {p['card']}; color: {p['text']}; border: 1px solid {p['border']};
            border-radius: 8px; padding: 6px; font-family: "{FONT}"; }}
        QMenu::item {{ padding: 9px 28px 9px 12px; border-radius: 4px; }}
        QMenu::item:selected {{ background: {p['hover']}; }}
        QMenu::separator {{ height: 1px; background: {p['border']}; margin: 5px 8px; }}
    '''


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(app_icon())
        self.resize(610, 620)
        self.setMinimumSize(420, 360)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 18)
        root.setSpacing(16)
        root.addWidget(QLabel('Appearance'))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName('content')
        self.rows = QVBoxLayout(content)
        self.rows.setContentsMargins(0, 4, 4, 0)
        self.rows.setSpacing(5)
        self.rows.addWidget(QLabel('Font Settings'))
        self.font_label = QLabel(config['font_family'])
        select_font = QPushButton('Select')
        select_font.clicked.connect(self.choose_font)
        self.add_row('Font:', self.font_label, select_font)
        self.color_button = QPushButton(config['text_color'])
        self.color_swatch = QLabel()
        self.color_swatch.setFixedSize(26, 26)
        self.color_button.setAccessibleName('Choose text color')
        self.color_button.clicked.connect(self.choose_color)
        self.add_row('Default Color:', self.color_swatch, self.color_button)
        self.size_slider, self.size_value = self.slider_row('Font Size:', 7, 20, config['font_size'])
        self.size_slider.valueChanged.connect(lambda value: self.change('font_size', value))
        self.rows.addSpacing(16)
        self.rows.addWidget(QLabel('Widget'))
        self.theme = QComboBox()
        self.theme.addItems(['Dark', 'Light', 'System'])
        self.theme.setCurrentText(config['theme'])
        self.theme.currentTextChanged.connect(lambda value: self.change('theme', value))
        self.add_row('UI Theme:', self.theme)
        self.transparency, self.transparency_value = self.slider_row(
            'Transparency:', 0, 100, config['transparency'])
        self.transparency.valueChanged.connect(lambda value: self.change('transparency', value))
        hint = QLabel('100% = background transparan. Warna teks diatur terpisah.\n'
                      'Taskbar kecil: ukuran font menyesuaikan tanpa mengubah pilihan Anda.\n'
                      'Hover lirik: − / + mengubah timing sebesar 0,1 detik.')
        hint.setWordWrap(True)
        hint.setObjectName('muted')
        self.rows.addWidget(hint)
        self.rows.addSpacing(16)
        self.auto_updates = QCheckBox('Periksa pembaruan otomatis (sekali sehari)')
        self.auto_updates.setChecked(config['check_updates'])
        self.auto_updates.toggled.connect(lambda enabled: self.change('check_updates', enabled))
        self.rows.addWidget(self.auto_updates)
        self.rows.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        preview_card = QFrame()
        preview_card.setObjectName('card')
        preview_row = QHBoxLayout(preview_card)
        caption = QLabel('Preview')
        caption.setObjectName('muted')
        preview_row.addWidget(caption)
        preview_row.addStretch()
        self.preview = QLabel('Lirik yang sedang diputar\nBaris lirik berikutnya')
        preview_row.addWidget(self.preview)
        root.addWidget(preview_card)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel, save = QPushButton('Cancel'), QPushButton('Save')
        save.setObjectName('save')
        save.setDefault(True)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.save)
        actions.addWidget(cancel)
        actions.addWidget(save)
        root.addLayout(actions)
        self.refresh()

    def add_row(self, title, *widgets):
        card = QFrame()
        card.setObjectName('card')
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 16, 12)
        label = QLabel(title)
        label.setBuddy(widgets[0])
        row.addWidget(label)
        row.addStretch()
        for widget in widgets:
            row.addWidget(widget)
        self.rows.addWidget(card)

    def slider_row(self, title, minimum, maximum, value):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        slider.setMinimumWidth(120)
        slider.setMaximumWidth(180)
        slider.setAccessibleName(title.rstrip(':'))
        number = QLabel(str(value))
        number.setMinimumWidth(32)
        self.add_row(title, slider, number)
        return slider, number

    def change(self, key, value):
        self.config[key] = value
        self.refresh()

    def choose_font(self):
        ok, font = QFontDialog.getFont(QFont(self.config['font_family'], self.config['font_size']), self)
        if ok:
            self.config['font_family'] = font.family()
            self.size_slider.setValue(max(7, min(20, font.pointSize())))
            self.refresh()

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.config['text_color']), self, 'Text Color')
        if color.isValid():
            self.change('text_color', color.name().upper())

    def refresh(self):
        self.setStyleSheet(stylesheet(self.config['theme']))
        self.font_label.setText(self.config['font_family'])
        self.size_value.setText(str(self.config['font_size']))
        self.transparency_value.setText(f"{self.config['transparency']}%")
        color = self.config['text_color']
        self.color_button.setText(color)
        self.color_swatch.setStyleSheet(f'background: {color}; border-radius: 3px;')
        self.preview.setFont(QFont(self.config['font_family'], self.config['font_size']))
        background = QColor(palette(self.config['theme'])['card'])
        alpha = round(255 * (100 - self.config['transparency']) / 100)
        self.preview.setStyleSheet(f'color: {color}; padding: 6px; border-radius: 4px; '
                                  f'font-size: {self.config["font_size"]}pt; '
                                  f'font-family: "{self.config["font_family"].replace(chr(34), "")}"; '
                                  f'background: rgba({background.red()}, {background.green()}, {background.blue()}, {alpha});')

    def save(self):
        try:
            save_settings(self.config)
        except OSError as exc:
            logging.exception('Cannot save widget settings')
            QMessageBox.warning(self, 'Settings', f'Pengaturan gagal disimpan:\n{exc}')
            return
        self.accept()

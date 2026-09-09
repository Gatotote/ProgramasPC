"""Tema de la GUI: paleta latón + acero de la maqueta «Bóveda Inteligente»,
en claro y oscuro. Se aplica como hoja de estilo Qt (QSS) global.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

DARK = {
    "bg": "#131519", "surface": "#1b1e23", "surface2": "#23272e", "raise": "#20242a",
    "border": "#2d323b", "border2": "#3a404b",
    "text": "#e7e9ec", "dim": "#9aa1ac", "faint": "#727884",
    "accent": "#cf9a4b", "accent_ink": "#1a1206", "accent_soft": "#3a2f1c",
    "ok": "#41b955", "warn": "#e0b341", "risk": "#e5675b",
    "rail": "#0f1114", "rail_text": "#e7e3d6", "rail_active": "#20242b",
}
LIGHT = {
    "bg": "#f4f1ea", "surface": "#fffdf8", "surface2": "#ece6d9", "raise": "#f9f6ef",
    "border": "#ddd4c2", "border2": "#c9bda3",
    "text": "#23262b", "dim": "#6d6a60", "faint": "#928d7f",
    "accent": "#9a6b22", "accent_ink": "#fffdf8", "accent_soft": "#f0e2c8",
    "ok": "#1f7a3d", "warn": "#9a6b0f", "risk": "#b23b30",
    "rail": "#1f232b", "rail_text": "#e7e3d6", "rail_active": "#2f3540",
}


def prefers_dark(app: QApplication) -> bool:
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return True


def palette(dark: bool) -> dict:
    return DARK if dark else LIGHT


def _qss(c: dict) -> str:
    mono = "monospace"
    for fam in ("IBM Plex Mono", "DejaVu Sans Mono", "Noto Sans Mono"):
        if fam in QFontDatabase.families():
            mono = fam
            break
    return f"""
    * {{ font-size: 13px; }}
    QWidget {{ background: {c['bg']}; color: {c['text']};
        font-family: "IBM Plex Sans","Noto Sans","DejaVu Sans",sans-serif; }}
    QLabel {{ background: transparent; }}
    QLabel[role="h1"] {{ font-size: 22px; font-weight: 600; }}
    QLabel[role="h2"] {{ font-size: 17px; font-weight: 600; }}
    QLabel[role="dim"] {{ color: {c['dim']}; }}
    QLabel[role="mono"] {{ font-family: "{mono}"; }}
    QLabel[role="label"] {{ color: {c['faint']}; font-size: 11px;
        letter-spacing: 1px; text-transform: uppercase; }}

    QFrame#card, QFrame[role="card"] {{
        background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 12px; }}
    QFrame[role="hline"] {{ background: {c['border']}; max-height: 1px; border: none; }}

    QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox {{
        background: {c['raise']}; border: 1px solid {c['border2']};
        border-radius: 8px; padding: 8px 10px; selection-background-color: {c['accent']}; }}
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {c['accent']}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}

    QPushButton {{
        background: {c['raise']}; border: 1px solid {c['border2']};
        border-radius: 8px; padding: 8px 16px; }}
    QPushButton:hover {{ border-color: {c['accent']}; }}
    QPushButton:disabled {{ color: {c['faint']}; border-color: {c['border']}; }}
    QPushButton#primary {{
        background: {c['accent']}; color: {c['accent_ink']};
        border: 1px solid {c['accent']}; font-weight: 600; }}
    QPushButton#primary:hover {{ background: {c['accent']}; }}
    QPushButton#primary:disabled {{ background: {c['surface2']}; color: {c['faint']};
        border-color: {c['border']}; }}
    QPushButton[role="link"] {{ background: transparent; border: none; color: {c['accent']};
        padding: 4px; text-decoration: underline; }}

    QProgressBar {{ background: {c['surface2']}; border: 1px solid {c['border']};
        border-radius: 6px; height: 8px; text-align: center; }}
    QProgressBar::chunk {{ background: {c['accent']}; border-radius: 6px; }}

    QListWidget#rail {{ background: {c['rail']}; border: none; padding: 8px; }}
    QListWidget#rail::item {{ color: {c['rail_text']}; padding: 10px 12px; border-radius: 8px; }}
    QListWidget#rail::item:selected {{ background: {c['rail_active']};
        border-left: 3px solid {c['accent']}; }}
    QListWidget#rail::item:hover {{ background: {c['rail_active']}; }}

    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c['border2']}; border-radius: 5px; min-height: 30px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

    QCheckBox {{ spacing: 8px; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {c['border2']};
        border-radius: 4px; background: {c['raise']}; }}
    QCheckBox::indicator:checked {{ background: {c['accent']}; border-color: {c['accent']}; }}

    QFrame[status="ok"]   {{ color: {c['ok']}; }}
    QFrame[status="warn"] {{ color: {c['warn']}; }}
    QFrame[status="risk"] {{ color: {c['risk']}; }}
    """


def apply(app: QApplication, dark: bool | None = None) -> dict:
    dark = prefers_dark(app) if dark is None else dark
    c = palette(dark)
    app.setStyleSheet(_qss(c))
    return c

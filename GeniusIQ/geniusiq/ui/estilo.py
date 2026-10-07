"""Hoja de estilo y colores de la interfaz (negro con acentos naranja, como el ícono)."""

from PySide6.QtGui import QColor, QPalette

ACENTO = "#ff7a1a"
ACENTO_OSCURO = "#e0560b"
ACENTO_CLARO = "#ffb347"
FONDO = "#0e0e0f"
TARJETA = "#1a1a1c"
CONTROL = "#232326"
BORDE = "#3a3a3e"
TEXTO = "#f3ece6"
SUAVE = "#b3a79c"
TINTA = "#1f1f22"   # tinta de las figuras (se dibujan sobre blanco)

QSS = f"""
QWidget {{ background: {FONDO}; color: {TEXTO}; font-size: 15px; }}
QLabel#titulo {{ font-size: 30px; font-weight: 800; color: {ACENTO}; }}
QLabel#subtitulo {{ font-size: 20px; font-weight: 600; }}
QLabel#suave {{ color: {SUAVE}; }}
QLabel#pregunta {{ font-size: 20px; font-weight: 600; }}
QLabel#grande {{ font-size: 34px; font-weight: 600; letter-spacing: 1px; color: {ACENTO_CLARO}; }}
QLabel#reloj {{ font-size: 18px; font-weight: 700; color: {ACENTO}; }}
QLabel#ci {{ font-size: 72px; font-weight: 800; color: {ACENTO}; }}
QLabel#aviso {{ background: #2b1a0c; border: 1px solid #7a4512; border-radius: 8px; padding: 10px;
                color: #ffc98a; }}
QFrame#tarjeta {{ background: {TARJETA}; border: 1px solid {BORDE}; border-radius: 12px; }}
QFrame#tarjeta QLabel, QFrame#tarjeta QCheckBox {{ background: transparent; }}
QFrame#tarjeta QLabel#aviso {{ background: #2b1a0c; }}
QPushButton {{ background: {CONTROL}; border: 1px solid {BORDE}; border-radius: 8px; padding: 8px 16px; }}
QPushButton:hover {{ border-color: {ACENTO}; background: #2c1d12; }}
QPushButton#principal {{ background: {ACENTO}; color: #111111; border: none; font-weight: 800;
                          padding: 12px 28px; font-size: 17px; }}
QPushButton#principal:hover {{ background: {ACENTO_CLARO}; }}
QPushButton#principal:disabled {{ background: #5a3a22; color: #2a2a2a; }}
QPushButton#opcion {{ font-size: 18px; padding: 14px; text-align: left; }}
QPushButton#tecla {{ font-size: 22px; font-weight: 700; min-width: 54px; min-height: 54px; }}
QPushButton#peligro {{ color: #ff6b5e; }}
QListWidget, QTableWidget, QComboBox, QLineEdit, QDateEdit {{
    background: {CONTROL}; border: 1px solid {BORDE}; border-radius: 8px; padding: 6px; }}
QComboBox QAbstractItemView {{ background: {CONTROL}; selection-background-color: {ACENTO};
                               selection-color: #111111; }}
QListWidget::item {{ padding: 10px; border-radius: 6px; }}
QListWidget::item:selected {{ background: {ACENTO}; color: #111111; font-weight: 700; }}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border-color: {ACENTO}; }}
QLineEdit#respuesta {{ font-size: 28px; padding: 10px; }}
QCheckBox {{ padding: 3px; }}
QTableWidget {{ gridline-color: {BORDE}; }}
QHeaderView::section {{ background: #2a2a2e; color: {TEXTO}; border: none; padding: 6px; font-weight: 600; }}
QTableCornerButton::section {{ background: #2a2a2e; border: none; }}
QScrollBar:vertical {{ background: {FONDO}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDE}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QMessageBox, QDialog {{ background: {TARJETA}; }}
"""


def paleta() -> QPalette:
    """Paleta oscura para lo que no cubre la hoja de estilo (casillas, calendario, diálogos)."""
    p = QPalette()
    for rol, color in [
        (QPalette.ColorRole.Window, TARJETA), (QPalette.ColorRole.WindowText, TEXTO),
        (QPalette.ColorRole.Base, CONTROL), (QPalette.ColorRole.AlternateBase, TARJETA),
        (QPalette.ColorRole.Text, TEXTO), (QPalette.ColorRole.Button, CONTROL),
        (QPalette.ColorRole.ButtonText, TEXTO), (QPalette.ColorRole.Highlight, ACENTO),
        (QPalette.ColorRole.HighlightedText, "#111111"), (QPalette.ColorRole.ToolTipBase, TARJETA),
        (QPalette.ColorRole.ToolTipText, TEXTO), (QPalette.ColorRole.PlaceholderText, SUAVE),
    ]:
        p.setColor(rol, QColor(color))
    return p

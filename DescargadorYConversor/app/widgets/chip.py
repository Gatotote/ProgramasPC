from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

COLORES = {
    "verde": ("#052e16", "#4ade80"),
    "azul": ("#0c1a3a", "#60a5fa"),
    "amarillo": ("#3b2a08", "#fbbf24"),
    "rojo": ("#3f0d0d", "#f87171"),
    "gris": ("#1f2430", "#9aa6bc"),
}


class Chip(QLabel):
    def __init__(self, texto, tono="gris"):
        super().__init__(texto)
        fondo, letra = COLORES.get(tono, COLORES["gris"])
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"background:{fondo};color:{letra};border-radius:9px;"
            f"padding:3px 10px;font-size:11px;font-weight:700;"
        )

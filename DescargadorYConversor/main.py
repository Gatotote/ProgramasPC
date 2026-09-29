"""Punto de entrada del Descargador y Conversor (interfaz PySide6).

Ejecutar con:  python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from app import config
from app.ui.main_window import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Descargador y Conversor")
    app.setFont(QFont("Segoe UI", 10))
    if config.RUTA_ICONO.exists():
        app.setWindowIcon(QIcon(str(config.RUTA_ICONO)))

    ventana = VentanaPrincipal()
    if config.RUTA_ICONO.exists():
        ventana.setWindowIcon(QIcon(str(config.RUTA_ICONO)))
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

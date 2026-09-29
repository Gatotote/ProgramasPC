"""Punto de entrada: `python -m estrespc` o `estrespc --version`."""

import argparse
import shutil
import sys

from . import AUTOR, __version__


def tema_oscuro(app):
    from PySide6.QtGui import QColor, QPalette
    app.setStyle("Fusion")
    p = QPalette()
    colores = {
        QPalette.Window: "#23262e", QPalette.WindowText: "#e1e4ea",
        QPalette.Base: "#1b1e24", QPalette.AlternateBase: "#262a33",
        QPalette.Text: "#e1e4ea", QPalette.Button: "#2d313b",
        QPalette.ButtonText: "#e1e4ea", QPalette.Highlight: "#4aa3ff",
        QPalette.HighlightedText: "#ffffff", QPalette.ToolTipBase: "#2d313b",
        QPalette.ToolTipText: "#e1e4ea", QPalette.PlaceholderText: "#8a8f98",
    }
    for rol, color in colores.items():
        p.setColor(rol, QColor(color))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor("#6b7080"))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#6b7080"))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#6b7080"))
    app.setPalette(p)


def main():
    ap = argparse.ArgumentParser(prog="gpustresscpu", description="Pruebas de estrés para Linux")
    ap.add_argument("--version", action="version", version=f"GPUStressCPU {__version__} — {AUTOR}")
    ap.parse_args()

    from PySide6.QtWidgets import QApplication, QMessageBox
    from .ventana import Ventana

    app = QApplication(sys.argv)
    app.setApplicationName("GPUStressCPU")
    app.setDesktopFileName("gpustresscpu")
    tema_oscuro(app)
    if not shutil.which("stress-ng"):
        QMessageBox.critical(None, "GPUStressCPU",
                             "Falta stress-ng. Instálalo con:\n\nsudo pacman -S stress-ng")
        return 1
    v = Ventana()
    v.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

"""Iconos vectoriales sencillos dibujados con QPainter (sin archivos externos)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def _lienzo(tamano):
    pixmap = QPixmap(tamano, tamano)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    return pixmap, painter


def icono(nombre, tamano=18, color="#c5d0e3"):
    pixmap, p = _lienzo(tamano)
    p.setPen(QPen(QColor(color), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    s = tamano
    if nombre == "dashboard":
        p.drawRect(int(s * 0.15), int(s * 0.15), int(s * 0.28), int(s * 0.28))
        p.drawRect(int(s * 0.55), int(s * 0.15), int(s * 0.28), int(s * 0.18))
        p.drawRect(int(s * 0.15), int(s * 0.55), int(s * 0.28), int(s * 0.28))
        p.drawRect(int(s * 0.55), int(s * 0.45), int(s * 0.28), int(s * 0.38))
    elif nombre == "descargar":
        p.drawLine(int(s * 0.5), int(s * 0.14), int(s * 0.5), int(s * 0.62))
        p.drawLine(int(s * 0.30), int(s * 0.42), int(s * 0.5), int(s * 0.64))
        p.drawLine(int(s * 0.70), int(s * 0.42), int(s * 0.5), int(s * 0.64))
        p.drawLine(int(s * 0.20), int(s * 0.80), int(s * 0.80), int(s * 0.80))
    elif nombre == "convertir":
        p.drawLine(int(s * 0.22), int(s * 0.36), int(s * 0.78), int(s * 0.36))
        p.drawLine(int(s * 0.66), int(s * 0.22), int(s * 0.82), int(s * 0.36))
        p.drawLine(int(s * 0.66), int(s * 0.50), int(s * 0.82), int(s * 0.36))
        p.drawLine(int(s * 0.22), int(s * 0.64), int(s * 0.78), int(s * 0.64))
        p.drawLine(int(s * 0.34), int(s * 0.50), int(s * 0.18), int(s * 0.64))
        p.drawLine(int(s * 0.34), int(s * 0.78), int(s * 0.18), int(s * 0.64))
    elif nombre == "historial":
        p.drawEllipse(int(s * 0.16), int(s * 0.16), int(s * 0.68), int(s * 0.68))
        p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.5), int(s * 0.28))
        p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.66), int(s * 0.60))
    elif nombre == "config":
        p.drawEllipse(int(s * 0.34), int(s * 0.34), int(s * 0.32), int(s * 0.32))
        for angulo in range(0, 360, 45):
            p.save()
            p.translate(s / 2, s / 2)
            p.rotate(angulo)
            p.drawLine(0, int(-s * 0.20), 0, int(-s * 0.42))
            p.restore()
    elif nombre == "carpeta":
        p.drawLine(int(s * 0.14), int(s * 0.30), int(s * 0.40), int(s * 0.30))
        p.drawLine(int(s * 0.40), int(s * 0.30), int(s * 0.48), int(s * 0.40))
        p.drawRect(int(s * 0.14), int(s * 0.30), int(s * 0.72), int(s * 0.44))
    elif nombre == "menu":
        p.drawLine(int(s * 0.2), int(s * 0.32), int(s * 0.8), int(s * 0.32))
        p.drawLine(int(s * 0.2), int(s * 0.5), int(s * 0.8), int(s * 0.5))
        p.drawLine(int(s * 0.2), int(s * 0.68), int(s * 0.8), int(s * 0.68))
    elif nombre == "campana":
        p.drawArc(int(s * 0.22), int(s * 0.16), int(s * 0.56), int(s * 0.52), 0, 180 * 16)
        p.drawLine(int(s * 0.22), int(s * 0.42), int(s * 0.22), int(s * 0.62))
        p.drawLine(int(s * 0.78), int(s * 0.42), int(s * 0.78), int(s * 0.62))
        p.drawLine(int(s * 0.18), int(s * 0.62), int(s * 0.82), int(s * 0.62))
        p.drawArc(int(s * 0.42), int(s * 0.64), int(s * 0.16), int(s * 0.16), 180 * 16, 180 * 16)
    p.end()
    return QIcon(pixmap)

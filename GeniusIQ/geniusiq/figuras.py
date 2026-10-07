"""Figuras que se dibujan con QPainter: celdas, matrices, series, polióminos y topología.

Todo objeto dibujable tiene `pintar(p: QPainter, r: QRectF)`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF

TINTA = QColor("#1f1f22")
RELLENO_CLARO = QColor("#ffc58f")

FORMAS = ["circulo", "cuadrado", "triangulo", "pentagono", "hexagono", "estrella"]
# "flecha" se usa solo cuando la regla es de rotación (las demás son simétricas).

# Posiciones (en unidades de celda) según cuántas figuras lleva la celda.
POSICIONES = {
    1: [(0, 0)],
    2: [(-1, 0), (1, 0)],
    3: [(0, -0.9), (-1, 0.8), (1, 0.8)],
    4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
    5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
}
# Separación de las figuras según cuántas hay; el tamaño NO depende de cuántas hay.
SEPARACION = {1: 0.0, 2: 0.29, 3: 0.29, 4: 0.31, 5: 0.32}
RADIO_TAMANO = (0.08, 0.125, 0.175)


def _poligono(n: int, r: float) -> list[QPointF]:
    return [QPointF(r * math.cos(math.radians(-90 + 360 * i / n)),
                    r * math.sin(math.radians(-90 + 360 * i / n))) for i in range(n)]


def ruta_forma(forma: str, r: float) -> QPainterPath:
    """Contorno de la forma centrado en el origen, «radio» r."""
    ruta = QPainterPath()
    if forma == "circulo":
        ruta.addEllipse(QPointF(0, 0), r, r)
        return ruta
    if forma == "cuadrado":
        pts = [QPointF(-r * .85, -r * .85), QPointF(r * .85, -r * .85),
               QPointF(r * .85, r * .85), QPointF(-r * .85, r * .85)]
    elif forma in ("triangulo", "pentagono", "hexagono"):
        n = {"triangulo": 3, "pentagono": 5, "hexagono": 6}[forma]
        pts = _poligono(n, r * (1.1 if n == 3 else 1.0))
        if n == 3:  # bajar un poco el triángulo para centrarlo a la vista
            pts = [QPointF(p.x(), p.y() + r * .15) for p in pts]
    elif forma == "estrella":
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = math.radians(-90 + 36 * i)
            pts.append(QPointF(rr * math.cos(a), rr * math.sin(a)))
    elif forma == "flecha":
        crudos = [(0, -1), (.75, -.1), (.3, -.1), (.3, 1), (-.3, 1), (-.3, -.1), (-.75, -.1)]
        pts = [QPointF(x * r, y * r) for x, y in crudos]
    else:
        raise ValueError(forma)
    ruta.addPolygon(QPolygonF(pts))
    ruta.closeSubpath()
    return ruta


def _pintar_forma(p: QPainter, ruta: QPainterPath, relleno: int, radio: float, grosor: float) -> None:
    """Relleno 0 = vacío, 1 = rayado (rayas proporcionales al tamaño), 2 = sólido."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(TINTA if relleno == 2 else QColor("white"))
    p.drawPath(ruta)
    if relleno == 1:
        p.save()
        p.setClipPath(ruta)
        p.setPen(QPen(TINTA, max(1.0, grosor * 0.7)))
        paso = max(3.0, radio / 3.2)
        k = -2 * radio
        while k <= 2 * radio:
            p.drawLine(QPointF(k - radio * 1.5, radio * 1.5), QPointF(k + radio * 1.5, -radio * 1.5))
            k += paso
        p.restore()
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(TINTA, grosor))
    p.drawPath(ruta)


def _cuadrado_centrado(r: QRectF, margen: float = 0.0) -> QRectF:
    lado = min(r.width(), r.height()) - 2 * margen
    return QRectF(r.center().x() - lado / 2, r.center().y() - lado / 2, lado, lado)


def _signo_interrogacion(p: QPainter, r: QRectF) -> None:
    f = QFont()
    f.setPixelSize(max(10, int(min(r.width(), r.height()) * 0.5)))
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#e0560b"))
    p.drawText(r, Qt.AlignmentFlag.AlignCenter, "?")


@dataclass(frozen=True)
class Celda:
    forma: str = "circulo"
    numero: int = 1
    tamano: int = 1      # 0 chico, 1 mediano, 2 grande
    relleno: int = 0     # 0 vacío, 1 rayado, 2 sólido
    rotacion: int = 0    # grados (solo se nota en la flecha)

    def firma(self) -> tuple:
        rot = self.rotacion % 360 if self.forma == "flecha" else 0
        return (self.forma, self.numero, self.tamano, self.relleno, rot)

    def pintar(self, p: QPainter, r: QRectF) -> None:
        lado = min(r.width(), r.height())
        radio = lado * RADIO_TAMANO[self.tamano]
        sep = lado * SEPARACION[self.numero]
        grosor = max(1.5, lado * 0.02)
        for x, y in POSICIONES[self.numero]:
            p.save()
            p.translate(r.center().x() + x * sep, r.center().y() + y * sep)
            p.rotate(self.rotacion)
            _pintar_forma(p, ruta_forma(self.forma, radio), self.relleno, radio, grosor)
            p.restore()


@dataclass
class Matriz:
    """Matriz 3×3; la celda que falta es None."""
    celdas: list

    def pintar(self, p: QPainter, r: QRectF) -> None:
        cuad = _cuadrado_centrado(r, 4)
        t = cuad.width() / 3
        p.setPen(QPen(QColor("#b9b2ab"), 1.5))
        p.setBrush(QColor("white"))
        p.drawRect(cuad)
        for i, celda in enumerate(self.celdas):
            caja = QRectF(cuad.left() + (i % 3) * t, cuad.top() + (i // 3) * t, t, t)
            p.setPen(QPen(QColor("#b9b2ab"), 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(caja)
            if celda is None:
                _signo_interrogacion(p, caja)
            else:
                celda.pintar(p, caja.adjusted(t * .06, t * .06, -t * .06, -t * .06))


@dataclass
class SerieFiguras:
    """Fila de celdas seguida de un «?»."""
    celdas: list

    def pintar(self, p: QPainter, r: QRectF) -> None:
        n = len(self.celdas) + 1
        t = min(r.width() / n, r.height())
        x0 = r.center().x() - t * n / 2
        y0 = r.center().y() - t / 2
        for i in range(n):
            caja = QRectF(x0 + i * t, y0, t, t)
            p.setPen(QPen(QColor("#b9b2ab"), 1.5))
            p.setBrush(QColor("white"))
            p.drawRect(caja.adjusted(2, 2, -2, -2))
            if i < len(self.celdas):
                self.celdas[i].pintar(p, caja.adjusted(t * .08, t * .08, -t * .08, -t * .08))
            else:
                _signo_interrogacion(p, caja)


@dataclass
class Poliomino:
    celdas: frozenset

    def pintar(self, p: QPainter, r: QRectF) -> None:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("white"))
        p.drawRoundedRect(_cuadrado_centrado(r), 10, 10)
        xs = [x for x, _ in self.celdas]
        ys = [y for _, y in self.celdas]
        ancho, alto = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
        lado = min(r.width(), r.height()) * 0.8 / max(ancho, alto)
        x0 = r.center().x() - ancho * lado / 2
        y0 = r.center().y() - alto * lado / 2
        p.setPen(QPen(TINTA, max(1.5, lado * 0.08)))
        p.setBrush(RELLENO_CLARO)
        for x, y in self.celdas:
            p.drawRect(QRectF(x0 + (x - min(xs)) * lado, y0 + (y - min(ys)) * lado, lado, lado))


# ---------- Topología (subprueba «Condiciones», estilo Cattell) ----------

def vertices_triangulo(cx: float, cy: float, s: float) -> list[tuple[float, float]]:
    r = s * 1.25
    return [(cx + r * math.cos(math.radians(-90 + 120 * i)),
             cy + r * math.sin(math.radians(-90 + 120 * i)) + s * 0.2) for i in range(3)]


def dentro(forma: tuple, x: float, y: float, margen: float = 0.0) -> bool:
    """¿El punto cae dentro de la forma? `margen` > 0 la agranda, < 0 la achica."""
    tipo, cx, cy, s = forma
    if tipo == "triangulo":
        cy += s * 0.2
        s += margen / 0.625      # 0.625·s es el radio inscrito del triángulo
        cy -= s * 0.2
    else:
        s += margen
    if s <= 0:
        return False
    if tipo == "circulo":
        return (x - cx) ** 2 + (y - cy) ** 2 <= s * s
    if tipo == "cuadrado":
        return abs(x - cx) <= s and abs(y - cy) <= s
    (x1, y1), (x2, y2), (x3, y3) = vertices_triangulo(cx, cy, s)
    d1 = (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
    d2 = (x - x3) * (y2 - y3) - (x2 - x3) * (y - y3)
    d3 = (x - x1) * (y3 - y1) - (x3 - x1) * (y - y1)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


@dataclass
class Topologia:
    formas: list = field(default_factory=list)  # [(tipo, cx, cy, s)] en [0, 1]

    def pintar(self, p: QPainter, r: QRectF) -> None:
        cuad = _cuadrado_centrado(r, 6)
        L = cuad.width()

        def punto(x: float, y: float) -> QPointF:
            return QPointF(cuad.left() + x * L, cuad.top() + y * L)

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(TINTA, max(1.5, L * 0.012)))
        for tipo, cx, cy, s in self.formas:
            if tipo == "circulo":
                p.drawEllipse(punto(cx, cy), s * L, s * L)
            elif tipo == "cuadrado":
                p.drawRect(QRectF(punto(cx - s, cy - s), punto(cx + s, cy + s)))
            else:
                p.drawPolygon(QPolygonF([punto(x, y) for x, y in vertices_triangulo(cx, cy, s)]))

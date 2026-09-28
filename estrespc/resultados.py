"""Calificación de una prueba de estrés y la ventana de resultados (con tacómetro).

Calificación (0-100 %):
  - Temperatura máxima (60 %): CPU ≤70 °C = 100, 95 °C = 0; GPU ≤65 °C = 100, 87 °C = 0.
  - Frecuencia sostenida (40 %): promedio bajo carga (uso > 80 %) / máximo visto en la prueba.
    ≥95 % = 100, ≤60 % = 0. Mide cuánto se frena el equipo por calor (throttling).
  - Topes: si hubo errores de cálculo, máximo 25 %; si se detuvo por temperatura, máximo 40 %.
"""

import math
import statistics

from PySide6.QtCore import QPointF, QRectF, Qt, QUrl, QVariantAnimation
from PySide6.QtGui import QColor, QDesktopServices, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

VERDE, AMARILLO, ROJO, AZUL, GRIS = "#3ecf6e", "#ffc53d", "#ff4d4f", "#4aa3ff", "#8a8f98"


def _lineal(v, bueno, malo):
    """100 si v está en `bueno` o mejor, 0 en `malo` o peor, lineal entre medio."""
    if v is None:
        return None
    return max(0.0, min(100.0, (v - malo) / (bueno - malo) * 100))


def calcular(muestras, estados, motivo, segundos):
    """muestras: [(t, {sensor: valor})]; estados: {prueba: (estado, errores)}."""
    def serie(clave, uso=None):
        return [d[clave] for _t, d in muestras
                if d.get(clave) is not None and (uso is None or (d.get(uso) or 0) > 80)]

    r = {"segundos": segundos, "partes": []}
    for pieza, temp, mhz, uso, t_bueno, t_malo in (("CPU", "cpu_temp", "cpu_mhz", "cpu_uso", 70, 95),
                                                   ("GPU", "gpu_temp", "gpu_mhz", "gpu_uso", 65, 87)):
        temps, bajo_carga, todas = serie(temp), serie(mhz, uso), serie(mhz)
        if not bajo_carga:
            if temps:
                r[f"{pieza}_temp_max"] = max(temps)
            continue  # esta pieza no trabajó en la prueba: no se califica
        t_max = max(temps) if temps else None
        prom, pico = statistics.mean(bajo_carga), max(todas)
        r[f"{pieza}_temp_max"], r[f"{pieza}_mhz_prom"], r[f"{pieza}_mhz_pico"] = t_max, prom, pico
        r["partes"].append((f"Temperatura {pieza}", _lineal(t_max, t_bueno, t_malo), 0.6,
                            f"máx. {t_max:.0f} °C" if t_max is not None else "sin sensor"))
        r["partes"].append((f"Frecuencia sostenida {pieza}", _lineal(prom / pico, 0.95, 0.60), 0.4,
                            f"{prom:.0f} de {pico:.0f} MHz ({prom / pico:.0%})"))
    validas = [(p, w) for _n, p, w, _d in r["partes"] if p is not None]
    puntaje = sum(p * w for p, w in validas) / sum(w for _p, w in validas) if validas else 100.0

    errores = sum(e for _s, e in estados.values())
    r["topes"] = []
    if errores:
        puntaje = min(puntaje, 25)
        r["topes"].append(f"Hubo {errores} error(es) de cálculo: máximo 25 %")
    if motivo.startswith("Temperatura"):
        puntaje = min(puntaje, 40)
        r["topes"].append("Se detuvo por temperatura: máximo 40 %")
    if any(s == "fallo" for s, _e in estados.values()):
        r["topes"].append("Alguna prueba no pudo correr completa (revisa el registro)")
    r["puntaje"] = round(puntaje)
    r["etiqueta"] = ("Excelente" if puntaje >= 85 else "Buena" if puntaje >= 70 else
                     "Regular" if puntaje >= 50 else "Mala")
    r["errores"] = errores
    r["estados"] = estados
    return r


def texto_informe(r):
    lineas = [f"Calificación: {r['puntaje']} % ({r['etiqueta']})"]
    for nombre, p, w, detalle in r["partes"]:
        lineas.append(f"  {nombre}: {'—' if p is None else f'{p:.0f} %'} (peso {w:.0%}) · {detalle}")
    lineas += [f"  Tope: {t}" for t in r["topes"]]
    return lineas


def color_de(p):
    return ROJO if p < 50 else AMARILLO if p < 75 else VERDE


class Tacometro(QWidget):
    """Medidor tipo tacómetro de 0 a 100 con aguja animada."""

    INICIO, BARRIDO = 225.0, 270.0  # grados (Qt: 0° = 3 en punto, sentido antihorario)

    def __init__(self, padre=None):
        super().__init__(padre)
        self.setMinimumSize(320, 280)
        self.valor = 0.0
        self.etiqueta = ""
        self._anim = QVariantAnimation(self, duration=1600)
        self._anim.valueChanged.connect(self._mover)

    def fijar(self, valor, etiqueta):
        self.etiqueta = etiqueta
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(float(valor))
        self._anim.start()

    def _mover(self, v):
        self.valor = float(v)
        self.update()

    def _angulo(self, v):
        return self.INICIO - self.BARRIDO * v / 100

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        lado = min(self.width(), self.height() * 1.15)
        c = QPointF(self.width() / 2, self.height() * 0.55)
        radio = lado * 0.42
        caja = QRectF(c.x() - radio, c.y() - radio, 2 * radio, 2 * radio)

        # Zonas de color (roja 0-50, amarilla 50-75, verde 75-100).
        grosor = radio * 0.13
        for desde, hasta, color in ((0, 50, ROJO), (50, 75, AMARILLO), (75, 100, VERDE)):
            p.setPen(QPen(QColor(color), grosor, Qt.SolidLine, Qt.FlatCap))
            p.drawArc(caja, int(self._angulo(desde) * 16), int(-self.BARRIDO * (hasta - desde) / 100 * 16))

        # Marcas y números cada 10.
        p.setFont(QFont("sans", max(8, int(radio * 0.07))))
        for v in range(0, 101, 5):
            a = math.radians(self._angulo(v))
            largo = radio * (0.16 if v % 10 == 0 else 0.08)
            ext = radio - grosor / 2 - 3
            p1 = QPointF(c.x() + ext * math.cos(a), c.y() - ext * math.sin(a))
            p2 = QPointF(c.x() + (ext - largo) * math.cos(a), c.y() - (ext - largo) * math.sin(a))
            p.setPen(QPen(QColor("#c8ccd4"), 2 if v % 10 == 0 else 1))
            p.drawLine(p1, p2)
            if v % 10 == 0:
                r2 = ext - largo - radio * 0.1
                pt = QPointF(c.x() + r2 * math.cos(a), c.y() - r2 * math.sin(a))
                p.drawText(QRectF(pt.x() - 20, pt.y() - 10, 40, 20), Qt.AlignCenter, str(v))

        # Aguja.
        a = math.radians(self._angulo(self.valor))
        punta = QPointF(c.x() + radio * 0.78 * math.cos(a), c.y() - radio * 0.78 * math.sin(a))
        cola = QPointF(c.x() - radio * 0.12 * math.cos(a), c.y() + radio * 0.12 * math.sin(a))
        p.setPen(QPen(QColor(color_de(self.valor)), max(3, radio * 0.03), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(cola, punta)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2d313b"))
        p.drawEllipse(c, radio * 0.09, radio * 0.09)
        p.setBrush(QColor(color_de(self.valor)))
        p.drawEllipse(c, radio * 0.04, radio * 0.04)

        # Número grande y etiqueta.
        p.setPen(QColor(color_de(self.valor)))
        p.setFont(QFont("sans", int(radio * 0.24), QFont.Bold))
        p.drawText(QRectF(c.x() - radio, c.y() + radio * 0.22, 2 * radio, radio * 0.34),
                   Qt.AlignCenter, f"{self.valor:.0f} %")
        p.setPen(QColor("#e1e4ea"))
        p.setFont(QFont("sans", int(radio * 0.1), QFont.Bold))
        p.drawText(QRectF(c.x() - radio, c.y() + radio * 0.56, 2 * radio, radio * 0.2),
                   Qt.AlignCenter, self.etiqueta if self._anim.state() != QVariantAnimation.Running else "")


class VentanaResultados(QDialog):
    def __init__(self, r, titulo, carpeta, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Resultados de la prueba")
        self.resize(760, 640)
        lay = QVBoxLayout(self)

        cab = QLabel(titulo)
        cab.setStyleSheet("font-size:17px; font-weight:bold")
        cab.setWordWrap(True)
        lay.addWidget(cab)

        fila = QHBoxLayout()
        self.taco = Tacometro()
        fila.addWidget(self.taco, 3)

        datos = QGridLayout()
        datos.setVerticalSpacing(8)
        seg = int(r["segundos"])
        filas = [("Tiempo de la prueba", f"{seg // 3600:02d}:{seg % 3600 // 60:02d}:{seg % 60:02d}", None)]
        for pieza in ("CPU", "GPU"):
            t = r.get(f"{pieza}_temp_max")
            if t is not None:
                filas.append((f"{pieza} · temperatura máxima", f"{t:.0f} °C",
                              ROJO if t >= (90 if pieza == "CPU" else 85) else
                              AMARILLO if t >= (80 if pieza == "CPU" else 75) else VERDE))
            m = r.get(f"{pieza}_mhz_prom")
            if m is not None:
                filas.append((f"{pieza} · MHz promedio bajo carga",
                              f"{m:.0f} MHz (pico {r[f'{pieza}_mhz_pico']:.0f})", None))
        for nombre, (estado, errores) in sorted(r["estados"].items()):
            filas.append((f"Errores · {nombre}", str(errores), ROJO if errores else VERDE))
        for i, (k, v, color) in enumerate(filas):
            lk = QLabel(k)
            lk.setStyleSheet("color:#aab")
            lv = QLabel(v)
            lv.setStyleSheet(f"font-size:15px; font-weight:bold; color:{color or '#e1e4ea'}")
            datos.addWidget(lk, i, 0)
            datos.addWidget(lv, i, 1)
        caja = QWidget()
        caja.setLayout(datos)
        fila.addWidget(caja, 2)
        lay.addLayout(fila, 1)

        desglose = ["<b>Cómo se calculó:</b>"]
        for nombre, p, w, detalle in r["partes"]:
            color = GRIS if p is None else color_de(p)
            desglose.append(f"{nombre}: <span style='color:{color}'><b>"
                            f"{'—' if p is None else f'{p:.0f} %'}</b></span> "
                            f"(peso {w:.0%}) · {detalle}")
        desglose += [f"<span style='color:{ROJO}'>{t}</span>" for t in r["topes"]]
        if not r["partes"]:
            desglose.append("No hubo carga suficiente de CPU ni GPU para calificar temperatura y frecuencia.")
        nota = QLabel("<br>".join(desglose))
        nota.setWordWrap(True)
        nota.setStyleSheet("color:#c8ccd4")
        lay.addWidget(nota)

        botones = QHBoxLayout()
        botones.addStretch(1)
        if carpeta:
            b = QPushButton("Abrir carpeta del informe")
            b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(carpeta)))
            botones.addWidget(b)
        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.accept)
        botones.addWidget(cerrar)
        lay.addLayout(botones)
        self.taco.fijar(r["puntaje"], r["etiqueta"])

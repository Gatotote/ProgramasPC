"""Widgets que aplican cada tipo de subprueba.

Todos emiten:
  * terminado(dict)  — resultado de la subprueba,
  * progreso(str)    — texto para la barra superior,
  * reloj(str)       — tiempo restante (o "" si no hay límite).
"""

from __future__ import annotations

import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QAbstractButton, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from .. import irt
from ..generadores import Item
from .estilo import ACENTO, TINTA

LETRAS = "ABCDEFGH"


# ------------------------------------------------------------------ piezas de dibujo

class Lienzo(QWidget):
    """Dibuja una figura (matriz, serie, polióminos…) ocupando todo el widget."""

    def __init__(self, figura, alto: int = 300):
        super().__init__()
        self.figura = figura
        self.setMinimumHeight(alto)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.figura.pintar(p, QRectF(self.rect()).adjusted(4, 4, -4, -4))


class BotonFigura(QAbstractButton):
    def __init__(self, figura, letra: str):
        super().__init__()
        self.figura, self.letra = figura, letra
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumSize(110, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        p.setPen(QPen(QColor(ACENTO if self.underMouse() else "#d8d2cc"), 3 if self.underMouse() else 1.5))
        p.setBrush(QColor("white"))
        p.drawRoundedRect(r, 10, 10)
        f = QFont()
        f.setPixelSize(14)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#8a8fb0"))
        p.drawText(r.adjusted(8, 4, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.letra)
        lado = min(r.width(), r.height()) - 26
        caja = QRectF(r.center().x() - lado / 2, r.center().y() - lado / 2 + 6, lado, lado)
        self.figura.pintar(p, caja)

    def enterEvent(self, e):
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.update()
        super().leaveEvent(e)


# ------------------------------------------------------------------ una pregunta

class VistaItem(QWidget):
    respondido = Signal(bool)

    def __init__(self, item: Item):
        super().__init__()
        self.item = item
        self._listo = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        lay = QVBoxLayout(self)
        lay.setSpacing(14)

        preg = QLabel(item.pregunta)
        preg.setObjectName("pregunta")
        preg.setWordWrap(True)
        lay.addWidget(preg)
        if item.texto_grande:
            grande = QLabel(item.texto_grande)
            grande.setObjectName("grande")
            grande.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(grande)
        if item.figura is not None:
            lay.addWidget(Lienzo(item.figura, 260), 3)

        if item.clase == "numero":
            fila = QHBoxLayout()
            self.entrada = QLineEdit()
            self.entrada.setObjectName("respuesta")
            self.entrada.setPlaceholderText("Escribe tu respuesta")
            self.entrada.setMaximumWidth(320)
            self.entrada.returnPressed.connect(self._numero)
            ok = QPushButton("Responder  ⏎")
            ok.setObjectName("principal")
            ok.clicked.connect(self._numero)
            fila.addStretch()
            fila.addWidget(self.entrada)
            fila.addWidget(ok)
            fila.addStretch()
            lay.addLayout(fila)
            QTimer.singleShot(0, self, self.entrada.setFocus)
        else:
            rejilla = QGridLayout()
            rejilla.setSpacing(10)
            n = len(item.opciones)
            columnas = 2 if item.clase == "texto" else (4 if n in (4, 8) else n)
            for i, op in enumerate(item.opciones):
                if item.clase == "texto":
                    b = QPushButton(f"{LETRAS[i]})  {op}")
                    b.setObjectName("opcion")
                    b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                else:
                    b = BotonFigura(op, LETRAS[i])
                b.clicked.connect(lambda _=False, i=i: self._elegir(i))
                rejilla.addWidget(b, i // columnas, i % columnas)
            lay.addLayout(rejilla, 2 if item.clase == "figura" else 0)

        pasar = QPushButton("No sé, siguiente →")
        pasar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pasar.clicked.connect(lambda: self._emitir(False))
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(pasar)
        lay.addLayout(fila)
        if item.clase != "figura":
            lay.addStretch()

    def _emitir(self, ok: bool) -> None:
        if not self._listo:
            self._listo = True
            self.respondido.emit(ok)

    def _elegir(self, i: int) -> None:
        self._emitir(i == self.item.correcta)

    def _numero(self) -> None:
        texto = self.entrada.text().strip().replace(",", ".").replace("$", "")
        if not texto:
            return
        try:
            self._emitir(abs(float(texto) - float(self.item.correcta)) < 1e-9)
        except ValueError:
            self._emitir(False)

    def keyPressEvent(self, e):
        if self.item.clase != "numero":
            t = e.text().upper()
            if t and t in LETRAS[:len(self.item.opciones)]:
                self._elegir(LETRAS.index(t))
                return
        super().keyPressEvent(e)


class PruebaItems(QWidget):
    """Aplica una lista de preguntas ordenadas por dificultad, con regla de suspensión."""
    terminado = Signal(dict)
    progreso = Signal(str)
    reloj = Signal(str)

    def __init__(self, sp, items: list[Item], inicio: int):
        super().__init__()
        self.sp, self.items, self.i = sp, items, inicio
        self.respuestas: list = []
        self.errores_seguidos = 0
        self.vista: VistaItem | None = None
        self.t0 = time.monotonic()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.tic = QTimer(self)
        self.tic.timeout.connect(self._tic)
        self.tic.start(250)
        QTimer.singleShot(0, self, self._mostrar)

    def _mostrar(self) -> None:
        sp = self.sp
        fin = (self.i >= len(self.items) or len(self.respuestas) >= sp.max_items
               or (sp.discontinuar and self.errores_seguidos >= sp.discontinuar))
        if fin:
            self.tic.stop()
            self.terminado.emit({"respuestas": self.respuestas})
            return
        nueva = VistaItem(self.items[self.i])
        nueva.respondido.connect(self._responder)
        if self.vista:
            self.lay.removeWidget(self.vista)
            self.vista.deleteLater()
        self.vista = nueva
        self.lay.addWidget(nueva)
        if self.items[self.i].clase != "numero":
            nueva.setFocus()
        self.t0 = time.monotonic()
        tope = min(sp.max_items, len(self.respuestas) + len(self.items) - self.i)
        self.progreso.emit(f"Pregunta {len(self.respuestas) + 1} de {tope} como máximo")
        self._tic()

    def _responder(self, ok: bool) -> None:
        it = self.items[self.i]
        self.respuestas.append((it.a, it.b, it.c, bool(ok)))
        self.errores_seguidos = 0 if ok else self.errores_seguidos + 1
        self.i += 1
        self._mostrar()

    def _tic(self) -> None:
        if not self.sp.tiempo_item or self.vista is None:
            self.reloj.emit("")
            return
        quedan = self.sp.tiempo_item - (time.monotonic() - self.t0)
        self.reloj.emit(f"⏱ {max(0, int(quedan + 0.999))} s")
        if quedan <= 0:
            self.vista._emitir(False)

    def detener(self) -> None:
        self.tic.stop()


# ------------------------------------------------------------------ memoria: dígitos

class PruebaDigitos(QWidget):
    terminado = Signal(dict)
    progreso = Signal(str)
    reloj = Signal(str)

    def __init__(self, edad: float, rng: random.Random):
        super().__init__()
        self.rng = rng
        self.partes = [("directo", 2 if edad < 9 else 3, 9), ("inverso", 2, 8)]
        self.parte = 0
        self.respuestas: list = []
        self.span = {"directo": 0, "inverso": 0}
        self._activos: list[QTimer] = []

        lay = QVBoxLayout(self)
        self.instr = QLabel()
        self.instr.setObjectName("pregunta")
        self.instr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instr.setWordWrap(True)
        self.numero = QLabel("")
        self.numero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.numero.setStyleSheet(f"font-size: 120px; font-weight: 800; color: {ACENTO};")
        self.numero.setMinimumHeight(200)
        self.entrada = QLineEdit()
        self.entrada.setObjectName("respuesta")
        self.entrada.setMaximumWidth(360)
        self.entrada.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.entrada.returnPressed.connect(self._revisar)
        self.boton = QPushButton("Continuar")
        self.boton.setObjectName("principal")
        self.boton.clicked.connect(self._iniciar_parte)
        lay.addStretch()
        lay.addWidget(self.instr)
        lay.addWidget(self.numero)
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(self.entrada)
        fila.addWidget(self.boton)
        fila.addStretch()
        lay.addLayout(fila)
        lay.addStretch()
        self.reloj.emit("")
        self._pantalla_parte()

    def _pantalla_parte(self) -> None:
        tipo = self.partes[self.parte][0]
        self.entrada.hide()
        self.numero.setText("")
        self.boton.show()
        if tipo == "directo":
            self.instr.setText("Parte 1: escribe los números en el MISMO orden en que aparecen.")
        else:
            self.instr.setText("Parte 2: ahora escríbelos AL REVÉS.\n"
                               "Ejemplo: si ves 3 – 8 – 1, escribe 183.")
        self.progreso.emit(f"Parte {self.parte + 1} de 2")

    def _iniciar_parte(self) -> None:
        self.boton.hide()
        _, self.longitud, self.maximo = self.partes[self.parte]
        self.intento, self.fallos = 0, 0
        self._ensayo()

    def _ensayo(self) -> None:
        digitos = []
        while len(digitos) < self.longitud:
            d = str(self.rng.randint(1, 9))
            if not digitos or d != digitos[-1]:
                digitos.append(d)
        self.secuencia = "".join(digitos)
        self.entrada.hide()
        self.instr.setText("Pon atención…")
        self.progreso.emit(f"Parte {self.parte + 1} de 2 · {self.longitud} números")
        t = 900
        for d in self.secuencia:
            QTimer.singleShot(t, self, lambda d=d: self.numero.setText(d))
            QTimer.singleShot(t + 750, self, lambda: self.numero.setText(""))
            t += 1000
        QTimer.singleShot(t, self, self._pedir)

    def _pedir(self) -> None:
        tipo = self.partes[self.parte][0]
        self.instr.setText("Escribe los números " + ("en el mismo orden" if tipo == "directo" else "AL REVÉS")
                           + " y presiona Enter.")
        self.entrada.clear()
        self.entrada.show()
        self.entrada.setFocus()

    def _revisar(self) -> None:
        texto = "".join(ch for ch in self.entrada.text() if ch.isdigit())
        if not texto or not self.entrada.isVisible():
            return
        tipo = self.partes[self.parte][0]
        esperado = self.secuencia if tipo == "directo" else self.secuencia[::-1]
        ok = texto == esperado
        self.respuestas.append((1.8, irt.b_span(tipo, self.longitud), 0.0, ok))
        if ok:
            self.span[tipo] = max(self.span[tipo], self.longitud)
        else:
            self.fallos += 1
        self.entrada.hide()
        if self.intento == 0:
            self.intento = 1
        else:
            if self.fallos == 2 or self.longitud >= self.maximo:
                self._siguiente_parte()
                return
            self.longitud += 1
            self.intento, self.fallos = 0, 0
        self.instr.setText("✓ Listo")
        QTimer.singleShot(600, self, self._ensayo)

    def _siguiente_parte(self) -> None:
        self.parte += 1
        if self.parte >= len(self.partes):
            self.terminado.emit({"respuestas": self.respuestas,
                                 "span": f"{self.span['directo']} directo / {self.span['inverso']} inverso"})
        else:
            self._pantalla_parte()

    def detener(self) -> None:
        pass


# ------------------------------------------------------------------ memoria: bloques de Corsi

POS_CORSI = [(0.12, 0.18), (0.45, 0.08), (0.80, 0.15), (0.28, 0.45), (0.62, 0.38),
             (0.88, 0.52), (0.10, 0.78), (0.45, 0.72), (0.75, 0.85)]


class TableroCorsi(QWidget):
    clic = Signal(int)

    def __init__(self):
        super().__init__()
        self.encendido = -1
        self.activo = False
        self.setMinimumSize(420, 360)

    def _rect(self, i: int) -> QRectF:
        w, h = self.width(), self.height()
        lado = min(w, h) * 0.14
        x, y = POS_CORSI[i]
        return QRectF(x * (w - lado), y * (h - lado), lado, lado)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i in range(9):
            p.setPen(QPen(QColor(TINTA), 2))
            p.setBrush(QColor("#fff2a8") if i == self.encendido else QColor(ACENTO if self.activo else "#7a3f14"))
            p.drawRoundedRect(self._rect(i), 8, 8)

    def mousePressEvent(self, e):
        if not self.activo:
            return
        for i in range(9):
            if self._rect(i).contains(QPointF(e.position())):
                self.encendido = i
                self.update()
                QTimer.singleShot(250, self, self._apagar)
                self.clic.emit(i)
                return

    def _apagar(self):
        self.encendido = -1
        self.update()


class PruebaCorsi(QWidget):
    terminado = Signal(dict)
    progreso = Signal(str)
    reloj = Signal(str)

    def __init__(self, edad: float, rng: random.Random):
        super().__init__()
        self.rng = rng
        self.longitud, self.maximo = 2, 9
        self.intento, self.fallos = 0, 0
        self.respuestas: list = []
        self.span = 0
        lay = QVBoxLayout(self)
        self.instr = QLabel("Pon atención a los cuadros que se iluminan…")
        self.instr.setObjectName("pregunta")
        self.instr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tablero = TableroCorsi()
        self.tablero.clic.connect(self._clic)
        lay.addWidget(self.instr)
        lay.addWidget(self.tablero, 1)
        self.reloj.emit("")
        QTimer.singleShot(800, self, self._ensayo)

    def _ensayo(self) -> None:
        self.secuencia = []
        while len(self.secuencia) < self.longitud:
            b = self.rng.randrange(9)
            if b not in self.secuencia:
                self.secuencia.append(b)
        self.clics: list[int] = []
        self.tablero.activo = False
        self.instr.setText("Pon atención…")
        self.progreso.emit(f"Secuencia de {self.longitud} cuadros")
        t = 700
        for b in self.secuencia:
            QTimer.singleShot(t, self, lambda b=b: self._encender(b))
            QTimer.singleShot(t + 650, self, lambda: self._encender(-1))
            t += 950
        QTimer.singleShot(t, self, self._pedir)

    def _encender(self, b: int) -> None:
        self.tablero.encendido = b
        self.tablero.update()

    def _pedir(self) -> None:
        self.instr.setText("Ahora haz clic en los cuadros en el mismo orden.")
        self.tablero.activo = True
        self.tablero.update()

    def _clic(self, b: int) -> None:
        self.clics.append(b)
        if len(self.clics) < self.longitud:
            return
        self.tablero.activo = False
        ok = self.clics == self.secuencia
        self.respuestas.append((1.8, irt.b_span("corsi", self.longitud), 0.0, ok))
        if ok:
            self.span = max(self.span, self.longitud)
        else:
            self.fallos += 1
        if self.intento == 0:
            self.intento = 1
        else:
            if self.fallos == 2 or self.longitud >= self.maximo:
                self.terminado.emit({"respuestas": self.respuestas, "span": self.span})
                return
            self.longitud += 1
            self.intento, self.fallos = 0, 0
        self.instr.setText("✓ Listo")
        QTimer.singleShot(900, self, self._ensayo)

    def detener(self) -> None:
        pass


# ------------------------------------------------------------------ velocidad

SIMBOLOS = list("◐◑◒◓▲▼◀▶◆◇○●□■△▽☆★⊕⊗⊞⊟♠♣♥♦")


class _PruebaCronometrada(QWidget):
    terminado = Signal(dict)
    progreso = Signal(str)
    reloj = Signal(str)
    DURACION = 120

    def __init__(self, rng: random.Random):
        super().__init__()
        self.rng = rng
        self.aciertos = self.errores = 0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.fin = time.monotonic() + self.DURACION
        self.tic = QTimer(self)
        self.tic.timeout.connect(self._tic)
        self.tic.start(200)

    def _tic(self) -> None:
        quedan = self.fin - time.monotonic()
        self.reloj.emit(f"⏱ {max(0, int(quedan + 0.999))} s")
        self.progreso.emit(f"Aciertos: {self.aciertos}")
        if quedan <= 0:
            self.tic.stop()
            self.terminado.emit({"aciertos": self.aciertos, "errores": self.errores})

    def _marcar(self, ok: bool) -> None:
        if self.tic.isActive():
            if ok:
                self.aciertos += 1
            else:
                self.errores += 1
            self._siguiente()

    def detener(self) -> None:
        self.tic.stop()

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self, self.setFocus)


def _etiqueta_simbolo(tam: int, estilo: str = "") -> QLabel:
    l = QLabel()
    l.setStyleSheet(f"font-size: {tam}px; {estilo}")
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l.setMinimumWidth(int(tam * 1.3))
    return l


class PruebaBusqueda(_PruebaCronometrada):
    DURACION = 120

    def __init__(self, rng: random.Random):
        super().__init__(rng)
        lay = QVBoxLayout(self)
        fila = QHBoxLayout()
        fila.addStretch()
        self.obj = [_etiqueta_simbolo(64, "background: #3a2414; color: #ffd2a8; border-radius: 10px;") for _ in range(2)]
        for l in self.obj:
            fila.addWidget(l)
        sep = QLabel("│")
        sep.setStyleSheet("font-size: 64px; color: #5a4a3e;")
        fila.addWidget(sep)
        self.grupo = [_etiqueta_simbolo(64, "background: #232326; border-radius: 10px;") for _ in range(5)]
        for l in self.grupo:
            fila.addWidget(l)
        fila.addStretch()
        botones = QHBoxLayout()
        si = QPushButton("✔  Sí está  (S / ←)")
        no = QPushButton("✘  No está  (N / →)")
        for b in (si, no):
            b.setObjectName("principal")
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setMinimumHeight(64)
        si.clicked.connect(lambda: self._marcar(self.presente))
        no.clicked.connect(lambda: self._marcar(not self.presente))
        botones.addStretch()
        botones.addWidget(si)
        botones.addSpacing(30)
        botones.addWidget(no)
        botones.addStretch()
        lay.addStretch()
        lay.addLayout(fila)
        lay.addSpacing(40)
        lay.addLayout(botones)
        lay.addStretch()
        self._siguiente()

    def _siguiente(self) -> None:
        obj = self.rng.sample(SIMBOLOS, 2)
        resto = [s for s in SIMBOLOS if s not in obj]
        grupo = self.rng.sample(resto, 5)
        self.presente = self.rng.random() < 0.5
        if self.presente:
            grupo[self.rng.randrange(5)] = self.rng.choice(obj)
        for l, s in zip(self.obj, obj):
            l.setText(s)
        for l, s in zip(self.grupo, grupo):
            l.setText(s)

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key.Key_S, Qt.Key.Key_Left):
            self._marcar(self.presente)
        elif k in (Qt.Key.Key_N, Qt.Key.Key_Right):
            self._marcar(not self.presente)
        else:
            super().keyPressEvent(e)


class PruebaClaves(_PruebaCronometrada):
    DURACION = 90

    def __init__(self, rng: random.Random):
        super().__init__(rng)
        self.clave = rng.sample(SIMBOLOS, 9)
        lay = QVBoxLayout(self)
        tabla = QGridLayout()
        tabla.setHorizontalSpacing(4)
        for i, s in enumerate(self.clave):
            sl = _etiqueta_simbolo(40, "background: #232326; border: 1px solid #3a3a3e;")
            sl.setText(s)
            nl = QLabel(str(i + 1))
            nl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nl.setStyleSheet("font-size: 22px; font-weight: 700; color: #111111; background: #ff7a1a;")
            tabla.addWidget(sl, 0, i)
            tabla.addWidget(nl, 1, i)
        fila_tabla = QHBoxLayout()
        fila_tabla.addStretch()
        fila_tabla.addLayout(tabla)
        fila_tabla.addStretch()
        self.actual = _etiqueta_simbolo(120)
        self.actual.setMinimumHeight(170)
        teclas = QHBoxLayout()
        teclas.addStretch()
        for i in range(9):
            b = QPushButton(str(i + 1))
            b.setObjectName("tecla")
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.clicked.connect(lambda _=False, i=i: self._marcar(i == self.indice))
            teclas.addWidget(b)
        teclas.addStretch()
        lay.addLayout(fila_tabla)
        lay.addStretch()
        lay.addWidget(self.actual)
        lay.addStretch()
        lay.addLayout(teclas)
        self.indice = -1
        self._siguiente()

    def _siguiente(self) -> None:
        nuevo = self.indice
        while nuevo == self.indice:
            nuevo = self.rng.randrange(9)
        self.indice = nuevo
        self.actual.setText(self.clave[nuevo])

    def keyPressEvent(self, e):
        t = e.text()
        if t and t in "123456789":
            self._marcar(int(t) - 1 == self.indice)
        else:
            super().keyPressEvent(e)

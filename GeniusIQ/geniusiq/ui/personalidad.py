"""Pantallas de las pruebas de personalidad: contestar el cuestionario y ver el perfil."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QProgressBar, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from ..personalidad import Cuestionario
from ..salud import AVISO_SALUD, CRISIS
from .estilo import ACENTO, ACENTO_CLARO, BORDE, SUAVE, TEXTO
from .pantallas import _etiqueta, _tarjeta, pie_autor

AVISO_PERSONALIDAD = ("ℹ Las pruebas de personalidad describen preferencias y estilos; no hay resultados "
                      "buenos ni malos y no son un diagnóstico psicológico.")


# ------------------------------------------------------------------ contestar

def _partir(texto: str, ancho: int = 15) -> str:
    """Parte el texto de un botón en renglones de ~ancho letras."""
    renglones, actual = [], ""
    for palabra in texto.split():
        if actual and len(actual) + 1 + len(palabra) > ancho:
            renglones.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    return "\n".join(renglones + [actual])


class PantallaCuestionario(QWidget):
    terminado = Signal(list)
    salir = Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 20, 40, 20)
        barra = QHBoxLayout()
        self.titulo = _etiqueta("", "subtitulo", False)
        self.progreso = _etiqueta("", "suave", False)
        salir = QPushButton("Salir")
        salir.setObjectName("peligro")
        salir.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        salir.clicked.connect(self.salir.emit)
        barra.addWidget(self.titulo)
        barra.addSpacing(16)
        barra.addWidget(self.progreso)
        barra.addStretch()
        barra.addWidget(salir)
        lay.addLayout(barra)
        self.barra = QProgressBar()
        self.barra.setTextVisible(False)
        self.barra.setFixedHeight(8)
        lay.addWidget(self.barra)
        self.aviso = _etiqueta("", "suave")
        lay.addWidget(self.aviso)
        lay.addStretch(1)

        self.pregunta = _etiqueta("", "pregunta")
        self.pregunta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pregunta.setStyleSheet("font-size: 26px;")
        lay.addWidget(self.pregunta)

        self.izq = _etiqueta("", "pregunta")
        self.der = _etiqueta("", "pregunta")
        for l, al in ((self.izq, Qt.AlignmentFlag.AlignRight), (self.der, Qt.AlignmentFlag.AlignLeft)):
            l.setAlignment(al | Qt.AlignmentFlag.AlignVCenter)
            l.setMinimumWidth(260)
        lay.addSpacing(20)

        self.botones = []
        fila = QHBoxLayout()
        fila.addWidget(self.izq, 1)
        for i in range(5):
            b = QPushButton()
            b.setObjectName("tecla")
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setMinimumSize(120, 70)
            b.clicked.connect(lambda _=False, v=i + 1: self._responder(v))
            self.botones.append(b)
            fila.addWidget(b)
        fila.addWidget(self.der, 1)
        lay.addLayout(fila)
        lay.addStretch(2)

        abajo = QHBoxLayout()
        self.anterior = QPushButton("← Anterior")
        self.anterior.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.anterior.clicked.connect(self._anterior)
        abajo.addWidget(self.anterior)
        abajo.addStretch()
        self.ayuda = _etiqueta("", "suave", False)
        abajo.addWidget(self.ayuda)
        lay.addLayout(abajo)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def iniciar(self, c: Cuestionario) -> None:
        self.c = c
        self.respuestas: list[int | None] = [None] * len(c.preguntas)
        self.i = 0
        self.titulo.setText(c.nombre)
        self.aviso.setText(c.aviso)
        self.barra.setMaximum(len(c.preguntas))
        bipolar = c.tipo == "bipolar"
        self.izq.setVisible(bipolar)
        self.der.setVisible(bipolar)
        self.pregunta.setVisible(not bipolar)
        self._mostrar()
        self.setFocus()

    def _mostrar(self) -> None:
        p = self.c.preguntas[self.i]
        if self.c.tipo == "bipolar":
            self.izq.setText(p[0])
            self.der.setText(p[1])
        else:
            self.pregunta.setText(p)
        self.progreso.setText(f"Pregunta {self.i + 1} de {len(self.c.preguntas)}")
        self.ayuda.setText(f"Puedes contestar con las teclas 1 a {len(self.c.opciones_de(self.i))}.")
        self.barra.setValue(self.i)
        marcada = self.respuestas[self.i]
        self.opciones = self.c.opciones_de(self.i)
        bipolar = self.c.tipo == "bipolar"
        largas = any(len(o) > 12 for o in self.opciones)
        for k, b in enumerate(self.botones):
            b.setVisible(k < len(self.opciones))
            if k >= len(self.opciones):
                continue
            b.setText(str(k + 1) if bipolar else f"{k + 1}\n{_partir(self.opciones[k])}")
            estilo = "font-size: 16px; min-width: 150px;" if largas and not bipolar else ""
            if marcada == k + 1:
                estilo += f" background: {ACENTO}; color: #111;"
            b.setStyleSheet(estilo)
        self.anterior.setEnabled(self.i > 0)

    def _responder(self, v: int) -> None:
        self.respuestas[self.i] = v
        if self.i + 1 >= len(self.c.preguntas):
            self.terminado.emit(list(self.respuestas))
            return
        self.i += 1
        self._mostrar()

    def _anterior(self) -> None:
        if self.i > 0:
            self.i -= 1
            self._mostrar()

    def keyPressEvent(self, e):
        t = e.text()
        if len(t) == 1 and t.isdigit() and 1 <= int(t) <= len(self.opciones):
            self._responder(int(t))
        elif e.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Left):
            self._anterior()
        else:
            super().keyPressEvent(e)


# ------------------------------------------------------------------ gráficas

class Barras(QWidget):
    """Barras horizontales 0–100. filas = [(nombre, valor, texto_derecha)]."""

    def __init__(self, filas: list[tuple], alto_fila: int = 34, ancho_nombre: int = 230, marca: float | None = None,
                 ancho_texto: int = 110):
        super().__init__()
        self.filas, self.alto, self.izq, self.marca, self.ancho_texto = filas, alto_fila, ancho_nombre, marca, ancho_texto
        self.setMinimumHeight(alto_fila * len(filas) + 8)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        der = self.width() - self.ancho_texto - 10
        f = QFont()
        f.setPixelSize(14)
        for i, (nombre, valor, texto) in enumerate(self.filas):
            y = 4 + i * self.alto
            p.setFont(f)
            p.setPen(QColor(TEXTO))
            p.drawText(QRectF(0, y, self.izq - 12, self.alto - 8),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, nombre)
            fondo = QRectF(self.izq, y + 6, der - self.izq, self.alto - 20)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#2a2a2e"))
            p.drawRoundedRect(fondo, 5, 5)
            p.setBrush(QColor(ACENTO))
            p.drawRoundedRect(QRectF(fondo.left(), fondo.top(), fondo.width() * max(0, min(100, valor)) / 100,
                                     fondo.height()), 5, 5)
            if self.marca is not None:
                x = fondo.left() + fondo.width() * self.marca / 100
                p.setPen(QPen(QColor(SUAVE), 1, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(x, y + 2), QPointF(x, y + self.alto - 10))
            p.setPen(QColor(ACENTO_CLARO))
            p.drawText(QRectF(der + 10, y, self.ancho_texto, self.alto - 8),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, texto)


class BarraBipolar(QWidget):
    """Una dimensión de los 16 tipos: de un polo al otro, con la marca de la persona."""

    def __init__(self, izquierda: str, derecha: str, puntos: int, maximo: int = 16):
        super().__init__()
        self.izquierda, self.derecha, self.puntos, self.maximo = izquierda, derecha, puntos, maximo
        self.setMinimumHeight(46)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ancho_txt = 170
        izq, der = ancho_txt, self.width() - ancho_txt
        y = self.height() / 2
        f = QFont()
        f.setPixelSize(15)
        gana_izq = self.puntos > 0
        for texto, rect, gana, al in (
                (self.izquierda, QRectF(0, 0, ancho_txt - 12, self.height()), gana_izq, Qt.AlignmentFlag.AlignRight),
                (self.derecha, QRectF(der + 12, 0, ancho_txt - 12, self.height()), not gana_izq,
                 Qt.AlignmentFlag.AlignLeft)):
            f.setBold(gana)
            p.setFont(f)
            p.setPen(QColor(ACENTO_CLARO if gana else SUAVE))
            p.drawText(rect, al | Qt.AlignmentFlag.AlignVCenter, texto)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#2a2a2e"))
        p.drawRoundedRect(QRectF(izq, y - 7, der - izq, 14), 7, 7)
        centro = (izq + der) / 2
        x = centro - self.puntos / self.maximo * (der - izq) / 2
        p.setBrush(QColor(ACENTO))
        p.drawRoundedRect(QRectF(min(centro, x), y - 7, abs(x - centro), 14), 7, 7)
        p.setPen(QPen(QColor(BORDE), 2))
        p.drawLine(QPointF(centro, y - 12), QPointF(centro, y + 12))


class BarraCortes(QWidget):
    """Escala de un tamizaje dividida en zonas (de verde a rojo) con la marca del puntaje."""

    COLORES = ["#4caf50", "#c0ca33", "#ffb300", "#fb8c00", "#e53935"]

    def __init__(self, total: int, maximo: int, cortes: list[dict]):
        super().__init__()
        self.total, self.maximo, self.cortes = total, maximo, cortes
        self.setMinimumHeight(86)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        izq, der, y, alto = 10, self.width() - 10, 24, 18
        escala = (der - izq) / self.maximo
        n = len(self.cortes)
        colores = [self.COLORES[round(i * (len(self.COLORES) - 1) / max(1, n - 1))] for i in range(n)]
        f = QFont()
        f.setPixelSize(12)
        p.setFont(f)
        for i, c in enumerate(self.cortes):
            x1 = izq + c["desde"] * escala
            x2 = izq + (self.cortes[i + 1]["desde"] if i + 1 < n else self.maximo) * escala
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(colores[i]))
            p.drawRect(QRectF(x1, y, x2 - x1, alto))
            p.setPen(QColor(SUAVE))
            p.drawText(QRectF(x1 + 2, y + alto + 4, x2 - x1 - 6, 34),
                       int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) | int(Qt.TextFlag.TextWordWrap),
                       f"{c['desde']}+ {c['nivel']}")
        x = izq + min(self.total, self.maximo) * escala
        p.setPen(QPen(QColor(TEXTO), 3))
        p.drawLine(QPointF(x, y - 8), QPointF(x, y + alto + 2))
        f.setBold(True)
        f.setPixelSize(14)
        p.setFont(f)
        p.drawText(QRectF(x - 40, 0, 80, 16), Qt.AlignmentFlag.AlignCenter, str(self.total))


# ------------------------------------------------------------------ resultados

class PantallaPerfil(QWidget):
    volver = Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 12)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        lay.addWidget(self.scroll, 1)
        fila = QHBoxLayout()
        fila.addStretch()
        ok = QPushButton("Volver al inicio")
        ok.setObjectName("principal")
        ok.clicked.connect(self.volver.emit)
        fila.addWidget(ok)
        lay.addLayout(fila)

    def mostrar(self, res: dict, persona: str, fecha: str) -> None:
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setSpacing(12)
        fecha_txt = datetime.fromisoformat(fecha).strftime("%d/%m/%Y %H:%M")
        salud = res.get("tipo") == "salud"
        lay.addWidget(_etiqueta(f"{'Resultado' if salud else 'Perfil'} de {persona}", "titulo"))
        lay.addWidget(_etiqueta(f"{res['nombre_bateria']}  ·  {fecha_txt}  ·  edad {int(res['edad'])} años", "suave"))
        if salud:
            self._tamizaje(res, lay)
        else:
            {"bigfive": self._bigfive, "hexaco": self._bigfive, "tipos16": self._tipos16,
             "eneagrama": self._eneagrama, "laboral": self._laboral, "valores": self._valores}[res["prueba"]](res, lay)
        lay.addWidget(_etiqueta(AVISO_SALUD if salud else AVISO_PERSONALIDAD, "aviso"))
        lay.addWidget(pie_autor())
        lay.addStretch()
        self.scroll.setWidget(cont)

    def _bigfive(self, res: dict, lay: QVBoxLayout) -> None:
        tarjeta, t = _tarjeta()
        t.addWidget(_etiqueta("Los seis factores" if res["prueba"] == "hexaco" else "Los cinco grandes rasgos",
                              "subtitulo"))
        t.addWidget(_etiqueta("La barra es el percentil aproximado: qué porcentaje de adultos queda por debajo. "
                              "La línea punteada marca el promedio (50).", "suave"))
        t.addWidget(Barras([(d["nombre"], d["percentil"], f"{d['percentil']:.0f} · {d['nivel']}")
                            for d in res["dominios"]], 40, 230, marca=50))
        lay.addWidget(tarjeta)
        for d in res["dominios"]:
            tarjeta, t = _tarjeta()
            t.addWidget(_etiqueta(f"{d['nombre']} — {d['nivel']} (percentil {d['percentil']:.0f})", "subtitulo"))
            t.addWidget(_etiqueta(d["descripcion"], "suave"))
            t.addWidget(_etiqueta(d["lectura"]))
            t.addWidget(Barras([(f["nombre"], f["puntos"], f"{f['puntos']}") for f in d["facetas"]], 30, 230))
            lay.addWidget(tarjeta)
        lay.addWidget(_etiqueta("En las facetas, 0 = la frase no te describe nada y 100 = te describe totalmente.",
                                "suave"))

    def _tipos16(self, res: dict, lay: QVBoxLayout) -> None:
        tarjeta, t = _tarjeta()
        fila = QHBoxLayout()
        codigo = _etiqueta(res["tipo16"], "ci", False)
        fila.addWidget(codigo)
        fila.addSpacing(20)
        fila.addWidget(_etiqueta(res["descripcion_tipo"], "subtitulo"), 1)
        t.addLayout(fila)
        lay.addWidget(tarjeta)
        tarjeta, t = _tarjeta()
        t.addWidget(_etiqueta("Tus cuatro preferencias", "subtitulo"))
        for d in res["dimensiones"]:
            t.addWidget(BarraBipolar(d["izquierda"], d["derecha"], d["puntos"]))
            t.addWidget(_etiqueta(f"{d['descripcion']}  Claridad de la preferencia: {d['claridad']}%.", "suave"))
        lay.addWidget(tarjeta)
        lay.addWidget(_etiqueta("Si alguna preferencia salió con claridad baja (menos de 25%), estás cerca del "
                                "medio y la letra contraria también te puede describir.", "suave"))

    def _eneagrama(self, res: dict, lay: QVBoxLayout) -> None:
        tarjeta, t = _tarjeta()
        fila = QHBoxLayout()
        fila.addWidget(_etiqueta(f"{res['eneatipo']}w{res['ala']}", "ci", False))
        fila.addSpacing(20)
        der = QVBoxLayout()
        der.addWidget(_etiqueta(f"Tipo {res['eneatipo']}: {res['nombre_tipo']}", "subtitulo"))
        der.addWidget(_etiqueta(res["descripcion_tipo"]))
        ala = next(x for x in res["tipos"] if x["tipo"] == res["ala"])
        der.addWidget(_etiqueta(f"Ala {res['ala']} ({ala['nombre']}): el tipo vecino que más influye.", "suave"))
        fila.addLayout(der, 1)
        t.addLayout(fila)
        lay.addWidget(tarjeta)
        tarjeta, t = _tarjeta()
        t.addWidget(_etiqueta("Puntaje en los 9 tipos", "subtitulo"))
        t.addWidget(Barras([(f"{x['tipo']}. {x['nombre']}", x["puntos"], str(x["puntos"]))
                            for x in res["tipos"]], 32, 230))
        lay.addWidget(tarjeta)

    def _laboral(self, res: dict, lay: QVBoxLayout) -> None:
        tarjeta, t = _tarjeta()
        t.addWidget(_etiqueta("Rasgos para el trabajo", "subtitulo"))
        t.addWidget(_etiqueta("0 = no te describe, 100 = te describe totalmente. No hay normas: compara tus rasgos "
                              "entre sí más que con otras personas.", "suave"))
        t.addWidget(Barras([(x["nombre"], x["puntos"], f"{x['puntos']} · {x['nivel']}") for x in res["rasgos"]],
                           34, 230, marca=50))
        if res["fortalezas"]:
            t.addWidget(_etiqueta("Tus puntos fuertes: " + ", ".join(res["fortalezas"]) + ".", "subtitulo"))
        for x in res["rasgos"]:
            t.addWidget(_etiqueta(f"<b>{x['nombre']}</b> ({x['descripcion'].rstrip('.').lower()}): {x['lectura']}"))
        lay.addWidget(tarjeta)
        tarjeta, t = _tarjeta()
        t.addWidget(_etiqueta("Riesgos bajo presión", "subtitulo"))
        t.addWidget(_etiqueta("Conductas que pueden aparecer con estrés, cansancio o exceso de confianza. Todos "
                              "tenemos algunas; conocerlas ayuda a controlarlas.", "suave"))
        t.addWidget(Barras([(x["nombre"], x["puntos"], f"{x['puntos']} · {x['nivel']}") for x in res["riesgos"]],
                           32, 230))
        a_cuidar = [x for x in res["riesgos"] if x["nivel"] != "Bajo"]
        if a_cuidar:
            for x in sorted(a_cuidar, key=lambda x: -x["puntos"]):
                t.addWidget(_etiqueta(f"<b>{x['nombre']}</b> ({x['nivel'].lower()}): {x['descripcion']}"))
        else:
            t.addWidget(_etiqueta("Ningún riesgo sale moderado o alto."))
        lay.addWidget(tarjeta)

    def _valores(self, res: dict, lay: QVBoxLayout) -> None:
        por_nombre = {x["nombre"]: x for x in res["valores"]}
        tarjeta, t = _tarjeta()
        t.addWidget(_etiqueta("Lo que más te mueve", "subtitulo"))
        for n in res["mas"]:
            t.addWidget(_etiqueta(f"<b>{n}</b>: {por_nombre[n]['descripcion']}"))
        t.addWidget(_etiqueta("Lo que menos pesa: " + ", ".join(res["menos"]) + ".", "suave"))
        if res.get("plano"):
            t.addWidget(_etiqueta("Calificaste casi todo igual, así que este orden no dice mucho. Vuelve a "
                                  "intentarlo distinguiendo lo que de verdad pesa más.", "aviso"))
        elif res["general"] >= 4.3:
            t.addWidget(_etiqueta("Calificaste casi todo como muy importante, así que las diferencias entre "
                                  "valores son pequeñas.", "suave"))
        lay.addWidget(tarjeta)
        for grupo, titulo in (("interpersonal", "Valores interpersonales (cómo quieres relacionarte)"),
                              ("personal", "Valores personales (cómo quieres vivir y trabajar)")):
            tarjeta, t = _tarjeta()
            t.addWidget(_etiqueta(titulo, "subtitulo"))
            filas = sorted((x for x in res["valores"] if x["grupo"] == grupo), key=lambda x: -x["relativo"])
            t.addWidget(Barras([(x["nombre"], x["puntos"], f"{x['puntos']}  ({x['relativo']:+.1f})") for x in filas],
                               32, 230))
            lay.addWidget(tarjeta)
        lay.addWidget(_etiqueta("La barra es qué tan importante calificaste ese valor (0–100). Entre paréntesis, "
                                "cuánto está arriba (+) o abajo (−) de tu propio promedio: eso marca tus "
                                "prioridades.", "suave"))

    def _tamizaje(self, res: dict, lay: QVBoxLayout) -> None:
        if res["urgente"]:
            lay.addWidget(_etiqueta(CRISIS, "aviso"))
        tarjeta, t = _tarjeta()
        fila = QHBoxLayout()
        fila.addWidget(_etiqueta(f"{res['puntaje']}", "ci", False))
        fila.addWidget(_etiqueta(f"de {res['maximo']}", "suave", False), 0, Qt.AlignmentFlag.AlignBottom)
        fila.addSpacing(24)
        der = QVBoxLayout()
        der.addWidget(_etiqueta(res["nivel"], "subtitulo"))
        der.addWidget(_etiqueta(res["lectura"]))
        fila.addLayout(der, 1)
        t.addLayout(fila)
        t.addWidget(BarraCortes(res["puntaje"], res["maximo"], res["cortes"]))
        if res.get("explicacion_total"):
            t.addWidget(_etiqueta(res["explicacion_total"], "suave"))
        t.addWidget(_etiqueta(("<b>Recomendación:</b> " if res["positivo"] or res["urgente"] else "")
                              + res["recomendacion"]))
        lay.addWidget(tarjeta)
        for a in res["alertas"]:   # las líneas de crisis ya salen arriba
            lay.addWidget(_etiqueta(a.replace(CRISIS, "").strip(), "aviso"))
        if res["subescalas"]:
            tarjeta, t = _tarjeta()
            t.addWidget(_etiqueta("Por grupos de síntomas", "subtitulo"))
            t.addWidget(Barras([(x["nombre"], 100 * x["puntos"] / x["maximo"],
                                 x.get("texto", f"{x['puntos']} de {x['maximo']}")) for x in res["subescalas"]],
                               32, 300, ancho_texto=210 if any("texto" in x for x in res["subescalas"]) else 110))
            for n in res.get("notas", []):
                t.addWidget(_etiqueta(n))
            lay.addWidget(tarjeta)

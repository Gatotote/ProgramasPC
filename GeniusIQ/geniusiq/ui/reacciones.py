"""Reacciones grabadas: analizar el video, línea de tiempo de emociones y reproductor por momentos."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QRectF, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QHeaderView, QMessageBox, QProgressDialog, QPushButton,
                               QSlider, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .. import emociones
from .estilo import SUAVE, TEXTO

COLORES = {"Enojo": "#e5484d", "Desprecio": "#a06cd5", "Asco": "#8a9a3b", "Miedo": "#6e56cf",
           "Alegría": "#f5c518", "Neutral": "#6b6b70", "Tristeza": "#3e8ed0", "Sorpresa": "#2ec4b6"}
SIN_CARA = "#26262a"


def _mmss(t: float) -> str:
    t = int(t)
    return f"{t // 60:02d}:{t % 60:02d}"


def _tramo_texto(tr: dict) -> str:
    if tr["tipo"] == "instrucciones":
        return f"Instrucciones: {tr['texto']}"
    return tr["texto"]


# ------------------------------------------------------------------ analizar

class _Hilo(QThread):
    avance = Signal(int)

    def __init__(self, video: str):
        super().__init__()
        self.video, self.muestras, self.fallo, self.parar = video, None, "", False

    def run(self):
        try:
            self.muestras = emociones.analizar(self.video, lambda f: self.avance.emit(int(f * 1000)),
                                               lambda: self.parar)
        except Exception as e:   # el video puede estar dañado o el modelo faltar
            self.fallo = str(e)


def analizar_con_dialogo(parent: QWidget, grabacion: dict) -> bool:
    """Analiza el video de `grabacion` con barra de avance; deja el resumen en grabacion['resumen']."""
    if not Path(grabacion["video"]).exists():
        QMessageBox.warning(parent, "Reacciones", f"No se encontró el video:\n{grabacion['video']}")
        return False
    dlg = QProgressDialog("Analizando las reacciones del video…\n(todo se hace en esta computadora)",
                          "Dejarlo para después", 0, 1000, parent)
    dlg.setWindowTitle("Reacciones")
    dlg.setWindowModality(Qt.WindowModality.WindowModal)
    dlg.setMinimumDuration(0)
    hilo = _Hilo(grabacion["video"])
    hilo.avance.connect(dlg.setValue)
    dlg.canceled.connect(lambda: setattr(hilo, "parar", True))
    hilo.finished.connect(dlg.reset)
    hilo.start()
    dlg.exec()
    hilo.wait()
    if hilo.fallo:
        QMessageBox.warning(parent, "Reacciones", f"No se pudo analizar el video:\n{hilo.fallo}")
        return False
    if hilo.muestras is None:
        return False
    emociones.guardar_muestras(grabacion["video"], hilo.muestras)
    grabacion["resumen"] = emociones.resumir(hilo.muestras, grabacion["eventos"])
    return True


# ------------------------------------------------------------------ gráficas

class LineaTiempo(QWidget):
    """Una franja: cada segundo pintado con la emoción principal; rayitas donde empieza cada parte."""

    def __init__(self, resumen: dict, eventos: list[dict]):
        super().__init__()
        self.linea = resumen["linea"]
        self.cortes = [e["t"] for e in eventos if e["tipo"] in ("instrucciones", "inicio")]
        self.setMinimumHeight(64)

    def paintEvent(self, _):
        p = QPainter(self)
        n = max(1, len(self.linea))
        ancho = self.width()
        franja = QRectF(0, 4, ancho, 34)
        p.fillRect(franja, QColor(SIN_CARA))
        for s, k in enumerate(self.linea):
            if k >= 0:
                p.fillRect(QRectF(s / n * ancho, franja.top(), ancho / n + 0.6, franja.height()),
                           QColor(COLORES[emociones.EMOCIONES[k]]))
        p.setPen(QColor(TEXTO))
        for t in self.cortes:
            x = t / n * ancho
            p.drawLine(int(x), 0, int(x), 42)
        f = QFont()
        f.setPixelSize(12)
        p.setFont(f)
        p.setPen(QColor(SUAVE))
        for k in range(5):
            x = k / 4 * ancho
            alin = Qt.AlignmentFlag.AlignLeft if k == 0 else (Qt.AlignmentFlag.AlignRight if k == 4
                                                              else Qt.AlignmentFlag.AlignHCenter)
            p.drawText(QRectF(min(max(x - 30, 0), ancho - 60), 44, 60, 18), alin, _mmss(k / 4 * n))


class Leyenda(QWidget):
    def __init__(self, porcentajes: dict):
        super().__init__()
        self.datos = sorted(porcentajes.items(), key=lambda kv: -kv[1])
        self.setMinimumHeight(26)

    def paintEvent(self, _):
        p = QPainter(self)
        f = QFont()
        f.setPixelSize(13)
        p.setFont(f)
        x = 0
        for nombre, pct in self.datos + [("Sin cara", None)]:
            p.fillRect(QRectF(x, 7, 12, 12), QColor(COLORES.get(nombre, SIN_CARA)))
            texto = nombre if pct is None else f"{nombre} {pct:g}%"
            p.setPen(QColor(TEXTO))
            ancho = p.fontMetrics().horizontalAdvance(texto)
            p.drawText(QRectF(x + 17, 2, ancho + 4, 22), Qt.AlignmentFlag.AlignVCenter, texto)
            x += ancho + 36


def _tabla_tramos(tramos: list[dict]) -> QTableWidget:
    tabla = QTableWidget(len(tramos), 5)
    tabla.setHorizontalHeaderLabels(["Momento", "Parte / pregunta", "Respuesta", "Expresión principal",
                                     "Reacción notable"])
    tabla.verticalHeader().hide()
    tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    h = tabla.horizontalHeader()
    h.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    for i, tr in enumerate(tramos):
        resp = tr["respuesta"]
        if tr["correcta"] is not None:
            resp = "✓ correcta" if tr["correcta"] else "✗ incorrecta"
        emocion = tr.get("emocion", "— (no se vio la cara)")
        reaccion = f"{tr['reaccion']} ({tr['fuerza'] * 100:.0f}%)" if tr.get("reaccion") else ""
        for j, v in enumerate([_mmss(tr["t0"]), _tramo_texto(tr), resp, emocion, reaccion]):
            celda = QTableWidgetItem(v)
            if j in (3, 4) and v and v.split(" ")[0] in COLORES:
                celda.setForeground(QColor(COLORES[v.split(" ")[0]]))
            tabla.setItem(i, j, celda)
    return tabla


# ------------------------------------------------------------------ reproductor

class DialogoVideo(QDialog):
    """Video de la prueba con la lista de momentos: clic en una fila salta a ese momento."""

    def __init__(self, parent, grabacion: dict, titulo: str):
        super().__init__(parent)
        self.setWindowTitle(f"Reacciones — {titulo}")
        self.resize(1100, 820)
        lay = QVBoxLayout(self)
        self.vista = QVideoWidget()
        self.vista.setMinimumHeight(380)
        lay.addWidget(self.vista, 3)
        self.player = QMediaPlayer(self)
        self.salida = QAudioOutput(self)
        self.player.setAudioOutput(self.salida)
        self.player.setVideoOutput(self.vista)
        self.player.setSource(QUrl.fromLocalFile(grabacion["video"]))

        fila = QHBoxLayout()
        self.btn = QPushButton("▶")
        self.btn.clicked.connect(self._alternar)
        self.barra = QSlider(Qt.Orientation.Horizontal)
        self.barra.sliderMoved.connect(self.player.setPosition)
        self.player.durationChanged.connect(lambda d: self.barra.setRange(0, d))
        self.player.positionChanged.connect(self._posicion)
        self.player.playbackStateChanged.connect(
            lambda e: self.btn.setText("⏸" if e == QMediaPlayer.PlaybackState.PlayingState else "▶"))
        self.reloj = QPushButton("00:00")
        self.reloj.setEnabled(False)
        fila.addWidget(self.btn)
        fila.addWidget(self.barra, 1)
        fila.addWidget(self.reloj)
        lay.addLayout(fila)

        resumen = grabacion.get("resumen")
        self.tramos = resumen["tramos"] if resumen else []
        if resumen:
            tabla = _tabla_tramos(self.tramos)
            tabla.cellClicked.connect(lambda i, _j: self._ir(self.tramos[i]["t0"]))
            lay.addWidget(tabla, 2)

    def _ir(self, t: float) -> None:
        self.player.setPosition(int(max(0, t - 1) * 1000))
        self.player.play()

    def _alternar(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _posicion(self, ms: int) -> None:
        if not self.barra.isSliderDown():
            self.barra.setValue(ms)
        self.reloj.setText(_mmss(ms / 1000))

    def done(self, r):
        self.player.stop()
        super().done(r)


# ------------------------------------------------------------------ tarjeta en los resultados

def tarjeta_reacciones(res: dict, persona: str, guardar: Callable[[dict], None]) -> QWidget:
    """Tarjeta para la pantalla de resultados. `guardar(res)` persiste el resumen recién calculado."""
    from .pantallas import _etiqueta, _tarjeta
    g = res["grabacion"]
    tarjeta, t = _tarjeta()
    t.addWidget(_etiqueta("Reacciones durante la prueba (cámara)", "subtitulo"))
    resumen = g.get("resumen")
    existe = Path(g["video"]).exists()
    botones = QHBoxLayout()

    if resumen:
        t.addWidget(_etiqueta(f"Duración {_mmss(resumen['duracion'])}  ·  cara visible el {resumen['cara']}% del "
                              f"tiempo  ·  {'con' if g.get('audio') else 'sin'} audio", "suave"))
        t.addWidget(LineaTiempo(resumen, g["eventos"]))
        t.addWidget(Leyenda(resumen["distribucion"]))
        for nombre, dist in resumen["comparacion"].items():
            top = [f"{k} {v:g}%" for k, v in sorted(dist.items(), key=lambda kv: -kv[1])[:3] if v > 0]
            t.addWidget(_etiqueta(f"<b>{nombre}:</b> " + "  ·  ".join(top)))
        notables = sorted((tr for tr in resumen["tramos"] if tr.get("reaccion")), key=lambda tr: -tr["fuerza"])[:8]
        if notables:
            t.addWidget(_etiqueta("Reacciones más marcadas (abre el video para verlas):", "suave"))
            tabla = _tabla_tramos(sorted(notables, key=lambda tr: tr["t0"]))
            tabla.setMinimumHeight(34 * len(notables) + 36)
            t.addWidget(tabla)
        t.addWidget(_etiqueta(emociones.AVISO, "aviso"))
    else:
        t.addWidget(_etiqueta("El video se grabó pero aún no se analizan las reacciones.", "suave"))
        if existe:
            analizar = QPushButton("Analizar reacciones")
            analizar.setObjectName("principal")

            def _analizar():
                if analizar_con_dialogo(tarjeta, g):
                    guardar(res)
            analizar.clicked.connect(_analizar)
            botones.addWidget(analizar)

    if existe:
        ver = QPushButton("🎥 Ver video por momentos…")
        ver.clicked.connect(lambda: DialogoVideo(tarjeta, g, persona).exec())
        botones.addWidget(ver)
        t.addWidget(_etiqueta(f"Video: {g['video']}", "suave"))
    else:
        t.addWidget(_etiqueta(f"El video ya no está en {g['video']}", "suave"))
    botones.addStretch()
    t.addLayout(botones)
    return tarjeta

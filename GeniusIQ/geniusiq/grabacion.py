"""Grabación de la cámara durante una prueba, con marcas de tiempo de cada pregunta y respuesta.

El video va a ~/Documentos/GeniusIQ/grabaciones (MP4 con video MPEG-4 parte 2: el FFmpeg LGPL que trae
PySide6 no tiene H.264 por software, y el de la NVIDIA falla en esta PC). El audio solo si se pide.
Las pantallas llaman a `marcar()`; si no se está grabando, no hace nada.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QEventLoop, QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import (QAudioInput, QCamera, QMediaCaptureSession, QMediaDevices, QMediaFormat,
                                  QMediaRecorder)

# Sin codificadores por hardware: con la NVIDIA, Qt elige h264_nvenc, falla y deja el archivo vacío.
# Tiene que quedar puesto antes de que Qt cargue su parte de multimedia.
os.environ.setdefault("QT_FFMPEG_ENCODING_HW_DEVICE_TYPES", "")

CARPETA = Path.home() / "Documentos" / "GeniusIQ" / "grabaciones"

_activa: Grabadora | None = None


def hay_camara() -> bool:
    return bool(QMediaDevices.videoInputs())


def marcar(tipo: str, texto: str = "", **extra) -> None:
    """Anota un momento de la prueba: instrucciones, inicio, pregunta, respuesta o fin."""
    if _activa is not None:
        _activa.marcar(tipo, texto, **extra)


def _formato_camara(dispositivo):
    """El formato más cercano a 1280×720 (o menos) y ≥15 cuadros/s: suficiente para la cara y no pesa."""
    buenos = [f for f in dispositivo.videoFormats()
              if f.resolution().height() <= 720 and f.maxFrameRate() >= 15]
    if not buenos:
        return None
    return max(buenos, key=lambda f: (f.resolution().height(), -abs(f.maxFrameRate() - 30)))


class Grabadora(QObject):
    error = Signal(str)

    def __init__(self, persona: str, prueba: str, audio: bool = False):
        super().__init__()
        CARPETA.mkdir(parents=True, exist_ok=True)
        limpio = re.sub(r"[^\w áéíóúñÁÉÍÓÚÑ-]", "", f"{persona} {prueba}").strip()
        self.base = CARPETA / f"GeniusIQ {limpio} {datetime.now():%Y-%m-%d %H%M%S}"
        self.audio = audio
        self.eventos: list[dict] = []
        self._al_terminar: Callable[[], None] | None = None

        self.sesion = QMediaCaptureSession()
        dispositivo = QMediaDevices.defaultVideoInput()
        self.camara = QCamera(dispositivo)
        formato = _formato_camara(dispositivo)
        if formato is not None:
            self.camara.setCameraFormat(formato)
        self.sesion.setCamera(self.camara)
        if audio:
            self.microfono = QAudioInput()
            self.sesion.setAudioInput(self.microfono)
        self.grabadora = QMediaRecorder()
        self.sesion.setRecorder(self.grabadora)
        fmt = QMediaFormat(QMediaFormat.FileFormat.MPEG4)
        fmt.setVideoCodec(QMediaFormat.VideoCodec.MPEG4)
        if audio:
            fmt.setAudioCodec(QMediaFormat.AudioCodec.AAC)
        self.grabadora.setMediaFormat(fmt)
        self.grabadora.setQuality(QMediaRecorder.Quality.NormalQuality)
        self.grabadora.setOutputLocation(QUrl.fromLocalFile(str(self.base.with_suffix(".mp4"))))
        self.grabadora.errorOccurred.connect(lambda _e, txt: self.error.emit(txt))
        self.camara.errorOccurred.connect(lambda _e, txt: self.error.emit(txt))
        self.grabadora.recorderStateChanged.connect(self._estado)

    @property
    def video(self) -> Path:
        real = self.grabadora.actualLocation().toLocalFile()
        return Path(real) if real else self.base.with_suffix(".mp4")

    def iniciar(self) -> None:
        global _activa
        _activa = self
        self.camara.start()
        self.grabadora.record()

    def marcar(self, tipo: str, texto: str = "", **extra) -> None:
        self.eventos.append({"t": round(self.grabadora.duration() / 1000, 2), "tipo": tipo, "texto": texto, **extra})

    def detener(self, al_terminar: Callable[[], None]) -> None:
        """Para la grabación; `al_terminar` se llama cuando el archivo ya quedó cerrado."""
        global _activa
        self.marcar("fin")
        _activa = None
        self.base.with_suffix(".marcas.json").write_text(json.dumps(self.eventos, ensure_ascii=False, indent=1))
        if self.grabadora.recorderState() == QMediaRecorder.RecorderState.StoppedState:
            self._soltar_camara()
            al_terminar()
            return
        self._al_terminar = al_terminar
        self.grabadora.stop()

    def cancelar(self) -> None:
        """Para y borra lo grabado (la persona salió sin terminar)."""
        def borrar():
            for ruta in (self.video, self.base.with_suffix(".marcas.json")):
                ruta.unlink(missing_ok=True)
        self.detener(borrar)

    def esperar(self, ms: int = 4000) -> None:
        """Espera a que el archivo quede cerrado (al cerrar el programa, antes de que se acabe el bucle de Qt)."""
        if self.grabadora.recorderState() == QMediaRecorder.RecorderState.StoppedState:
            return
        bucle = QEventLoop()
        self.grabadora.recorderStateChanged.connect(bucle.quit)
        QTimer.singleShot(ms, bucle.quit)
        bucle.exec()

    def _estado(self, estado) -> None:
        if estado == QMediaRecorder.RecorderState.StoppedState and self._al_terminar is not None:
            self._soltar_camara()
            llamar, self._al_terminar = self._al_terminar, None
            llamar()

    def _soltar_camara(self) -> None:
        """Suelta la cámara de verdad: con solo `stop()` Qt la deja apartada y la siguiente prueba
        en la misma sesión del programa graba un video vacío («Camera is in use»)."""
        if self.camara is None:
            return
        self.camara.stop()
        self.sesion.setCamera(None)
        self.camara.deleteLater()
        self.camara = None

    def datos(self) -> dict:
        """Lo que se guarda junto al resultado de la prueba."""
        return {"video": str(self.video), "audio": self.audio, "eventos": self.eventos}

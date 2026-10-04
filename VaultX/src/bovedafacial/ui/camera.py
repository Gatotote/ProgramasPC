"""Hilo de cámara para la GUI: captura frames y los emite. La conversión a
QImage se hace aquí para no arrastrar OpenCV a los widgets."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPixmap


def bgr_to_qpixmap(bgr: np.ndarray) -> QPixmap:
    h, w = bgr.shape[:2]
    rgb = np.ascontiguousarray(bgr[:, :, ::-1])
    img = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img.copy())


class CameraThread(QThread):
    frame = Signal(object)   # np.ndarray BGR
    failed = Signal(str)

    def __init__(self, parent=None, interval_ms: int = 33) -> None:
        super().__init__(parent)
        self._alive = True
        self._interval = interval_ms

    def run(self) -> None:
        try:
            from ..face import default_camera
        except ImportError as e:  # pragma: no cover
            self.failed.emit(f"Falta el extra facial: {e}")
            return
        try:
            cam = default_camera()
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))
            return
        with cam:
            while self._alive:
                try:
                    self.frame.emit(cam.read())
                except Exception as e:  # noqa: BLE001
                    self.failed.emit(str(e))
                    break
                self.msleep(self._interval)

    def stop(self) -> None:
        self._alive = False
        self.wait(2500)

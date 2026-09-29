"""Abstracción de la fuente de vídeo.

- `V4L2Camera`: webcam local vía OpenCV (MJPG 1280x720 por defecto).
- `FileCamera`: una imagen o lista de imágenes; para pruebas y para desarrollar
  sin cámara.
- `default_camera()`: primera `/dev/video*` que abra de verdad; si no hay,
  lanza `CameraError` para que la UI ofrezca la frase de recuperación.

Todos los frames se entregan en BGR (formato de OpenCV), que es lo que espera
InsightFace.
"""

from __future__ import annotations

import glob
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class CameraError(Exception):
    pass


def _fourcc(cv2, code: str) -> float:
    fn = getattr(cv2, "VideoWriter_fourcc", None)
    if fn is None:  # OpenCV 5 movió la función
        fn = cv2.VideoWriter.fourcc
    return fn(*code)


class BaseCamera(ABC):
    @abstractmethod
    def read(self) -> np.ndarray:
        """Devuelve un frame BGR (H, W, 3) uint8 o lanza CameraError."""

    def open(self) -> "BaseCamera":
        return self

    def close(self) -> None:  # noqa: B027 - opcional
        pass

    def __enter__(self) -> "BaseCamera":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()


class V4L2Camera(BaseCamera):
    def __init__(
        self,
        source: int | str = 0,
        width: int = 1280,
        height: int = 720,
        fourcc: str = "MJPG",
        warmup: int = 5,
    ) -> None:
        self.source = source
        self.width = width
        self.height = height
        self.fourcc = fourcc
        self.warmup = warmup
        self._cap = None

    def open(self) -> "V4L2Camera":
        import cv2

        if self._cap is not None and self._cap.isOpened():
            return self  # idempotente: no reabrir (dispositivo ocupado)

        src = self.source
        if isinstance(src, str) and src.startswith("/dev/video") and src[10:].isdigit():
            src = int(src[10:])  # el backend V4L2 prefiere el índice al nombre

        cap = cv2.VideoCapture(src, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(src)  # backend por defecto
        if not cap.isOpened():
            raise CameraError(f"No se pudo abrir la cámara {self.source!r}.")
        cap.set(cv2.CAP_PROP_FOURCC, _fourcc(cv2, self.fourcc))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        for _ in range(self.warmup):  # descartar frames de autoexposición
            cap.read()
        self._cap = cap
        return self

    def read(self) -> np.ndarray:
        if self._cap is None:
            self.open()
        ok, frame = self._cap.read()
        if not ok or frame is None:
            raise CameraError("Fallo al leer un frame de la cámara.")
        return frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class FileCamera(BaseCamera):
    """Reproduce imágenes de disco (o arrays ya cargados) en bucle."""

    def __init__(self, images: str | Path | list) -> None:
        self._items = images if isinstance(images, list) else [images]
        self._frames: list[np.ndarray] = []
        self._i = 0

    def open(self) -> "FileCamera":
        self._frames = []
        for item in self._items:
            if isinstance(item, np.ndarray):
                self._frames.append(item)
            else:
                import cv2

                img = cv2.imread(str(item), cv2.IMREAD_COLOR)
                if img is None:
                    raise CameraError(f"No se pudo leer la imagen {item!r}.")
                self._frames.append(img)
        if not self._frames:
            raise CameraError("FileCamera sin imágenes.")
        self._i = 0
        return self

    def read(self) -> np.ndarray:
        if not self._frames:
            self.open()
        frame = self._frames[self._i % len(self._frames)]
        self._i += 1
        return frame.copy()


def list_v4l2_devices() -> list[str]:
    return sorted(glob.glob("/dev/video*"))


def default_camera(**kwargs) -> V4L2Camera:
    devices = list_v4l2_devices()
    if not devices:
        raise CameraError(
            "No hay ninguna cámara conectada (/dev/video*). "
            "Conecta la webcam o entra con la frase de recuperación."
        )
    last_err: Exception | None = None
    for dev in devices:
        try:
            return V4L2Camera(dev, **kwargs).open()
        except CameraError as e:
            last_err = e
    raise CameraError(f"Ninguna cámara respondió. Última: {last_err}")

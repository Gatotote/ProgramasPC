"""Widgets compartidos de la GUI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy

from .camera import bgr_to_qpixmap


class VideoView(QLabel):
    """Muestra frames BGR escalados manteniendo proporción."""

    def __init__(self, w: int = 420, h: int = 300, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(w, h)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background:#0c0d10;border:1px solid #2d323b;border-radius:12px;")
        self.setText("cámara…")
        self._pix = None

    def set_frame(self, bgr) -> None:
        self._pix = bgr_to_qpixmap(bgr)
        self._rescale()

    def _rescale(self) -> None:
        if self._pix is None:
            return
        self.setPixmap(self._pix.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, ev) -> None:  # noqa: N802
        self._rescale()
        super().resizeEvent(ev)


def hline() -> QFrame:
    f = QFrame()
    f.setProperty("role", "hline")
    f.setFixedHeight(1)
    return f


def label(text: str, role: str | None = None) -> QLabel:
    lbl = QLabel(text)
    if role:
        lbl.setProperty("role", role)
    lbl.setWordWrap(role in (None, "dim"))
    return lbl

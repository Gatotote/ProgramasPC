"""Widgets compartidos de la GUI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .camera import bgr_to_qpixmap

_PILL_COLORS = {
    "ok": ("#1f7a3d", "#dcecdd"), "warn": ("#9a6b0f", "#f3e6c4"),
    "risk": ("#b23b30", "#f2ddd8"), "neutral": ("#6d6a60", "#00000012"),
}


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


def section_label(text: str) -> QLabel:
    return label(text.upper(), "label")


def pill(text: str, kind: str = "neutral") -> QLabel:
    fg, bg = _PILL_COLORS.get(kind, _PILL_COLORS["neutral"])
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{fg};background:{bg};border:1px solid {fg}55;"
        "border-radius:9px;padding:2px 9px;font-size:11px;font-weight:600;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


class Card(QFrame):
    """Tarjeta con título opcional; añade contenido a `self.body`.
    `set_badge()` pone un texto tenue a la derecha del título."""

    def __init__(self, title: str = "", icon: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setProperty("role", "card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)
        self._badge = None
        if title or icon:
            head = QHBoxLayout()
            head.setSpacing(9)
            if icon:
                ic = QLabel(icon)
                ic.setStyleSheet("font-size:17px;font-weight:400;")
                ic.setFixedWidth(24)
                head.addWidget(ic)
            h = QLabel(title)
            h.setProperty("role", "h2")
            head.addWidget(h)
            head.addStretch(1)
            self._badge = QLabel("")
            self._badge.setProperty("role", "dim")
            head.addWidget(self._badge)
            self.head = head
            outer.addLayout(head)
        self.body = QVBoxLayout()
        self.body.setSpacing(6)
        outer.addLayout(self.body)

    def set_badge(self, text: str) -> None:
        if self._badge is not None:
            self._badge.setText(text)


class StatTile(QFrame):
    def __init__(self, caption: str, value: str, sub: str = "", flag: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self.setProperty("role", "card")
        v = QVBoxLayout(self)
        v.setContentsMargins(15, 13, 15, 13)
        v.setSpacing(3)
        c = QLabel(caption)
        c.setProperty("role", "dim")
        c.setStyleSheet("font-size:11px;")
        val = QLabel(value)
        val.setStyleSheet(f"font-size:20px;font-weight:600;{'color:#e0b341;' if flag else ''}")
        v.addWidget(c)
        v.addWidget(val)
        if sub:
            s = QLabel(sub)
            s.setProperty("role", "dim")
            s.setStyleSheet("font-size:11px;")
            s.setWordWrap(True)
            v.addWidget(s)
        self.value_label = val


class Banner(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("role", "card")
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(12)
        self._dot = QLabel("🟢")
        self._dot.setStyleSheet("font-size:18px;")
        col = QVBoxLayout()
        col.setSpacing(1)
        self._title = QLabel("")
        self._title.setProperty("role", "h2")
        self._detail = QLabel("")
        self._detail.setProperty("role", "dim")
        self._detail.setWordWrap(True)
        col.addWidget(self._title)
        col.addWidget(self._detail)
        row.addWidget(self._dot)
        row.addLayout(col, 1)

    def set(self, dot: str, title: str, detail: str, level: str = "warn") -> None:  # noqa: A003
        self._dot.setText(dot)
        self._title.setText(title)
        self._detail.setText(detail)
        border = _PILL_COLORS.get(level, _PILL_COLORS["warn"])[0]
        self.setStyleSheet(f"QFrame{{border-color:{border}66;}}")


def scroll_page(widget: QWidget):
    from PySide6.QtWidgets import QScrollArea
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(widget)
    return sa


class StrengthMeter(QWidget):
    """Indicador visual de fortaleza: 3 segmentos rojo / amarillo / verde."""

    _COLOR = {1: "#e5675b", 2: "#e0b341", 3: "#41b955"}
    _WORD = {1: "Débil", 2: "Aceptable", 3: "Fuerte"}
    _LEVEL = {"débil": 1, "aceptable": 2, "fuerte": 3}
    _OFF = "rgba(128,128,128,0.30)"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(4)
        self._segs = []
        for _ in range(3):
            s = QFrame()
            s.setFixedSize(44, 6)
            s.setStyleSheet(f"background:{self._OFF};border:none;border-radius:3px;")
            self._segs.append(s)
            row.addWidget(s)
        self._lbl = QLabel("")
        self._lbl.setStyleSheet("font-size:11px;")
        row.addWidget(self._lbl)
        row.addStretch(1)

    def set_password(self, pw: str) -> None:
        from ..pwgen import strength

        level = self._LEVEL[strength(pw)] if pw else 0
        col = self._COLOR.get(level, self._OFF)
        for i, seg in enumerate(self._segs):
            fill = col if i < level else self._OFF
            seg.setStyleSheet(f"background:{fill};border:none;border-radius:3px;")
        self._lbl.setText(self._WORD.get(level, ""))
        self._lbl.setStyleSheet(
            f"font-size:11px;color:{col if level else 'palette(mid)'};")

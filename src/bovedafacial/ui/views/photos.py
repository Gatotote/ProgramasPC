"""Vista Fotografías: galería de las imágenes de la bóveda. Las miniaturas se
descifran a un área temporal en RAM en un hilo aparte."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
MAX_THUMBS = 60
COLS = 4


def _is_image(name: str) -> bool:
    return any(name.lower().endswith(e) for e in IMG_EXT)


def _collect(node: dict, prefix: str, out: list) -> None:
    for name, child in node.get("entries", {}).items():
        vpath = f"{prefix}/{name}"
        t = child["type"]
        if t == "dir":
            _collect(child, vpath, out)
        elif t == "file" and _is_image(name):
            out.append((vpath, name))
        elif t == "item":
            for a in child.get("attachments", []):
                if _is_image(a.get("name", "")):
                    out.append((vpath, a["name"]))
                    break


class _ThumbWorker(QThread):
    thumb = Signal(str, object)   # vpath, QImage

    def __init__(self, session, vpaths: list[str]) -> None:
        super().__init__()
        self.session = session
        self.vpaths = vpaths
        self._alive = True

    def run(self) -> None:
        for vpath in self.vpaths:
            if not self._alive:
                return
            try:
                path = self.session.checkout(vpath)
                img = QImage(str(path))
                if not img.isNull():
                    self.thumb.emit(vpath, img.scaled(
                        260, 200, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation))
            except Exception:  # noqa: BLE001
                pass

    def stop(self) -> None:
        self._alive = False
        self.wait(3000)


class _Tile(QFrame):
    def __init__(self, vpath: str, name: str, on_open) -> None:
        super().__init__()
        self.setProperty("role", "card")
        self.vpath = vpath
        self._on_open = on_open
        self.setFixedSize(180, 170)
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(4)
        self.pic = QLabel("🖼")
        self.pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pic.setFixedHeight(120)
        self.pic.setStyleSheet("font-size:32px;background:#00000022;border-radius:6px;")
        cap = QLabel(name)
        cap.setProperty("role", "dim")
        cap.setWordWrap(False)
        cap.setStyleSheet("font-size:10px;")
        v.addWidget(self.pic)
        v.addWidget(cap)

    def set_image(self, img: QImage) -> None:
        self.pic.setPixmap(QPixmap.fromImage(img).scaled(
            self.pic.width() or 168, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation))
        self.pic.setText("")

    def mouseDoubleClickEvent(self, _ev) -> None:  # noqa: N802
        self._on_open(self.vpath)


class PhotosView(QWidget):
    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self._worker: _ThumbWorker | None = None
        self._tiles: dict[str, _Tile] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 24)
        root.setSpacing(12)
        head = QHBoxLayout()
        h = QLabel("Fotografías")
        h.setProperty("role", "h1")
        head.addWidget(h)
        head.addStretch(1)
        self.info = QLabel("")
        self.info.setProperty("role", "dim")
        head.addWidget(self.info)
        root.addLayout(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll.setWidget(self.grid_host)
        root.addWidget(self.scroll, 1)

        self.refresh()

    def refresh(self) -> None:
        self._stop_worker()
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        self._tiles.clear()

        found: list[tuple[str, str]] = []
        _collect(self.session.index, "", found)
        found = found[:MAX_THUMBS]
        self.info.setText(f"{len(found)} imagen(es)" + (" · miniaturas cifradas" if found else ""))
        if not found:
            empty = QLabel("Aún no hay imágenes. Impórtalas desde Archivos.")
            empty.setProperty("role", "dim")
            self.grid.addWidget(empty, 0, 0)
            return

        for i, (vpath, name) in enumerate(found):
            tile = _Tile(vpath, name, self._open)
            self._tiles[vpath] = tile
            self.grid.addWidget(tile, i // COLS, i % COLS)

        self._worker = _ThumbWorker(self.session, [v for v, _ in found])
        self._worker.thumb.connect(self._set_thumb)
        self._worker.start()

    def _set_thumb(self, vpath: str, img: QImage) -> None:
        tile = self._tiles.get(vpath)
        if tile:
            tile.set_image(img)

    def _open(self, vpath: str) -> None:
        try:
            path = self.session.checkout(vpath)
        except Exception:  # noqa: BLE001
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _stop_worker(self) -> None:
        if self._worker:
            self._worker.stop()
            self._worker = None

    def shutdown(self) -> None:
        self._stop_worker()

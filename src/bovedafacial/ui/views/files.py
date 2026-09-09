"""Vista Archivos: explorador del árbol de la bóveda. «Abrir» descifra a un área
temporal en RAM y lo lanza con el programa del sistema."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...vault import KIND_LABELS, ItemKind
from .. import config
from ..widgets import hline

_PATH_ROLE = Qt.ItemDataRole.UserRole
_TYPE_ROLE = Qt.ItemDataRole.UserRole + 1


class FilesView(QWidget):
    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 22, 24, 24)
        v.setSpacing(12)

        head = QHBoxLayout()
        h = QLabel("Archivos")
        h.setProperty("role", "h1")
        head.addWidget(h)
        head.addStretch(1)
        imp_f = QPushButton("Importar archivos…")
        imp_f.clicked.connect(self._import_files)
        imp_d = QPushButton("Importar carpeta…")
        imp_d.clicked.connect(self._import_folder)
        head.addWidget(imp_f)
        head.addWidget(imp_d)
        v.addLayout(head)
        v.addWidget(hline())

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Nombre", "Tamaño"])
        self.tree.setColumnWidth(0, 380)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.itemDoubleClicked.connect(self._on_double)
        v.addWidget(self.tree, 1)

        bar = QHBoxLayout()
        for text, slot in (("Abrir", self._open), ("Exportar copia…", self._export),
                           ("Eliminar", self._delete)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch(1)
        self.info = QLabel("")
        self.info.setProperty("role", "dim")
        bar.addWidget(self.info)
        v.addLayout(bar)

        self.refresh()

    # ---------- construir árbol ----------
    def refresh(self) -> None:
        self.tree.clear()
        self._add_children(self.session.index, "", self.tree.invisibleRootItem())
        self.tree.expandToDepth(0)
        stor = self.session.storage_stats()
        self.info.setText(f"{stor['files']} archivos · {stor['on_disk_bytes'] / 1e6:.1f} MB")

    def _add_children(self, node: dict, prefix: str, parent_item) -> None:
        for name, child in sorted(node.get("entries", {}).items(),
                                  key=lambda kv: (kv[1]["type"] != "dir", kv[0].lower())):
            vpath = f"{prefix}/{name}"
            t = child["type"]
            if t == "dir":
                it = QTreeWidgetItem(parent_item, [f"📁  {name}", ""])
                it.setData(0, _TYPE_ROLE, "dir")
                self._add_children(child, vpath, it)
            elif t == "item":
                kind = ItemKind(child["kind"])
                sz = sum(a.get("size", 0) for a in child.get("attachments", []))
                it = QTreeWidgetItem(parent_item,
                                     [f"🗂  {name}  ({KIND_LABELS[kind]})", _hsize(sz)])
                it.setData(0, _TYPE_ROLE, "item")
            else:
                it = QTreeWidgetItem(parent_item, [f"📄  {name}", _hsize(child.get("size", 0))])
                it.setData(0, _TYPE_ROLE, "file")
            it.setData(0, _PATH_ROLE, vpath)

    # ---------- selección ----------
    def _sel(self):
        it = self.tree.currentItem()
        if it is None:
            return None, None, None
        return it, it.data(0, _PATH_ROLE), it.data(0, _TYPE_ROLE)

    def _current_dir(self) -> str:
        it, vpath, typ = self._sel()
        if vpath is None:
            return "/"
        if typ == "dir":
            return vpath
        return vpath.rsplit("/", 1)[0] or "/"

    # ---------- acciones ----------
    def _on_double(self, item, _col) -> None:
        if item.data(0, _TYPE_ROLE) == "dir":
            item.setExpanded(not item.isExpanded())
        else:
            self._open()

    def _open(self) -> None:
        _it, vpath, typ = self._sel()
        if not vpath or typ == "dir":
            return
        try:
            path = self.session.checkout(vpath)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Abrir", str(e))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        self.info.setText(f"Abierto en RAM: {path.name} · se borra al bloquear")

    def _export(self) -> None:
        _it, vpath, typ = self._sel()
        if not vpath or typ == "dir":
            return
        name = vpath.rsplit("/", 1)[-1]
        dest, _ = QFileDialog.getSaveFileName(self, "Exportar copia (en claro)", name)
        if not dest:
            return
        try:
            self.session.extract(vpath, Path(dest))
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Exportar", str(e))
            return
        self.info.setText(f"Copia exportada: {dest}")

    def _shred_pref(self) -> bool:
        if not config.get("shred_on_import", False):
            return False
        return QMessageBox.question(
            self, "Borrado seguro",
            "Los originales se sobrescribirán y borrarán tras importarlos. ¿Continuar?"
        ) == QMessageBox.StandardButton.Yes

    def _import_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Importar archivos")
        if not files:
            return
        dest = self._current_dir()
        sd = self._shred_pref()
        n = 0
        for f in files:
            n += self.session.import_path(Path(f), dest, secure_delete=sd)
        self.refresh()
        self.info.setText(f"Importados {n} archivo(s) en {dest}"
                          + (" · originales borrados" if sd else ""))

    def _import_folder(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Importar carpeta")
        if not d:
            return
        dest = self._current_dir()
        sd = self._shred_pref()
        n = self.session.import_path(Path(d), dest, secure_delete=sd)
        self.refresh()
        self.info.setText(f"Importados {n} archivo(s) en {dest}"
                          + (" · originales borrados" if sd else ""))

    def _delete(self) -> None:
        _it, vpath, _typ = self._sel()
        if not vpath:
            return
        if QMessageBox.question(self, "Eliminar",
                                f"¿Eliminar «{vpath}» de la bóveda?") \
                == QMessageBox.StandardButton.Yes:
            self.session.remove(vpath)
            self.refresh()


def _hsize(n: int) -> str:
    if not n:
        return ""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

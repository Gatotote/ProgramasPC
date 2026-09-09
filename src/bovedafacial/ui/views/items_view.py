"""Vista genérica de elementos tipados (contraseñas, finanzas, familiar…).
Reutilizable pasándole la lista de `kinds` que muestra."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...vault import ItemKind, KIND_LABELS, spec_for
from ..item_editor import ItemEditor

# qué campo se copia con el botón «Copiar» según el tipo
_COPY_KEY = {
    ItemKind.PASSWORD: "password", ItemKind.CARD: "numero",
    ItemKind.ACCOUNT: "numero", ItemKind.CONTACT: "telefono",
    ItemKind.INSURANCE: "poliza", ItemKind.WILL: "ubicacion", ItemKind.NOTE: "contenido",
}


def _preview(kind: ItemKind, fields: dict) -> str:
    parts = []
    for fs in spec_for(kind):
        if fs.secret or fs.multiline or fs.key not in fields:
            continue
        parts.append(f"{fields[fs.key]}")
        if len(parts) == 2:
            break
    return "  ·  ".join(parts)


class ItemsView(QWidget):
    def __init__(self, session, kinds, title: str, *, base_dir: str = "/",
                 navigate=None, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.kinds = [ItemKind(k) if not isinstance(k, ItemKind) else k for k in kinds]
        self.base_dir = base_dir

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 22, 24, 24)
        v.setSpacing(14)

        head = QHBoxLayout()
        h = QLabel(title)
        h.setProperty("role", "h1")
        head.addWidget(h)
        head.addStretch(1)
        self.new_btn = QPushButton("Nuevo elemento")
        self.new_btn.setObjectName("primary")
        self.new_btn.clicked.connect(self._new_clicked)
        head.addWidget(self.new_btn)
        v.addLayout(head)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Detalle", "Modificado"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(lambda: self._edit(self._current_path()))
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._menu)
        v.addWidget(self.table, 1)

        bar = QHBoxLayout()
        for text, slot in (("Copiar", self._copy), ("Editar", lambda: self._edit(self._current_path())),
                           ("Eliminar", self._delete)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            bar.addWidget(b)
        bar.addStretch(1)
        self.count_lbl = QLabel("")
        self.count_lbl.setProperty("role", "dim")
        bar.addWidget(self.count_lbl)
        v.addLayout(bar)

        self.refresh()

    # ---------- datos ----------
    def refresh(self) -> None:
        rows = []
        for k in self.kinds:
            rows += self.session.list_items("/", kind=k)
        rows.sort(key=lambda r: r["path"].lower())
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            kind = ItemKind(r["kind"])
            it = self.session.get_item(r["path"])
            self._set(i, 0, r["name"], r["path"])
            self._set(i, 1, KIND_LABELS[kind])
            self._set(i, 2, _preview(kind, it["fields"]))
            self._set(i, 3, _fmt(r["modified"]))
        self.count_lbl.setText(f"{len(rows)} elemento(s)")

    def _set(self, row, col, text, path=None) -> None:
        item = QTableWidgetItem(text or "")
        if path is not None:
            item.setData(Qt.ItemDataRole.UserRole, path)
        self.table.setItem(row, col, item)

    def _current_path(self):
        r = self.table.currentRow()
        if r < 0:
            return None
        return self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)

    # ---------- acciones ----------
    def _new_clicked(self) -> None:
        if len(self.kinds) == 1:
            self._new(self.kinds[0])
            return
        m = QMenu(self)
        for k in self.kinds:
            m.addAction(KIND_LABELS[k], lambda k=k: self._new(k))
        m.exec(self.new_btn.mapToGlobal(self.new_btn.rect().bottomLeft()))

    def _new(self, kind: ItemKind) -> None:
        dlg = ItemEditor(kind, dir_path=self.base_dir, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, fields = dlg.result_data()
            try:
                self.session.add_item(self.base_dir, kind, name, fields)
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self, "No se pudo crear", str(e))
                return
            self.refresh()

    def _edit(self, path) -> None:
        if not path:
            return
        it = self.session.get_item(path)
        name = path.rsplit("/", 1)[-1]
        dlg = ItemEditor(it["kind"], name=name, fields=it["fields"], parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            _, fields = dlg.result_data()
            self.session.update_item(path, fields, replace=True)
            self.refresh()

    def _copy(self) -> None:
        path = self._current_path()
        if not path:
            return
        it = self.session.get_item(path)
        key = _COPY_KEY.get(ItemKind(it["kind"]), "")
        val = it["fields"].get(key, "")
        if val:
            QApplication.clipboard().setText(val)
            self.count_lbl.setText(f"«{key}» copiado al portapapeles")

    def _delete(self) -> None:
        path = self._current_path()
        if not path:
            return
        if QMessageBox.question(self, "Eliminar",
                                f"¿Eliminar «{path.rsplit('/', 1)[-1]}» de la bóveda?") \
                == QMessageBox.StandardButton.Yes:
            self.session.remove(path)
            self.refresh()

    def _menu(self, pos) -> None:
        path = self._current_path()
        if not path:
            return
        m = QMenu(self)
        m.addAction("Editar", lambda: self._edit(path))
        m.addAction("Copiar", self._copy)
        m.addSeparator()
        m.addAction("Eliminar", self._delete)
        m.exec(self.table.viewport().mapToGlobal(pos))


def _fmt(ts) -> str:
    if not ts:
        return "—"
    import datetime as dt
    return dt.datetime.fromtimestamp(ts).strftime("%d %b %Y")

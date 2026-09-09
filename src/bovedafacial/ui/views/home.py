"""Vista Inicio: banner de seguridad + tarjetas por categoría + actividad."""

from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...vault import ItemKind
from .. import status as status_mod
from ..widgets import Banner, Card, StatTile, section_label

# sin emoji en las tarjetas: en este KDE el glifo de color deja un halo sobre el
# título en negrita. La iconografía vive en la barra lateral.
CATEGORIES = [
    ("Documentos", "", "files", None),
    ("Contraseñas", "", "items", [ItemKind.PASSWORD]),
    ("Información Financiera", "", "items", [ItemKind.ACCOUNT, ItemKind.CARD]),
    ("Información Familiar", "", "items", [ItemKind.CONTACT, ItemKind.WILL, ItemKind.INSURANCE]),
]
NAV_FOR = {"Documentos": "Archivos", "Contraseñas": "Contraseñas",
           "Información Financiera": "Finanzas", "Información Familiar": "Reportes"}


class HomeView(QWidget):
    navigate = Signal(str)

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(24, 22, 24, 72)
        self._root.setSpacing(16)
        self.refresh()

    def refresh(self) -> None:
        while self._root.count():
            item = self._root.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        s = status_mod.compute(self.session)
        banner = Banner()
        detail = " · ".join(t for _, t in s["reasons"][:3])
        banner.set(s["dot"], f"Estado: {s['label']}", detail, s["level"])
        self._root.addWidget(banner)

        grid = QGridLayout()
        grid.setSpacing(14)
        stor = self.session.storage_stats()
        for idx, (name, icon, src, kinds) in enumerate(CATEGORIES):
            grid.addWidget(self._category_card(name, icon, src, kinds, stor), idx // 2, idx % 2)
        self._root.addLayout(grid)

        self._root.addWidget(section_label("Actividad"))
        summ = self.session.activity_summary()
        tiles = QHBoxLayout()
        tiles.setSpacing(14)
        tiles.addWidget(StatTile("Último acceso", _last(summ["last_unlock"]), "PIN + rostro"))
        tiles.addWidget(StatTile("Archivos hoy", str(summ["files_added_today"]),
                                 f"{summ['items_added_today']} elementos"))
        tiles.addWidget(StatTile("Intentos bloqueados", str(summ["blocked_attempts_24h"]),
                                 "últimas 24 h", flag=summ["blocked_attempts_24h"] > 0))
        tiles.addWidget(StatTile("Espacio usado", f"{stor['on_disk_bytes'] / 1e6:.1f} MB",
                                 f"{stor['files']} archivos · {stor['items']} elementos"))
        self._root.addLayout(tiles)
        self._root.addStretch(1)

    def _category_card(self, name, icon, src, kinds, stor) -> Card:
        card = Card(name, icon)
        if src == "files":
            card.set_badge(_plural(stor["files"], "archivo", "archivos"))
            for lbl in ("Actas", "Contratos", "Identificaciones"):
                card.body.addWidget(QLabel(f"·  {lbl}"))
        else:
            n = 0
            for k in kinds:
                rows = self.session.list_items("/", kind=k)
                n += len(rows)
                card.body.addWidget(QLabel(f"·  {_kind_plural(k)}  ({len(rows)})"))
            card.set_badge(_plural(n, "elemento", "elementos"))
        btn = QPushButton(f"Ver {name.split()[0].lower()}")
        btn.setProperty("role", "link")
        btn.clicked.connect(lambda: self.navigate.emit(NAV_FOR[name]))
        card.body.addWidget(btn)
        return card


def _plural(n: int, sing: str, plur: str) -> str:
    return f"{n} {sing if n == 1 else plur}"


def _kind_plural(k: ItemKind) -> str:
    return {ItemKind.PASSWORD: "Credenciales", ItemKind.ACCOUNT: "Cuentas",
            ItemKind.CARD: "Tarjetas", ItemKind.CONTACT: "Contactos de emergencia",
            ItemKind.WILL: "Testamentos", ItemKind.INSURANCE: "Seguros"}.get(k, k.value)


def _last(ts) -> str:
    if not ts:
        return "—"
    return dt.datetime.fromtimestamp(ts).strftime("%d %b · %H:%M")

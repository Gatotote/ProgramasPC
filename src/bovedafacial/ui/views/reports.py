"""Vista Reportes: de dónde sale el indicador + inventario + almacenamiento."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from ...vault import ItemKind, KIND_LABELS
from .. import status as status_mod
from ..widgets import Banner, Card, section_label


class ReportsView(QWidget):
    navigate = Signal(str)

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(24, 22, 24, 24)
        self._root.setSpacing(16)
        self.refresh()

    def refresh(self) -> None:
        while self._root.count():
            it = self._root.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

        title = QLabel("Reportes")
        title.setProperty("role", "h1")
        self._root.addWidget(title)

        s = status_mod.compute(self.session)
        banner = Banner()
        banner.set(s["dot"], f"Estado de seguridad: {s['label']}",
                   f"{sum(1 for sev, _ in s['reasons'] if sev == 'ok')} correctas · "
                   f"{sum(1 for sev, _ in s['reasons'] if sev != 'ok')} requieren atención",
                   s["level"])
        self._root.addWidget(banner)

        checks = Card("Comprobaciones")
        for sev, text in s["reasons"]:
            row = QHBoxLayout()
            ic = QLabel("✓" if sev == "ok" else "!")
            ic.setStyleSheet(
                f"color:{'#41b955' if sev == 'ok' else '#e0b341'};font-weight:700;min-width:16px;")
            row.addWidget(ic)
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            row.addWidget(lbl, 1)
            checks.body.addLayout(row)
        self._root.addWidget(checks)

        cols = QHBoxLayout()
        cols.setSpacing(14)
        cols.addWidget(self._inventory())
        cols.addWidget(self._storage())
        self._root.addLayout(cols)
        self._root.addStretch(1)

    def _inventory(self) -> Card:
        card = Card("Inventario por tipo")
        stor = self.session.storage_stats()
        counts = [("Archivos", stor["files"])]
        for k in ItemKind:
            counts.append((KIND_LABELS[k], len(self.session.list_items("/", kind=k))))
        top = max((c for _, c in counts), default=1) or 1
        for name, c in counts:
            row = QHBoxLayout()
            n = QLabel(name)
            n.setMinimumWidth(120)
            n.setProperty("role", "dim")
            bar = QProgressBar()
            bar.setRange(0, top)
            bar.setValue(c)
            bar.setTextVisible(False)
            bar.setFixedHeight(9)
            v = QLabel(str(c))
            v.setProperty("role", "mono")
            row.addWidget(n)
            row.addWidget(bar, 1)
            row.addWidget(v)
            card.body.addLayout(row)
        return card

    def _storage(self) -> Card:
        card = Card("Almacenamiento")
        stor = self.session.storage_stats()
        total_mb = stor["on_disk_bytes"] / 1e6
        card.body.addWidget(QLabel(f"{total_mb:.1f} MB cifrados en disco"))
        card.body.addWidget(section_label("Por carpeta de nivel superior"))
        by = sorted(stor["by_category"].items(), key=lambda kv: -kv[1])
        for name, b in by[:8]:
            row = QHBoxLayout()
            row.addWidget(QLabel(name or "(raíz)"))
            row.addStretch(1)
            mb = QLabel(f"{b / 1e6:.1f} MB")
            mb.setProperty("role", "mono")
            row.addWidget(mb)
            card.body.addLayout(row)
        if not by:
            card.body.addWidget(_dim("Aún no hay archivos."))
        return card


def _dim(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("role", "dim")
    return lbl

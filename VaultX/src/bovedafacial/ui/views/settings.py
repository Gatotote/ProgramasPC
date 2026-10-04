"""Vista Configuración: bloqueo automático, cámara, tema, rostro, respaldo."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ... import desktop_integration
from .. import config
from ..widgets import Card

_LOCK_OPTIONS = [("1 min", 60), ("3 min", 180), ("5 min", 300), ("10 min", 600), ("Nunca", 0)]


class SettingsView(QWidget):
    themeChanged = Signal(str)     # "system" | "light" | "dark"
    reenrollRequested = Signal()
    lockNow = Signal()

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 22, 24, 24)
        v.setSpacing(16)
        h = QLabel("Configuración")
        h.setProperty("role", "h1")
        v.addWidget(h)

        card = Card("Seguridad")
        pol = session.header.get("policy", {})

        self.lock_combo = QComboBox()
        for label, secs in _LOCK_OPTIONS:
            self.lock_combo.addItem(label, secs)
        cur = pol.get("auto_lock_seconds", 180)
        idx = next((i for i, (_, s) in enumerate(_LOCK_OPTIONS) if s == cur), 1)
        self.lock_combo.setCurrentIndex(idx)
        self.lock_combo.currentIndexChanged.connect(self._save_lock)
        card.body.addLayout(_row("Bloqueo automático por inactividad", self.lock_combo))

        self.cam_combo = QComboBox()
        try:
            from ..camera import CameraThread  # noqa: F401
            from ...face import list_v4l2_devices
            devs = list_v4l2_devices() or ["(ninguna)"]
        except Exception:  # noqa: BLE001
            devs = ["(extra facial no instalado)"]
        self.cam_combo.addItems(devs)
        card.body.addLayout(_row("Cámara", self.cam_combo))

        thr = pol.get("face_threshold") or 0.45
        card.body.addLayout(_row("Umbral de coincidencia facial", QLabel(f"{thr:.2f}")))
        v.addWidget(card)

        card2 = Card("Rostro y recuperación")
        re = QPushButton("Volver a enrolar rostro")
        re.clicked.connect(self.reenrollRequested.emit)
        card2.body.addWidget(re)
        ph = QPushButton("Mostrar frase de recuperación")
        ph.clicked.connect(lambda: QMessageBox.information(
            self, "Frase de recuperación",
            "Por seguridad, la frase solo se muestra al crear la bóveda. "
            "Si la perdiste, crea una bóveda nueva y reimporta el contenido."))
        card2.body.addWidget(ph)
        pin = QPushButton("Cambiar PIN")
        pin.clicked.connect(lambda: QMessageBox.information(
            self, "Cambiar PIN", "Disponible en una versión próxima."))
        card2.body.addWidget(pin)
        v.addWidget(card2)

        card3 = Card("Apariencia y datos")
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Según el sistema", "system")
        self.theme_combo.addItem("Claro", "light")
        self.theme_combo.addItem("Oscuro", "dark")
        cur_theme = config.get("theme", "system")
        self.theme_combo.setCurrentIndex(
            {"system": 0, "light": 1, "dark": 2}.get(cur_theme, 0))
        self.theme_combo.currentIndexChanged.connect(
            lambda: self._set_theme(self.theme_combo.currentData()))
        card3.body.addLayout(_row("Tema", self.theme_combo))

        bk = QPushButton("Marcar respaldo hecho ahora")
        bk.clicked.connect(self._mark_backup)
        card3.body.addWidget(bk)
        self.backup_lbl = QLabel(self._backup_text())
        self.backup_lbl.setProperty("role", "dim")
        card3.body.addWidget(self.backup_lbl)
        v.addWidget(card3)

        card4 = Card("Sistema")
        self.shred_chk = QCheckBox("Borrar los originales de forma segura al importar")
        self.shred_chk.setChecked(bool(config.get("shred_on_import", False)))
        self.shred_chk.toggled.connect(lambda on: config.set("shred_on_import", bool(on)))
        card4.body.addWidget(self.shred_chk)

        self.sys_lbl = QLabel("")
        self.sys_lbl.setProperty("role", "dim")
        self.sys_lbl.setWordWrap(True)
        excl = QPushButton("Excluir la bóveda del buscador de KDE (Baloo)")
        excl.clicked.connect(self._exclude_baloo)
        card4.body.addWidget(excl)
        launcher = QPushButton("Instalar el lanzador en el menú de KDE")
        launcher.clicked.connect(self._install_launcher)
        card4.body.addWidget(launcher)
        card4.body.addWidget(self.sys_lbl)
        v.addWidget(card4)
        v.addStretch(1)

    def _exclude_baloo(self) -> None:
        try:
            self.sys_lbl.setText(desktop_integration.exclude_from_baloo(self.session.path))
        except Exception as e:  # noqa: BLE001
            self.sys_lbl.setText(f"No se pudo: {e}")

    def _install_launcher(self) -> None:
        try:
            p = desktop_integration.install_desktop_entry()
            self.sys_lbl.setText(f"Lanzador instalado: {p}")
        except Exception as e:  # noqa: BLE001
            self.sys_lbl.setText(f"No se pudo: {e}")

    def _save_lock(self) -> None:
        self.session.set_policy(auto_lock_seconds=self.lock_combo.currentData())

    def _set_theme(self, value: str) -> None:
        config.set("theme", value)
        self.themeChanged.emit(value)

    def _mark_backup(self) -> None:
        self.session.mark_backup()
        self.backup_lbl.setText(self._backup_text())

    def _backup_text(self) -> str:
        ts = self.session.header.get("stats", {}).get("last_backup")
        if not ts:
            return "La bóveda nunca se ha respaldado."
        import datetime as dt
        return "Último respaldo: " + dt.datetime.fromtimestamp(ts).strftime("%d %b %Y %H:%M")


def _row(text: str, w: QWidget):
    row = QHBoxLayout()
    lbl = QLabel(text)
    row.addWidget(lbl, 1)
    row.addWidget(w)
    return row

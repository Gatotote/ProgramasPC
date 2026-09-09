"""Ventana principal: barra lateral + tarjetas + panel de actividad + editor de
elementos + botón «Agregar» + bloqueo automático por inactividad."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..vault import ItemKind
from . import status as status_mod
from . import theme
from .views.files import FilesView
from .views.home import HomeView
from .views.items_view import ItemsView
from .views.photos import PhotosView
from .views.reports import ReportsView
from .views.settings import SettingsView
from .widgets import hline, scroll_page

RAIL = [
    ("🏠", "Inicio"), ("📁", "Archivos"), ("🔑", "Contraseñas"), ("💳", "Finanzas"),
    ("📸", "Fotografías"), ("📊", "Reportes"), ("⚙️", "Configuración"),
]
ADD_ACTIONS = [
    ("📄", "Documento", "Archivos"), ("🔑", "Contraseña", "Contraseñas"),
    ("🖼️", "Imagen", "Fotografías"), ("🎞️", "Vídeo", "Fotografías"),
    ("📁", "Carpeta", "Archivos"),
]


class MainWindow(QWidget):
    locked = Signal()

    def __init__(self, session, parent=None) -> None:
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Bóveda Inteligente")
        self.resize(1040, 680)

        # --- barra lateral ---
        self.rail = QListWidget()
        self.rail.setObjectName("rail")
        self.rail.setFixedWidth(220)
        for icon, name in RAIL:
            QListWidgetItem(f"{icon}   {name}", self.rail)
        self.rail.currentRowChanged.connect(self._on_rail)

        lock_btn = QPushButton("🔒  Bloquear ahora")
        lock_btn.clicked.connect(self._do_lock)
        rail_col = QVBoxLayout()
        rail_col.setContentsMargins(0, 0, 0, 0)
        rail_col.setSpacing(8)
        brand = QLabel("🔐  Bóveda\nInteligente")
        brand.setStyleSheet("color:#e7e3d6;font-size:16px;font-weight:600;padding:12px;")
        rail_col.addWidget(brand)
        rail_col.addWidget(self.rail, 1)
        rail_col.addWidget(lock_btn)
        rail_wrap = QWidget()
        rail_wrap.setStyleSheet("background:transparent;")
        rail_wrap.setLayout(rail_col)
        rail_wrap.setFixedWidth(228)

        # --- barra superior ---
        self.crumb = QLabel("Inicio")
        self.crumb.setProperty("role", "h2")
        self.status_pill = QPushButton("Seguro")
        self.status_pill.setFlat(True)
        self.status_pill.clicked.connect(lambda: self._goto("Reportes"))
        top = QHBoxLayout()
        top.setContentsMargins(20, 12, 20, 12)
        top.addWidget(self.crumb)
        top.addStretch(1)
        top.addWidget(QLabel("Genaro Velasco"))
        top.addWidget(self.status_pill)
        topbar = QWidget()
        topbar.setLayout(top)

        # --- vistas ---
        self.stack = QStackedWidget()
        self.home = HomeView(session)
        self.home.navigate.connect(self._goto)
        self.passwords = ItemsView(session, [ItemKind.PASSWORD], "Contraseñas",
                                   base_dir="/Contraseñas")
        self.finances = ItemsView(session, [ItemKind.ACCOUNT, ItemKind.CARD],
                                  "Información Financiera", base_dir="/Finanzas")
        self.files = FilesView(session)
        self.photos = PhotosView(session)
        self.reports = ReportsView(session)
        self.settings = SettingsView(session)
        self.settings.themeChanged.connect(self._apply_theme)
        self.settings.reenrollRequested.connect(self._reenroll)

        self._views = {
            "Inicio": scroll_page(self.home),
            "Archivos": self.files,
            "Contraseñas": self.passwords,
            "Finanzas": self.finances,
            "Fotografías": self.photos,
            "Reportes": scroll_page(self.reports),
            "Configuración": scroll_page(self.settings),
        }
        for _, name in RAIL:
            self.stack.addWidget(self._views[name])

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(topbar)
        content.addWidget(hline())
        content.addWidget(self.stack, 1)
        content_wrap = QWidget()
        content_wrap.setLayout(content)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(rail_wrap)
        root.addWidget(content_wrap, 1)

        # --- botón flotante ---
        self.fab = QPushButton("＋", self)
        self.fab.setObjectName("primary")
        self.fab.setFixedSize(52, 52)
        self.fab.setStyleSheet("QPushButton#primary{border-radius:26px;font-size:24px;}")
        self.fab.clicked.connect(self._add_menu)
        self.fab.raise_()

        # --- bloqueo por inactividad ---
        self._idle = QTimer(self)
        self._idle.setSingleShot(True)
        self._idle.timeout.connect(self._do_lock)
        QApplication.instance().installEventFilter(self)
        self._reset_idle()

        self.rail.setCurrentRow(0)

    # ---------- navegación ----------
    def _on_rail(self, row: int) -> None:
        if row < 0:
            return
        name = RAIL[row][1]
        self.crumb.setText(name)
        self.stack.setCurrentIndex(row)
        w = self.stack.currentWidget()
        inner = w.widget() if hasattr(w, "widget") and callable(w.widget) else w
        if hasattr(inner, "refresh"):
            try:
                inner.refresh()
            except Exception:  # noqa: BLE001
                pass
        self._update_status()

    def _goto(self, name: str) -> None:
        for i, (_, n) in enumerate(RAIL):
            if n == name:
                self.rail.setCurrentRow(i)
                return

    # ---------- estado ----------
    def _update_status(self) -> None:
        try:
            s = status_mod.compute(self.session)
        except Exception:  # noqa: BLE001
            return
        self.status_pill.setText(f"{s['dot']}  {s['label']}")

    # ---------- añadir ----------
    def _add_menu(self) -> None:
        m = QMenu(self)
        for icon, label, target in ADD_ACTIONS:
            m.addAction(f"{icon}  {label}", lambda t=target, lb=label: self._add(t, lb))
        m.exec(self.fab.mapToGlobal(self.fab.rect().topLeft()))

    def _add(self, target: str, label: str) -> None:
        self._goto(target)
        if target == "Contraseñas":
            self.passwords._new(ItemKind.PASSWORD)
        elif label == "Carpeta":
            self.files._import_folder()
        else:
            self.files._import_files()

    # ---------- tema ----------
    def _apply_theme(self, value: str) -> None:
        app = QApplication.instance()
        dark = None if value == "system" else (value == "dark")
        theme.apply(app, dark=dark)

    def _reenroll(self) -> None:
        from .enroll_widget import EnrollWidget
        from PySide6.QtWidgets import QDialog, QVBoxLayout as V

        dlg = QDialog(self)
        dlg.setWindowTitle("Volver a enrolar rostro")
        dlg.resize(460, 460)
        lay = V(dlg)
        ew = EnrollWidget()
        lay.addWidget(ew)

        def done(tpl):
            try:
                from ..face import save_template
                save_template(self.session.path, self.session.mk, tpl)
                self.session.log_event("enroll", f"{tpl.count} muestras")
                QMessageBox.information(dlg, "Rostro", "Rostro actualizado.")
            except Exception as e:  # noqa: BLE001
                QMessageBox.warning(dlg, "Rostro", str(e))
            dlg.accept()

        ew.enrolled.connect(done)
        dlg.exec()
        ew.shutdown()

    # ---------- bloqueo ----------
    def eventFilter(self, obj, ev):  # noqa: N802
        if ev.type() in (QEvent.Type.MouseMove, QEvent.Type.KeyPress,
                         QEvent.Type.MouseButtonPress, QEvent.Type.Wheel):
            self._reset_idle()
        return super().eventFilter(obj, ev)

    def _reset_idle(self) -> None:
        secs = self.session.header.get("policy", {}).get("auto_lock_seconds", 180)
        if secs and secs > 0:
            self._idle.start(int(secs) * 1000)
        else:
            self._idle.stop()

    def _do_lock(self) -> None:
        if getattr(self, "_locking", False):
            return
        self._locking = True
        try:
            self.photos.shutdown()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.session.log_event("lock")
        except Exception:  # noqa: BLE001
            pass
        self.session.close()   # re-cifra check-outs y borra el área en RAM
        self.locked.emit()
        self.close()

    # ---------- geometría ----------
    def resizeEvent(self, ev):  # noqa: N802
        super().resizeEvent(ev)
        self.fab.move(self.width() - self.fab.width() - 26,
                      self.height() - self.fab.height() - 24)

    def closeEvent(self, ev):  # noqa: N802
        try:
            QApplication.instance().removeEventFilter(self)
            self.photos.shutdown()
            if not self.session._closed:
                self.session.close()
        except Exception:  # noqa: BLE001
            pass
        super().closeEvent(ev)

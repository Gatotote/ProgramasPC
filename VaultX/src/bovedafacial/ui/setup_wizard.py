"""Asistente de primer arranque: ubicación → PIN → rostro → frase de recuperación."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..pwgen import strength
from ..vault import create_vault
from ..vault.session import MIN_PIN_LEN
from .enroll_widget import EnrollWidget
from .widgets import hline


class SetupWizard(QDialog):
    def __init__(self, default_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurar VaultX")
        self.setModal(True)
        self.resize(560, 560)

        self.vault_path = Path(default_path)
        self._template = None
        self._phrase = ""
        self._session = None

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_location())
        self.stack.addWidget(self._page_pin())
        self.stack.addWidget(self._page_face())
        self.stack.addWidget(self._page_phrase())

        self.back_btn = QPushButton("Atrás")
        self.next_btn = QPushButton("Siguiente")
        self.next_btn.setObjectName("primary")
        self.back_btn.clicked.connect(self._back)
        self.next_btn.clicked.connect(self._next)

        nav = QHBoxLayout()
        nav.addWidget(self.back_btn)
        nav.addStretch(1)
        nav.addWidget(self.next_btn)

        root = QVBoxLayout(self)
        root.addWidget(self.stack, 1)
        root.addWidget(hline())
        root.addLayout(nav)
        self._sync_nav()

    # ---------- páginas ----------
    def _page_location(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)
        t = QLabel("VaultX")
        t.setProperty("role", "h1")
        v.addWidget(t)
        v.addWidget(_p("Una caja fuerte cifrada para tus documentos, contraseñas, "
                       "finanzas e información familiar. Se abre con tu PIN y tu rostro."))
        v.addWidget(hline())
        v.addWidget(_lbl("Dónde guardar la bóveda"))
        row = QHBoxLayout()
        self.path_edit = QLineEdit(str(self.vault_path))
        self.path_edit.setReadOnly(True)
        pick = QPushButton("Cambiar…")
        pick.clicked.connect(self._pick_dir)
        row.addWidget(self.path_edit, 1)
        row.addWidget(pick)
        v.addLayout(row)
        v.addWidget(_p("Dentro solo habrá datos cifrados. Puedes ponerla en una "
                       "carpeta que sincronices a la nube: sin el PIN y tu rostro no "
                       "sirve de nada.", dim=True))
        v.addStretch(1)
        return w

    def _page_pin(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)
        h = QLabel("Elige un PIN")
        h.setProperty("role", "h2")
        v.addWidget(h)
        v.addWidget(_p(f"Mínimo {MIN_PIN_LEN} caracteres. Es la raíz criptográfica de "
                       "la bóveda: cuanto más largo, mejor. Tu rostro será el segundo "
                       "factor."))
        v.addWidget(hline())
        self.pin1 = QLineEdit()
        self.pin1.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin1.setPlaceholderText("PIN")
        self.pin2 = QLineEdit()
        self.pin2.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin2.setPlaceholderText("Repite el PIN")
        self.pin_hint = QLabel(" ")
        self.pin_hint.setProperty("role", "dim")
        for e in (self.pin1, self.pin2):
            e.textChanged.connect(self._check_pin)
        v.addWidget(_lbl("PIN"))
        v.addWidget(self.pin1)
        v.addWidget(_lbl("Confirmación"))
        v.addWidget(self.pin2)
        self.show_pin = QCheckBox("Mostrar PIN")
        self.show_pin.toggled.connect(
            lambda on: [e.setEchoMode(QLineEdit.EchoMode.Normal if on
                                      else QLineEdit.EchoMode.Password)
                        for e in (self.pin1, self.pin2)])
        v.addWidget(self.show_pin)
        v.addWidget(self.pin_hint)
        v.addStretch(1)
        return w

    def _page_face(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)
        h = QLabel("Enrola tu rostro")
        h.setProperty("role", "h2")
        v.addWidget(h)
        v.addWidget(_p("Se toman unas 10 muestras de tu cara. Podrás volver a "
                       "hacerlo cuando quieras desde Configuración."))
        self.enroll = EnrollWidget()
        self.enroll.enrolled.connect(self._on_enrolled)
        v.addWidget(self.enroll, 1)
        self.skip_face = QCheckBox("Omitir por ahora (podré enrolar más tarde)")
        self.skip_face.toggled.connect(self._sync_nav)
        v.addWidget(self.skip_face)
        return w

    def _page_phrase(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(12)
        h = QLabel("Frase de recuperación")
        h.setProperty("role", "h2")
        v.addWidget(h)
        v.addWidget(_p("24 palabras. Es la ÚNICA forma de entrar si falla la cámara "
                       "o cambia tu aspecto. Anótala en papel y guárdala fuera del "
                       "equipo. No se volverá a mostrar."))
        self.phrase_box = QPlainTextEdit()
        self.phrase_box.setReadOnly(True)
        self.phrase_box.setProperty("role", "mono")
        self.phrase_box.setFixedHeight(120)
        v.addWidget(self.phrase_box)
        row = QHBoxLayout()
        copy = QPushButton("Copiar al portapapeles")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self._phrase))
        row.addWidget(copy)
        row.addStretch(1)
        v.addLayout(row)
        self.wrote_it = QCheckBox("La he anotado en papel, fuera del equipo")
        self.wrote_it.toggled.connect(self._sync_nav)
        v.addWidget(self.wrote_it)
        v.addStretch(1)
        return w

    # ---------- navegación ----------
    def _sync_nav(self) -> None:
        i = self.stack.currentIndex()
        self.back_btn.setEnabled(i > 0 and i < 3)
        if i == 0:
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Siguiente")
        elif i == 1:
            self.next_btn.setEnabled(self._pin_ok())
            self.next_btn.setText("Siguiente")
        elif i == 2:
            self.next_btn.setEnabled(self._template is not None or self.skip_face.isChecked())
            self.next_btn.setText("Crear bóveda")
        elif i == 3:
            self.back_btn.setEnabled(False)
            self.next_btn.setEnabled(self.wrote_it.isChecked())
            self.next_btn.setText("Terminar")

    def _back(self) -> None:
        self.stack.setCurrentIndex(max(0, self.stack.currentIndex() - 1))
        self._sync_nav()

    def _next(self) -> None:
        i = self.stack.currentIndex()
        if i < 2:
            self.stack.setCurrentIndex(i + 1)
            self._sync_nav()
        elif i == 2:
            if self._create_vault():
                self.stack.setCurrentIndex(3)
                self._sync_nav()
        else:
            self.accept()

    # ---------- lógica ----------
    def _pick_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Carpeta para la bóveda",
                                             str(self.vault_path.parent))
        if d:
            self.vault_path = Path(d) / "principal.vault"
            self.path_edit.setText(str(self.vault_path))

    def _pin_ok(self) -> bool:
        return len(self.pin1.text()) >= MIN_PIN_LEN and self.pin1.text() == self.pin2.text()

    def _check_pin(self) -> None:
        p1, p2 = self.pin1.text(), self.pin2.text()
        if len(p1) < MIN_PIN_LEN:
            self.pin_hint.setText(f"Faltan {MIN_PIN_LEN - len(p1)} caracteres")
        elif p2 and p1 != p2:
            self.pin_hint.setText("No coinciden")
        else:
            self.pin_hint.setText(f"Fortaleza: {strength(p1)}")
        self._sync_nav()

    def _on_enrolled(self, template) -> None:
        self._template = template
        self._sync_nav()

    def _create_vault(self) -> bool:
        try:
            if self.vault_path.exists():
                raise FileExistsError(f"Ya existe {self.vault_path}")
            self._phrase, self._session = create_vault(self.vault_path, self.pin1.text())
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "No se pudo crear la bóveda", str(e))
            return False
        if self._template is not None:
            try:
                from ..face import save_template
                save_template(self._session.path, self._session.mk, self._template)
                self._session.log_event("enroll", f"{self._template.count} muestras")
            except Exception as e:  # noqa: BLE001
                QMessageBox.warning(self, "Rostro", f"La bóveda se creó pero no se pudo "
                                                    f"guardar el rostro: {e}")
        try:
            from ..desktop_integration import exclude_from_baloo
            exclude_from_baloo(self.vault_path)
        except Exception:  # noqa: BLE001
            pass
        self._session.close()
        self.phrase_box.setPlainText(self._phrase)
        return True

    def closeEvent(self, ev) -> None:  # noqa: N802
        try:
            self.enroll.shutdown()
        except Exception:
            pass
        super().closeEvent(ev)


def _p(text: str, dim: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    if dim:
        lbl.setProperty("role", "dim")
    return lbl


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("role", "label")
    return lbl

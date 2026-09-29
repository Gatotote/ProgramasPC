"""Diálogo para crear / editar un elemento tipado. Los campos se generan a
partir de FIELD_SPECS del tipo."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from ..pwgen import generate
from ..vault import KIND_LABELS, spec_for
from ..vault.items import coerce_kind
from .widgets import StrengthMeter


class ItemEditor(QDialog):
    def __init__(self, kind, *, name: str = "", fields: dict | None = None,
                 dir_path: str = "/", parent=None) -> None:
        super().__init__(parent)
        self.kind = coerce_kind(kind)
        self.dir_path = dir_path
        self._new = not name
        fields = fields or {}
        self.setWindowTitle(("Nuevo " if self._new else "Editar ") + KIND_LABELS[self.kind].lower())
        self.setModal(True)
        self.resize(460, 520)

        self._edits: dict[str, QLineEdit | QPlainTextEdit] = {}
        v = QVBoxLayout(self)
        v.setSpacing(8)

        v.addWidget(_lbl("Nombre"))
        self.name_edit = QLineEdit(name)
        self.name_edit.setReadOnly(not self._new)
        self.name_edit.setPlaceholderText("p. ej. Banco BBVA")
        v.addWidget(self.name_edit)

        for fs in spec_for(self.kind):
            v.addWidget(_lbl(fs.label))
            if fs.multiline:
                ed = QPlainTextEdit(fields.get(fs.key, ""))
                ed.setFixedHeight(80)
                v.addWidget(ed)
            else:
                ed = QLineEdit(fields.get(fs.key, ""))
                if fs.secret:
                    ed.setEchoMode(QLineEdit.EchoMode.Password)
                    v.addLayout(self._secret_row(ed, fs.key))
                    if fs.key == "password":
                        meter = StrengthMeter()
                        ed.textChanged.connect(meter.set_password)
                        meter.set_password(ed.text())
                        v.addWidget(meter)
                else:
                    v.addWidget(ed)
            self._edits[fs.key] = ed

        v.addStretch(1)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        bb.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        bb.accepted.connect(self._try_accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def _secret_row(self, ed: QLineEdit, key: str):
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(ed, 1)

        eye = QPushButton("Ver")
        eye.setCheckable(True)
        eye.setToolTip("Mostrar u ocultar")
        eye.toggled.connect(lambda on: (
            ed.setEchoMode(QLineEdit.EchoMode.Normal if on
                           else QLineEdit.EchoMode.Password),
            eye.setText("Ocultar" if on else "Ver")))
        row.addWidget(eye)

        cp = QPushButton("Copiar")
        cp.clicked.connect(lambda: QApplication.clipboard().setText(ed.text()))
        row.addWidget(cp)

        if key in ("password", "poliza"):
            gen = QPushButton("Generar")
            gen.setToolTip("Crear una contraseña segura")
            gen.clicked.connect(lambda: ed.setText(generate(20)))
            row.addWidget(gen)
        return row

    def _try_accept(self) -> None:
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        self.accept()

    def result_data(self) -> tuple[str, dict]:
        fields = {}
        for key, ed in self._edits.items():
            val = ed.toPlainText() if isinstance(ed, QPlainTextEdit) else ed.text()
            if val.strip():
                fields[key] = val
        return self.name_edit.text().strip(), fields


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("role", "label")
    return lbl

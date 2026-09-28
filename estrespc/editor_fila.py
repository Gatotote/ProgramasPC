"""Ventana para crear o editar una fila de tareas."""

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from .fila import PERFILES, TIPOS_CPU, TIPOS_GPU, duracion_vuelta


class EditorFila(QDialog):
    def __init__(self, nombre, pasos, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Fila de tareas")
        self.resize(900, 520)
        lay = QVBoxLayout(self)

        fila = QHBoxLayout()
        fila.addWidget(QLabel("Nombre:"))
        # Los perfiles de fábrica no se sobrescriben: se guarda una copia con otro nombre.
        self.nombre = QLineEdit(nombre if nombre not in PERFILES else f"{nombre} (mía)")
        fila.addWidget(self.nombre, 1)
        lay.addLayout(fila)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Paso", "Segundos", "CPU", "Hilos CPU", "GPU"])
        self.tabla.verticalHeader().setVisible(True)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        lay.addWidget(self.tabla, 1)
        for p in pasos:
            self._agregar(p)

        botones = QHBoxLayout()
        for texto, fn in (("+ Agregar paso", lambda: self._agregar(None)),
                          ("Duplicar", self._duplicar), ("Quitar", self._quitar),
                          ("↑ Subir", lambda: self._mover(-1)), ("↓ Bajar", lambda: self._mover(1))):
            b = QPushButton(texto)
            b.clicked.connect(fn)
            botones.addWidget(b)
        botones.addStretch(1)
        self.total = QLabel()
        botones.addWidget(self.total)
        lay.addLayout(botones)

        ayuda = QLabel("<b>CPU:</b> " + " · ".join(f"<i>{n}</i>: {d}" for k, (n, d) in TIPOS_CPU.items()
                                                  if k != "nada")
                       + "<br><b>GPU:</b> " + " · ".join(f"<i>{n}</i>: {d}" for k, (n, d) in TIPOS_GPU.items()
                                                       if k != "nada")
                       + "<br>Hilos 0 = automático (todos; «Ligera» usa 2). La fila se repite hasta "
                         "cumplir la duración elegida.")
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color:#aab")
        lay.addWidget(ayuda)

        caja = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        caja.accepted.connect(self._aceptar)
        caja.rejected.connect(self.reject)
        lay.addWidget(caja)
        self._total()

    # ------------------------------------------------------------ filas de la tabla
    def _combo(self, tipos, actual):
        c = QComboBox()
        for k, (n, d) in tipos.items():
            c.addItem(n, k)
            c.setItemData(c.count() - 1, d, 3)  # 3 = ToolTipRole
        c.setCurrentIndex(max(0, c.findData(actual)))
        return c

    def _agregar(self, p, fila=None):
        p = p or {"nombre": "Paso nuevo", "segundos": 30, "cpu": "pesada", "hilos": 0, "gpu": "nada"}
        r = self.tabla.rowCount() if fila is None else fila
        self.tabla.insertRow(r)
        self.tabla.setItem(r, 0, QTableWidgetItem(p["nombre"]))
        seg = QSpinBox(minimum=1, maximum=86_400, value=p["segundos"], suffix=" s")
        seg.valueChanged.connect(self._total)
        self.tabla.setCellWidget(r, 1, seg)
        self.tabla.setCellWidget(r, 2, self._combo(TIPOS_CPU, p["cpu"]))
        self.tabla.setCellWidget(r, 3, QSpinBox(minimum=0, maximum=512, value=p.get("hilos", 0),
                                                specialValueText="auto"))
        self.tabla.setCellWidget(r, 4, self._combo(TIPOS_GPU, p["gpu"]))
        self._total()

    def _leer(self, r):
        return {"nombre": (self.tabla.item(r, 0).text() or f"Paso {r + 1}").strip(),
                "segundos": self.tabla.cellWidget(r, 1).value(),
                "cpu": self.tabla.cellWidget(r, 2).currentData(),
                "hilos": self.tabla.cellWidget(r, 3).value(),
                "gpu": self.tabla.cellWidget(r, 4).currentData()}

    def pasos(self):
        return [self._leer(r) for r in range(self.tabla.rowCount())]

    def _duplicar(self):
        r = self.tabla.currentRow()
        if r >= 0:
            self._agregar(self._leer(r), r + 1)

    def _quitar(self):
        r = self.tabla.currentRow()
        if r >= 0:
            self.tabla.removeRow(r)
            self._total()

    def _mover(self, d):
        r = self.tabla.currentRow()
        if r < 0 or not 0 <= r + d < self.tabla.rowCount():
            return
        p = self._leer(r)
        self.tabla.removeRow(r)
        self._agregar(p, r + d)
        self.tabla.selectRow(r + d)

    def _total(self, *_):
        s = duracion_vuelta(self.pasos())
        self.total.setText(f"Una vuelta: {s // 60} min {s % 60} s")

    def _aceptar(self):
        nombre = self.nombre.text().strip()
        if not nombre or nombre in PERFILES:
            QMessageBox.warning(self, "Fila de tareas", "Ponle un nombre distinto a los perfiles de fábrica.")
            return
        if not self.pasos():
            QMessageBox.warning(self, "Fila de tareas", "Agrega al menos un paso.")
            return
        if all(p["cpu"] in ("nada", "reposo") and p["gpu"] in ("nada", "reposo") for p in self.pasos()):
            QMessageBox.warning(self, "Fila de tareas", "Todos los pasos están en reposo: no probaría nada.")
            return
        self.accept()

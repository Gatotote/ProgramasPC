import os
import sys
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.widgets.chip import Chip
from app.widgets.tabla import crear_tabla
from app.widgets.tarjeta import Panel

_TONO_TIPO = {"descarga": "azul", "conversion": "amarillo"}


class HistorialPage(QWidget):
    def __init__(self):
        super().__init__()
        self._filas = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        cabecera = QLabel("Historial")
        cabecera.setStyleSheet("font-size:20px;font-weight:800;")
        layout.addWidget(cabecera)

        self.panel = Panel("Descargas y conversiones", borde="#a78bfa", acento="#c4b5fd")
        self._cont_tabla = QVBoxLayout()
        self.panel.layout_panel.addLayout(self._cont_tabla)
        layout.addWidget(self.panel, 1)

        fila_b = QHBoxLayout()
        b_abrir = QPushButton("Abrir carpeta")
        b_abrir.setObjectName("ghost")
        b_abrir.clicked.connect(self._abrir_carpeta)
        b_refrescar = QPushButton("Actualizar")
        b_refrescar.setObjectName("ghost")
        b_refrescar.clicked.connect(self.refrescar)
        b_borrar_sel = QPushButton("Borrar selección")
        b_borrar_sel.setObjectName("ghost")
        b_borrar_sel.clicked.connect(self._borrar_seleccion)
        b_borrar = QPushButton("Borrar historial")
        b_borrar.setObjectName("peligro")
        b_borrar.clicked.connect(self._borrar)
        fila_b.addWidget(b_abrir)
        fila_b.addWidget(b_refrescar)
        fila_b.addWidget(b_borrar_sel)
        fila_b.addStretch()
        fila_b.addWidget(b_borrar)
        layout.addLayout(fila_b)

        self.tabla = None
        self.refrescar()

    def refrescar(self):
        while self._cont_tabla.count():
            item = self._cont_tabla.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._filas = list(reversed(config.cargar_historial()))
        self._total = len(self._filas)
        if not self._filas:
            vacio = QLabel("Aún no hay nada en el historial.")
            vacio.setStyleSheet("color:#8b97ad;padding:10px;")
            self._cont_tabla.addWidget(vacio)
            self.tabla = None
            return

        filas = [
            (
                "Descarga" if f.get("tipo") == "descarga" else "Conversión",
                (f.get("titulo") or "")[:70],
                f.get("detalle") or "",
                "OK" if f.get("estado") == "ok" else "Error",
                f.get("fecha") or "",
            )
            for f in self._filas
        ]
        self.tabla = crear_tabla(
            ["Tipo", "Título", "Detalle", "Estado", "Fecha"],
            filas,
            chips={
                0: lambda v: Chip(v, _TONO_TIPO.get("descarga" if v == "Descarga" else "conversion", "gris")),
                3: lambda v: Chip(v, "verde" if v == "OK" else "rojo"),
            },
            resize={0: 110, 2: 160, 3: 90, 4: 130},
        )
        self.tabla.itemDoubleClicked.connect(lambda *_: self._abrir_carpeta())
        self._cont_tabla.addWidget(self.tabla)

    def _fila_seleccionada(self):
        if not self.tabla:
            return None
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self._filas):
            return self._filas[fila]
        return None

    def _abrir_carpeta(self):
        f = self._fila_seleccionada()
        if not f:
            QMessageBox.information(self, "Historial", "Selecciona una fila primero.")
            return
        carpeta = f.get("carpeta") or ""
        if carpeta and os.path.isdir(carpeta):
            if sys.platform == "win32":
                os.startfile(carpeta)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", carpeta])
            else:
                subprocess.Popen(["xdg-open", carpeta])
        else:
            QMessageBox.warning(self, "Carpeta no encontrada", "Esa carpeta ya no existe.")

    def _borrar_seleccion(self):
        if not self.tabla:
            return
        fila = self.tabla.currentRow()
        if not (0 <= fila < self._total):
            QMessageBox.information(self, "Historial", "Selecciona una fila primero.")
            return
        entrada = self._filas[fila]
        titulo = (entrada.get("titulo") or "esta entrada")[:60]
        if QMessageBox.question(self, "Borrar entrada", f"¿Borrar «{titulo}» del historial?") != QMessageBox.Yes:
            return
        # self._filas está en orden inverso al guardado: fila 0 = última entrada.
        indice_real = self._total - 1 - fila
        config.borrar_entrada_historial(indice_real)
        self.refrescar()

    def _borrar(self):
        if not self._filas:
            return
        if QMessageBox.question(self, "Borrar historial", "¿Borrar todo el historial?") == QMessageBox.Yes:
            config.limpiar_historial()
            self.refrescar()

    def showEvent(self, evento):
        self.refrescar()
        super().showEvent(evento)

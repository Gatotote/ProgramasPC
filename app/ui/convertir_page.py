import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.services import conversion, ffmpeg
from app.widgets.campos import SelectorCarpeta
from app.widgets.tarjeta import Panel


class ConvertirPage(QWidget):
    trabajo_terminado = Signal()

    def __init__(self):
        super().__init__()
        self.worker = None
        s = config.cargar_settings()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        cabecera = QLabel("Convertir archivos")
        cabecera.setStyleSheet("font-size:20px;font-weight:800;")
        layout.addWidget(cabecera)
        sub = QLabel("Convierte vídeo y audio entre formatos con FFmpeg. Puedes añadir varios archivos.")
        sub.setStyleSheet("color:#8b97ad;font-size:11px;")
        layout.addWidget(sub)

        self.aviso = QLabel("⚠ FFmpeg no está instalado. Instálalo para poder convertir (ver Configuración).")
        self.aviso.setWordWrap(True)
        self.aviso.setStyleSheet("color:#fbbf24;font-size:11px;")
        self.aviso.setVisible(not ffmpeg.disponible())
        layout.addWidget(self.aviso)

        # --- Archivos ---
        arch = Panel("Archivos a convertir", borde="#3b82f6", acento="#93c5fd")
        self.lista = QListWidget()
        self.lista.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lista.setFixedHeight(150)
        arch.layout_panel.addWidget(self.lista)
        fila_b = QHBoxLayout()
        b_add = QPushButton("Añadir archivos…")
        b_add.setObjectName("ghost")
        b_add.clicked.connect(self._añadir)
        b_quitar = QPushButton("Quitar seleccionados")
        b_quitar.setObjectName("ghost")
        b_quitar.clicked.connect(self._quitar)
        b_vaciar = QPushButton("Vaciar lista")
        b_vaciar.setObjectName("ghost")
        b_vaciar.clicked.connect(self.lista.clear)
        for b in (b_add, b_quitar, b_vaciar):
            fila_b.addWidget(b)
        fila_b.addStretch()
        arch.layout_panel.addLayout(fila_b)
        layout.addWidget(arch)

        # --- Salida ---
        salida = Panel("Formato de salida", borde="#f59e0b", acento="#fbbf24")
        fila_tipo = QHBoxLayout()
        fila_tipo.setSpacing(10)
        fila_tipo.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Vídeo", "Audio"])
        self.combo_tipo.setFixedWidth(140)
        self.combo_tipo.currentTextChanged.connect(self._recargar_formatos)
        fila_tipo.addWidget(self.combo_tipo)
        fila_tipo.addSpacing(16)
        fila_tipo.addWidget(QLabel("Formato:"))
        self.combo_formato = QComboBox()
        self.combo_formato.setFixedWidth(260)
        fila_tipo.addWidget(self.combo_formato)
        fila_tipo.addStretch()
        salida.layout_panel.addLayout(fila_tipo)

        salida.layout_panel.addWidget(QLabel("Carpeta de destino:"))
        self.sel_carpeta = SelectorCarpeta(s["carpeta_conversiones"], "Carpeta de conversiones")
        salida.layout_panel.addWidget(self.sel_carpeta)
        layout.addWidget(salida)
        self._recargar_formatos("Vídeo")

        # --- Acciones ---
        acciones = QHBoxLayout()
        self.btn_convertir = QPushButton("Convertir")
        self.btn_convertir.setCursor(Qt.PointingHandCursor)
        self.btn_convertir.clicked.connect(self._iniciar)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("ghost")
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.clicked.connect(self._cancelar)
        acciones.addWidget(self.btn_convertir)
        acciones.addWidget(self.btn_cancelar)
        acciones.addStretch()
        layout.addLayout(acciones)

        # --- Progreso ---
        progreso = Panel("Progreso", borde="#22c55e", acento="#86efac")
        self.lbl_actual = QLabel("Ningún archivo en proceso.")
        self.lbl_actual.setWordWrap(True)
        self.lbl_actual.setStyleSheet("font-weight:700;")
        self.barra = QProgressBar()
        self.lbl_sub = QLabel("Listo para convertir.")
        self.lbl_sub.setStyleSheet("color:#8b97ad;font-size:11px;")
        progreso.layout_panel.addWidget(self.lbl_actual)
        progreso.layout_panel.addWidget(self.barra)
        progreso.layout_panel.addWidget(self.lbl_sub)
        layout.addWidget(progreso)
        layout.addStretch()

        scroll.setWidget(cont)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.addWidget(scroll)

    # -- lista de archivos -----------------------------------------------

    def _añadir(self):
        rutas, _ = QFileDialog.getOpenFileNames(
            self, "Elegir archivos", "", conversion.FILTRO_ARCHIVOS
        )
        existentes = {self.lista.item(i).text() for i in range(self.lista.count())}
        for r in rutas:
            if r not in existentes:
                self.lista.addItem(r)

    def _quitar(self):
        for item in self.lista.selectedItems():
            self.lista.takeItem(self.lista.row(item))

    def _recargar_formatos(self, tipo):
        self.combo_formato.clear()
        tabla = conversion.VIDEO if tipo == "Vídeo" else conversion.AUDIO
        self.combo_formato.addItems(list(tabla.keys()))

    # -- conversión -----------------------------------------------------

    def _iniciar(self):
        if not ffmpeg.disponible():
            QMessageBox.critical(self, "Falta FFmpeg", "Instala FFmpeg para convertir (ver Configuración).")
            return
        entradas = [self.lista.item(i).text() for i in range(self.lista.count())]
        entradas = [e for e in entradas if os.path.isfile(e)]
        if not entradas:
            QMessageBox.warning(self, "Sin archivos", "Añade al menos un archivo a la lista.")
            return
        carpeta = self.sel_carpeta.valor()
        config.guardar_settings({"carpeta_conversiones": carpeta})

        self.btn_convertir.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        self.barra.setValue(0)
        self._formato_actual = self.combo_formato.currentText()

        self.worker = conversion.ConversionWorker(entradas, carpeta, self._formato_actual)
        self.worker.empieza_uno.connect(self._al_empezar_uno)
        self.worker.progreso.connect(self._al_progreso)
        self.worker.uno_terminado.connect(self._al_terminar_uno)
        self.worker.todo_terminado.connect(self._al_terminar_todo)
        self.worker.start()

    def _cancelar(self):
        if self.worker:
            self.worker.cancelar()
            self.btn_cancelar.setEnabled(False)
            self.lbl_sub.setText("Cancelando…")

    def _al_empezar_uno(self, idx, total, nombre):
        self.barra.setValue(0)
        self.lbl_actual.setText(f"[{idx}/{total}] {nombre}")
        self.lbl_sub.setText(f"Convirtiendo a {self._formato_actual}…")

    def _al_progreso(self, pct, texto):
        self.barra.setValue(pct)

    def _al_terminar_uno(self, salida, ok):
        config.agregar_historial(
            "conversion",
            os.path.basename(salida) if ok else "Conversión fallida",
            detalle=self._formato_actual,
            origen=os.path.basename(salida),
            carpeta=self.sel_carpeta.valor(),
            estado="ok" if ok else "error",
        )

    def _al_terminar_todo(self, ok, total, errores):
        self.btn_convertir.setEnabled(True)
        self.btn_cancelar.setEnabled(False)
        self.worker = None
        self.barra.setValue(100 if ok else 0)
        self.lbl_actual.setText("Ningún archivo en proceso.")
        self.lbl_sub.setText(f"Completado: {ok} de {total}.")
        self.trabajo_terminado.emit()
        if errores and errores[0][0] == "":
            QMessageBox.critical(self, "Error", errores[0][1])
            return
        if errores:
            det = "\n".join(f"• {a}: {m}" for a, m in errores[:5])
            QMessageBox.warning(self, "Terminó con errores", f"{ok} de {total} correctos.\n\n{det}")
        else:
            QMessageBox.information(self, "Listo", f"Se convirtieron {ok} de {total} archivo(s).")

    def hay_trabajo(self):
        return self.worker is not None and self.worker.isRunning()

    def detener(self):
        if self.worker:
            self.worker.cancelar()
            self.worker.wait(3000)

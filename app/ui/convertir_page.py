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
from app.services import conversion, ffmpeg, imagenes
from app.widgets.campos import SelectorCarpeta
from app.widgets.tarjeta import Panel


class ConvertirPage(QWidget):
    trabajo_terminado = Signal()

    def __init__(self):
        super().__init__()
        self.worker = None
        self._formato_actual = ""
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
        sub = QLabel(
            "Convierte vídeo y audio (FFmpeg) o imágenes, incluidas RAW de cámara "
            "(CR2/CR3, NEF, ARW, RAF, RW2, ORF…). Puedes añadir varios archivos."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#8b97ad;font-size:11px;")
        layout.addWidget(sub)

        self.aviso = QLabel("⚠ FFmpeg no está instalado. Necesario para vídeo y audio (ver Configuración).")
        self.aviso.setWordWrap(True)
        self.aviso.setStyleSheet("color:#fbbf24;font-size:11px;")
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
        self.combo_tipo.addItems(["Vídeo", "Audio", "Imagen"])
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

        # Fila de tamaño, solo para imágenes
        self.fila_tam = QWidget()
        lay_tam = QHBoxLayout(self.fila_tam)
        lay_tam.setContentsMargins(0, 0, 0, 0)
        lay_tam.setSpacing(10)
        lay_tam.addWidget(QLabel("Tamaño:"))
        self.combo_tam = QComboBox()
        self.combo_tam.addItems(imagenes.LADOS_MAX)
        self.combo_tam.setFixedWidth(180)
        self.combo_tam.setToolTip("Reduce la imagen si su lado mayor supera ese valor. No amplía.")
        lay_tam.addWidget(self.combo_tam)
        lay_tam.addStretch()
        salida.layout_panel.addWidget(self.fila_tam)

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

    def _filtro_archivos(self):
        if self.combo_tipo.currentText() == "Imagen":
            return imagenes.FILTRO_ARCHIVOS
        return conversion.FILTRO_ARCHIVOS

    def _añadir(self):
        rutas, _ = QFileDialog.getOpenFileNames(
            self, "Elegir archivos", "", self._filtro_archivos()
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
        if tipo == "Imagen":
            self.combo_formato.addItems(list(imagenes.SALIDA.keys()))
        elif tipo == "Audio":
            self.combo_formato.addItems(list(conversion.AUDIO.keys()))
        else:
            self.combo_formato.addItems(list(conversion.VIDEO.keys()))
        es_imagen = tipo == "Imagen"
        self.fila_tam.setVisible(es_imagen)
        self.aviso.setVisible(not es_imagen and not ffmpeg.disponible())

    # -- conversión -----------------------------------------------------

    def _iniciar(self):
        entradas = [self.lista.item(i).text() for i in range(self.lista.count())]
        entradas = [e for e in entradas if os.path.isfile(e)]
        if not entradas:
            QMessageBox.warning(self, "Sin archivos", "Añade al menos un archivo a la lista.")
            return

        tipo = self.combo_tipo.currentText()
        carpeta = self.sel_carpeta.valor()
        config.guardar_settings({"carpeta_conversiones": carpeta})
        self._formato_actual = self.combo_formato.currentText()

        if tipo == "Imagen":
            if not imagenes.pillow_disponible():
                QMessageBox.critical(self, "Falta Pillow", "Instala Pillow para convertir imágenes.")
                return
            if any(imagenes.es_raw(e) for e in entradas) and not imagenes.raw_disponible():
                QMessageBox.critical(
                    self, "Falta rawpy",
                    "Para abrir archivos RAW (CR2/CR3, NEF, ARW…) hace falta rawpy.\n\n"
                    "Instálalo con:  pip install rawpy",
                )
                return
            lado = imagenes.lado_a_pixeles(self.combo_tam.currentText())
            self.worker = imagenes.ConversionImagenWorker(
                entradas, carpeta, self._formato_actual, lado_max=lado
            )
        else:
            if not ffmpeg.disponible():
                QMessageBox.critical(
                    self, "Falta FFmpeg", "Instala FFmpeg para convertir vídeo o audio (ver Configuración)."
                )
                return
            self.worker = conversion.ConversionWorker(entradas, carpeta, self._formato_actual)

        self.btn_convertir.setEnabled(False)
        self.btn_cancelar.setEnabled(True)
        self.barra.setValue(0)
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
        if texto:
            self.lbl_sub.setText(texto)

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

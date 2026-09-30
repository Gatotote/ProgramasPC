import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
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

# Extensiones que sabe convertir la app, por categoría.
EXT_IMAGEN = imagenes.EXT_PILLOW | imagenes.EXT_RAW


def _categoria_de(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    if ext in EXT_IMAGEN:
        return "Imagen"
    if ext in conversion.EXT_AUDIO:
        return "Audio"
    if ext in conversion.EXT_VIDEO:
        return "Vídeo"
    return ""


def _filtro_completo():
    """Un filtro que muestra TODO lo compatible primero, para que no dependa
    del tipo de salida elegido (antes las RAW no salían si 'Tipo' era Vídeo)."""
    imgs = " ".join(sorted(f"*{e}" for e in EXT_IMAGEN))
    vid = " ".join(sorted(f"*{e}" for e in conversion.EXT_VIDEO))
    aud = " ".join(sorted(f"*{e}" for e in conversion.EXT_AUDIO))
    return (
        f"Todo lo compatible ({imgs} {vid} {aud});;"
        f"Imágenes y RAW ({imgs});;"
        f"Vídeo ({vid});;"
        f"Audio ({aud});;"
        "Todos los archivos (*.*)"
    )


class _ListaArchivos(QListWidget):
    """QListWidget que acepta archivos arrastrados desde el gestor de archivos."""

    archivos_soltados = Signal(list)

    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            rutas = [u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile()]
            if rutas:
                self.archivos_soltados.emit(rutas)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)


class ConvertirPage(QWidget):
    trabajo_terminado = Signal()

    def __init__(self):
        super().__init__()
        self.worker = None
        self._formato_actual = ""
        self._ultimas_salidas = []
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
            "(CR2/CR3, NEF, ARW, RAF, RW2, ORF…). Arrastra los archivos a la lista "
            "o usa «Añadir archivos…»."
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
        self.lista = _ListaArchivos()
        self.lista.setFixedHeight(150)
        self.lista.archivos_soltados.connect(self._agregar_rutas)
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
        self.combo_formato.setFixedWidth(320)
        fila_tipo.addWidget(self.combo_formato)
        fila_tipo.addStretch()
        salida.layout_panel.addLayout(fila_tipo)

        # Ajuste rápido: deja las fotos listas para los expedientes.
        fila_preset = QHBoxLayout()
        fila_preset.setSpacing(8)
        lbl_preset = QLabel("Ajuste rápido:")
        lbl_preset.setStyleSheet("color:#8b97ad;")
        self.btn_preset_exp = QPushButton("Para expediente")
        self.btn_preset_exp.setObjectName("ghost")
        self.btn_preset_exp.setToolTip(
            "Deja las fotos como JPEG, 1600 px máximo y calidad alta:\n"
            "el formato y tamaño correctos para subir a Administrativo\n"
            "y para el reconocimiento facial de Centro de Control."
        )
        self.btn_preset_exp.clicked.connect(self._preset_expediente)
        self.btn_preset_davinci = QPushButton("Para DaVinci")
        self.btn_preset_davinci.setObjectName("ghost")
        self.btn_preset_davinci.setToolTip(
            "Deja los vídeos de celular listos para DaVinci Resolve gratuito\n"
            "(que no abre H.264/H.265 ni audio AAC): DNxHR 1080p + audio PCM\n"
            "en .mov, con frame rate constante para que el audio no se desfase.\n"
            "Ocupa mucho: ~65 GB por hora de vídeo."
        )
        self.btn_preset_davinci.clicked.connect(self._preset_davinci)
        fila_preset.addWidget(lbl_preset)
        fila_preset.addWidget(self.btn_preset_exp)
        fila_preset.addWidget(self.btn_preset_davinci)
        fila_preset.addStretch()
        salida.layout_panel.addLayout(fila_preset)

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

        self.setAcceptDrops(True)

    # -- arrastrar y soltar sobre toda la página ------------------------

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            self._agregar_rutas([u.toLocalFile() for u in e.mimeData().urls()])
            e.acceptProposedAction()

    # -- lista de archivos -----------------------------------------------

    def _añadir(self):
        rutas, _ = QFileDialog.getOpenFileNames(
            self, "Elegir archivos", "", _filtro_completo()
        )
        self._agregar_rutas(rutas)

    def _agregar_rutas(self, rutas):
        """Añade archivos a la lista (sin duplicar) y ajusta el 'Tipo' de salida
        según lo que se añadió (imágenes/RAW → Imagen, etc.)."""
        existentes = {self.lista.item(i).text() for i in range(self.lista.count())}
        nuevos = []
        for r in rutas:
            if r and os.path.isfile(r) and r not in existentes:
                self.lista.addItem(r)
                existentes.add(r)
                nuevos.append(r)
        if nuevos:
            self._autoseleccionar_tipo(nuevos)

    def _autoseleccionar_tipo(self, rutas):
        cats = {c for c in (_categoria_de(r) for r in rutas) if c}
        if len(cats) == 1:
            cat = next(iter(cats))
            if cat != self.combo_tipo.currentText():
                self.combo_tipo.setCurrentText(cat)

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

    def _preset_expediente(self):
        """Configura salida = JPEG · 1600 px · calidad alta, el formato y
        tamaño que piden los expedientes de Administrativo y el
        reconocimiento facial de Centro de Control."""
        p = imagenes.PRESET_EXPEDIENTE
        self.combo_tipo.setCurrentText("Imagen")  # dispara _recargar_formatos
        i = self.combo_formato.findText(p["formato"])
        if i >= 0:
            self.combo_formato.setCurrentIndex(i)
        j = self.combo_tam.findText(p["tamano"])
        if j >= 0:
            self.combo_tam.setCurrentIndex(j)
        self.lbl_sub.setText(
            f"Ajuste para expediente: {p['formato']} · {p['tamano']} máx."
        )

    def _preset_davinci(self):
        """Configura salida = DNxHR 1080p + PCM (.mov), que DaVinci Resolve
        gratuito sí abre en Linux."""
        self.combo_tipo.setCurrentText("Vídeo")  # dispara _recargar_formatos
        i = self.combo_formato.findText(conversion.PRESET_DAVINCI)
        if i >= 0:
            self.combo_formato.setCurrentIndex(i)
        self.lbl_sub.setText("Ajuste para DaVinci: DNxHR 1080p + audio PCM (.mov).")

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

        self._ultimas_salidas = []
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
        if ok:
            self._ultimas_salidas.append(salida)
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

        salidas = list(self._ultimas_salidas)
        carpeta = self.sel_carpeta.valor()

        if errores:
            icono = QMessageBox.Warning
            titulo = "Terminó con errores"
            det = "\n".join(f"• {a}: {m}" for a, m in errores[:5])
            texto = f"{ok} de {total} correctos.\n\n{det}"
        else:
            icono = QMessageBox.Information
            titulo = "Listo"
            texto = f"Se convirtieron {ok} de {total} archivo(s)."

        if salidas:
            if len(salidas) == 1:
                texto += f"\n\nGuardado en:\n{salidas[0]}"
            else:
                texto += f"\n\n{len(salidas)} archivos guardados en:\n{carpeta}"

        box = QMessageBox(icono, titulo, texto, QMessageBox.Ok, self)
        btn_abrir = None
        if salidas:
            btn_abrir = box.addButton("Abrir carpeta", QMessageBox.ActionRole)
            box.setDefaultButton(btn_abrir)
        box.exec()
        if btn_abrir is not None and box.clickedButton() is btn_abrir:
            self._abrir_carpeta_salida(salidas[0])

    def _abrir_carpeta_salida(self, ruta):
        """Abre el gestor de archivos en la carpeta del archivo generado."""
        carpeta = ruta if os.path.isdir(ruta) else os.path.dirname(ruta)
        if carpeta and os.path.isdir(carpeta):
            QDesktopServices.openUrl(QUrl.fromLocalFile(carpeta))

    def hay_trabajo(self):
        return self.worker is not None and self.worker.isRunning()

    def detener(self):
        if self.worker:
            self.worker.cancelar()
            self.worker.wait(3000)

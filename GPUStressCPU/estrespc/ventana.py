"""Ventana principal de GPUStressCPU."""

import csv
import datetime as dt
import os
import shutil
import threading
import time

import pyqtgraph as pg
from PySide6.QtCore import QTimer, QUrl, Signal, Qt
from PySide6.QtGui import QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSpinBox, QSplitter,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from . import AUTOR, __version__
from . import videos
from .benchmark import MEDIDAS, TERMICOS, Benchmark, historial
from .editor_fila import EditorFila
from .fila import PERFILES, Fila, borrar_fila, describir, filas_propias, guardar_fila
from .resultados import VentanaResultados, calcular, texto_informe
from .pruebas import (PruebaCPU, PruebaDisco, PruebaGPU, PruebaRAM, PruebaVideo,
                      listar_gpus)
from .sensores import MonitorNvidia, Sensores, disco_de_ruta

CARPETA_REGISTROS = os.path.expanduser("~/.local/share/estrespc/registros")
HISTORIA = 600  # puntos visibles en las gráficas (10 min a 1 Hz)

DURACIONES = [("5 minutos", 300), ("15 minutos", 900), ("30 minutos", 1800),
              ("1 hora", 3600), ("2 horas", 7200), ("Sin límite", 0)]

COLOR_ESTADO = {"lista": "#8a8f98", "corriendo": "#4aa3ff", "ok": "#3ecf6e",
                "errores": "#ff4d4f", "fallo": "#ffa940"}
TEXTO_ESTADO = {"lista": "En espera", "corriendo": "Corriendo…", "ok": "Sin errores",
                "errores": "¡ERRORES!", "fallo": "Falló"}

# (clave, nombre, unidad, color, gráfica)
SERIES = [
    ("cpu_temp", "CPU temperatura", "°C", "#ff6b6b", "temp"),
    ("gpu_temp", "GPU NVIDIA temperatura", "°C", "#51cf66", "temp"),
    ("igpu_temp", "GPU integrada temperatura", "°C", "#fcc419", "temp"),
    ("cpu_uso", "CPU uso", "%", "#ff6b6b", "uso"),
    ("gpu_uso", "GPU NVIDIA uso", "%", "#51cf66", "uso"),
    ("gpu_dec", "GPU decodificador de video", "%", "#e599f7", "uso"),
    ("gpu_enc", "GPU codificador de video", "%", "#ffa94d", "uso"),
    ("cpu_mhz", "CPU frecuencia promedio", "MHz", "#ff6b6b", "mhz"),
    ("cpu_mhz_max", "CPU frecuencia máxima", "MHz", "#ffa8a8", None),
    ("gpu_mhz", "GPU NVIDIA frecuencia", "MHz", "#51cf66", "mhz"),
    ("gpu_w", "GPU NVIDIA consumo", "W", "#51cf66", None),
    ("gpu_mem_mb", "GPU NVIDIA VRAM usada", "MB", "#51cf66", None),
    ("ram_usada_mb", "RAM usada", "MB", "#b197fc", None),
]
COLORES_NVME = ["#4dabf7", "#e599f7", "#63e6be", "#ffd43b"]


class Tarjeta(QFrame):
    """Recuadro de estado de una prueba."""

    def __init__(self, nombre):
        super().__init__()
        self.setObjectName("tarjeta")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        self.titulo = QLabel(nombre)
        self.titulo.setStyleSheet("font-weight:bold; font-size:14px")
        self.estado = QLabel()
        self.estado.setStyleSheet("font-size:13px; font-weight:bold")
        self.detalle = QLabel()
        self.detalle.setStyleSheet("color:#aab")
        for w in (self.titulo, self.estado, self.detalle):
            lay.addWidget(w)

    def mostrar(self, prueba, activa):
        estado = prueba.estado if activa else "lista"
        color = COLOR_ESTADO[estado]
        self.setStyleSheet(f"#tarjeta{{border:2px solid {color}; border-radius:8px}}")
        self.estado.setText(TEXTO_ESTADO[estado] if activa else "No seleccionada")
        self.estado.setStyleSheet(f"font-size:13px; font-weight:bold; color:{color}")
        partes = []
        if activa and prueba.estado != "lista":
            partes.append(f"Errores: {prueba.errores}")
        if activa and prueba.dato:
            partes.append(prueba.dato)
        self.detalle.setText("  ·  ".join(partes))


class Ventana(QMainWindow):
    gpus_listas = Signal(list)
    aviso_videos = Signal(str)
    videos_listos = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"GPUStressCPU {__version__}")
        ruta_icono = os.path.join(os.path.dirname(__file__), "icono.svg")
        self.setWindowIcon(QIcon(ruta_icono))
        self.resize(1400, 900)

        self.sensores = Sensores()
        self.nvidia = MonitorNvidia(self)
        self.pruebas = {p.nombre: p for p in
                        (PruebaCPU(self), PruebaRAM(self), PruebaGPU(self), PruebaVideo(self),
                         PruebaDisco(self))}
        for p in self.pruebas.values():
            p.registro.connect(self._registrar)
            p.cambio.connect(self._refrescar_tarjetas)
            p.terminada.connect(self._prueba_terminada)

        self.bench = Benchmark(self)
        self.bench.registro.connect(self._registrar)
        self.bench.paso_actual.connect(self._bench_paso)
        self.bench.terminado.connect(self._bench_terminado)

        self.fila = Fila(self)
        self.fila.registro.connect(self._registrar)
        self.fila.cambio.connect(self._refrescar_tarjetas)
        self.fila.paso.connect(self._fila_paso)
        self.fila.terminada.connect(self._finalizar)
        self.modo_fila = False

        self.activas = set()
        self.inicio = None
        self.duracion = 0
        self.motivo_paro = ""
        self.historia = {}
        self.extremos = {}
        self.muestras = []
        self.exceso = {}
        self.carpeta_corrida = None
        self.gpus = []

        self._series_nvme()
        self._construir()
        self.gpus_listas.connect(self._llenar_gpus)
        threading.Thread(target=lambda: self.gpus_listas.emit(listar_gpus()),
                         daemon=True).start()

        self.reloj = QTimer(self)
        self.reloj.timeout.connect(self._tic)
        self.reloj.start(1000)
        self._tic()

    # ------------------------------------------------------------ interfaz
    def _series_nvme(self):
        self.series = list(SERIES)
        for i, n in enumerate(self.sensores.nvme):
            color = COLORES_NVME[i % len(COLORES_NVME)]
            c = n["ctrl"]
            self.series += [
                (f"{c}_temp", f"SSD {n['modelo']} ({c}) temperatura", "°C", color, "temp"),
                (f"{c}_lee", f"SSD {c} lectura", "MB/s", color, None),
                (f"{c}_esc", f"SSD {c} escritura", "MB/s", color, None),
            ]
        for i in range(1, 5):
            self.series.append((f"vent{i}_rpm", f"Ventilador {i}", "RPM", "#adb5bd", None))

    def _construir(self):
        central = QWidget()
        raiz = QHBoxLayout(central)
        self.setCentralWidget(central)

        # --- Columna izquierda: configuración ---
        izq = QWidget()
        col = QVBoxLayout(izq)
        col.setContentsMargins(0, 0, 0, 0)

        self.g_fila = QGroupBox("Fila de tareas (varias cargas en secuencia)")
        f = QVBoxLayout(self.g_fila)
        self.fila_cb = QComboBox()
        self.fila_desc = QLabel()
        self.fila_desc.setWordWrap(True)
        self.fila_desc.setStyleSheet("color:#aab")
        botones = QHBoxLayout()
        b_editar = QPushButton("Editar / copiar…")
        b_editar.clicked.connect(lambda: self._fila_editar(False))
        b_nueva = QPushButton("Nueva…")
        b_nueva.clicked.connect(lambda: self._fila_editar(True))
        self.b_fila_borrar = QPushButton("Borrar")
        self.b_fila_borrar.clicked.connect(self._fila_borrar)
        for b in (b_editar, b_nueva, self.b_fila_borrar):
            botones.addWidget(b)
        f.addWidget(self.fila_cb)
        f.addWidget(self.fila_desc)
        f.addLayout(botones)
        self.fila_cb.currentIndexChanged.connect(self._fila_mostrar)
        self._fila_llenar()

        self.g_cpu = QGroupBox("CPU")
        f = QFormLayout(self.g_cpu)
        self.cpu_hilos = QSpinBox(minimum=1, maximum=self.sensores.cpus,
                                  value=self.sensores.cpus)
        self.cpu_metodo = QComboBox()
        self.cpu_metodo.addItems(PruebaCPU.METODOS)
        f.addRow("Hilos:", self.cpu_hilos)
        f.addRow("Tipo de carga:", self.cpu_metodo)

        self.g_ram = QGroupBox("Memoria RAM")
        f = QFormLayout(self.g_ram)
        self.ram_pct = QSpinBox(minimum=10, maximum=90, value=70, suffix=" % de la libre")
        self.ram_hilos = QSpinBox(minimum=1, maximum=self.sensores.cpus, value=4)
        self.ram_info = QLabel()
        self.ram_info.setStyleSheet("color:#aab")
        f.addRow("Memoria a probar:", self.ram_pct)
        f.addRow("Hilos:", self.ram_hilos)
        f.addRow(self.ram_info)
        self.ram_pct.valueChanged.connect(self._actualizar_ram_info)

        self.g_gpu = QGroupBox("GPU (OpenCL)")
        f = QFormLayout(self.g_gpu)
        self.gpu_disp = QComboBox()
        self.gpu_disp.addItem("Buscando GPUs…")
        self.gpu_mem = QSpinBox(minimum=10, maximum=90, value=70, suffix=" % de la VRAM")
        f.addRow("Tarjeta:", self.gpu_disp)
        f.addRow("VRAM a usar:", self.gpu_mem)

        self.g_video = QGroupBox("Video 4K (motor de video de la GPU)")
        f = QFormLayout(self.g_video)
        self.video_flujos = QSpinBox(minimum=1, maximum=12, value=4)
        self.video_flujos.setToolTip("Cuántos videos 4K se decodifican a la vez")
        self.video_recodificar = QCheckBox("Recodificar también (NVENC)")
        self.video_recodificar.setToolTip("Además de decodificar, vuelve a comprimir cada "
                                          "video: carga el codificador y más la GPU")
        self.video_mostrar = QCheckBox("Mostrar un video en ventana")
        self.video_info = QLabel()
        self.video_info.setStyleSheet("color:#aab")
        self.video_info.setWordWrap(True)
        self.b_generar = QPushButton("Generar videos 4K de prueba (~1.5 min)")
        self.b_generar.setToolTip("H.264, HEVC 10 bits y AV1 hechos en tu equipo: "
                                  "sin derechos de autor de nadie")
        self.b_generar.clicked.connect(self._generar_videos)
        self.b_descargar = QPushButton(f"Descargar {videos.DESCARGAS[0]['nombre']}")
        self.b_descargar.setToolTip(videos.DESCARGAS[0]["credito"])
        self.b_descargar.clicked.connect(self._descargar_video)
        b_carpeta = QPushButton("Abrir carpeta de videos")
        b_carpeta.setToolTip("Puedes poner aquí tus propios videos 4K")
        b_carpeta.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(videos.CARPETA_VIDEOS)))
        f.addRow("Videos a la vez:", self.video_flujos)
        f.addRow(self.video_recodificar)
        f.addRow(self.video_mostrar)
        f.addRow(self.video_info)
        f.addRow(self.b_generar)
        f.addRow(self.b_descargar)
        f.addRow(b_carpeta)
        self.aviso_videos.connect(lambda t: (self._registrar("Videos", t),
                                             self.statusBar().showMessage(t, 8000)))
        self.videos_listos.connect(self._actualizar_video_info)

        self.g_disco = QGroupBox("Disco")
        f = QFormLayout(self.g_disco)
        fila = QHBoxLayout()
        self.disco_carpeta = QComboBox()
        self.disco_carpeta.setEditable(True)
        for ruta in self._carpetas_disco():
            self.disco_carpeta.addItem(ruta)
        boton = QPushButton("…")
        boton.setFixedWidth(32)
        boton.clicked.connect(self._elegir_carpeta)
        fila.addWidget(self.disco_carpeta, 1)
        fila.addWidget(boton)
        self.disco_mb = QSpinBox(minimum=256, maximum=200_000, value=4096,
                                 singleStep=1024, suffix=" MB")
        self.disco_info = QLabel()
        self.disco_info.setStyleSheet("color:#aab")
        self.disco_info.setWordWrap(True)
        f.addRow("Carpeta:", fila)
        f.addRow("Tamaño de prueba:", self.disco_mb)
        f.addRow(self.disco_info)
        self.disco_carpeta.currentTextChanged.connect(self._actualizar_disco_info)

        self.g_fila.setCheckable(True)
        self.g_fila.setChecked(False)
        col.addWidget(self.g_fila)
        for g in (self.g_cpu, self.g_ram, self.g_gpu, self.g_video, self.g_disco):
            g.setCheckable(True)
            col.addWidget(g)
            # Fila y pruebas sueltas se excluyen: marcar una desmarca la otra.
            g.toggled.connect(lambda si: si and self.g_fila.setChecked(False))
        self.g_fila.toggled.connect(lambda si: si and [
            g.setChecked(False) for g in (self.g_cpu, self.g_ram, self.g_gpu, self.g_video, self.g_disco)])
        self.g_gpu.setChecked(False)
        self.g_video.setChecked(False)
        self.g_disco.setChecked(False)
        self.g_ram.setChecked(False)

        g = QGroupBox("Duración y protección")
        f = QFormLayout(g)
        self.duracion_cb = QComboBox()
        for texto, seg in DURACIONES:
            self.duracion_cb.addItem(texto, seg)
        self.duracion_cb.setCurrentIndex(1)
        self.lim_cpu = QSpinBox(minimum=60, maximum=105, value=95, suffix=" °C")
        self.lim_gpu = QSpinBox(minimum=60, maximum=95, value=87, suffix=" °C")
        self.lim_nvme = QSpinBox(minimum=50, maximum=85, value=75, suffix=" °C")
        self.vigilar_gpu = QCheckBox("Vigilar la GPU NVIDIA aunque no se pruebe")
        self.vigilar_gpu.setToolTip("Consultar la GPU la mantiene despierta y gasta más batería")
        self.vigilar_gpu.setEnabled(MonitorNvidia.disponible())
        f.addRow("Duración:", self.duracion_cb)
        f.addRow("Parar si CPU pasa de:", self.lim_cpu)
        f.addRow("Parar si GPU pasa de:", self.lim_gpu)
        f.addRow("Parar si SSD pasa de:", self.lim_nvme)
        f.addRow(self.vigilar_gpu)
        col.addWidget(g)

        self.b_iniciar = QPushButton("▶  Iniciar prueba")
        self.b_iniciar.setMinimumHeight(44)
        self.b_iniciar.setStyleSheet("font-size:15px; font-weight:bold")
        self.b_iniciar.clicked.connect(self.iniciar)
        self.b_detener = QPushButton("■  Detener")
        self.b_detener.setMinimumHeight(44)
        self.b_detener.setStyleSheet("font-size:15px; font-weight:bold")
        self.b_detener.setEnabled(False)
        self.b_detener.clicked.connect(lambda: self.detener("Detenida por el usuario"))
        b_registros = QPushButton("Abrir carpeta de registros")
        b_registros.clicked.connect(self._abrir_registros)
        col.addWidget(self.b_iniciar)
        col.addWidget(self.b_detener)
        col.addWidget(b_registros)
        col.addStretch(1)

        desplazable = QScrollArea()
        desplazable.setWidget(izq)
        desplazable.setWidgetResizable(True)
        desplazable.setFixedWidth(390)
        desplazable.setFrameShape(QFrame.NoFrame)
        raiz.addWidget(desplazable)

        # --- Columna derecha: estado, gráficas, sensores, registro ---
        der = QVBoxLayout()
        raiz.addLayout(der, 1)

        cabecera = QHBoxLayout()
        self.lbl_tiempo = QLabel("00:00:00")
        self.lbl_tiempo.setFont(QFont("monospace", 26, QFont.Bold))
        self.lbl_general = QLabel("Listo para probar")
        self.lbl_general.setStyleSheet("font-size:18px; font-weight:bold")
        self.lbl_cargador = QLabel()
        cabecera.addWidget(self.lbl_tiempo)
        cabecera.addSpacing(20)
        cabecera.addWidget(self.lbl_general, 1)
        cabecera.addWidget(self.lbl_cargador)
        der.addLayout(cabecera)

        tarjetas = QGridLayout()
        self.tarjetas = {}
        for i, nombre in enumerate(self.pruebas):
            t = Tarjeta({"RAM": "Memoria RAM", "Video": "Video 4K"}.get(nombre, nombre))
            self.tarjetas[nombre] = t
            tarjetas.addWidget(t, 0, i)
        der.addLayout(tarjetas)

        pg.setConfigOptions(antialias=True, background="#1b1e24", foreground="#c8ccd4")
        self.graficas = {}
        self.curvas = {}
        pestanas = QTabWidget()
        cont = pg.GraphicsLayoutWidget()
        for i, (clave, titulo, unidad) in enumerate(
                [("temp", "Temperaturas", "°C"), ("uso", "Uso", "%"),
                 ("mhz", "Frecuencias", "MHz")]):
            p = cont.addPlot(row=i, col=0, title=titulo)
            p.setLabel("left", unidad)
            p.showGrid(x=True, y=True, alpha=0.2)
            p.addLegend(offset=(5, 5), labelTextSize="8pt", brush=pg.mkBrush(27, 30, 36, 210))
            p.setLabel("bottom", "segundos")
            p.setMouseEnabled(x=False, y=False)
            p.hideButtons()
            if clave == "uso":
                p.setYRange(0, 100)
            self.graficas[clave] = p
        for clave, nombre, _u, color, graf in self.series:
            if graf:
                corto = nombre.replace(" temperatura", "").replace(" frecuencia", "")
                self.curvas[clave] = self.graficas[graf].plot(
                    [], [], pen=pg.mkPen(color, width=2), name=corto)
        pestanas.addTab(cont, "Gráficas")

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Sensor", "Actual", "Mínimo", "Máximo"])
        self.tabla.verticalHeader().hide()
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.filas_tabla = {}
        pestanas.addTab(self.tabla, "Sensores")
        pestanas.addTab(self._construir_benchmark(), "Benchmark")

        self.log = QPlainTextEdit(readOnly=True)
        self.log.setFont(QFont("monospace", 9))
        self.log.setMaximumBlockCount(5000)
        separador = QSplitter(Qt.Vertical)
        separador.addWidget(pestanas)
        separador.addWidget(self.log)
        separador.setSizes([650, 200])
        der.addWidget(separador, 1)

        pie = QLabel(f"GPUStressCPU v{__version__}  ·  {AUTOR}")
        pie.setStyleSheet("color:#8a8f98")
        self.statusBar().addPermanentWidget(pie)

        self._actualizar_ram_info()
        self._actualizar_disco_info()
        self._actualizar_video_info()
        self._refrescar_tarjetas()

    def _construir_benchmark(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        expl = QLabel("Mide el rendimiento con una carga fija (~3 min) y lo guarda para comparar: "
                      "el mismo equipo antes y después de un mantenimiento, o contra otro equipo. "
                      "Hazlo siempre con cargador, el mismo perfil de energía y el equipo en reposo.")
        expl.setWordWrap(True)
        expl.setStyleSheet("color:#aab")
        lay.addWidget(expl)

        fila = QHBoxLayout()
        self.bench_nota = QLineEdit(placeholderText="Nota (p. ej. «antes de cambiar la pasta»)")
        self.bench_gpu = QCheckBox("GPU")
        self.bench_video = QCheckBox("Video 4K")
        self.bench_disco = QCheckBox("Disco")
        for c in (self.bench_gpu, self.bench_video, self.bench_disco):
            c.setChecked(True)
        self.bench_disco.setToolTip("Usa la carpeta elegida en «Disco» (escribe 2 GB y los borra)")
        self.b_bench = QPushButton("▶  Correr benchmark")
        self.b_bench.setStyleSheet("font-weight:bold")
        self.b_bench.clicked.connect(self._bench_iniciar)
        self.b_bench_cancelar = QPushButton("■  Cancelar")
        self.b_bench_cancelar.setEnabled(False)
        self.b_bench_cancelar.clicked.connect(self.bench.cancelar)
        fila.addWidget(self.bench_nota, 1)
        for x in (self.bench_gpu, self.bench_video, self.bench_disco, self.b_bench,
                  self.b_bench_cancelar):
            fila.addWidget(x)
        lay.addLayout(fila)

        self.bench_barra = QProgressBar()
        self.bench_barra.setFormat("En espera")
        self.bench_barra.setValue(0)
        lay.addWidget(self.bench_barra)

        fila = QHBoxLayout()
        self.bench_a = QComboBox()
        self.bench_b = QComboBox()
        self.bench_a.currentIndexChanged.connect(self._bench_mostrar)
        self.bench_b.currentIndexChanged.connect(self._bench_mostrar)
        fila.addWidget(QLabel("Corrida:"))
        fila.addWidget(self.bench_a, 1)
        fila.addWidget(QLabel("Comparar con:"))
        fila.addWidget(self.bench_b, 1)
        lay.addLayout(fila)

        self.bench_tabla = QTableWidget(0, 4)
        self.bench_tabla.setHorizontalHeaderLabels(["Medida", "Corrida", "Comparada", "Cambio"])
        self.bench_tabla.verticalHeader().hide()
        self.bench_tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.bench_tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.bench_filas = [(k, n, u, mejor, None) for k, n, u, mejor in MEDIDAS]
        for paso, etiqueta in (("cpun", "durante CPU todos los hilos"), ("gpu", "durante GPU")):
            for k, n, u, mejor in TERMICOS:
                if k.startswith(paso[:3]):
                    self.bench_filas.append((f"{paso}:{k}", f"{n} ({etiqueta})", u, mejor, paso))
        self.bench_tabla.setRowCount(len(self.bench_filas))
        for i, (_k, n, _u, _m, _p) in enumerate(self.bench_filas):
            self.bench_tabla.setItem(i, 0, QTableWidgetItem(n))
            for c in (1, 2, 3):
                it = QTableWidgetItem()
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.bench_tabla.setItem(i, c, it)
        lay.addWidget(self.bench_tabla, 1)
        self.bench_info = QLabel()
        self.bench_info.setWordWrap(True)
        self.bench_info.setStyleSheet("color:#aab")
        lay.addWidget(self.bench_info)
        self._bench_llenar_historial()
        return w

    # ------------------------------------------------------------ benchmark
    @staticmethod
    def _bench_valor(corrida, clave):
        if not corrida:
            return None
        if ":" in clave:
            paso, k = clave.split(":")
            return corrida.get("termicos", {}).get(paso, {}).get(k)
        return corrida.get("resultados", {}).get(clave)

    @staticmethod
    def _bench_etiqueta(c):
        fecha = dt.datetime.fromisoformat(c["fecha"]).strftime("%Y-%m-%d %H:%M")
        extra = "" if c.get("completo", True) else " (incompleta)"
        if c.get("cargador") is False:
            extra += " (batería)"
        return f"{fecha} · {c['nota']}{extra}" if c.get("nota") else f"{fecha}{extra}"

    def _bench_llenar_historial(self):
        self._bench_hist = historial()
        # Por defecto: la corrida más nueva contra la anterior («(nada)» es el índice 0 de la segunda lista).
        for combo, defecto in ((self.bench_a, 0), (self.bench_b, 2 if len(self._bench_hist) > 1 else 0)):
            combo.blockSignals(True)
            combo.clear()
            if combo is self.bench_b:
                combo.addItem("(nada)", None)
            for i, c in enumerate(self._bench_hist):
                combo.addItem(self._bench_etiqueta(c), i)
            combo.setCurrentIndex(min(defecto, combo.count() - 1))
            combo.blockSignals(False)
        self._bench_mostrar()

    def _bench_mostrar(self, *_):
        a = self._bench_hist[self.bench_a.currentData()] if self.bench_a.currentData() is not None else None
        b = self._bench_hist[self.bench_b.currentData()] if self.bench_b.currentData() is not None else None
        for i, (clave, _n, unidad, mas_es_mejor, _p) in enumerate(self.bench_filas):
            va, vb = self._bench_valor(a, clave), self._bench_valor(b, clave)
            decimales = {"TFLOPS": 2, "GB/s": 1}.get(unidad, 0)
            fmt = (lambda v: "" if v is None else f"{v:,.{decimales}f} {unidad}")
            self.bench_tabla.item(i, 1).setText(fmt(va))
            self.bench_tabla.item(i, 2).setText(fmt(vb))
            cambio = self.bench_tabla.item(i, 3)
            if va is not None and vb:
                pct = (va - vb) / vb * 100
                bueno = pct >= 0 if mas_es_mejor else pct <= 0
                cambio.setText(f"{pct:+.1f} %")
                cambio.setForeground(pg.mkColor("#3ecf6e" if abs(pct) < 1 or bueno else "#ff6b6b")
                                     if abs(pct) >= 1 else pg.mkColor("#8a8f98"))
            else:
                cambio.setText("")
        partes = []
        for etiqueta, c in (("Corrida", a), ("Comparada", b)):
            if c:
                e = c.get("equipo", {})
                partes.append(f"{etiqueta}: {e.get('cpu', '')} · {e.get('gpu', '') or 'sin NVIDIA'} · "
                              f"perfil {e.get('perfil_energia') or '?'} · kernel {e.get('kernel', '')}")
        self.bench_info.setText("\n".join(partes))

    def _bench_iniciar(self):
        if self.inicio is not None:
            return
        d = self.sensores.leer()
        if d.get("cargador") is False and QMessageBox.question(
                self, "Sin cargador",
                "El equipo está usando la batería: el resultado saldrá más bajo y no se podrá "
                "comparar con uno hecho con cargador.\n\n¿Continuar de todos modos?"
        ) != QMessageBox.Yes:
            return
        if not shutil.which("7z"):
            QMessageBox.warning(self, "Benchmark", "Falta 7-Zip. Instálalo con:\n\nsudo pacman -S 7zip")
            return
        gpu = (self.gpu_disp.currentData() or "") if self.bench_gpu.isChecked() and self.gpus else None
        lista_videos = videos.lista() if self.bench_video.isChecked() else []
        if self.bench_video.isChecked() and not lista_videos:
            self._registrar("Benchmark", "Sin videos 4K: se omite esa prueba (usa «Generar videos 4K»)")
        carpeta = None
        if self.bench_disco.isChecked():
            carpeta = self.disco_carpeta.currentText()
            try:
                if shutil.disk_usage(carpeta).free < (4 << 30) or not os.access(carpeta, os.W_OK):
                    raise OSError
            except OSError:
                self._registrar("Benchmark", "La carpeta de disco no sirve (no existe, sin permiso "
                                "o <4 GB libres): se omite esa prueba")
                carpeta = None
        self.log.clear()
        self.exceso = {}
        self.motivo_paro = ""
        if gpu is not None or lista_videos:
            self.nvidia.iniciar()
        self._bloquear_bench(True)
        self.bench.iniciar(gpu, lista_videos, carpeta, self.bench_nota.text(), d.get("cargador"))

    def _bench_paso(self, nombre, n, total):
        self.bench_barra.setMaximum(total)
        self.bench_barra.setValue(n - 1)
        self.bench_barra.setFormat(f"{n}/{total} · {nombre}…")
        self.lbl_general.setText(f"Benchmark: {nombre}")
        self.lbl_general.setStyleSheet("font-size:18px; font-weight:bold; color:#4aa3ff")

    def _bench_terminado(self, corrida):
        if not self.vigilar_gpu.isChecked():
            self.nvidia.detener()
        self._bloquear_bench(False)
        self.bench_barra.setValue(self.bench_barra.maximum())
        if corrida.get("completo"):
            texto, color = "Benchmark terminado", "#3ecf6e"
        else:
            texto, color = f"Benchmark detenido{': ' + self.motivo_paro if self.motivo_paro else ''}", "#ffa940"
        self.bench_barra.setFormat(texto)
        self.lbl_general.setText(texto)
        self.lbl_general.setStyleSheet(f"font-size:18px; font-weight:bold; color:{color}")
        if corrida.get("_ruta"):
            self._registrar("Benchmark", f"Guardado en {corrida['_ruta']}")
        self._bench_llenar_historial()

    def _bloquear_bench(self, corriendo):
        for x in (self.g_fila, self.g_cpu, self.g_ram, self.g_gpu, self.g_video, self.g_disco, self.duracion_cb,
                  self.b_iniciar, self.b_bench, self.bench_nota, self.bench_gpu, self.bench_video,
                  self.bench_disco):
            x.setEnabled(not corriendo)
        self.b_bench_cancelar.setEnabled(corriendo)

    # ------------------------------------------------------------ fila de tareas
    def _fila_todas(self):
        return {**PERFILES, **filas_propias()}

    def _fila_llenar(self, elegir=None):
        actual = elegir or self.fila_cb.currentText()
        self.fila_cb.blockSignals(True)
        self.fila_cb.clear()
        for nombre in PERFILES:
            self.fila_cb.addItem(nombre)
        for nombre in filas_propias():
            self.fila_cb.addItem(nombre)
        i = self.fila_cb.findText(actual)
        self.fila_cb.setCurrentIndex(max(0, i))
        self.fila_cb.blockSignals(False)
        self._fila_mostrar()

    def _fila_mostrar(self, *_):
        nombre = self.fila_cb.currentText()
        pasos = self._fila_todas().get(nombre, [])
        self.fila_desc.setText(describir(pasos) if pasos else "")
        self.b_fila_borrar.setEnabled(nombre not in PERFILES)

    def _fila_editar(self, nueva):
        nombre = "" if nueva else self.fila_cb.currentText()
        pasos = [] if nueva else self._fila_todas().get(nombre, [])
        dlg = EditorFila(nombre or "Mi fila", pasos, self)
        if dlg.exec():
            nuevo = dlg.nombre.text().strip()
            guardar_fila(nuevo, dlg.pasos())
            self._fila_llenar(nuevo)
            self.g_fila.setChecked(True)

    def _fila_borrar(self):
        nombre = self.fila_cb.currentText()
        if nombre in PERFILES:
            return
        if QMessageBox.question(self, "Fila de tareas", f"¿Borrar la fila «{nombre}»?") == QMessageBox.Yes:
            borrar_fila(nombre)
            self._fila_llenar()

    def _fila_paso(self, n, total, vuelta, nombre):
        self.lbl_general.setText(f"Fila · vuelta {vuelta} · paso {n}/{total}: {nombre}")
        self.lbl_general.setStyleSheet("font-size:18px; font-weight:bold; color:#4aa3ff")

    def _fuente(self):
        """De dónde leen las tarjetas y el informe: pruebas sueltas o los componentes de la fila."""
        return self.fila.componentes if self.modo_fila else self.pruebas

    def _carpetas_disco(self):
        """Carpeta personal más puntos de montaje en SSD donde se pueda escribir."""
        rutas = [os.path.expanduser("~")]
        vistos = {disco_de_ruta(rutas[0])}
        for linea in open("/proc/mounts"):
            src, punto = linea.split()[:2]
            if not src.startswith("/dev/") or punto.startswith(("/boot", "/efi")):
                continue
            ctrl = disco_de_ruta(punto)
            if ctrl and ctrl not in vistos and os.access(punto, os.W_OK):
                vistos.add(ctrl)
                rutas.append(punto)
        return rutas

    def _elegir_carpeta(self):
        ruta = QFileDialog.getExistingDirectory(self, "Carpeta para la prueba de disco",
                                                self.disco_carpeta.currentText())
        if ruta:
            self.disco_carpeta.setCurrentText(ruta)

    def _actualizar_ram_info(self):
        d = self.sensores.leer()
        libre = d.get("ram_disponible_mb", 0)
        self.ram_info.setText(f"≈ {libre * self.ram_pct.value() / 100 / 1024:.1f} GB "
                              f"de {libre / 1024:.1f} GB libres")

    def _actualizar_disco_info(self):
        ruta = self.disco_carpeta.currentText()
        try:
            libre = shutil.disk_usage(ruta).free / 2**30
        except OSError:
            self.disco_info.setText("La carpeta no existe")
            return
        ctrl = disco_de_ruta(ruta)
        modelo = next((n["modelo"] for n in self.sensores.nvme if n["ctrl"] == ctrl), None)
        self.disco_info.setText(f"{modelo + ' · ' if modelo else ''}{libre:.0f} GB libres. "
                                "Los archivos de prueba se borran al terminar.")

    def _actualizar_video_info(self):
        lista = videos.lista()
        if lista:
            nombres = ", ".join(os.path.basename(v) for v in lista)
            self.video_info.setText(f"{len(lista)} video(s): {nombres}")
        else:
            self.video_info.setText("No hay videos todavía: genéralos o descárgalos.")
        ocupado = getattr(self, "_videos_ocupado", False)
        self.b_generar.setEnabled(not ocupado)
        self.b_descargar.setEnabled(not ocupado and not os.path.exists(
            os.path.join(videos.CARPETA_VIDEOS, videos.DESCARGAS[0]["archivo"])))

    def _en_fondo(self, tarea):
        """Corre la tarea de videos en un hilo, avisando por la barra de estado."""
        self._videos_ocupado = True
        self._actualizar_video_info()

        def correr():
            try:
                tarea(self.aviso_videos.emit)
            except Exception as e:  # red caída, disco lleno…
                self.aviso_videos.emit(f"Error: {e}")
            self._videos_ocupado = False
            self.videos_listos.emit()
        threading.Thread(target=correr, daemon=True).start()

    def _generar_videos(self):
        self._en_fondo(videos.generar)

    def _descargar_video(self):
        self._en_fondo(lambda avisar: videos.descargar(0, avisar))

    def _llenar_gpus(self, lista):
        self.gpus = lista
        self.gpu_disp.clear()
        for g in lista:
            self.gpu_disp.addItem(f"{g['nombre']} ({g['memoria'] >> 20} MB)", g["id"])
        if not lista:
            self.gpu_disp.addItem("No hay GPU OpenCL disponible")
            self.g_gpu.setChecked(False)
            self.g_gpu.setEnabled(False)

    # ------------------------------------------------------------ pruebas
    def _seleccion(self):
        return {n for n, g in (("CPU", self.g_cpu), ("RAM", self.g_ram),
                               ("GPU", self.g_gpu), ("Video", self.g_video),
                               ("Disco", self.g_disco))
                if g.isChecked()}

    def iniciar(self):
        if self.g_fila.isChecked():
            self._iniciar_fila()
            return
        self.modo_fila = False
        activas = self._seleccion()
        if not activas:
            QMessageBox.information(self, "GPUStressCPU", "Selecciona al menos una prueba.")
            return
        self.log.clear()
        d = self.sensores.leer()
        if d.get("cargador") is False and QMessageBox.question(
                self, "Sin cargador",
                "El equipo está usando la batería. Con carga máxima la batería se "
                "acaba rápido y el rendimiento baja.\n\n¿Continuar de todos modos?"
        ) != QMessageBox.Yes:
            return

        if "Video" in activas and not videos.lista():
            QMessageBox.warning(self, "Video 4K", "No hay videos: usa «Generar videos 4K "
                                "de prueba» o descarga uno primero.")
            return
        if "Disco" in activas:
            ruta = self.disco_carpeta.currentText()
            try:
                libre = shutil.disk_usage(ruta).free >> 20
            except OSError:
                QMessageBox.warning(self, "Disco", "La carpeta de prueba no existe.")
                return
            if not os.access(ruta, os.W_OK):
                QMessageBox.warning(self, "Disco", "No se puede escribir en esa carpeta.")
                return
            if libre < self.disco_mb.value() + 2048:
                QMessageBox.warning(self, "Disco", f"Solo hay {libre} MB libres; "
                                    "deja al menos 2 GB de margen.")
                return

        p = self.pruebas
        p["CPU"].hilos = self.cpu_hilos.value()
        p["CPU"].metodo = PruebaCPU.METODOS[self.cpu_metodo.currentText()]
        p["RAM"].megas = int(d["ram_disponible_mb"] * self.ram_pct.value() / 100)
        p["RAM"].hilos = self.ram_hilos.value()
        p["GPU"].dispositivo = self.gpu_disp.currentData() or ""
        p["GPU"].memoria = self.gpu_mem.value() / 100
        vram = next((g["memoria"] >> 20 for g in self.gpus
                     if g["id"] == p["GPU"].dispositivo), 0)
        if "Video" in activas and vram:
            # ¿Caben los videos en la VRAM? (medido en RTX 3060: ~650 MB por video decodificando,
            # ~1000 MB recodificando, ~1.6 GB la ventana de mpv, ~1.2 GB del escritorio, y la
            # prueba GPU necesita al menos el 10 %.)
            por_flujo = 1000 if self.video_recodificar.isChecked() else 650
            fijo = 1200 + (1600 if self.video_mostrar.isChecked() else 0) + \
                (vram // 10 if "GPU" in activas else 0)
            caben = max(0, (vram - fijo) // por_flujo)
            if self.video_flujos.value() > caben:
                if caben == 0:
                    QMessageBox.warning(self, "Video 4K", f"Con esta combinación no cabe ni un video en "
                                        f"los {vram} MB de VRAM. Quita «Mostrar un video» o «Recodificar».")
                    return
                if QMessageBox.question(
                        self, "Video 4K",
                        f"{self.video_flujos.value()} videos a la vez no caben en los {vram} MB de VRAM "
                        f"con esta combinación (recodificar / mostrar / prueba GPU).\n\n"
                        f"¿Bajar a {caben} video(s)?") != QMessageBox.Yes:
                    return
                self.video_flujos.setValue(caben)
                p["Video"].flujos = caben
        if {"GPU", "Video"} <= activas and vram:
            # Cada video 4K necesita su VRAM (medido en RTX 3060: ~600 MB
            # decodificando, ~1000 MB recodificando); más ~1.2 GB del escritorio.
            por_flujo = 1000 if self.video_recodificar.isChecked() else 650
            libre = vram - 1200 - self.video_flujos.value() * por_flujo
            if self.video_mostrar.isChecked():
                libre -= 1600  # la ventana de mpv reserva ~1.6 GB en la NVIDIA
            fraccion = max(0.1, min(p["GPU"].memoria, libre / vram))
            if fraccion < p["GPU"].memoria:
                p["GPU"].memoria = fraccion
                self._registrar("GPUStressCPU", f"Con Video 4K activo, la prueba GPU usa "
                                f"{fraccion:.0%} de la VRAM para dejar lugar a los videos")
        p["Disco"].carpeta = self.disco_carpeta.currentText()
        p["Disco"].megas = self.disco_mb.value()
        p["Video"].videos = videos.lista()
        p["Video"].flujos = self.video_flujos.value()
        p["Video"].recodificar = self.video_recodificar.isChecked()
        p["Video"].mostrar = self.video_mostrar.isChecked()

        self.activas = activas
        self.duracion = self.duracion_cb.currentData()
        self.motivo_paro = ""
        self.exceso = {}
        self.muestras = []
        self.historia = {}
        self.extremos = {}
        self.inicio = time.monotonic()
        self.hora_inicio = dt.datetime.now()
        self.carpeta_corrida = os.path.join(
            CARPETA_REGISTROS, self.hora_inicio.strftime("%Y-%m-%d_%H%M%S"))
        os.makedirs(self.carpeta_corrida, exist_ok=True)

        self._registrar("GPUStressCPU", f"Inicio: {', '.join(sorted(activas))} · "
                        f"{self.duracion_cb.currentText()}")
        if activas & {"GPU", "Video"} or self.vigilar_gpu.isChecked():
            self.nvidia.iniciar()
        for nombre in sorted(activas):
            p[nombre].iniciar()
        self._bloquear(True)
        self.lbl_general.setText("Probando…")
        self.lbl_general.setStyleSheet("font-size:18px; font-weight:bold; color:#4aa3ff")
        self._refrescar_tarjetas()

    def _iniciar_fila(self):
        pasos = self._fila_todas().get(self.fila_cb.currentText())
        if not pasos:
            QMessageBox.information(self, "GPUStressCPU", "Elige una fila de tareas.")
            return
        d = self.sensores.leer()
        if d.get("cargador") is False and QMessageBox.question(
                self, "Sin cargador", "El equipo está usando la batería. ¿Continuar de todos modos?"
        ) != QMessageBox.Yes:
            return
        usa_gpu = any(p["gpu"] not in ("nada", "reposo") for p in pasos)
        if usa_gpu and not self.gpus:
            QMessageBox.warning(self, "GPUStressCPU", "Esta fila usa la GPU pero no se encontró ninguna "
                                "con OpenCL (espera a que termine «Buscando GPUs…»).")
            return
        self.log.clear()
        self.modo_fila = True
        self.duracion = self.duracion_cb.currentData()
        self.motivo_paro = ""
        self.exceso, self.muestras, self.historia, self.extremos = {}, [], {}, {}
        self.inicio = time.monotonic()
        self.hora_inicio = dt.datetime.now()
        self.carpeta_corrida = os.path.join(
            CARPETA_REGISTROS, self.hora_inicio.strftime("%Y-%m-%d_%H%M%S"))
        os.makedirs(self.carpeta_corrida, exist_ok=True)
        self.nombre_fila = self.fila_cb.currentText()
        self._registrar("GPUStressCPU", f"Inicio de la fila «{self.nombre_fila}» · {self.duracion_cb.currentText()}")
        if usa_gpu or self.vigilar_gpu.isChecked():
            self.nvidia.iniciar()
        self.fila.iniciar(pasos, self.gpu_disp.currentData() or "", videos.lista())
        self.activas = self.fila.usa()
        self._bloquear(True)
        self._refrescar_tarjetas()

    def detener(self, motivo):
        if not self.motivo_paro:
            self.motivo_paro = motivo
            self._registrar("GPUStressCPU", motivo)
        if self.modo_fila:
            self.fila.detener()
        else:
            for n in self.activas:
                self.pruebas[n].detener()
        self.bench.cancelar()
        self.b_detener.setEnabled(False)

    def _prueba_terminada(self, nombre):
        prueba = self.pruebas[nombre]
        if prueba.estado in ("errores", "fallo") and not self.motivo_paro:
            self._registrar("GPUStressCPU", f"La prueba de {nombre} terminó: "
                            f"{TEXTO_ESTADO[prueba.estado]}")
        if any(self.pruebas[n].corriendo() for n in self.activas):
            return
        self._finalizar()

    def _finalizar(self):
        if self.inicio is None:
            return
        transcurrido = time.monotonic() - self.inicio
        self.inicio = None
        if not self.vigilar_gpu.isChecked():
            self.nvidia.detener()
        self._bloquear(False)
        malas = [n for n in self.activas if self._fuente()[n].estado != "ok"]
        if malas:
            texto, color = f"PROBLEMAS en: {', '.join(sorted(malas))}", "#ff4d4f"
        elif self.motivo_paro.startswith("Temperatura"):
            texto, color = "Detenida por temperatura", "#ffa940"
        else:
            texto, color = "Terminó SIN ERRORES", "#3ecf6e"
        self.lbl_general.setText(texto)
        self.lbl_general.setStyleSheet(f"font-size:18px; font-weight:bold; color:{color}")
        estados = {n: (self._fuente()[n].estado, self._fuente()[n].errores) for n in self.activas}
        self._calificacion = calcular(self.muestras, estados, self.motivo_paro, transcurrido)
        self._guardar_informe(transcurrido, texto)
        self._refrescar_tarjetas()
        que = f"fila «{self.nombre_fila}»" if self.modo_fila else ", ".join(sorted(self.activas))
        self._ventana_resultados = VentanaResultados(
            self._calificacion, f"{texto} · {que}" + (f" · {self.motivo_paro}" if self.motivo_paro else ""),
            self.carpeta_corrida, self)
        self._ventana_resultados.show()

    def _bloquear(self, corriendo):
        for w in (self.g_fila, self.g_cpu, self.g_ram, self.g_gpu, self.g_video, self.g_disco,
                  self.duracion_cb):
            w.setEnabled(not corriendo)
        self.b_iniciar.setEnabled(not corriendo)
        self.b_detener.setEnabled(corriendo)
        self.b_bench.setEnabled(not corriendo)

    # ------------------------------------------------------------ monitoreo
    def _tic(self):
        d = self.sensores.leer()
        if self.vigilar_gpu.isChecked() and not self.nvidia.activo():
            self.nvidia.iniciar()
        elif not self.vigilar_gpu.isChecked() and self.nvidia.activo() and \
                not (self.inicio and self.activas & {"GPU", "Video"}) and not self.bench.corriendo():
            self.nvidia.detener()
        d.update(self.nvidia.valores)

        cargador = d.get("cargador")
        self.lbl_cargador.setText({True: "🔌 Con cargador", False: "🔋 Con batería",
                                   None: ""}[cargador])

        ahora = time.monotonic()
        t = (ahora - self.inicio) if self.inicio else 0
        for clave, _n, _u, _c, _g in self.series:
            v = d.get(clave)
            if v is None:
                continue
            h = self.historia.setdefault(clave, ([], []))
            h[0].append(ahora)
            h[1].append(v)
            if len(h[0]) > HISTORIA:
                del h[0][0], h[1][0]
            if self.inicio:
                mn, mx = self.extremos.get(clave, (v, v))
                self.extremos[clave] = (min(mn, v), max(mx, v))
        for clave, curva in self.curvas.items():
            h = self.historia.get(clave)
            if h:
                curva.setData([x - ahora for x in h[0]], h[1])
        self._actualizar_tabla(d)

        if self.bench.corriendo():
            self.bench.muestra(d)
            self._revisar_temperaturas(d)

        if self.inicio:
            self.lbl_tiempo.setText(time.strftime("%H:%M:%S", time.gmtime(t)))
            self.muestras.append((round(t, 1), d))
            self._revisar_temperaturas(d)
            if self.duracion and t >= self.duracion:
                self.detener("Tiempo cumplido")
            # Refresca datos que vienen de los sensores (solo pruebas sueltas)
            if self.modo_fila:
                self._refrescar_tarjetas()
                return
            if "Disco" in self.activas:
                ctrl = disco_de_ruta(self.pruebas["Disco"].carpeta)
                lee, esc = d.get(f"{ctrl}_lee"), d.get(f"{ctrl}_esc")
                if lee is not None:
                    self.pruebas["Disco"].dato = f"L {lee:.0f} · E {esc:.0f} MB/s"
            if "CPU" in self.activas and d.get("cpu_mhz"):
                self.pruebas["CPU"].dato = f"{d['cpu_mhz']:.0f} MHz prom."
            if "RAM" in self.activas:
                self.pruebas["RAM"].dato = f"{self.pruebas['RAM'].megas / 1024:.1f} GB en prueba"
            self._refrescar_tarjetas()

    def _revisar_temperaturas(self, d):
        """Para todo si una temperatura pasa el límite 3 segundos seguidos."""
        limites = [("cpu_temp", "CPU", self.lim_cpu.value()),
                   ("gpu_temp", "GPU", self.lim_gpu.value())]
        limites += [(f"{n['ctrl']}_temp", f"SSD {n['ctrl']}", self.lim_nvme.value())
                    for n in self.sensores.nvme]
        for clave, nombre, limite in limites:
            v = d.get(clave)
            if v is not None and v >= limite:
                self.exceso[clave] = self.exceso.get(clave, 0) + 1
                if self.exceso[clave] >= 3 and not self.motivo_paro:
                    self.detener(f"Temperatura: {nombre} llegó a {v:.0f} °C (límite {limite} °C)")
            else:
                self.exceso[clave] = 0

    def _actualizar_tabla(self, d):
        for clave, nombre, unidad, _c, _g in self.series:
            v = d.get(clave)
            if v is None:
                continue
            fila = self.filas_tabla.get(clave)
            if fila is None:
                fila = self.tabla.rowCount()
                self.tabla.insertRow(fila)
                self.tabla.setItem(fila, 0, QTableWidgetItem(nombre))
                for c in (1, 2, 3):
                    it = QTableWidgetItem()
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.tabla.setItem(fila, c, it)
                self.filas_tabla[clave] = fila
            mn, mx = self.extremos.get(clave, (None, None))
            for c, x in ((1, v), (2, mn), (3, mx)):
                self.tabla.item(fila, c).setText("" if x is None else f"{x:.0f} {unidad}")

    def _refrescar_tarjetas(self):
        for nombre, t in self.tarjetas.items():
            t.mostrar(self._fuente().get(nombre, self.pruebas[nombre]), nombre in self.activas)

    def _registrar(self, origen, linea):
        hora = dt.datetime.now().strftime("%H:%M:%S")
        texto = f"[{hora}] {origen}: {linea}"
        if "fail:" in linea or "error" in linea.lower():
            self.log.appendHtml(f'<span style="color:#ff6b6b">{texto}</span>')
        else:
            self.log.appendPlainText(texto)

    # ------------------------------------------------------------ informe
    def _guardar_informe(self, transcurrido, resultado):
        if not self.carpeta_corrida:
            return
        claves = [s[0] for s in self.series]
        with open(os.path.join(self.carpeta_corrida, "sensores.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["segundo"] + claves)
            for t, d in self.muestras:
                w.writerow([t] + ["" if d.get(k) is None else round(d[k], 2) for k in claves])
        lineas = [
            f"GPUStressCPU v{__version__}",
            f"Inicio: {self.hora_inicio:%Y-%m-%d %H:%M:%S}",
            f"Duración: {time.strftime('%H:%M:%S', time.gmtime(transcurrido))}",
            f"Resultado: {resultado}",
            f"Motivo de fin: {self.motivo_paro or 'Las pruebas terminaron solas'}",
            "",
            *texto_informe(self._calificacion),
            "",
            "Pruebas:",
        ]
        for n in sorted(self.activas):
            p = self._fuente()[n]
            lineas.append(f"  {n}: {TEXTO_ESTADO[p.estado]} · errores {p.errores}"
                          f"{' · ' + p.dato if p.dato else ''}")
        if self.modo_fila:
            lineas += ["", f"Fila de tareas: «{self.nombre_fila}»",
                       "  (vuelta · paso · nombre · errores CPU acumulados · errores GPU acumulados)"]
            lineas += [f"  {v} · {n} · {nom} · {ec} · {eg}" for v, n, nom, ec, eg in self.fila.historial]
        lineas += ["", "Sensores (mín / máx):"]
        for clave, nombre, unidad, _c, _g in self.series:
            if clave in self.extremos:
                mn, mx = self.extremos[clave]
                lineas.append(f"  {nombre}: {mn:.0f} / {mx:.0f} {unidad}")
        lineas += ["", "Registro:", self.log.toPlainText(), "", AUTOR]
        with open(os.path.join(self.carpeta_corrida, "informe.txt"), "w") as f:
            f.write("\n".join(lineas))
        self._registrar("GPUStressCPU", f"Informe guardado en {self.carpeta_corrida}")

    def _abrir_registros(self):
        os.makedirs(CARPETA_REGISTROS, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.carpeta_corrida or CARPETA_REGISTROS))

    def closeEvent(self, ev):
        if self.bench.corriendo():
            if QMessageBox.question(self, "GPUStressCPU",
                                    "Hay un benchmark corriendo. ¿Cancelarlo y salir?") != QMessageBox.Yes:
                ev.ignore()
                return
            self.bench.cancelar()
            if self.bench.proc and not self.bench.proc.waitForFinished(8000):
                self.bench.proc.kill()
        if self.inicio is not None:
            if QMessageBox.question(self, "GPUStressCPU",
                                    "Hay una prueba corriendo. ¿Detenerla y salir?") != QMessageBox.Yes:
                ev.ignore()
                return
            self.detener("Ventana cerrada")
            procesos = [c.proc for c in self.fila.cargas] if self.modo_fila else \
                [self.pruebas[n].proc for n in self.activas]
            for proc in procesos:
                if proc and not proc.waitForFinished(8000):
                    proc.kill()
        self.nvidia.detener()
        ev.accept()

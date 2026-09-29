"""Benchmark: mide el rendimiento con una receta fija (misma carga siempre) para
comparar el mismo equipo antes/después (p. ej. cambio de pasta térmica) o contra
otros equipos. Cada paso corre en su propio proceso, uno tras otro.

Resultados en ~/.local/share/estrespc/benchmarks/<fecha_hora>.json
"""

import datetime as dt
import glob
import json
import os
import platform
import re
import shutil
import signal
import statistics
import subprocess
import sys

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from . import __version__

CARPETA_BENCH = os.path.expanduser("~/.local/share/estrespc/benchmarks")

# (clave, nombre, unidad, ¿más es mejor?)
MEDIDAS = [
    ("cpu1", "CPU · 1 hilo (7-Zip)", "MIPS", True),
    ("cpun", "CPU · todos los hilos (7-Zip)", "MIPS", True),
    ("ram", "Memoria RAM · copia", "GB/s", True),
    ("gpu", "GPU · cálculo FP32 (OpenCL)", "TFLOPS", True),
    ("video", "Video 4K · decodificación (4 flujos)", "fps", True),
    ("disco_lee", "Disco · lectura secuencial", "MB/s", True),
    ("disco_esc", "Disco · escritura secuencial", "MB/s", True),
    ("disco_4k", "Disco · lectura aleatoria 4K", "IOPS", True),
]
# Datos de temperatura/frecuencia que se guardan por paso (menos es mejor en temperatura).
TERMICOS = [("cpu_temp_max", "CPU temperatura máxima", "°C", False),
            ("cpu_mhz_prom", "CPU frecuencia promedio (carga)", "MHz", True),
            ("gpu_temp_max", "GPU temperatura máxima", "°C", False),
            ("gpu_mhz_prom", "GPU frecuencia promedio (carga)", "MHz", True)]

RE_7Z_TOT = re.compile(r"^Tot:\s+\d+\s+\d+\s+(\d+)")


def info_equipo():
    """Datos para saber con qué se hizo la medición."""
    def cmd(*a):
        try:
            return subprocess.run(a, capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            return ""
    cpu = ""
    try:
        with open("/proc/cpuinfo") as f:
            cpu = next((l.split(":", 1)[1].strip() for l in f if l.startswith("model name")), "")
    except OSError:
        pass
    gpu = cmd("nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader") \
        if shutil.which("nvidia-smi") else ""
    perfil = cmd("powerprofilesctl", "get") if shutil.which("powerprofilesctl") else ""
    return {"equipo": platform.node(), "cpu": cpu, "hilos": os.cpu_count(), "gpu": gpu,
            "kernel": platform.release(), "perfil_energia": perfil,
            "estrespc": __version__}


def historial():
    """Corridas anteriores, la más nueva primero."""
    res = []
    for ruta in sorted(glob.glob(os.path.join(CARPETA_BENCH, "*.json")), reverse=True):
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            d["_ruta"] = ruta
            res.append(d)
        except (OSError, ValueError):
            pass
    return res


class Benchmark(QObject):
    registro = Signal(str, str)        # (origen, línea)
    paso_actual = Signal(str, int, int)  # (nombre, número, total)
    medida = Signal(str, float)        # (clave, valor) — también térmicos
    terminado = Signal(dict)           # la corrida completa (o parcial si se canceló)

    def __init__(self, padre=None):
        super().__init__(padre)
        self.proc = None
        self.pasos = []
        self.i = -1
        self.corrida = None
        self.cancelado = False
        self._muestras = []
        self._valores = []
        self._reloj = QTimer(self)
        self._reloj.setSingleShot(True)
        self._reloj.timeout.connect(self._tiempo_cumplido)

    def corriendo(self):
        return self.corrida is not None

    # ------------------------------------------------------------ receta
    def iniciar(self, gpu_id, videos, carpeta_disco, nota, cargador):
        py = sys.executable
        hilos = os.cpu_count() or 1
        self.pasos = [
            ("cpu1", "CPU 1 hilo (7-Zip)", "7z", ["b", "-mmt1"], 0),
            ("cpun", f"CPU {hilos} hilos (7-Zip)", "7z", ["b", f"-mmt{hilos}"], 0),
            ("ram", "Memoria RAM", py, ["-m", "estrespc.bench_trabajador", "ram"], 0),
        ]
        if gpu_id is not None:
            self.pasos.append(("gpu", "GPU (OpenCL)", py,
                               ["-m", "estrespc.gpu_trabajador", "--dispositivo", gpu_id,
                                "--memoria", "0.3"], 20))
        if videos:
            self.pasos.append(("video", "Video 4K", py,
                               ["-m", "estrespc.video_trabajador", "--flujos", "4"] + videos, 20))
        if carpeta_disco:
            self.pasos.append(("disco", "Disco", py,
                               ["-m", "estrespc.bench_trabajador", "disco",
                                "--carpeta", carpeta_disco, "--mb", "2048"], 0))
        ahora = dt.datetime.now()
        self.corrida = {"fecha": ahora.isoformat(timespec="seconds"), "nota": nota.strip(),
                        "cargador": cargador, "equipo": info_equipo(), "resultados": {},
                        "termicos": {}, "pasos_omitidos": []}
        if gpu_id is None:
            self.corrida["pasos_omitidos"].append("gpu")
        if not videos:
            self.corrida["pasos_omitidos"].append("video")
        if not carpeta_disco:
            self.corrida["pasos_omitidos"].append("disco")
        self.cancelado = False
        self.i = -1
        self._siguiente()

    def cancelar(self):
        if not self.corriendo():
            return
        self.cancelado = True
        self._parar_proceso()

    # ------------------------------------------------------------ sensores
    def muestra(self, d):
        """La ventana manda aquí la lectura de sensores de cada segundo."""
        if self.corriendo() and 0 <= self.i < len(self.pasos):
            self._muestras.append(d)

    def _resumir_sensores(self, clave):
        m = self._muestras[len(self._muestras) // 5:] or self._muestras  # sin el arranque
        res = {}
        # Con 1 hilo el promedio de todos los núcleos engaña (los demás están en reposo):
        # se usa la frecuencia del núcleo más rápido.
        mhz = "cpu_mhz_max" if clave == "cpu1" else "cpu_mhz"
        for nombre, dato, fn in (("cpu_temp_max", "cpu_temp", max), ("cpu_mhz_prom", mhz, statistics.mean),
                                 ("gpu_temp_max", "gpu_temp", max), ("gpu_mhz_prom", "gpu_mhz", statistics.mean)):
            vals = [x[dato] for x in m if x.get(dato) is not None]
            if vals and (nombre.startswith("cpu") or clave in ("gpu", "video")):
                res[nombre] = round(fn(vals), 1)
        if res:
            self.corrida["termicos"][clave] = res

    # ------------------------------------------------------------ pasos
    def _siguiente(self):
        self.i += 1
        if self.cancelado or self.i >= len(self.pasos):
            self._terminar()
            return
        clave, nombre, programa, args, segundos = self.pasos[self.i]
        self._muestras, self._valores, self._salida = [], [], []
        self.paso_actual.emit(nombre, self.i + 1, len(self.pasos))
        self.registro.emit("Benchmark", f"{self.i + 1}/{len(self.pasos)} {nombre}…")
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._leer)
        self.proc.finished.connect(self._fin_paso)
        self.proc.start(programa, args)
        if segundos:
            self._reloj.start(segundos * 1000)

    def _tiempo_cumplido(self):
        self._parar_proceso()

    def _parar_proceso(self):
        self._reloj.stop()
        if self.proc and self.proc.state() != QProcess.NotRunning:
            pid = self.proc.processId()
            try:
                os.kill(pid, signal.SIGINT)
            except (ProcessLookupError, TypeError):
                pass
            proc = self.proc
            QTimer.singleShot(8000, lambda: proc.state() != QProcess.NotRunning and proc.kill())

    def _leer(self):
        while self.proc.canReadLine():
            linea = bytes(self.proc.readLine()).decode(errors="replace").rstrip()
            if not linea:
                continue
            self._salida.append(linea)
            clave = self.pasos[self.i][0]
            try:
                d = json.loads(linea)
            except ValueError:
                m = RE_7Z_TOT.match(linea)
                if m:
                    self._valores.append(float(m.group(1)))
                continue
            tipo = d.get("tipo")
            if tipo == "progreso":
                if clave == "gpu":
                    self._valores.append(d["gflops"] / 1000)
                elif clave == "video":
                    self._valores.append(d["fps"])
            elif tipo == "resultado":
                self._valores.append(d)
            elif tipo == "error":
                self.registro.emit("Benchmark", "ERROR: " + d.get("mensaje", ""))

    def _fin_paso(self, *_):
        self._leer()
        self._reloj.stop()
        clave, nombre = self.pasos[self.i][:2]
        v = self._valores
        res = {}
        if clave in ("cpu1", "cpun") and v:
            res[clave] = v[-1]
        elif clave == "ram" and v and isinstance(v[-1], dict):
            res["ram"] = v[-1]["gbs"]
        elif clave in ("gpu", "video"):
            # Se descartan los primeros 5 s (arranque, reloj subiendo); mediana del resto.
            estables = v[5:] if len(v) > 8 else v
            if estables:
                res[clave] = round(statistics.median(estables), 2 if clave == "gpu" else 1)
        elif clave == "disco" and v and isinstance(v[-1], dict):
            res = {"disco_lee": v[-1]["lectura_mbs"], "disco_esc": v[-1]["escritura_mbs"],
                   "disco_4k": v[-1]["aleatoria_iops"]}
        if not res and not self.cancelado:
            self.registro.emit("Benchmark", f"{nombre}: sin resultado. Salida: "
                               + " | ".join(self._salida[-3:]))
        for k, x in res.items():
            self.corrida["resultados"][k] = x
            self.medida.emit(k, float(x))
        self._resumir_sensores(clave)
        for k, x in self.corrida["termicos"].get(clave, {}).items():
            self.medida.emit(f"{clave}:{k}", float(x))
        self._siguiente()

    def _terminar(self):
        c = self.corrida
        c["completo"] = not self.cancelado
        if c["resultados"]:
            os.makedirs(CARPETA_BENCH, exist_ok=True)
            nombre = dt.datetime.fromisoformat(c["fecha"]).strftime("%Y-%m-%d_%H%M%S")
            c["_ruta"] = os.path.join(CARPETA_BENCH, nombre + ".json")
            with open(c["_ruta"], "w", encoding="utf-8") as f:
                json.dump({k: x for k, x in c.items() if not k.startswith("_")}, f,
                          ensure_ascii=False, indent=2)
        self.corrida = None
        self.i = -1
        self.terminado.emit(c)

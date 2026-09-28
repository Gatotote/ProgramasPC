"""Pruebas de estrés: cada una corre en su propio proceso (stress-ng o el
trabajador OpenCL) y reporta errores de verificación."""

import json
import os
import re
import signal
import sys

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

RE_FALLO = re.compile(r"\bfail:")
RE_FALLIDOS = re.compile(r"\bfailed: (\d+)")


class Prueba(QObject):
    """Base: lanza un proceso, junta su salida y cuenta errores."""

    registro = Signal(str, str)      # (prueba, línea)
    cambio = Signal()                # estado/errores/dato actualizados
    terminada = Signal(str)          # nombre

    nombre = ""

    def __init__(self, padre=None):
        super().__init__(padre)
        self.proc = None
        self.errores = 0
        self.dato = ""               # texto corto de rendimiento
        self.estado = "lista"        # lista | corriendo | ok | errores | fallo
        self._deteniendo = False

    # --- a implementar por cada prueba ---
    def comando(self):
        raise NotImplementedError

    def procesar_linea(self, linea):
        self.registro.emit(self.nombre, linea)

    # --- ciclo de vida ---
    def iniciar(self):
        programa, args = self.comando()
        self.errores, self.dato, self._deteniendo = 0, "", False
        self.estado = "corriendo"
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._leer)
        self.proc.finished.connect(self._fin)
        self.proc.errorOccurred.connect(self._error_proc)
        entorno = getattr(self, "entorno", None)
        if entorno:
            from PySide6.QtCore import QProcessEnvironment
            env = QProcessEnvironment.systemEnvironment()
            for k, v in entorno.items():
                env.insert(k, v)
            self.proc.setProcessEnvironment(env)
        self.registro.emit(self.nombre, "$ " + " ".join([programa] + args))
        self.proc.start(programa, args)
        self.cambio.emit()

    def detener(self):
        """Pide al proceso que termine limpio (SIGINT) y, si no, lo mata."""
        if not self.corriendo():
            return
        self._deteniendo = True
        pid = self.proc.processId()
        if pid:
            try:
                os.kill(pid, signal.SIGINT)
            except ProcessLookupError:
                pass
        proc = self.proc
        QTimer.singleShot(8000, lambda: proc.state() != QProcess.NotRunning and proc.kill())

    def corriendo(self):
        return self.proc is not None and self.proc.state() != QProcess.NotRunning

    def _leer(self):
        while self.proc.canReadLine():
            linea = bytes(self.proc.readLine()).decode(errors="replace").rstrip()
            if linea:
                self.procesar_linea(linea)

    def _error_proc(self, err):
        if err == QProcess.FailedToStart:
            self.registro.emit(self.nombre, "No se pudo iniciar el proceso")
            self.estado = "fallo"
            self.cambio.emit()
            self.terminada.emit(self.nombre)

    def _fin(self, codigo, tipo_salida):
        self._leer()
        if self.errores:
            self.estado = "errores"
        elif tipo_salida == QProcess.CrashExit and not self._deteniendo:
            self.estado = "fallo"
        elif codigo not in (0, None) and not self._deteniendo:
            self.estado = "fallo"
            self.registro.emit(self.nombre, f"El proceso terminó con código {codigo}")
        else:
            self.estado = "ok"
        self.cambio.emit()
        self.terminada.emit(self.nombre)


class PruebaStressNg(Prueba):
    """Prueba basada en stress-ng con --verify."""

    def procesar_linea(self, linea):
        super().procesar_linea(linea)
        if RE_FALLO.search(linea):
            self.errores += 1
            self.cambio.emit()
        m = RE_FALLIDOS.search(linea)
        if m and int(m.group(1)) > 0:
            self.errores = max(self.errores, int(m.group(1)))
            self.cambio.emit()

    def _fin(self, codigo, tipo_salida):
        # stress-ng devuelve 2 cuando un estresor falló la verificación.
        if codigo == 2 and not self.errores:
            self.errores = 1
        super()._fin(codigo, tipo_salida)


class PruebaCPU(PruebaStressNg):
    nombre = "CPU"
    METODOS = {
        "Máximo calor (matrices)": "matrixprod",
        "Punto flotante (FFT)": "fft",
        "Mixto (todos los métodos)": "all",
        "Enteros (primos)": "prime",
    }

    def __init__(self, padre=None):
        super().__init__(padre)
        self.hilos = os.cpu_count() or 1
        self.metodo = "matrixprod"

    def comando(self):
        return "stress-ng", ["--cpu", str(self.hilos), "--cpu-method", self.metodo,
                             "--verify", "--metrics-brief"]


class PruebaRAM(PruebaStressNg):
    nombre = "RAM"

    def __init__(self, padre=None):
        super().__init__(padre)
        self.megas = 1024
        self.hilos = 4

    def comando(self):
        return "stress-ng", ["--vm", str(self.hilos), "--vm-bytes", f"{self.megas}m",
                             "--vm-method", "all", "--vm-keep", "--verify",
                             "--metrics-brief"]


class PruebaDisco(PruebaStressNg):
    nombre = "Disco"

    def __init__(self, padre=None):
        super().__init__(padre)
        self.carpeta = os.path.expanduser("~")
        self.megas = 2048
        self.hilos = 2

    def comando(self):
        # Directo (sin caché) para que de verdad trabaje el SSD; stress-ng borra
        # sus archivos temporales al terminar.
        return "stress-ng", ["--hdd", str(self.hilos),
                             "--hdd-bytes", f"{self.megas}m",
                             "--hdd-opts", "direct,wr-seq,rd-rnd",
                             "--temp-path", self.carpeta, "--verify",
                             "--metrics-brief"]


class PruebaGPU(Prueba):
    nombre = "GPU"

    def __init__(self, padre=None):
        super().__init__(padre)
        self.dispositivo = ""
        self.memoria = 0.7

    def comando(self):
        return sys.executable, ["-m", "estrespc.gpu_trabajador",
                                "--dispositivo", self.dispositivo,
                                "--memoria", str(self.memoria)]

    def procesar_linea(self, linea):
        try:
            d = json.loads(linea)
        except ValueError:
            self.registro.emit(self.nombre, linea)
            return
        tipo = d.get("tipo")
        if tipo == "progreso":
            self.dato = f"{d['gflops'] / 1000:.2f} TFLOPS"
            if d["errores"] > self.errores:
                self.registro.emit(self.nombre,
                                   f"¡{d['errores'] - self.errores} error(es) de cálculo nuevos!")
            self.errores = d["errores"]
            self.cambio.emit()
        elif tipo == "inicio":
            self.registro.emit(self.nombre,
                               f"{d['dispositivo']}: usando {d['vram_mb']} MB de VRAM")
        elif tipo == "fin":
            self.errores = max(self.errores, d["errores"])
            self.registro.emit(self.nombre, f"Terminó con {self.errores} error(es)")
        elif tipo == "error":
            self.registro.emit(self.nombre, "ERROR: " + d["mensaje"])


class PruebaVideo(Prueba):
    """Decodifica videos 4K en bucle con la GPU (NVDEC) y, si se pide, los
    vuelve a codificar (NVENC)."""

    nombre = "Video"

    def __init__(self, padre=None):
        super().__init__(padre)
        self.videos = []
        self.flujos = 4
        self.recodificar = False
        self.mostrar = False

    def comando(self):
        args = ["-m", "estrespc.video_trabajador", "--flujos", str(self.flujos)]
        if self.recodificar:
            args.append("--recodificar")
        if self.mostrar:
            args.append("--mostrar")
        return sys.executable, args + self.videos

    def procesar_linea(self, linea):
        try:
            d = json.loads(linea)
        except ValueError:
            self.registro.emit(self.nombre, linea)
            return
        tipo = d.get("tipo")
        if tipo == "progreso":
            self.dato = f"{d['fps']:.0f} fps 4K · {d['vivos']} flujos"
            self.errores = d["errores"]
            self.cambio.emit()
        elif tipo == "inicio":
            self.registro.emit(self.nombre, f"{d['flujos']} flujos con: {', '.join(d['videos'])}"
                               + (" · recodificando con NVENC" if d["recodificar"] else ""))
        elif tipo == "aviso":
            self.registro.emit(self.nombre, "error: " + d["mensaje"])
        elif tipo == "recurso":
            self.registro.emit(self.nombre, "Aviso (no es falla del equipo): " + d["mensaje"])
        elif tipo == "fin":
            self.errores = max(self.errores, d["errores"])
            self.registro.emit(self.nombre, f"Terminó con {self.errores} error(es)")
        elif tipo == "error":
            self.registro.emit(self.nombre, "ERROR: " + d["mensaje"])


def listar_gpus():
    """Pregunta al trabajador qué GPUs OpenCL hay (en otro proceso)."""
    import subprocess
    try:
        r = subprocess.run([sys.executable, "-m", "estrespc.gpu_trabajador", "--listar"],
                           capture_output=True, text=True, timeout=30)
        for linea in r.stdout.splitlines():
            d = json.loads(linea)
            if d.get("tipo") == "dispositivos":
                return d["lista"]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return []


RE_GLMARK_FPS = re.compile(r"FPS:\s*(\d+)")


class Carga(Prueba):
    """Proceso genérico para un paso de una fila de tareas.

    formato: "stressng" (cuenta `fail:` y el código 2), "json" (trabajadores propios:
    errores y dato en las líneas de progreso) o "glmark2" (solo rendimiento).
    """

    def __init__(self, nombre, programa, args, formato="stressng", entorno=None, padre=None):
        super().__init__(padre)
        self.nombre = nombre
        self._programa, self._args = programa, args
        self.formato = formato
        self.entorno = entorno or {}

    def comando(self):
        return self._programa, self._args

    def procesar_linea(self, linea):
        if self.formato == "stressng":
            super().procesar_linea(linea)
            if RE_FALLO.search(linea):
                self.errores += 1
                self.cambio.emit()
            m = RE_FALLIDOS.search(linea)
            if m and int(m.group(1)) > 0:
                self.errores = max(self.errores, int(m.group(1)))
                self.cambio.emit()
            return
        if self.formato == "glmark2":
            m = RE_GLMARK_FPS.search(linea)
            if m:
                self.dato = f"glmark2 {m.group(1)} fps"
                self.cambio.emit()
            elif "error" in linea.lower():
                self.registro.emit(self.nombre, linea)
            return
        try:
            d = json.loads(linea)
        except ValueError:
            self.registro.emit(self.nombre, linea)
            return
        tipo = d.get("tipo")
        if tipo == "progreso":
            if "gflops" in d:
                self.dato = f"{d['gflops'] / 1000:.2f} TFLOPS"
            elif "fps" in d:
                self.dato = f"{d['fps']:.0f} fps"
            if d.get("errores", 0) > self.errores:
                self.registro.emit(self.nombre, f"¡{d['errores'] - self.errores} error(es) nuevos!")
            self.errores = max(self.errores, d.get("errores", 0))
            self.cambio.emit()
        elif tipo == "inicio":
            self.registro.emit(self.nombre, "inicio: " + ", ".join(
                f"{k}={v}" for k, v in d.items() if k != "tipo"))
        elif tipo in ("aviso", "recurso", "error"):
            self.registro.emit(self.nombre, f"{tipo}: {d.get('mensaje', '')}")
        elif tipo == "fin":
            self.errores = max(self.errores, d.get("errores", 0))

    def _fin(self, codigo, tipo_salida):
        if self.formato == "stressng" and codigo == 2 and not self.errores:
            self.errores = 1
        super()._fin(codigo, tipo_salida)

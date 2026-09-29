"""Filas de tareas: una secuencia de pasos que se repite. Cada paso dura N segundos y tiene
una parte de CPU y una de GPU (cualquiera puede ser «nada» o «reposo»).

Por qué: muchas fallas no salen con carga constante sino en los CAMBIOS de carga (de reposo a
máximo el voltaje salta de golpe), con cargas de distinto tipo (enteros, flotante, compresión)
y en la parte gráfica de la GPU, que es distinta de la de cálculo.

Filas propias en ~/.local/share/estrespc/filas/<nombre>.json
"""

import glob
import json
import os
import shutil
import sys

from PySide6.QtCore import QObject, QTimer, Signal

from .pruebas import Carga

CARPETA_FILAS = os.path.expanduser("~/.local/share/estrespc/filas")
MEDIOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "medios")


def escenas_disponibles():
    """Escenas del catálogo medios/modelos3d/escenas.json cuyos archivos existen."""
    try:
        with open(os.path.join(MEDIOS, "modelos3d", "escenas.json"), encoding="utf-8") as f:
            catalogo = json.load(f)["escenas"]
    except (OSError, ValueError, KeyError):
        return []
    res = []
    for e in catalogo:
        glb = os.path.join(MEDIOS, "modelos3d", e["archivo"])
        if os.path.exists(glb):
            hdri = os.path.join(MEDIOS, "hdri", "listos", e.get("hdri", ""))
            # (ojo: «ruta» en el catálogo es el camino de la CÁMARA; el archivo va en «archivo_glb»)
            res.append(dict(e, archivo_glb=glb, archivo_hdri=hdri if e.get("hdri") and os.path.exists(hdri) else ""))
    return res
ENTORNO_NVIDIA = {"__NV_PRIME_RENDER_OFFLOAD": "1", "__GLX_VENDOR_LIBRARY_NAME": "nvidia"}

# tipo: (nombre visible, descripción)
TIPOS_CPU = {
    "nada": ("—", "sin carga de CPU en este paso"),
    "reposo": ("Reposo", "CPU sin carga (para medir el salto de reposo a máximo)"),
    "pesada": ("Pesada", "multiplicación de matrices: la que más calienta"),
    "ligera": ("Ligera", "operaciones de enteros con pocos hilos"),
    "rafagas": ("Ráfagas", "encender y apagar todos los hilos cada segundo: castiga el voltaje"),
    "mixta": ("Mixta", "mitad de hilos punto flotante (FFT) y mitad compresión (zlib)"),
    "un_hilo": ("Un hilo", "un solo hilo al máximo: la CPU sube a su frecuencia y voltaje más altos"),
}
TIPOS_GPU = {
    "nada": ("—", "sin carga de GPU en este paso"),
    "reposo": ("Reposo", "GPU sin carga"),
    "calculo": ("Cálculo", "OpenCL con verificación (la prueba GPU de siempre)"),
    "render": ("Render 3D", "escena 3D procedural en 4K con imagen de control (detecta artefactos)"),
    "escena": ("Escena 3D", "escenas reales (Bistro, Sponza…) con HDRI, sombras y antialiasing; se van alternando"),
    "glmark2": ("glmark2", "escenas variadas de glmark2 en 4K (solo rendimiento)"),
    "video": ("Video 4K", "decodificar 4 videos 4K a la vez (NVDEC)"),
    "calculo_render": ("Cálculo + render", "las dos partes de la GPU a la vez"),
}

PERFILES = {
    "CPU · carga variable": [
        {"nombre": "Pesada, todos los hilos", "segundos": 60, "cpu": "pesada", "hilos": 0, "gpu": "nada"},
        {"nombre": "Ligera, 2 hilos", "segundos": 20, "cpu": "ligera", "hilos": 2, "gpu": "nada"},
        {"nombre": "Ráfagas de 1 s", "segundos": 30, "cpu": "rafagas", "hilos": 0, "gpu": "nada"},
        {"nombre": "Reposo", "segundos": 10, "cpu": "reposo", "hilos": 0, "gpu": "nada"},
        {"nombre": "Mixta (FFT + compresión)", "segundos": 45, "cpu": "mixta", "hilos": 0, "gpu": "nada"},
        {"nombre": "Un hilo al máximo", "segundos": 20, "cpu": "un_hilo", "hilos": 1, "gpu": "nada"},
    ],
    "GPU · mixta": [
        {"nombre": "Cálculo", "segundos": 60, "cpu": "nada", "hilos": 0, "gpu": "calculo"},
        {"nombre": "Render 3D", "segundos": 60, "cpu": "nada", "hilos": 0, "gpu": "render"},
        {"nombre": "Escena 3D real", "segundos": 60, "cpu": "nada", "hilos": 0, "gpu": "escena"},
        {"nombre": "glmark2", "segundos": 45, "cpu": "nada", "hilos": 0, "gpu": "glmark2"},
        {"nombre": "Video 4K", "segundos": 45, "cpu": "nada", "hilos": 0, "gpu": "video"},
        {"nombre": "Reposo", "segundos": 10, "cpu": "nada", "hilos": 0, "gpu": "reposo"},
        {"nombre": "Cálculo + render", "segundos": 60, "cpu": "nada", "hilos": 0, "gpu": "calculo_render"},
    ],
    "Todo el equipo": [
        {"nombre": "CPU pesada + render 3D", "segundos": 60, "cpu": "pesada", "hilos": 0, "gpu": "render"},
        {"nombre": "CPU ligera + cálculo GPU", "segundos": 30, "cpu": "ligera", "hilos": 2, "gpu": "calculo"},
        {"nombre": "CPU pesada + escena 3D real", "segundos": 60, "cpu": "pesada", "hilos": 0, "gpu": "escena"},
        {"nombre": "Ráfagas + GPU en reposo", "segundos": 30, "cpu": "rafagas", "hilos": 0, "gpu": "reposo"},
        {"nombre": "Todo en reposo", "segundos": 10, "cpu": "reposo", "hilos": 0, "gpu": "reposo"},
        {"nombre": "CPU mixta + cálculo y render", "segundos": 60, "cpu": "mixta", "hilos": 0, "gpu": "calculo_render"},
        {"nombre": "Un hilo + video 4K", "segundos": 30, "cpu": "un_hilo", "hilos": 1, "gpu": "video"},
    ],
}


def filas_propias():
    res = {}
    for ruta in sorted(glob.glob(os.path.join(CARPETA_FILAS, "*.json"))):
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            res[d["nombre"]] = d["pasos"]
        except (OSError, ValueError, KeyError):
            pass
    return res


def guardar_fila(nombre, pasos):
    os.makedirs(CARPETA_FILAS, exist_ok=True)
    seguro = "".join(c if c.isalnum() or c in " -_" else "_" for c in nombre).strip() or "fila"
    with open(os.path.join(CARPETA_FILAS, seguro + ".json"), "w", encoding="utf-8") as f:
        json.dump({"nombre": nombre, "pasos": pasos}, f, ensure_ascii=False, indent=2)


def borrar_fila(nombre):
    for ruta in glob.glob(os.path.join(CARPETA_FILAS, "*.json")):
        try:
            with open(ruta, encoding="utf-8") as f:
                if json.load(f).get("nombre") == nombre:
                    os.remove(ruta)
        except (OSError, ValueError):
            pass


def duracion_vuelta(pasos):
    return sum(p["segundos"] for p in pasos)


def describir(pasos):
    return "  →  ".join(
        f"{p['nombre']} ({p['segundos']} s)" for p in pasos) + f"   ·   una vuelta = {duracion_vuelta(pasos) // 60} min {duracion_vuelta(pasos) % 60} s"


class Componente:
    """Estado acumulado de CPU o GPU durante toda la fila (para las tarjetas y el informe)."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.estado = "lista"
        self.errores = 0
        self.dato = ""
        self.proc = None

    def corriendo(self):
        return self.estado == "corriendo"

    def detener(self):
        pass


class Fila(QObject):
    registro = Signal(str, str)
    cambio = Signal()
    paso = Signal(int, int, int, str)     # (número, total, vuelta, nombre)
    terminada = Signal()

    def __init__(self, padre=None):
        super().__init__(padre)
        self.componentes = {"CPU": Componente("CPU"), "GPU": Componente("GPU")}
        self.pasos = []
        self.cargas = []
        self.i = -1
        self.vuelta = 1
        self.activa = False
        self.deteniendo = False
        self.gpu_id = ""
        self.videos = []
        self.reloj = QTimer(self)
        self.reloj.setSingleShot(True)
        self.reloj.timeout.connect(self._fin_de_paso)
        self.historial = []  # (vuelta, paso, nombre, errores_cpu, errores_gpu, dato)
        self._indice_escena = 0

    # ------------------------------------------------------------ cargas
    def _cargas_cpu(self, p):
        hilos_eq = os.cpu_count() or 1
        h = p.get("hilos") or 0
        tipo = p["cpu"]
        base = ["--verify", "--metrics-brief"]
        if tipo == "pesada":
            return [("stress-ng", ["--cpu", str(h or hilos_eq), "--cpu-method", "matrixprod"] + base)]
        if tipo == "ligera":
            return [("stress-ng", ["--cpu", str(h or 2), "--cpu-method", "bitops"] + base)]
        if tipo == "rafagas":
            return [("stress-ng", ["--cpu", str(h or hilos_eq), "--cpu-method", "matrixprod",
                                   "--cpu-load", "50", "--cpu-load-slice", "1000"] + base)]
        if tipo == "mixta":
            n = h or hilos_eq
            return [("stress-ng", ["--cpu", str(max(1, n // 2)), "--cpu-method", "fft",
                                   "--zlib", str(max(1, n - n // 2))] + base)]
        if tipo == "un_hilo":
            return [("stress-ng", ["--cpu", "1", "--cpu-method", "matrixprod"] + base)]
        return []

    def _cargas_gpu(self, p):
        py = sys.executable
        tipo = p["gpu"]
        calculo = (py, ["-m", "estrespc.gpu_trabajador", "--dispositivo", self.gpu_id,
                        "--memoria", "0.3" if tipo == "calculo_render" else "0.6"], "json", None)
        render = (py, ["-m", "estrespc.render_trabajador"], "json", None)
        if tipo == "calculo":
            return [calculo]
        if tipo == "render":
            return [render]
        if tipo == "calculo_render":
            return [calculo, render]
        if tipo == "escena":
            escenas = escenas_disponibles()
            if not escenas:
                self.registro.emit("Fila", "No hay escenas 3D en medios/modelos3d: se usa el render procedural")
                return [render]
            e = escenas[self._indice_escena % len(escenas)]
            self._indice_escena += 1
            self.registro.emit("Fila", f"Escena 3D: {e['nombre']}")
            args = ["-m", "estrespc.render_trabajador", "--escena", e["archivo_glb"], "--camara", e.get("camara", "dentro"),
                    "--exposicion", str(e.get("exposicion", 1.0))]
            if e["archivo_hdri"]:
                args += ["--hdri", e["archivo_hdri"]]
            if e.get("ruta"):
                # «--ruta=…» pegado: si la ruta empieza con un número negativo, argparse la confunde con una opción
                args.append("--ruta=" + ";".join(",".join(str(c) for c in p) for p in e["ruta"]))
            return [(py, args, "json", None)]
        if tipo == "glmark2":
            if not shutil.which("glmark2"):
                self.registro.emit("Fila", "glmark2 no está instalado: se omite en este paso")
                return []
            return [("glmark2", ["--off-screen", "-s", "3840x2160", "--run-forever"],
                     "glmark2", ENTORNO_NVIDIA)]
        if tipo == "video":
            if not self.videos:
                self.registro.emit("Fila", "Sin videos 4K: se omite el video en este paso")
                return []
            return [(py, ["-m", "estrespc.video_trabajador", "--flujos", "4"] + self.videos, "json", None)]
        return []

    # ------------------------------------------------------------ ciclo
    def iniciar(self, pasos, gpu_id, videos):
        self.pasos = [dict(p) for p in pasos if p.get("segundos", 0) > 0]
        self.gpu_id, self.videos = gpu_id, videos
        self.i, self.vuelta = -1, 1
        self.activa, self.deteniendo = True, False
        self.historial = []
        usa = {"CPU": any(p["cpu"] not in ("nada",) for p in self.pasos),
               "GPU": any(p["gpu"] not in ("nada",) for p in self.pasos)}
        for n, c in self.componentes.items():
            c.estado = "corriendo" if usa[n] else "lista"
            c.errores, c.dato = 0, ""
        self._siguiente()

    def usa(self):
        return {n for n, c in self.componentes.items() if c.estado != "lista"}

    def detener(self):
        if not self.activa or self.deteniendo:
            return
        self.deteniendo = True
        self.reloj.stop()
        if not any(c.corriendo() for c in self.cargas):
            self._cerrar()
        for c in self.cargas:
            c.detener()

    def _siguiente(self):
        if self.deteniendo:
            self._cerrar()
            return
        self.i += 1
        if self.i >= len(self.pasos):
            self.i, self.vuelta = 0, self.vuelta + 1
        p = self.pasos[self.i]
        self.paso.emit(self.i + 1, len(self.pasos), self.vuelta, p["nombre"])
        self.registro.emit("Fila", f"Vuelta {self.vuelta} · paso {self.i + 1}/{len(self.pasos)}: "
                                   f"{p['nombre']} ({p['segundos']} s) · CPU {TIPOS_CPU[p['cpu']][0]} · "
                                   f"GPU {TIPOS_GPU[p['gpu']][0]}")
        self.cargas = []
        for parte, lista in (("CPU", [(a, b, "stressng", None) for a, b in self._cargas_cpu(p)]),
                             ("GPU", self._cargas_gpu(p))):
            for programa, args, formato, entorno in lista:
                c = Carga(parte, programa, args, formato, entorno, self)
                c.registro.connect(self.registro)
                c.cambio.connect(self._actualizar)
                c.terminada.connect(self._carga_terminada)
                self.cargas.append(c)
        for n in ("CPU", "GPU"):
            if self.componentes[n].estado != "lista":
                self.componentes[n].dato = "reposo" if not any(c.nombre == n for c in self.cargas) else ""
        self._base = {n: c.errores for n, c in self.componentes.items()}
        for c in self.cargas:
            c.iniciar()
        self.cambio.emit()
        self.reloj.start(p["segundos"] * 1000)

    def _actualizar(self):
        for n, comp in self.componentes.items():
            mias = [c for c in self.cargas if c.nombre == n]
            if mias:
                comp.errores = self._base[n] + sum(c.errores for c in mias)
                datos = [c.dato for c in mias if c.dato]
                comp.dato = " + ".join(datos)
        self.cambio.emit()

    def _fin_de_paso(self):
        if not any(c.corriendo() for c in self.cargas):   # (incluye cargas que murieron antes)
            self._paso_cerrado()
            return
        for c in self.cargas:
            c.detener()

    def _carga_terminada(self, _nombre):
        if any(c.corriendo() for c in self.cargas):
            return
        if self.reloj.isActive() and not self.deteniendo:
            # Una carga terminó antes de tiempo (falló al arrancar o se cayó): se registra y el paso
            # espera el resto de su duración (si no, la fila daría vueltas sin parar).
            for c in self.cargas:
                if c.estado == "fallo":
                    self.registro.emit("Fila", f"La carga de {c.nombre} terminó antes de tiempo; "
                                               "el paso espera su duración")
            return
        self._paso_cerrado()

    def _paso_cerrado(self):
        self._actualizar()
        p = self.pasos[self.i]
        self.historial.append((self.vuelta, self.i + 1, p["nombre"],
                               self.componentes["CPU"].errores, self.componentes["GPU"].errores))
        for c in self.cargas:
            if c.estado == "fallo":
                comp = self.componentes[c.nombre]
                if comp.estado == "corriendo" and not comp.errores:
                    comp.fallos = getattr(comp, "fallos", 0) + 1
        self.cargas = []
        if self.deteniendo:
            self._cerrar()
        else:
            self._siguiente()

    def _cerrar(self):
        if not self.activa:
            return
        self.activa = False
        self.reloj.stop()
        for comp in self.componentes.values():
            if comp.estado == "corriendo":
                comp.estado = "errores" if comp.errores else ("fallo" if getattr(comp, "fallos", 0) else "ok")
            comp.fallos = 0
        self.cambio.emit()
        self.terminada.emit()

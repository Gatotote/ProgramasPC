"""Lectura de sensores del equipo (hwmon, cpufreq, /proc, nvidia-smi)."""

import glob
import os
import shutil
import time

from PySide6.QtCore import QObject, QProcess


def _leer(ruta, defecto=None):
    try:
        with open(ruta) as f:
            return f.read().strip()
    except OSError:
        return defecto


def _hwmon():
    """Devuelve {nombre: [rutas hwmon]} para todos los sensores del sistema."""
    res = {}
    for h in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
        res.setdefault(_leer(f"{h}/name", ""), []).append(h)
    return res


def discos_nvme():
    """Lista de NVMe: {dispositivo, modelo, hwmon} (p. ej. nvme0n1)."""
    lista = []
    for h in _hwmon().get("nvme", []):
        ctrl = os.path.basename(os.path.realpath(f"{h}/device"))  # nvme0
        modelo = _leer(f"/sys/class/nvme/{ctrl}/model", ctrl)
        lista.append({"ctrl": ctrl, "modelo": modelo, "hwmon": h})
    return lista


def disco_de_ruta(ruta):
    """Controlador NVMe (nvme0…) donde vive `ruta`, o None."""
    try:
        dev = os.stat(ruta).st_dev
    except OSError:
        return None
    base = os.path.realpath(f"/sys/dev/block/{os.major(dev)}:{os.minor(dev)}")
    # btrfs usa dispositivos virtuales (0:xx); buscamos en /proc/mounts.
    if "/virtual/" in base or not os.path.exists(base):
        mejor, fuente = "", None
        for linea in open("/proc/mounts"):
            src, punto = linea.split()[:2]
            if (ruta + "/").startswith(punto.rstrip("/") + "/") and len(punto) >= len(mejor):
                mejor, fuente = punto, src
        if not fuente or not fuente.startswith("/dev/"):
            return None
        base = os.path.realpath(f"/sys/class/block/{os.path.basename(fuente)}")
    for parte in base.split("/"):
        if parte.startswith("nvme") and parte[4:].isdigit():
            return parte
    return None


class Sensores:
    def __init__(self):
        hw = _hwmon()
        self._cpu = hw.get("k10temp", hw.get("coretemp", [None]))[0]
        self._igpu = hw.get("amdgpu", [None])[0]
        self._ventiladores = []
        for h in hw.get("asus", []) + hw.get("thinkpad", []) + hw.get("dell_smm", []):
            self._ventiladores += sorted(glob.glob(f"{h}/fan*_input"))
        self.nvme = discos_nvme()
        self._stat_previo = None
        self._io_previo = {}
        self.cpus = os.cpu_count() or 1

    def _velocidad_disco(self, ctrl, ahora):
        """(lectura, escritura) en MB/s del disco nvmeXn1 desde la última lectura."""
        campos = _leer(f"/sys/block/{ctrl}n1/stat", "").split()
        if len(campos) < 7:
            return None, None
        leidos, escritos = int(campos[2]) * 512, int(campos[6]) * 512
        previo = self._io_previo.get(ctrl)
        self._io_previo[ctrl] = (ahora, leidos, escritos)
        if not previo or ahora <= previo[0]:
            return None, None
        dt = ahora - previo[0]
        return (leidos - previo[1]) / dt / 1e6, (escritos - previo[2]) / dt / 1e6

    def _uso_cpu(self):
        campos = list(map(int, _leer("/proc/stat").splitlines()[0].split()[1:]))
        inactivo, total = campos[3] + campos[4], sum(campos)
        uso = None
        if self._stat_previo:
            di, dt = inactivo - self._stat_previo[0], total - self._stat_previo[1]
            uso = 100.0 * (1 - di / dt) if dt else 0.0
        self._stat_previo = (inactivo, total)
        return uso

    def leer(self):
        d = {}
        if self._cpu:
            t = _leer(f"{self._cpu}/temp1_input")
            d["cpu_temp"] = int(t) / 1000 if t else None
        frec = [int(x) for x in (_leer(f) for f in glob.glob(
            "/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_cur_freq")) if x]
        if frec:
            d["cpu_mhz"] = sum(frec) / len(frec) / 1000
            d["cpu_mhz_max"] = max(frec) / 1000
        d["cpu_uso"] = self._uso_cpu()
        mem = {}
        for linea in _leer("/proc/meminfo", "").splitlines():
            k, v = linea.split(":")
            mem[k] = int(v.split()[0])
        if mem:
            d["ram_total_mb"] = mem["MemTotal"] / 1024
            d["ram_usada_mb"] = (mem["MemTotal"] - mem["MemAvailable"]) / 1024
            d["ram_disponible_mb"] = mem["MemAvailable"] / 1024
        if self._igpu:
            t = _leer(f"{self._igpu}/temp1_input")
            d["igpu_temp"] = int(t) / 1000 if t else None
        ahora = time.monotonic()
        for n in self.nvme:
            t = _leer(f"{n['hwmon']}/temp1_input")
            d[f"{n['ctrl']}_temp"] = int(t) / 1000 if t else None
            d[f"{n['ctrl']}_lee"], d[f"{n['ctrl']}_esc"] = self._velocidad_disco(n["ctrl"], ahora)
        for i, f in enumerate(self._ventiladores, 1):
            v = _leer(f)
            d[f"vent{i}_rpm"] = int(v) if v else None
        adp = glob.glob("/sys/class/power_supply/A*/online")
        if adp:
            d["cargador"] = _leer(adp[0]) == "1"
        return d


class MonitorNvidia(QObject):
    """Lee la GPU NVIDIA con `nvidia-smi -lms`. Solo se enciende cuando hace
    falta, porque consultar la GPU la despierta y gasta batería."""

    CAMPOS = ("temperature.gpu", "utilization.gpu", "power.draw",
              "clocks.gr", "memory.used", "fan.speed",
              "utilization.decoder", "utilization.encoder")
    CLAVES = ("gpu_temp", "gpu_uso", "gpu_w", "gpu_mhz", "gpu_mem_mb", "gpu_vent",
              "gpu_dec", "gpu_enc")

    def __init__(self, padre=None):
        super().__init__(padre)
        self.valores = {}
        self._proc = None

    @staticmethod
    def disponible():
        return shutil.which("nvidia-smi") is not None

    def activo(self):
        return self._proc is not None

    def iniciar(self):
        if self._proc or not self.disponible():
            return
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._leer)
        self._proc.start("nvidia-smi", [
            f"--query-gpu={','.join(self.CAMPOS)}",
            "--format=csv,noheader,nounits", "-lms", "1000"])

    def detener(self):
        if self._proc:
            self._proc.kill()
            self._proc.waitForFinished(2000)
            self._proc = None
        self.valores = {}

    def _leer(self):
        while self._proc and self._proc.canReadLine():
            partes = bytes(self._proc.readLine()).decode().strip().split(",")
            if len(partes) != len(self.CLAVES):
                continue
            for k, v in zip(self.CLAVES, partes):
                try:
                    self.valores[k] = float(v)
                except ValueError:
                    self.valores[k] = None

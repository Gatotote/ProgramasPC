"""Proceso aparte que estresa el decodificador (y opcionalmente el codificador)
de video de la GPU reproduciendo videos 4K en bucle, varios a la vez.

Cada flujo es un `ffmpeg` que decodifica con la GPU lo más rápido que puede
(sin esperar al reloj), así el motor de video trabaja al 100 %. Con --mostrar
el primer flujo se ve en una ventana de mpv a velocidad normal.

Salida: una línea JSON por evento en stdout.
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time

RE_ERROR = re.compile(r"error|corrupt|invalid|concealing", re.I)
# Avisos del empaquetador de salida (`[null @ …]`: la salida se descarta) y de marcas de
# tiempo al reiniciar el bucle: no tienen que ver con decodificar ni con la GPU.
RE_INOFENSIVO = re.compile(r"^\[null @|non monotonically increasing dts|Past duration", re.I)
# Falta de VRAM o de sesiones del codificador: es de configuración, no una
# falla del hardware, así que no se cuenta como error.
RE_RECURSO = re.compile(r"out of memory|OUT_OF_MEMORY|OpenEncodeSession|"
                        r"No capable devices|too many", re.I)
# Variables para que mpv dibuje con la NVIDIA en laptops con dos GPUs (PRIME).
ENTORNO_NVIDIA = {"__NV_PRIME_RENDER_OFFLOAD": "1", "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
                  "__VK_LAYER_NV_optimus": "NVIDIA_only"}


apagando = threading.Event()


def emitir(**datos):
    print(json.dumps(datos), flush=True)


class Flujo:
    def __init__(self, n, video, recodificar):
        self.n, self.video = n, video
        self.fps = 0.0
        self.errores = 0
        self.sin_recursos = False
        args = ["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "error",
                "-progress", "pipe:1", "-stream_loop", "-1",
                "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
                "-i", video, "-an"]
        if recodificar:
            args += ["-c:v", "hevc_nvenc", "-preset", "p4", "-b:v", "40M"]
        args += ["-f", "null", "-"]
        # Sesión propia: un Ctrl+C en la terminal no debe llegarles directo.
        self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     stdin=subprocess.DEVNULL, text=True,
                                     start_new_session=True)
        threading.Thread(target=self._progreso, daemon=True).start()
        threading.Thread(target=self._errores, daemon=True).start()

    def _progreso(self):
        for linea in self.proc.stdout:
            if linea.startswith("fps="):
                try:
                    self.fps = float(linea[4:])
                except ValueError:
                    pass

    def _errores(self):
        for linea in self.proc.stderr:
            linea = linea.strip()
            if not linea or apagando.is_set():
                continue
            if self.sin_recursos:
                continue  # lo que sigue son consecuencias de la falta de VRAM
            if RE_RECURSO.search(linea) or "Cannot allocate memory" in linea:
                self.sin_recursos = True
                emitir(tipo="recurso", mensaje=f"Flujo {self.n}: {linea[:200]}")
                self.proc.kill()
            elif RE_INOFENSIVO.search(linea):
                continue
            elif RE_ERROR.search(linea):
                self.errores += 1
                emitir(tipo="aviso", mensaje=f"Flujo {self.n}: {linea[:200]}")

    def vivo(self):
        return self.proc.poll() is None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flujos", type=int, default=4)
    ap.add_argument("--recodificar", action="store_true")
    ap.add_argument("--mostrar", action="store_true")
    ap.add_argument("videos", nargs="+")
    args = ap.parse_args()

    parar = False

    def al_senal(*_):
        nonlocal parar
        parar = True

    signal.signal(signal.SIGINT, al_senal)
    signal.signal(signal.SIGTERM, al_senal)

    videos = [v for v in args.videos if os.path.isfile(v)]
    if not videos:
        emitir(tipo="error", mensaje="No hay videos 4K; descárgalos o genéralos primero")
        return 1

    flujos = [Flujo(i + 1, videos[i % len(videos)], args.recodificar)
              for i in range(args.flujos)]
    ventana = None
    if args.mostrar:
        ventana = subprocess.Popen(
            ["mpv", "--loop-file=inf", "--hwdec=nvdec", "--no-audio",
             "--title=GPUStressCPU — video 4K", "--autofit=50%", "--really-quiet", videos[0]],
            env={**os.environ, **ENTORNO_NVIDIA},
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)
    emitir(tipo="inicio", flujos=len(flujos),
           videos=[os.path.basename(v) for v in videos],
           recodificar=args.recodificar, mostrar=args.mostrar)

    muertos_avisados = set()
    while not parar:
        time.sleep(1)
        for f in flujos:
            if not f.vivo() and f.n not in muertos_avisados and not parar:
                muertos_avisados.add(f.n)
                if f.sin_recursos:
                    emitir(tipo="recurso", mensaje=f"Flujo {f.n} no arrancó: sin VRAM o "
                           "sesiones libres; baja los videos a la vez o la VRAM de la prueba GPU")
                else:
                    f.errores += 1
                    emitir(tipo="aviso", mensaje=f"Flujo {f.n} se detuvo (código {f.proc.returncode})")
        vivos = [f for f in flujos if f.vivo()]
        emitir(tipo="progreso", fps=round(sum(f.fps for f in vivos), 1),
               vivos=len(vivos), errores=sum(f.errores for f in flujos))
        if not vivos:
            break

    apagando.set()
    for f in flujos:
        if f.vivo():
            f.proc.terminate()
    if ventana and ventana.poll() is None:
        ventana.terminate()
    for p in [f.proc for f in flujos] + ([ventana] if ventana else []):
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            p.kill()
    emitir(tipo="fin", errores=sum(f.errores for f in flujos))
    return 0


if __name__ == "__main__":
    sys.exit(main())

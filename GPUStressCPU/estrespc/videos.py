"""Videos 4K libres para la prueba de video: se generan en la propia GPU
(sin derechos de autor de nadie) o se descargan películas abiertas de la
Blender Foundation (licencia Creative Commons Atribución)."""

import glob
import os
import subprocess
import urllib.request
import zipfile

CARPETA_VIDEOS = os.path.expanduser("~/.local/share/estrespc/videos")
# Videos que vienen CON el programa (van en el instalador): no hay que descargarlos.
CARPETA_INCLUIDOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "medios", "videos")
EXTENSIONES = (".mp4", ".mkv", ".mov", ".webm")

# (archivo, códec, argumentos de ffmpeg) — 15 s de 4K 60 fps con mucho detalle
# (ruido) para que el decodificador no descanse.
GENERADOS = [
    ("generado_4k60_h264.mp4", "H.264", ["-c:v", "h264_nvenc", "-preset", "p4",
                                         "-b:v", "80M", "-pix_fmt", "yuv420p"]),
    ("generado_4k60_hevc10.mkv", "HEVC 10 bits", ["-c:v", "hevc_nvenc", "-preset", "p4",
                                                  "-b:v", "80M", "-pix_fmt", "p010le"]),
    # Las RTX 30 decodifican AV1 pero no lo codifican: se hace con la CPU (~1 min).
    ("generado_4k60_av1.mkv", "AV1", ["-c:v", "libsvtav1", "-preset", "9",
                                      "-b:v", "60M", "-pix_fmt", "yuv420p"]),
]
FUENTE = "testsrc2=size=3840x2160:rate=60,noise=alls=25:allf=t+u"
SEGUNDOS = 15

DESCARGAS = [
    {"nombre": "Big Buck Bunny 4K 60 fps (H.264, 672 MB)",
     "url": "https://download.blender.org/demo/movies/BBB/bbb_sunflower_2160p_60fps_normal.mp4.zip",
     "archivo": "bbb_sunflower_2160p_60fps_normal.mp4",
     "credito": "Big Buck Bunny © Blender Foundation | peach.blender.org — CC BY 3.0"},
]


def lista():
    """Videos disponibles en la carpeta (incluye los que ponga el usuario)."""
    os.makedirs(CARPETA_VIDEOS, exist_ok=True)
    todos = glob.glob(os.path.join(CARPETA_INCLUIDOS, "*")) + glob.glob(os.path.join(CARPETA_VIDEOS, "*"))
    vistos, res = set(), []
    for v in sorted(todos):
        nombre = os.path.basename(v)
        if v.lower().endswith(EXTENSIONES) and ".parcial" not in v and nombre not in vistos:
            vistos.add(nombre)
            res.append(v)
    return res


def generar(avisar):
    """Crea los videos sintéticos con NVENC. `avisar(texto)` informa avance."""
    os.makedirs(CARPETA_VIDEOS, exist_ok=True)
    for archivo, codec, args in GENERADOS:
        destino = os.path.join(CARPETA_VIDEOS, archivo)
        if os.path.exists(destino):
            continue
        avisar(f"Generando video 4K {codec}…")
        temporal = destino + ".parcial" + os.path.splitext(archivo)[1]
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", FUENTE, "-t", str(SEGUNDOS)] + args + [temporal],
                           capture_output=True, text=True)
        if r.returncode != 0:
            if os.path.exists(temporal):
                os.remove(temporal)
            avisar(f"No se pudo generar {codec}: {r.stderr.strip()[-200:]}")
            continue
        os.replace(temporal, destino)
    avisar("Videos generados")


def descargar(indice, avisar):
    """Descarga y descomprime una película abierta."""
    d = DESCARGAS[indice]
    os.makedirs(CARPETA_VIDEOS, exist_ok=True)
    destino = os.path.join(CARPETA_VIDEOS, d["archivo"])
    if os.path.exists(destino):
        avisar(f"{d['nombre']} ya estaba descargado")
        return
    zip_tmp = destino + ".zip.parcial"
    # Retoma lo que ya se había bajado (encabezado Range) y reintenta si se corta la red.
    total, intento = 0, 0
    while True:
        hecho = os.path.getsize(zip_tmp) if os.path.exists(zip_tmp) else 0
        if total and hecho >= total:
            break
        cab = {"User-Agent": "GPUStressCPU"}
        if hecho:
            cab["Range"] = f"bytes={hecho}-"
        try:
            with urllib.request.urlopen(urllib.request.Request(d["url"], headers=cab), timeout=30) as r:
                if hecho and r.status != 206:      # el servidor no aceptó retomar: desde cero
                    hecho = 0
                    open(zip_tmp, "wb").close()
                resto = int(r.headers.get("Content-Length", 0))
                total = hecho + resto
                if hecho:
                    avisar(f"Retomando {d['nombre']} desde {hecho * 100 // total} %")
                ultimo = -1
                with open(zip_tmp, "ab") as f:
                    while bloque := r.read(1 << 20):
                        f.write(bloque)
                        hecho += len(bloque)
                        pct = hecho * 100 // total if total else 0
                        if pct != ultimo and pct % 5 == 0:
                            ultimo = pct
                            avisar(f"Descargando {d['nombre']}: {pct} %")
            if hecho >= total:
                break
            raise OSError("la conexión se cerró antes de terminar")
        except OSError as e:
            intento += 1
            if intento > 5:
                raise OSError(f"la descarga se cortó 5 veces ({e}). Lo bajado se conserva: "
                              "vuelve a presionar el botón para retomarla") from e
            avisar(f"Se cortó la descarga ({e}); reintento {intento} de 5 en 5 s…")
            import time
            time.sleep(5)
    avisar("Descomprimiendo…")
    with zipfile.ZipFile(zip_tmp) as z:
        miembro = next(m for m in z.namelist() if m.endswith(d["archivo"]))
        with z.open(miembro) as src, open(destino + ".parcial", "wb") as dst:
            while bloque := src.read(1 << 20):
                dst.write(bloque)
    os.replace(destino + ".parcial", destino)
    os.remove(zip_tmp)
    with open(os.path.join(CARPETA_VIDEOS, "CREDITOS.txt"), "a") as f:
        f.write(d["credito"] + "\n")
    avisar(f"Listo: {d['nombre']}")

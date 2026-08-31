"""Localización de FFmpeg / FFprobe y utilidades para lanzarlo sin consola."""

import os
import shutil
import subprocess
import sys

from app import config

# En Windows, evita que aparezca una ventana negra de consola por cada llamada.
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _candidatos(nombre):
    manual = (config.cargar_settings().get("ffmpeg_manual") or "").strip()
    if manual:
        p = manual
        if os.path.isdir(p):
            p = os.path.join(p, nombre + (".exe" if sys.platform == "win32" else ""))
        base = os.path.dirname(p)
        yield p
        yield os.path.join(base, nombre + (".exe" if sys.platform == "win32" else ""))
    yield shutil.which(nombre)
    # yt-dlp trae a veces un ffmpeg embebido junto a imageio-ffmpeg
    try:
        import imageio_ffmpeg
        yield imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass


def ruta_ffmpeg():
    for c in _candidatos("ffmpeg"):
        if c and os.path.isfile(c):
            return c
    return None


def ruta_ffprobe():
    ff = ruta_ffmpeg()
    if ff:
        cand = os.path.join(os.path.dirname(ff), "ffprobe" + (".exe" if sys.platform == "win32" else ""))
        if os.path.isfile(cand):
            return cand
    return shutil.which("ffprobe")


def disponible():
    return ruta_ffmpeg() is not None


def version():
    ff = ruta_ffmpeg()
    if not ff:
        return None
    try:
        salida = subprocess.run(
            [ff, "-version"], capture_output=True, text=True, timeout=10,
            creationflags=_NO_WINDOW,
        ).stdout
        return salida.splitlines()[0] if salida else "ffmpeg"
    except Exception:
        return "ffmpeg"


def duracion_segundos(ruta):
    """Duración del archivo con ffprobe (float) o None si no se puede saber."""
    fp = ruta_ffprobe()
    if not fp:
        return None
    try:
        salida = subprocess.run(
            [fp, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nokey=1:noprint_wrappers=1", ruta],
            capture_output=True, text=True, timeout=20, creationflags=_NO_WINDOW,
        ).stdout.strip()
        return float(salida)
    except Exception:
        return None


def popen(args):
    """Lanza ffmpeg leyendo su progreso por stderr, línea a línea."""
    return subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_NO_WINDOW,
    )

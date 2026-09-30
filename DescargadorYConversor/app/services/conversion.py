"""Conversión de vídeo y audio con FFmpeg, en un hilo aparte."""

import os
import re

from PySide6.QtCore import QThread, Signal

from app.services import ffmpeg

# Formatos de salida ofrecidos y los argumentos de códec que usa cada uno.
VIDEO = {
    "MP4 (H.264 + AAC)":  {"ext": "mp4",  "args": ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-c:a", "aac", "-b:a", "192k"]},
    "MKV (H.264 + AAC)":  {"ext": "mkv",  "args": ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-c:a", "aac", "-b:a", "192k"]},
    "WebM (VP9 + Opus)":  {"ext": "webm", "args": ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32", "-c:a", "libopus", "-b:a", "128k"]},
    "AVI (MPEG-4)":       {"ext": "avi",  "args": ["-c:v", "mpeg4", "-qscale:v", "4", "-c:a", "libmp3lame", "-q:a", "3"]},
    "MOV (H.264 + AAC)":  {"ext": "mov",  "args": ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-c:a", "aac", "-b:a", "192k"]},
    "GIF animado":        {"ext": "gif",  "args": ["-vf", "fps=12,scale=480:-1:flags=lanczos", "-an"]},
    # DaVinci Resolve gratuito en Linux no lee H.264/H.265 ni audio AAC (los
    # .mp4 de celular se ven en negro). DNxHR + PCM en .mov sí lo abre.
    # "davinci": frame rate constante (ver _args_fps) y decodificación por GPU.
    "DaVinci · DNxHR 1080p (para editar)": {"ext": "mov", "davinci": True, "args": [
        "-vf", "scale='if(gt(iw,ih),-2,min(1080,iw))':'if(gt(iw,ih),min(1080,ih),-2)':flags=lanczos,format=yuv422p",
        "-c:v", "dnxhd", "-profile:v", "dnxhr_sq", "-c:a", "pcm_s16le", "-ar", "48000"]},
    "DaVinci · DNxHR resolución original (pesado)": {"ext": "mov", "davinci": True, "args": [
        "-vf", "format=yuv422p",
        "-c:v", "dnxhd", "-profile:v", "dnxhr_hq", "-c:a", "pcm_s16le", "-ar", "48000"]},
}

PRESET_DAVINCI = "DaVinci · DNxHR 1080p (para editar)"

# Frame rates estándar; si el vídeo ya va a uno de estos se respeta tal cual.
_FPS_ESTANDAR = (23.976, 24, 25, 29.97, 30, 50, 59.94, 60)
AUDIO = {
    "MP3 (192 kbps)":  {"ext": "mp3",  "args": ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"]},
    "MP3 (320 kbps)":  {"ext": "mp3",  "args": ["-vn", "-c:a", "libmp3lame", "-b:a", "320k"]},
    "M4A / AAC":       {"ext": "m4a",  "args": ["-vn", "-c:a", "aac", "-b:a", "256k"]},
    "WAV (sin pérdida)": {"ext": "wav", "args": ["-vn", "-c:a", "pcm_s16le"]},
    "FLAC (sin pérdida)": {"ext": "flac", "args": ["-vn", "-c:a", "flac"]},
    "OGG (Vorbis)":    {"ext": "ogg",  "args": ["-vn", "-c:a", "libvorbis", "-q:a", "5"]},
}

EXT_VIDEO = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".mpg", ".mpeg", ".ts", ".3gp"}
EXT_AUDIO = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma"}

FILTRO_ARCHIVOS = (
    "Multimedia (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.m4v *.mpg *.mpeg *.ts "
    "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus *.wma);;Todos los archivos (*.*)"
)

_TIEMPO_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")


def preset_por_nombre(nombre):
    return VIDEO.get(nombre) or AUDIO.get(nombre)


def _args_fps(entrada):
    """Frame rate constante para DaVinci. Los celulares graban con frame rate
    variable y DaVinci desfasa el audio; se fija a 30 o 60 según el promedio."""
    fps = ffmpeg.fps_promedio(entrada)
    if not fps:
        return []
    cercano = min(_FPS_ESTANDAR, key=lambda e: abs(fps - e))
    if abs(fps - cercano) / cercano < 0.01:
        return ["-fps_mode", "cfr", "-r", str(cercano)]
    return ["-fps_mode", "cfr", "-r", "30" if fps <= 35 else "60"]


def es_salida_audio(nombre):
    return nombre in AUDIO


def ruta_salida(entrada, carpeta_destino, preset):
    base = os.path.splitext(os.path.basename(entrada))[0]
    destino = os.path.join(carpeta_destino, f"{base}.{preset['ext']}")
    n = 1
    while os.path.abspath(destino) == os.path.abspath(entrada) or os.path.exists(destino):
        destino = os.path.join(carpeta_destino, f"{base} ({n}).{preset['ext']}")
        n += 1
    return destino


class ConversionWorker(QThread):
    progreso = Signal(int, str)               # porcentaje, texto
    empieza_uno = Signal(int, int, str)       # indice, total, nombre archivo
    uno_terminado = Signal(str, bool)         # salida, ok
    todo_terminado = Signal(int, int, list)   # ok, total, errores [(archivo, msg)]

    def __init__(self, entradas, carpeta_destino, nombre_preset, parent=None):
        super().__init__(parent)
        self.entradas = entradas
        self.carpeta_destino = carpeta_destino
        self.nombre_preset = nombre_preset
        self._cancelar = False
        self._proc = None

    def cancelar(self):
        self._cancelar = True
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.kill()
            except Exception:
                pass

    def run(self):
        ff = ffmpeg.ruta_ffmpeg()
        preset = preset_por_nombre(self.nombre_preset)
        total = len(self.entradas)
        if not ff:
            self.todo_terminado.emit(0, total, [("", "FFmpeg no está instalado")])
            return
        if not preset:
            self.todo_terminado.emit(0, total, [("", "Formato de salida no válido")])
            return

        os.makedirs(self.carpeta_destino, exist_ok=True)
        ok = 0
        errores = []

        for i, entrada in enumerate(self.entradas, start=1):
            if self._cancelar:
                break
            self.empieza_uno.emit(i, total, os.path.basename(entrada))
            self.progreso.emit(0, "Analizando…")
            dur = ffmpeg.duracion_segundos(entrada) or 0
            salida = ruta_salida(entrada, self.carpeta_destino, preset)
            if preset.get("davinci"):
                cmd = [ff, "-y", "-hwaccel", "auto", "-i", entrada, *preset["args"],
                       *_args_fps(entrada), "-progress", "pipe:2", salida]
            else:
                cmd = [ff, "-y", "-i", entrada, *preset["args"], "-progress", "pipe:2", salida]

            try:
                self._proc = ffmpeg.popen(cmd)
                ultimo_err = ""
                for linea in self._proc.stderr:
                    if self._cancelar:
                        break
                    linea = linea.strip()
                    m = _TIEMPO_RE.search(linea)
                    if m and dur > 0:
                        h, mnt, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                        seg = h * 3600 + mnt * 60 + s
                        pct = max(0, min(99, int(seg / dur * 100)))
                        self.progreso.emit(pct, f"{pct}%")
                    elif linea and not linea.startswith(("frame=", "size=", "bitrate=", "speed=")):
                        ultimo_err = linea
                codigo = self._proc.wait()
                self._proc = None

                if self._cancelar:
                    if os.path.exists(salida):
                        try:
                            os.remove(salida)
                        except OSError:
                            pass
                    break
                if codigo == 0 and os.path.exists(salida) and os.path.getsize(salida) > 0:
                    ok += 1
                    self.progreso.emit(100, "100%")
                    self.uno_terminado.emit(salida, True)
                else:
                    errores.append((os.path.basename(entrada), ultimo_err or f"ffmpeg salió con código {codigo}"))
                    self.uno_terminado.emit(entrada, False)
            except Exception as e:
                errores.append((os.path.basename(entrada), str(e)[:200]))
                self.uno_terminado.emit(entrada, False)

        self.todo_terminado.emit(ok, total, errores)

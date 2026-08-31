"""Descarga de vídeos con yt-dlp, en un hilo aparte para no congelar la GUI."""

import os
import urllib.request

from PySide6.QtCore import QThread, Signal

from app.services import ffmpeg

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

CALIDADES = ["Mejor calidad disponible", "1080p", "720p", "480p", "360p"]

# Navegadores de los que yt-dlp puede leer cookies para saltarse el
# "Sign in to confirm you're not a bot" de YouTube. Clave = etiqueta visible,
# valor = nombre que espera yt-dlp ("" = no usar cookies).
NAVEGADORES_COOKIES = {
    "Ninguno": "",
    "Chrome": "chrome",
    "Edge": "edge",
    "Firefox": "firefox",
    "Brave": "brave",
    "Opera": "opera",
    "Vivaldi": "vivaldi",
    "Chromium": "chromium",
}

_MSG_BOT = ("sign in to confirm", "confirm you're not a bot", "confirm you are not a bot")
_MSG_FORMATO = ("requested format is not available", "requested format not available")


def es_error_de_cookies(mensaje):
    m = (mensaje or "").lower()
    return any(t in m for t in _MSG_BOT)


def es_error_de_formato(mensaje):
    m = (mensaje or "").lower()
    return any(t in m for t in _MSG_FORMATO)


def _aplicar_cookies(opciones, navegador):
    if navegador:
        opciones["cookiesfrombrowser"] = (navegador,)


def yt_dlp_disponible():
    return yt_dlp is not None


def version_yt_dlp():
    if yt_dlp is None:
        return None
    return getattr(yt_dlp.version, "__version__", "desconocida")


_ALTURA = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}


def formato_para(calidad, con_ffmpeg):
    """Cadena 'format' de yt-dlp según la calidad elegida y si hay FFmpeg.

    Cada opción lleva varios respaldos ('/') para que, si el sitio no ofrece
    exactamente eso, yt-dlp baje lo más parecido en vez de fallar con
    "Requested format is not available".
    """
    if con_ffmpeg:
        if calidad not in _ALTURA:
            return "bv*+ba/b/bv*+ba*"
        h = _ALTURA[calidad]
        return (
            f"bv*[height<={h}]+ba/b[height<={h}]/"
            f"bv*[height<={h}]+ba*/bv*+ba/b"
        )
    # Sin FFmpeg no se pueden fusionar pistas: hay que quedarse con un único
    # stream que ya traiga vídeo+audio. Si no existe, se coge el mejor a secas.
    if calidad not in _ALTURA:
        return "b/bv*+ba"
    h = _ALTURA[calidad]
    return f"b[height<={h}]/b/bv*[height<={h}]+ba"


def info_previa(url, navegador=""):
    """Devuelve (titulo, bytes_miniatura|None) sin descargar el vídeo."""
    if yt_dlp is None:
        return None, None
    try:
        opciones = {"quiet": True, "skip_download": True, "noplaylist": True}
        _aplicar_cookies(opciones, navegador)
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)
        titulo = info.get("title", "Vídeo")
        datos = None
        thumb = info.get("thumbnail")
        if thumb:
            try:
                pet = urllib.request.Request(thumb, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(pet, timeout=10) as resp:
                    datos = resp.read()
            except Exception:
                datos = None
        return titulo, datos
    except Exception:
        return None, None


class DescargaWorker(QThread):
    progreso = Signal(int, str)        # porcentaje, texto
    empieza_uno = Signal(int, int, str)   # indice, total, url
    info_lista = Signal(str, bytes)   # titulo, miniatura (b"" si no hay)
    uno_terminado = Signal(str, bool)  # titulo, ok
    todo_terminado = Signal(int, int, list)  # ok, total, errores [(url, msg)]

    def __init__(self, urls, carpeta, calidad, solo_audio, navegador_cookies="", parent=None):
        super().__init__(parent)
        self.urls = urls
        self.carpeta = carpeta
        self.calidad = calidad
        self.solo_audio = solo_audio
        self.navegador_cookies = navegador_cookies
        self._cancelar = False

    def cancelar(self):
        self._cancelar = True

    def _hook(self, d):
        if self._cancelar:
            raise RuntimeError("CANCELADO_POR_USUARIO")
        estado = d.get("status")
        if estado == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            hecho = d.get("downloaded_bytes", 0)
            if total:
                self.progreso.emit(int(hecho / total * 100), d.get("_percent_str", "").strip())
        elif estado == "finished":
            self.progreso.emit(100, "Procesando archivo final…")

    def run(self):
        if yt_dlp is None:
            self.todo_terminado.emit(0, len(self.urls), [("", "yt-dlp no está instalado")])
            return

        con_ffmpeg = ffmpeg.disponible()
        total = len(self.urls)
        ok = 0
        errores = []

        for i, url in enumerate(self.urls, start=1):
            if self._cancelar:
                break
            self.empieza_uno.emit(i, total, url)
            titulo_prev, miniatura = info_previa(url, self.navegador_cookies)
            self.info_lista.emit(f"[{i}/{total}] {titulo_prev or 'Vídeo'}", miniatura or b"")
            if self._cancelar:
                break

            os.makedirs(self.carpeta, exist_ok=True)
            opciones = {
                "outtmpl": os.path.join(self.carpeta, "%(title)s.%(ext)s"),
                "progress_hooks": [self._hook],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }
            ff = ffmpeg.ruta_ffmpeg()
            if ff:
                opciones["ffmpeg_location"] = ff
            _aplicar_cookies(opciones, self.navegador_cookies)

            if self.solo_audio:
                opciones["format"] = "bestaudio/best"
                opciones["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            else:
                opciones["format"] = formato_para(self.calidad, con_ffmpeg)
                if con_ffmpeg:
                    opciones["merge_output_format"] = "mp4"

            try:
                with yt_dlp.YoutubeDL(opciones) as ydl:
                    info = ydl.extract_info(url, download=True)
                titulo = info.get("title", titulo_prev or "Vídeo")
                ok += 1
                self.uno_terminado.emit(titulo, True)
            except Exception as e:
                if "CANCELADO_POR_USUARIO" in str(e) or self._cancelar:
                    break
                errores.append((url, str(e).splitlines()[-1][:200]))
                self.uno_terminado.emit(url, False)

        self.todo_terminado.emit(ok, total, errores)

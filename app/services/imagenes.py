"""Conversión de imágenes (incluye RAW de cámara) con rawpy + Pillow."""

import os

from PySide6.QtCore import QThread, Signal

try:
    import rawpy
except Exception:  # rawpy trae LibRaw; si falla la carga, se desactiva RAW
    rawpy = None

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    ImageOps = None

# RAW de cámara (LibRaw). Los que pidió el usuario van primero.
EXT_RAW = {
    ".cr2", ".cr3",          # Canon
    ".nef", ".nrw",          # Nikon
    ".arw", ".sr2", ".srf",  # Sony
    ".raf",                  # Fujifilm
    ".rw2",                  # Panasonic
    ".orf",                  # Olympus / OM System
    ".dng",                 # Adobe / genérico
    ".pef",                 # Pentax
    ".srw",                 # Samsung
    ".raw", ".rwl", ".3fr", ".erf", ".mef", ".mos", ".mrw", ".x3f", ".iiq",
}
EXT_PILLOW = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif", ".ppm"}

# Formatos de salida ofrecidos.
SALIDA = {
    "JPEG (calidad alta)":   {"ext": "jpg",  "fmt": "JPEG", "sin_alpha": True,
                              "params": {"quality": 95, "subsampling": 0, "optimize": True}},
    "JPEG (calidad media)":  {"ext": "jpg",  "fmt": "JPEG", "sin_alpha": True,
                              "params": {"quality": 85, "subsampling": 1, "optimize": True}},
    "PNG":                   {"ext": "png",  "fmt": "PNG",  "sin_alpha": False,
                              "params": {"optimize": True}},
    "WebP (calidad alta)":   {"ext": "webp", "fmt": "WEBP", "sin_alpha": False,
                              "params": {"quality": 92, "method": 6}},
    "TIFF (sin pérdida)":    {"ext": "tiff", "fmt": "TIFF", "sin_alpha": False,
                              "params": {"compression": "tiff_lzw"}},
    "BMP":                   {"ext": "bmp",  "fmt": "BMP",  "sin_alpha": True, "params": {}},
}

LADOS_MAX = ["Tamaño original", "4000 px", "2560 px", "1920 px", "1280 px", "1024 px"]

FILTRO_ARCHIVOS = (
    "Imágenes y RAW (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif "
    "*.cr2 *.cr3 *.nef *.nrw *.arw *.sr2 *.raf *.rw2 *.orf *.dng *.pef *.srw "
    "*.raw *.3fr *.erf *.mrw *.x3f *.iiq);;Todos los archivos (*.*)"
)


def raw_disponible():
    return rawpy is not None and Image is not None


def pillow_disponible():
    return Image is not None


def es_raw(ruta):
    return os.path.splitext(ruta)[1].lower() in EXT_RAW


def lado_a_pixeles(texto):
    if not texto or texto == LADOS_MAX[0]:
        return 0
    try:
        return int(texto.split()[0])
    except (ValueError, IndexError):
        return 0


def ruta_salida(entrada, carpeta_destino, preset):
    base = os.path.splitext(os.path.basename(entrada))[0]
    destino = os.path.join(carpeta_destino, f"{base}.{preset['ext']}")
    n = 1
    while os.path.abspath(destino) == os.path.abspath(entrada) or os.path.exists(destino):
        destino = os.path.join(carpeta_destino, f"{base} ({n}).{preset['ext']}")
        n += 1
    return destino


def _abrir(ruta):
    """Devuelve un PIL.Image en RGB/RGBA a partir de un archivo normal o RAW."""
    if es_raw(ruta):
        if rawpy is None:
            raise RuntimeError("rawpy no está instalado; no se pueden abrir archivos RAW.")
        with rawpy.imread(ruta) as raw:
            rgb = raw.postprocess(use_camera_wb=True, output_bps=8, no_auto_bright=False)
        return Image.fromarray(rgb)
    img = Image.open(ruta)
    img.load()
    if ImageOps is not None:
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
    return img


def _guardar(img, ruta, preset, lado_max):
    if lado_max and max(img.size) > lado_max:
        img = img.copy()
        img.thumbnail((lado_max, lado_max), Image.LANCZOS)

    if preset.get("sin_alpha") and img.mode in ("RGBA", "LA", "P"):
        base = img.convert("RGBA")
        fondo = Image.new("RGB", base.size, (255, 255, 255))
        fondo.paste(base, mask=base.split()[-1])
        img = fondo
    elif img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")

    img.save(ruta, preset["fmt"], **preset["params"])


class ConversionImagenWorker(QThread):
    progreso = Signal(int, str)
    empieza_uno = Signal(int, int, str)
    uno_terminado = Signal(str, bool)
    todo_terminado = Signal(int, int, list)

    def __init__(self, entradas, carpeta_destino, nombre_preset, lado_max=0, parent=None):
        super().__init__(parent)
        self.entradas = entradas
        self.carpeta_destino = carpeta_destino
        self.nombre_preset = nombre_preset
        self.lado_max = lado_max
        self._cancelar = False

    def cancelar(self):
        self._cancelar = True

    def run(self):
        if Image is None:
            self.todo_terminado.emit(0, len(self.entradas), [("", "Pillow no está instalado")])
            return
        preset = SALIDA.get(self.nombre_preset)
        if not preset:
            self.todo_terminado.emit(0, len(self.entradas), [("", "Formato de salida no válido")])
            return

        os.makedirs(self.carpeta_destino, exist_ok=True)
        total = len(self.entradas)
        ok = 0
        errores = []

        for i, entrada in enumerate(self.entradas, start=1):
            if self._cancelar:
                break
            self.empieza_uno.emit(i, total, os.path.basename(entrada))
            es_raw_archivo = es_raw(entrada)
            self.progreso.emit(0, "Revelando RAW…" if es_raw_archivo else "Convirtiendo…")
            try:
                img = _abrir(entrada)
                salida = ruta_salida(entrada, self.carpeta_destino, preset)
                _guardar(img, salida, preset, self.lado_max)
                if os.path.exists(salida) and os.path.getsize(salida) > 0:
                    ok += 1
                    self.progreso.emit(100, "100%")
                    self.uno_terminado.emit(salida, True)
                else:
                    errores.append((os.path.basename(entrada), "no se generó el archivo"))
                    self.uno_terminado.emit(entrada, False)
            except Exception as e:
                errores.append((os.path.basename(entrada), str(e)[:200]))
                self.uno_terminado.emit(entrada, False)

        self.todo_terminado.emit(ok, total, errores)

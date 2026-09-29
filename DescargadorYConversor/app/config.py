"""Configuración e historial persistentes.

Se reutiliza la carpeta ~/.descargador_videos que ya usaba la versión Tkinter,
para no perder el historial ni la última carpeta guardada.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

if getattr(sys, "frozen", False):
    # Empaquetado con PyInstaller: los datos van junto al ejecutable.
    RAIZ_PROYECTO = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
else:
    RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
_ASSETS = RAIZ_PROYECTO / "assets"

# Icono de ventana/exe: el nuevo emblema; si no está, el gato de la 1ª versión.
RUTA_ICONO = _ASSETS / "icono.ico"
if not RUTA_ICONO.exists():
    RUTA_ICONO = RAIZ_PROYECTO / "cat_icon.ico"

# Emblema para la barra lateral y la cabecera (variante clara sobre fondo oscuro).
RUTA_LOGO_CLARO = _ASSETS / "logo_claro.png"

RUTA_TEMA = RAIZ_PROYECTO / "app" / "resources" / "theme.qss"

# Se puede redirigir con DESCARGADOR_CONFIG_DIR (útil para pruebas).
CARPETA_CONFIG = os.environ.get("DESCARGADOR_CONFIG_DIR") or os.path.join(
    os.path.expanduser("~"), ".descargador_videos"
)
ARCHIVO_SETTINGS = os.path.join(CARPETA_CONFIG, "settings.json")
ARCHIVO_HISTORIAL = os.path.join(CARPETA_CONFIG, "historial.json")

_DESCARGAS_POR_DEFECTO = os.path.join(os.path.expanduser("~"), "Downloads")

DEFAULTS = {
    "carpeta_descargas": _DESCARGAS_POR_DEFECTO,
    "carpeta_conversiones": _DESCARGAS_POR_DEFECTO,
    "calidad": "Mejor calidad disponible",
    "solo_audio": False,
    "ffmpeg_manual": "",       # ruta a ffmpeg.exe si no está en el PATH
    "navegador_cookies": "",   # navegador del que leer cookies (YouTube "no soy un bot")
}


def _leer_json(ruta, por_defecto):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return por_defecto


def _escribir_json(ruta, datos):
    os.makedirs(CARPETA_CONFIG, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


# --- Ajustes -----------------------------------------------------------------

def cargar_settings():
    datos = _leer_json(ARCHIVO_SETTINGS, {})
    settings = dict(DEFAULTS)
    settings.update({k: v for k, v in datos.items() if k in DEFAULTS})
    # Compatibilidad con la versión vieja: guardaba "ultima_carpeta".
    if "ultima_carpeta" in datos and datos["ultima_carpeta"]:
        settings.setdefault("carpeta_descargas", datos["ultima_carpeta"])
        if not datos.get("carpeta_descargas"):
            settings["carpeta_descargas"] = datos["ultima_carpeta"]
    return settings


def guardar_settings(settings):
    datos = _leer_json(ARCHIVO_SETTINGS, {})
    datos.update(settings)
    # Se mantiene la clave vieja sincronizada por si se abre la versión Tkinter.
    datos["ultima_carpeta"] = settings.get(
        "carpeta_descargas", datos.get("ultima_carpeta", _DESCARGAS_POR_DEFECTO)
    )
    _escribir_json(ARCHIVO_SETTINGS, datos)


# --- Historial -------------------------------------------------------------

def cargar_historial():
    datos = _leer_json(ARCHIVO_HISTORIAL, [])
    if not isinstance(datos, list):
        return []
    # Entradas viejas no tienen "tipo": eran todas descargas.
    for entrada in datos:
        entrada.setdefault("tipo", "descarga")
        entrada.setdefault("estado", "ok")
    return datos


def guardar_historial(historial):
    _escribir_json(ARCHIVO_HISTORIAL, historial)


def agregar_historial(tipo, titulo, detalle="", carpeta="", estado="ok", origen=""):
    historial = cargar_historial()
    historial.append({
        "tipo": tipo,               # "descarga" | "conversion"
        "titulo": titulo,
        "detalle": detalle,         # formato / calidad / mensaje de error
        "origen": origen,           # url o archivo de entrada
        "carpeta": carpeta,
        "estado": estado,           # "ok" | "error"
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    guardar_historial(historial)
    return historial


def limpiar_historial():
    guardar_historial([])


def borrar_entrada_historial(indice):
    """Borra una entrada por su índice en el historial guardado (orden cronológico)."""
    historial = cargar_historial()
    if 0 <= indice < len(historial):
        historial.pop(indice)
        guardar_historial(historial)
    return historial

"""Mapa de extensiones a categorías (nombres de carpeta en español)."""

from __future__ import annotations

CATEGORIAS: dict[str, set[str]] = {
    "Imágenes": {
        "jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "tif", "svg",
        "heic", "heif", "ico", "raw", "cr2", "cr3", "nef", "arw", "dng",
        "orf", "rw2", "psd", "xcf", "avif",
    },
    "Vídeos": {
        "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "mpg",
        "mpeg", "3gp", "ts", "m2ts", "vob", "ogv",
    },
    "Audio": {
        "mp3", "wav", "flac", "aac", "ogg", "oga", "m4a", "wma", "opus",
        "aiff", "aif", "mid", "midi", "amr",
    },
    "Documentos": {
        "pdf", "doc", "docx", "odt", "rtf", "txt", "md", "tex", "epub",
        "mobi", "pages", "wpd",
    },
    "Hojas de cálculo": {"xls", "xlsx", "ods", "csv", "tsv"},
    "Presentaciones": {"ppt", "pptx", "odp", "key"},
    "Comprimidos": {
        "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "zst", "tgz", "tbz2",
        "lz", "lzma", "iso", "cab",
    },
    "Instaladores": {
        "exe", "msi", "appimage", "deb", "rpm", "pkg", "dmg", "apk",
        "flatpakref", "run", "bin",
    },
    "Código": {
        "py", "js", "mjs", "ts", "jsx", "tsx", "html", "htm", "css", "scss",
        "c", "cpp", "cc", "h", "hpp", "java", "kt", "kts", "rs", "go", "rb",
        "php", "sh", "bash", "fish", "zsh", "ps1", "bat", "sql", "json",
        "xml", "yaml", "yml", "toml", "ini", "cfg", "lua", "pl", "r", "swift",
    },
    "Fuentes": {"ttf", "otf", "woff", "woff2", "eot"},
}

OTROS = "Otros"
CARPETAS = "Carpetas"

# Índice inverso extensión -> categoría.
_INDICE: dict[str, str] = {}
for _cat, _exts in CATEGORIAS.items():
    for _e in _exts:
        _INDICE[_e] = _cat

# Carpetas que la app crea: nunca se tocan al re-escanear (hace la operación repetible).
CARPETAS_CATEGORIA: set[str] = set(CATEGORIAS) | {OTROS, CARPETAS}


def categoria_de(nombre_archivo: str) -> str:
    """Devuelve la categoría de un archivo por su extensión."""
    if "." in nombre_archivo:
        ext = nombre_archivo.rsplit(".", 1)[-1].lower()
    else:
        ext = ""
    return _INDICE.get(ext, OTROS)

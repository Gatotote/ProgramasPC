"""Regenera assets/icono.png a partir de assets/icono.svg (anillo + símbolo de nodos).

El icono se edita en `assets/icono.svg` (Inkscape). Este script solo lo
rasteriza a PNG 256x256. Usa rsvg-convert; si no está, prueba con inkscape.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "assets"
SVG = ASSETS / "icono.svg"
PNG = ASSETS / "icono.png"
TAM = 256

if not SVG.exists():
    sys.exit(f"No existe {SVG}")

if shutil.which("rsvg-convert"):
    cmd = ["rsvg-convert", "-w", str(TAM), "-h", str(TAM), str(SVG), "-o", str(PNG)]
elif shutil.which("inkscape"):
    cmd = ["inkscape", str(SVG), "-w", str(TAM), "-h", str(TAM), "-o", str(PNG)]
else:
    sys.exit("Hace falta rsvg-convert (paquete librsvg) o inkscape.")

subprocess.run(cmd, check=True)
print("escrito:", PNG)

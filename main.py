"""Punto de entrada del Organizador de Archivos.

Ejecutar con:  python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from organizador.ventana import main

if __name__ == "__main__":
    raise SystemExit(main())

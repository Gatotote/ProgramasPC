"""Borrado best-effort de archivos en claro sacados de la bóveda.

En tmpfs (/dev/shm) el contenido ya vive solo en RAM; aun así se sobrescribe
antes de desvincular para no dejar restos en las páginas liberadas. No pretende
resistir un análisis forense de disco (eso lo cubre no escribir nunca en claro
en el disco físico).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB


def shred_file(path: Path) -> None:
    path = Path(path)
    try:
        size = path.stat().st_size
    except OSError:
        return
    try:
        with open(path, "r+b", buffering=0) as f:
            written = 0
            while written < size:
                n = min(_CHUNK, size - written)
                f.write(os.urandom(n))
                written += n
            f.flush()
            os.fsync(f.fileno())
            f.seek(0)
            f.truncate(0)
    except OSError:
        pass
    try:
        path.unlink()
    except OSError:
        pass


def shred_tree(root: Path) -> None:
    root = Path(root)
    if not root.exists():
        return
    for p in sorted(root.rglob("*"), reverse=True):
        if p.is_file() or p.is_symlink():
            shred_file(p)
    shutil.rmtree(root, ignore_errors=True)

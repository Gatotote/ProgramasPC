"""Subclaves derivadas de la clave maestra (MK) por HKDF-SHA256.

Cada uso tiene su propia subclave con un `info` distinto, de modo que un fallo
en un dominio (p. ej. nombres de objeto) no compromete los demás.
"""

from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

INFO_INDEX = b"bovedafacial:index:v1"        # cifra index.enc
INFO_DATA = b"bovedafacial:object-data:v1"   # cifra los chunks
INFO_NAMES = b"bovedafacial:object-names:v1"  # HMAC para los nombres de chunk
INFO_TEMPLATES = b"bovedafacial:face-templates:v1"  # Fase 2: cifra los embeddings


def subkey(mk: bytes, info: bytes, length: int = 32) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    ).derive(mk)

"""Guardado cifrado de la plantilla facial dentro de la bóveda (`faces.enc`).

La plantilla se cifra con una subclave HKDF derivada de la MK, así que solo
existe en claro cuando la bóveda ya está desbloqueada por el PIN. La Fase 3
llama a esto justo después de recuperar la MK y antes del gate facial.
"""

from __future__ import annotations

from pathlib import Path

from ..crypto import container as C
from ..crypto.subkeys import INFO_TEMPLATES, subkey
from .enroll import Template

_AAD_FACES = b"bovedafacial:faces:v1"


def save_template(vault_dir: Path, mk: bytes, template: Template) -> None:
    key = subkey(mk, INFO_TEMPLATES)
    C.write_secret(Path(vault_dir), C.FACES_NAME, key, _AAD_FACES, template.to_bytes())


def load_template(vault_dir: Path, mk: bytes) -> Template | None:
    key = subkey(mk, INFO_TEMPLATES)
    raw = C.read_secret(Path(vault_dir), C.FACES_NAME, key, _AAD_FACES)
    return None if raw is None else Template.from_bytes(raw)


def has_template(vault_dir: Path) -> bool:
    return (Path(vault_dir) / C.FACES_NAME).exists()

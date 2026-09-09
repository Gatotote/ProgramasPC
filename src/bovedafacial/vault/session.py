"""Sesión de bóveda abierta: mantiene la MK y el índice en memoria y ofrece las
operaciones de alto nivel (importar, extraer, listar, eliminar).

Fase 1: sin rostro y sin borrado seguro del original. El desbloqueo real
(PIN -> MK -> gate facial) se monta en la Fase 3 encima de esto.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ..crypto import container as C
from ..crypto.keyslots import (
    DEFAULT_KDF,
    KeySlot,
    generate_recovery_phrase,
    new_master_key,
    unwrap_pin_slot,
    unwrap_recovery_slot,
    wrap_pin_slot,
    wrap_recovery_slot,
)
from . import tree

VAULT_SUFFIX = ".vault"
MIN_PIN_LEN = 6


class VaultError(Exception):
    pass


def _translate(fn):
    """Convierte errores internos (árbol/contenedor) en VaultError para la UI."""
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (tree.TreeError, C.ContainerError) as e:
            raise VaultError(str(e)) from e

    return wrapper


@dataclass
class Session:
    path: Path
    _mk: bytearray
    header: dict
    index: dict
    _dirty: bool = False
    _closed: bool = False

    # --- propiedades internas ---------------------------------------------
    @property
    def mk(self) -> bytes:
        if self._closed:
            raise VaultError("La sesión de bóveda ya está cerrada.")
        return bytes(self._mk)

    @property
    def chunk_size(self) -> int:
        return self.header["chunk_size"]

    # --- operaciones -----------------------------------------------------
    @_translate
    def import_path(self, src: Path, dest_dir: str = "/") -> int:
        """Importa un archivo o un árbol de carpetas. Devuelve nº de archivos."""
        src = Path(src)
        if not src.exists():
            raise VaultError(f"No existe el origen: {src}")
        count = 0
        if src.is_file():
            self._import_file(src, dest_dir, src.name)
            count = 1
        else:
            base = dest_dir.rstrip("/") + "/" + src.name
            tree.ensure_dir(self.index, base)
            for root, _dirs, files in os.walk(src):
                rel = Path(root).relative_to(src)
                vdir = base if rel == Path(".") else f"{base}/{rel.as_posix()}"
                tree.ensure_dir(self.index, vdir)
                for fname in sorted(files):
                    self._import_file(Path(root) / fname, vdir, fname)
                    count += 1
        self._dirty = True
        return count

    def _import_file(self, fpath: Path, vdir: str, name: str) -> None:
        data = fpath.read_bytes()
        object_id = C.new_object_id()
        descriptor = C.write_object(self.path, self.mk, object_id, data, self.chunk_size)
        tree.add_file(self.index, vdir, name, descriptor, fpath.stat().st_mtime)

    @_translate
    def list_dir(self, path: str = "/") -> list[dict]:
        return tree.listing(tree.get_node(self.index, path))

    @_translate
    def extract(self, vpath: str, dest: Path) -> Path:
        """Extrae un archivo o una carpeta a `dest` (en claro)."""
        dest = Path(dest)
        node = tree.get_node(self.index, vpath)
        if node["type"] == "file":
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(C.read_object(self.path, self.mk, node))
            os.utime(dest, (node["mtime"], node["mtime"]))
            return dest
        self._extract_dir(node, dest)
        return dest

    def _extract_dir(self, node: dict, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        for name, child in node["entries"].items():
            target = dest / name
            if child["type"] == "dir":
                self._extract_dir(child, target)
            else:
                target.write_bytes(C.read_object(self.path, self.mk, child))
                os.utime(target, (child["mtime"], child["mtime"]))

    @_translate
    def remove(self, vpath: str) -> None:
        for descriptor in tree.remove(self.index, vpath):
            C.delete_object(self.path, self.mk, descriptor)
        self._dirty = True

    def save(self) -> None:
        if self._dirty and not self._closed:
            C.encrypt_index(self.path, self.mk, self.index)
            self._dirty = False

    def close(self) -> None:
        if self._closed:
            return
        self.save()
        for i in range(len(self._mk)):   # borrado best-effort (Python no garantiza)
            self._mk[i] = 0
        self._closed = True

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# --- creación y desbloqueo -------------------------------------------------

def _validate_pin(pin: str) -> None:
    if len(pin) < MIN_PIN_LEN:
        raise VaultError(f"El PIN debe tener al menos {MIN_PIN_LEN} caracteres.")


def create_vault(path: os.PathLike | str, pin: str, *, kdf: dict | None = None) -> tuple[str, Session]:
    """Crea una bóveda nueva. Devuelve (frase_de_recuperación, sesión abierta).
    La frase solo se devuelve aquí: hay que apuntarla en papel."""
    _validate_pin(pin)
    path = Path(path)
    if path.suffix != VAULT_SUFFIX:
        path = path.with_suffix(VAULT_SUFFIX)
    kdf = kdf or DEFAULT_KDF

    mk = new_master_key()
    phrase = generate_recovery_phrase()
    pin_slot = wrap_pin_slot(pin, mk, kdf)
    recovery_slot = wrap_recovery_slot(phrase, mk)

    C.init_layout(path)
    header = C.write_header(path, pin_slot=pin_slot, recovery_slot=recovery_slot, kdf=kdf)
    C.encrypt_index(path, mk, tree.empty_root())

    session = Session(path=path, _mk=bytearray(mk), header=header, index=tree.empty_root())
    return phrase, session


def _open(path: Path, mk: bytes) -> Session:
    header = C.read_header(path)
    index = C.decrypt_index(path, mk)
    return Session(path=path, _mk=bytearray(mk), header=header, index=index)


@_translate
def unlock_with_pin(path: os.PathLike | str, pin: str) -> Session:
    path = Path(path)
    header = C.read_header(path)
    slot = KeySlot.from_json(header["keyslots"]["pin"])
    mk = unwrap_pin_slot(pin, slot, header["kdf"])   # lanza WrongSecret si falla
    return _open(path, mk)


@_translate
def unlock_with_recovery(path: os.PathLike | str, phrase: str) -> Session:
    path = Path(path)
    header = C.read_header(path)
    slot = KeySlot.from_json(header["keyslots"]["recovery"])
    mk = unwrap_recovery_slot(phrase, slot)          # lanza WrongSecret si falla
    return _open(path, mk)

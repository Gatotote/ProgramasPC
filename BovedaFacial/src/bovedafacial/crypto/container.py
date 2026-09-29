"""Contenedor en disco de la bóveda.

Estructura de un directorio `algo.vault/`:

    header.json   -> metadatos NO secretos: versión, id, params Argon2id y los
                     dos keyslots con la MK envuelta.
    index.enc     -> árbol real de carpetas/archivos (nombres, tamaños, fechas),
                     cifrado con AES-256-GCM.
    objects/xx/.. -> datos troceados en chunks de 4 MiB, cada chunk cifrado por
                     separado. El nombre de cada chunk es un HMAC, no hay texto
                     legible ni extensiones.
    .noindex, .trackerignore, .metadata_never_index
                  -> centinelas para que los indexadores de escritorio lo ignoren.

Nada del contenido aparece en `locate`, en el indexador de KDE (Baloo) ni al
abrir el `.vault` en un explorador de archivos: solo se ven blobs cifrados.
"""

from __future__ import annotations

import hmac
import json
import os
import time
from hashlib import sha256
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .keyslots import DEFAULT_KDF, KeySlot
from .subkeys import INFO_DATA, INFO_INDEX, INFO_NAMES, subkey

CONTAINER_VERSION = 1
HEADER_NAME = "header.json"
INDEX_NAME = "index.enc"
FACES_NAME = "faces.enc"
AUDIT_NAME = "audit.enc"
OBJECTS_DIR = "objects"
NOINDEX_SENTINELS = (".noindex", ".trackerignore", ".metadata_never_index")

DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024
NONCE_LEN = 12
OBJECT_ID_LEN = 16

_AAD_INDEX = b"bovedafacial:index:v1"


class ContainerError(Exception):
    pass


# --- cabecera --------------------------------------------------------------

DEFAULT_POLICY = {
    "require_face": True,       # exigir rostro si hay plantilla enrolada
    "auto_lock_seconds": 180,   # bloqueo por inactividad (lo aplica la UI)
    "face_threshold": None,     # None = usar el de la plantilla
}


def write_header(
    vault_dir: Path,
    *,
    pin_slot: KeySlot,
    recovery_slot: KeySlot,
    kdf: dict = DEFAULT_KDF,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    policy: dict | None = None,
) -> dict:
    header = {
        "version": CONTAINER_VERSION,
        "vault_id": os.urandom(8).hex(),
        "created": time.time(),
        "kdf": kdf,
        "chunk_size": chunk_size,
        "keyslots": {
            "pin": pin_slot.to_json(),
            "recovery": recovery_slot.to_json(),
        },
        "policy": {**DEFAULT_POLICY, **(policy or {})},
        # estado en claro (no hay MK disponible antes de acertar el PIN)
        "backoff": {"failures": 0, "locked_until": 0.0},
        "stats": {"last_unlock": None, "failed_total": 0},
    }
    _atomic_write(vault_dir / HEADER_NAME, json.dumps(header, indent=2).encode("utf-8"))
    return header


def read_header(vault_dir: Path) -> dict:
    try:
        raw = (vault_dir / HEADER_NAME).read_bytes()
    except FileNotFoundError as e:
        raise ContainerError(f"No es una bóveda válida: falta {HEADER_NAME}") from e
    header = json.loads(raw)
    if header.get("version") != CONTAINER_VERSION:
        raise ContainerError(f"Versión de contenedor no soportada: {header.get('version')}")
    header.setdefault("policy", dict(DEFAULT_POLICY))
    header.setdefault("backoff", {"failures": 0, "locked_until": 0.0})
    header.setdefault("stats", {"last_unlock": None, "failed_total": 0})
    return header


def save_header(vault_dir: Path, header: dict) -> None:
    _atomic_write(vault_dir / HEADER_NAME, json.dumps(header, indent=2).encode("utf-8"))


def secret_exists(vault_dir: Path, name: str) -> bool:
    return (Path(vault_dir) / name).exists()


def init_layout(vault_dir: Path) -> None:
    vault_dir.mkdir(parents=True, exist_ok=False)
    (vault_dir / OBJECTS_DIR).mkdir()
    for name in NOINDEX_SENTINELS:
        (vault_dir / name).write_bytes(b"")


# --- índice --------------------------------------------------------------

def encrypt_index(vault_dir: Path, mk: bytes, index: dict) -> None:
    key = subkey(mk, INFO_INDEX)
    nonce = os.urandom(NONCE_LEN)
    blob = AESGCM(key).encrypt(
        nonce, json.dumps(index, separators=(",", ":")).encode("utf-8"), _AAD_INDEX
    )
    _atomic_write(vault_dir / INDEX_NAME, nonce + blob)


def decrypt_index(vault_dir: Path, mk: bytes) -> dict:
    raw = (vault_dir / INDEX_NAME).read_bytes()
    key = subkey(mk, INFO_INDEX)
    nonce, blob = raw[:NONCE_LEN], raw[NONCE_LEN:]
    try:
        plain = AESGCM(key).decrypt(nonce, blob, _AAD_INDEX)
    except Exception as e:
        raise ContainerError("El índice está corrupto o la clave no corresponde.") from e
    return json.loads(plain)


# --- ficheros secretos genéricos (p. ej. faces.enc) -----------------------

def write_secret(vault_dir: Path, name: str, key: bytes, aad: bytes, data: bytes) -> None:
    nonce = os.urandom(NONCE_LEN)
    _atomic_write(vault_dir / name, nonce + AESGCM(key).encrypt(nonce, data, aad))


def read_secret(vault_dir: Path, name: str, key: bytes, aad: bytes) -> bytes | None:
    path = vault_dir / name
    if not path.exists():
        return None
    raw = path.read_bytes()
    nonce, blob = raw[:NONCE_LEN], raw[NONCE_LEN:]
    try:
        return AESGCM(key).decrypt(nonce, blob, aad)
    except Exception as e:
        raise ContainerError(f"{name} está corrupto o la clave no corresponde.") from e


# --- objetos (datos troceados) -----------------------------------------------

def new_object_id() -> str:
    return os.urandom(OBJECT_ID_LEN).hex()


def _chunk_name(mk: bytes, object_id: str, seq: int) -> str:
    name_key = subkey(mk, INFO_NAMES)
    msg = bytes.fromhex(object_id) + seq.to_bytes(4, "big")
    return hmac.new(name_key, msg, sha256).hexdigest()


def _chunk_path(vault_dir: Path, name: str) -> Path:
    return vault_dir / OBJECTS_DIR / name[:2] / name


def write_object(vault_dir: Path, mk: bytes, object_id: str, data: bytes, chunk_size: int) -> dict:
    """Trocea, cifra y escribe un objeto. Devuelve su descriptor para el índice."""
    data_key = subkey(mk, INFO_DATA)
    aead = AESGCM(data_key)
    chunks: list[int] = []
    for seq, start in enumerate(range(0, max(len(data), 1), chunk_size)):
        piece = data[start:start + chunk_size]
        nonce = os.urandom(NONCE_LEN)
        aad = bytes.fromhex(object_id) + seq.to_bytes(4, "big")
        blob = nonce + aead.encrypt(nonce, piece, aad)
        path = _chunk_path(vault_dir, _chunk_name(mk, object_id, seq))
        path.parent.mkdir(exist_ok=True)
        _atomic_write(path, blob)
        chunks.append(len(piece))
        if not data:  # objeto vacío: un único chunk de 0 bytes
            break
    return {
        "object_id": object_id,
        "size": len(data),
        "chunks": chunks,
        "sha256": sha256(data).hexdigest(),
    }


def read_object(vault_dir: Path, mk: bytes, descriptor: dict) -> bytes:
    data_key = subkey(mk, INFO_DATA)
    aead = AESGCM(data_key)
    object_id = descriptor["object_id"]
    out = bytearray()
    for seq in range(len(descriptor["chunks"])):
        path = _chunk_path(vault_dir, _chunk_name(mk, object_id, seq))
        raw = path.read_bytes()
        nonce, blob = raw[:NONCE_LEN], raw[NONCE_LEN:]
        aad = bytes.fromhex(object_id) + seq.to_bytes(4, "big")
        try:
            out += aead.decrypt(nonce, blob, aad)
        except Exception as e:
            raise ContainerError(f"Chunk {seq} del objeto {object_id} corrupto.") from e
    data = bytes(out)
    if len(data) != descriptor["size"] or sha256(data).hexdigest() != descriptor["sha256"]:
        raise ContainerError(f"El objeto {object_id} no supera la verificación de integridad.")
    return data


def delete_object(vault_dir: Path, mk: bytes, descriptor: dict) -> None:
    object_id = descriptor["object_id"]
    for seq in range(len(descriptor["chunks"])):
        path = _chunk_path(vault_dir, _chunk_name(mk, object_id, seq))
        path.unlink(missing_ok=True)


# --- utilidad ------------------------------------------------------------

def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

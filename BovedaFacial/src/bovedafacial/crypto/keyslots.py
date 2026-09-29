"""Keyslots estilo LUKS: la clave maestra (MK) se guarda envuelta por dos KEK
independientes, una derivada del PIN (Argon2id) y otra de la frase de
recuperación de 24 palabras (BIP39 -> HKDF). Cualquiera de las dos abre la MK.

La biometría NO interviene aquí: no es un secreto ni es estable bit a bit, así
que nunca se usa como material de clave. El rostro es una puerta de
autenticación que se comprueba *después* de recuperar la MK con el PIN.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from mnemonic import Mnemonic

MK_LEN = 32        # clave maestra de 256 bits
SALT_LEN = 16
NONCE_LEN = 12

# Parámetros Argon2id por defecto. Se guardan en la cabecera para poder subirlos
# en el futuro sin invalidar bóvedas antiguas. El PIN es de baja entropía, así
# que el coste alto es deliberado (ataque offline sobre una bóveda robada).
DEFAULT_KDF = {
    "type": "argon2id",
    "time_cost": 3,
    "memory_cost": 262144,   # 256 MiB
    "parallelism": 4,
}

_AAD_PIN = b"bovedafacial:keyslot:pin:v1"
_AAD_RECOVERY = b"bovedafacial:keyslot:recovery:v1"
_HKDF_RECOVERY_INFO = b"bovedafacial:recovery-kek:v1"

_MNEMO = Mnemonic("english")


class WrongSecret(Exception):
    """El PIN o la frase de recuperación son incorrectos."""


def new_master_key() -> bytes:
    return os.urandom(MK_LEN)


def generate_recovery_phrase() -> str:
    """24 palabras BIP39 (256 bits de entropía + checksum)."""
    return _MNEMO.generate(strength=256)


def normalize_phrase(phrase: str) -> str:
    return " ".join(phrase.lower().split())


def phrase_is_valid(phrase: str) -> bool:
    return _MNEMO.check(normalize_phrase(phrase))


# --- derivación de KEK -------------------------------------------------------

def _kek_from_pin(pin: str, salt: bytes, kdf: dict) -> bytes:
    return hash_secret_raw(
        secret=pin.encode("utf-8"),
        salt=salt,
        time_cost=kdf["time_cost"],
        memory_cost=kdf["memory_cost"],
        parallelism=kdf["parallelism"],
        hash_len=MK_LEN,
        type=Type.ID,
    )


def _kek_from_phrase(phrase: str, salt: bytes) -> bytes:
    norm = normalize_phrase(phrase)
    if not _MNEMO.check(norm):
        raise WrongSecret("La frase de recuperación no es válida (checksum BIP39).")
    entropy = bytes(_MNEMO.to_entropy(norm))  # 32 bytes
    return HKDF(
        algorithm=hashes.SHA256(),
        length=MK_LEN,
        salt=salt,
        info=_HKDF_RECOVERY_INFO,
    ).derive(entropy)


# --- modelo de keyslot -----------------------------------------------------

@dataclass
class KeySlot:
    salt: bytes
    nonce: bytes
    wrapped_mk: bytes

    def to_json(self) -> dict:
        return {
            "salt": self.salt.hex(),
            "nonce": self.nonce.hex(),
            "wrapped_mk": self.wrapped_mk.hex(),
        }

    @classmethod
    def from_json(cls, d: dict) -> "KeySlot":
        return cls(
            bytes.fromhex(d["salt"]),
            bytes.fromhex(d["nonce"]),
            bytes.fromhex(d["wrapped_mk"]),
        )


def wrap_pin_slot(pin: str, mk: bytes, kdf: dict) -> KeySlot:
    salt = os.urandom(SALT_LEN)
    kek = _kek_from_pin(pin, salt, kdf)
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(kek).encrypt(nonce, mk, _AAD_PIN)
    return KeySlot(salt, nonce, ct)


def unwrap_pin_slot(pin: str, slot: KeySlot, kdf: dict) -> bytes:
    kek = _kek_from_pin(pin, slot.salt, kdf)
    try:
        return AESGCM(kek).decrypt(slot.nonce, slot.wrapped_mk, _AAD_PIN)
    except Exception as e:  # cryptography.exceptions.InvalidTag
        raise WrongSecret("PIN incorrecto.") from e


def wrap_recovery_slot(phrase: str, mk: bytes) -> KeySlot:
    salt = os.urandom(SALT_LEN)
    kek = _kek_from_phrase(phrase, salt)
    nonce = os.urandom(NONCE_LEN)
    ct = AESGCM(kek).encrypt(nonce, mk, _AAD_RECOVERY)
    return KeySlot(salt, nonce, ct)


def unwrap_recovery_slot(phrase: str, slot: KeySlot) -> bytes:
    kek = _kek_from_phrase(phrase, slot.salt)  # ya lanza WrongSecret si no es válida
    try:
        return AESGCM(kek).decrypt(slot.nonce, slot.wrapped_mk, _AAD_RECOVERY)
    except Exception as e:
        raise WrongSecret("Frase de recuperación incorrecta para esta bóveda.") from e

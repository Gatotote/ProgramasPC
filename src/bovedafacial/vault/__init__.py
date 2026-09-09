"""Capa lógica de la bóveda: árbol de carpetas y sesión abierta en memoria."""

from .session import (
    FaceRejected,
    Session,
    VaultError,
    VaultLocked,
    create_vault,
    open_vault,
    unlock_with_pin,
    unlock_with_recovery,
    vault_status,
)

__all__ = [
    "Session",
    "VaultError",
    "VaultLocked",
    "FaceRejected",
    "create_vault",
    "open_vault",
    "unlock_with_pin",
    "unlock_with_recovery",
    "vault_status",
]

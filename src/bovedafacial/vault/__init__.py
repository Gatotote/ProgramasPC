"""Capa lógica de la bóveda: árbol de carpetas y sesión abierta en memoria."""

from .session import Session, VaultError, create_vault, unlock_with_pin, unlock_with_recovery

__all__ = [
    "Session",
    "VaultError",
    "create_vault",
    "unlock_with_pin",
    "unlock_with_recovery",
]

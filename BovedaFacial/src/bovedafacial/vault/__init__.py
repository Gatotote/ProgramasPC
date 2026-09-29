"""Capa lógica de la bóveda: árbol, elementos tipados, registro de actividad y
sesión abierta en memoria."""

from . import audit
from .items import FIELD_SPECS, KIND_LABELS, FieldSpec, ItemKind, spec_for
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
    "audit",
    "ItemKind",
    "FieldSpec",
    "FIELD_SPECS",
    "KIND_LABELS",
    "spec_for",
]

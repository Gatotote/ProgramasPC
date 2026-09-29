"""Elementos con estructura que guarda la bóveda además de archivos: contraseñas,
tarjetas, cuentas, contactos, testamentos, seguros y notas.

Cada elemento es una entrada del índice (`type: "item"`) con:
  - `kind`: el tipo (uno de ItemKind).
  - `fields`: un dict pequeño; va cifrado *dentro* de index.enc, no necesita
    objeto propio.
  - `attachments`: archivos adjuntos (descriptor de objeto troceado), opcional.

Los campos marcados `secret=True` los enmascara la GUI por defecto.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ItemKind(str, Enum):
    PASSWORD = "password"
    CARD = "card"
    ACCOUNT = "account"
    CONTACT = "contact"
    WILL = "will"
    INSURANCE = "insurance"
    NOTE = "note"


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    secret: bool = False
    multiline: bool = False


# El "nombre" del elemento es su clave en el árbol; aquí van solo los datos.
FIELD_SPECS: dict[ItemKind, list[FieldSpec]] = {
    ItemKind.PASSWORD: [
        FieldSpec("usuario", "Usuario"),
        FieldSpec("password", "Contraseña", secret=True),
        FieldSpec("url", "Sitio / URL"),
        FieldSpec("totp", "Semilla TOTP", secret=True),
        FieldSpec("notas", "Notas", multiline=True),
    ],
    ItemKind.CARD: [
        FieldSpec("titular", "Titular"),
        FieldSpec("numero", "Número", secret=True),
        FieldSpec("vence", "Vence (MM/AA)"),
        FieldSpec("cvv", "CVV", secret=True),
        FieldSpec("pin", "PIN", secret=True),
        FieldSpec("banco", "Banco / emisor"),
        FieldSpec("notas", "Notas", multiline=True),
    ],
    ItemKind.ACCOUNT: [
        FieldSpec("institucion", "Institución"),
        FieldSpec("numero", "Número de cuenta", secret=True),
        FieldSpec("clabe", "CLABE", secret=True),
        FieldSpec("titular", "Titular"),
        FieldSpec("saldo", "Saldo aproximado"),
        FieldSpec("notas", "Notas", multiline=True),
    ],
    ItemKind.CONTACT: [
        FieldSpec("parentesco", "Parentesco / relación"),
        FieldSpec("telefono", "Teléfono"),
        FieldSpec("correo", "Correo"),
        FieldSpec("direccion", "Dirección", multiline=True),
        FieldSpec("notas", "Notas", multiline=True),
    ],
    ItemKind.WILL: [
        FieldSpec("ubicacion", "Dónde está el documento"),
        FieldSpec("albacea", "Albacea"),
        FieldSpec("notaria", "Notaría"),
        FieldSpec("fecha", "Fecha"),
        FieldSpec("notas", "Notas", multiline=True),
    ],
    ItemKind.INSURANCE: [
        FieldSpec("aseguradora", "Aseguradora"),
        FieldSpec("poliza", "Nº de póliza", secret=True),
        FieldSpec("cobertura", "Cobertura"),
        FieldSpec("beneficiario", "Beneficiario"),
        FieldSpec("vence", "Vence"),
        FieldSpec("prima", "Prima"),
        FieldSpec("notas", "Notas", multiline=True),
    ],
    ItemKind.NOTE: [
        FieldSpec("contenido", "Contenido", multiline=True),
    ],
}

KIND_LABELS: dict[ItemKind, str] = {
    ItemKind.PASSWORD: "Contraseña",
    ItemKind.CARD: "Tarjeta",
    ItemKind.ACCOUNT: "Cuenta",
    ItemKind.CONTACT: "Contacto",
    ItemKind.WILL: "Testamento",
    ItemKind.INSURANCE: "Seguro",
    ItemKind.NOTE: "Nota",
}


def coerce_kind(kind) -> ItemKind:
    if isinstance(kind, ItemKind):
        return kind
    try:
        return ItemKind(str(kind).lower())
    except ValueError as e:
        opciones = ", ".join(k.value for k in ItemKind)
        raise ValueError(f"Tipo de elemento desconocido: {kind!r}. Opciones: {opciones}") from e


def spec_for(kind) -> list[FieldSpec]:
    return FIELD_SPECS[coerce_kind(kind)]


def secret_keys(kind) -> set[str]:
    return {f.key for f in spec_for(kind) if f.secret}


def clean_fields(kind, fields: dict) -> dict:
    """Deja solo las claves conocidas del tipo, como texto y sin vacías."""
    allowed = {f.key for f in spec_for(kind)}
    out: dict[str, str] = {}
    for k, v in (fields or {}).items():
        if k in allowed and v not in (None, ""):
            out[k] = str(v)
    return out

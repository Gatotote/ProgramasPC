"""Generador de contraseñas. Puro y sin dependencias: lo usan la CLI y la GUI."""

from __future__ import annotations

import secrets

# sin caracteres ambiguos (l 1 I | O 0) en los conjuntos "sin ambiguos"
_UP = "ABCDEFGHJKLMNPQRSTUVWXYZ"
_UP_FULL = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LO = "abcdefghijkmnopqrstuvwxyz"
_LO_FULL = "abcdefghijklmnopqrstuvwxyz"
_NUM = "23456789"
_NUM_FULL = "0123456789"
_SYM = "!@#$%^&*-_=+?"
_SYM_FULL = "!@#$%^&*-_=+?.,:;()[]{}"


def generate(
    length: int = 20,
    *,
    upper: bool = True,
    lower: bool = True,
    digits: bool = True,
    symbols: bool = True,
    avoid_ambiguous: bool = True,
) -> str:
    up = _UP if avoid_ambiguous else _UP_FULL
    lo = _LO if avoid_ambiguous else _LO_FULL
    num = _NUM if avoid_ambiguous else _NUM_FULL
    sym = _SYM if avoid_ambiguous else _SYM_FULL

    groups = [g for g, on in ((up, upper), (lo, lower), (num, digits), (sym, symbols)) if on]
    if not groups:
        raise ValueError("Hay que permitir al menos un tipo de carácter.")
    length = max(length, len(groups))
    pool = "".join(groups)

    # al menos uno de cada grupo elegido, el resto del pool completo
    chars = [secrets.choice(g) for g in groups]
    chars += [secrets.choice(pool) for _ in range(length - len(groups))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def strength(pw: str) -> str:
    """Etiqueta rápida (no es zxcvbn): 'débil' | 'aceptable' | 'fuerte'."""
    classes = sum((
        any(c.isupper() for c in pw),
        any(c.islower() for c in pw),
        any(c.isdigit() for c in pw),
        any(not c.isalnum() for c in pw),
    ))
    n = len(pw)
    if n >= 16 and classes >= 3:
        return "fuerte"
    if n >= 12 and classes >= 2:
        return "aceptable"
    return "débil"

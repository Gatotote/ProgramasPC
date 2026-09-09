"""Cálculo del indicador de seguridad 🟢🟡🔴 a partir del estado de la bóveda."""

from __future__ import annotations

from ..pwgen import strength
from ..vault import ItemKind, vault_status

LEVEL_LABEL = {"ok": "Seguro", "warn": "Advertencia", "risk": "Riesgo detectado"}
LEVEL_DOT = {"ok": "🟢", "warn": "🟡", "risk": "🔴"}


def weak_passwords(session) -> list[str]:
    """Rutas de credenciales con contraseña débil o repetida."""
    seen: dict[str, str] = {}
    bad: list[str] = []
    for row in session.list_items("/", kind=ItemKind.PASSWORD):
        pw = session.get_item(row["path"])["fields"].get("password", "")
        if not pw:
            continue
        if strength(pw) == "débil":
            bad.append(row["path"])
        elif pw in seen.values():
            bad.append(row["path"])
        seen[row["path"]] = pw
    return bad


def compute(session) -> dict:
    """Devuelve {level, label, reasons: [(sev, texto)], weak: [...]}."""
    st = vault_status(session.path)
    reasons: list[tuple[str, str]] = []
    level = "ok"

    if st["locked_for"] > 0:
        reasons.append(("risk", f"Bloqueada por intentos fallidos ({st['locked_for']:.0f} s)."))
        level = "risk"
    if st["wipe_flag"]:
        reasons.append(("risk", "Se alcanzó el límite de intentos fallidos."))
        level = "risk"

    if st["require_face"] and not st["has_face"]:
        reasons.append(("warn", "No hay rostro enrolado; se entra solo con PIN."))
        level = _raise(level, "warn")

    weak = weak_passwords(session)
    if weak:
        reasons.append(("warn", f"{len(weak)} contraseña(s) débil(es) o repetida(s)."))
        level = _raise(level, "warn")

    last_backup = session.header.get("stats", {}).get("last_backup")
    if last_backup is None:
        reasons.append(("warn", "La bóveda nunca se ha respaldado."))
        level = _raise(level, "warn")
    else:
        import time
        days = (time.time() - last_backup) / 86400
        if days > 30:
            reasons.append(("warn", f"Último respaldo hace {days:.0f} días."))
            level = _raise(level, "warn")

    summ = session.activity_summary()
    if summ["blocked_attempts_24h"]:
        reasons.append(("warn", f"{summ['blocked_attempts_24h']} intento(s) bloqueado(s) en 24 h."))
        level = _raise(level, "warn")

    if not reasons:
        reasons.append(("ok", "Todo en orden."))

    return {"level": level, "label": LEVEL_LABEL[level], "dot": LEVEL_DOT[level],
            "reasons": reasons, "weak": weak}


def _raise(current: str, to: str) -> str:
    order = {"ok": 0, "warn": 1, "risk": 2}
    return to if order[to] > order[current] else current

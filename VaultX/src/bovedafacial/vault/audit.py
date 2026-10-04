"""Registro de actividad cifrado (`audit.enc`) para el panel de la GUI.

Se guarda como una lista JSON cifrada con una subclave HKDF de la MK; se reescribe
entera en cada `record()` (los eventos son diminutos y se recorta a los últimos
`MAX_EVENTS`). Los intentos fallidos de PIN/rostro NO caben aquí (ocurren antes
de tener MK) — esos viven en `header["stats"]` en claro.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from ..crypto import container as C
from ..crypto.subkeys import INFO_AUDIT, subkey

MAX_EVENTS = 500
_AAD = b"bovedafacial:audit:v1"

# tipos de evento conocidos (texto libre, pero esto documenta el vocabulario)
UNLOCK_OK = "unlock_ok"
LOCK = "lock"
ENROLL = "enroll"
ITEM_ADD = "item_add"
ITEM_UPDATE = "item_update"
ITEM_REMOVE = "item_remove"
FILE_IMPORT = "file_import"
FILE_OPEN = "file_open"
FILE_EXPORT = "file_export"


def _key(mk: bytes) -> bytes:
    return subkey(mk, INFO_AUDIT)


def load(vault_dir, mk: bytes) -> list[dict]:
    raw = C.read_secret(Path(vault_dir), C.AUDIT_NAME, _key(mk), _AAD)
    if raw is None:
        return []
    try:
        events = json.loads(raw)
        return events if isinstance(events, list) else []
    except json.JSONDecodeError:
        return []


def record(session, kind: str, detail: str = "", *, count: int = 1, ts: float | None = None) -> None:
    """Añade un evento. `session` solo necesita `.path` y `.mk`."""
    events = load(session.path, session.mk)
    events.append({
        "ts": time.time() if ts is None else ts,
        "kind": kind,
        "detail": detail,
        "count": count,
    })
    if len(events) > MAX_EVENTS:
        events = events[-MAX_EVENTS:]
    C.write_secret(Path(session.path), C.AUDIT_NAME, _key(session.mk), _AAD,
                   json.dumps(events, separators=(",", ":")).encode("utf-8"))


def recent(session, limit: int = 50, kind: str | None = None) -> list[dict]:
    events = load(session.path, session.mk)
    if kind is not None:
        events = [e for e in events if e.get("kind") == kind]
    return events[-limit:][::-1]   # más reciente primero


def summary(session) -> dict:
    """Cifras para el dashboard de actividad."""
    events = load(session.path, session.mk)
    now = time.time()
    day_ago = now - 86400
    stats = session.header.get("stats", {})

    def _count(kinds, since=None):
        return sum(e.get("count", 1) for e in events
                   if e["kind"] in kinds and (since is None or e["ts"] >= since))

    fail_times = stats.get("fail_times", [])
    blocked_24h = sum(1 for t in fail_times if t >= day_ago)

    return {
        "last_unlock": stats.get("last_unlock"),
        "files_added_today": _count({FILE_IMPORT}, day_ago),
        "items_added_today": _count({ITEM_ADD}, day_ago),
        "blocked_attempts_24h": blocked_24h,
        "failed_total": stats.get("failed_total", 0),
        "events": len(events),
    }

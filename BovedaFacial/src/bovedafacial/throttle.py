"""Política de reintentos: bloqueo creciente tras fallos consecutivos de
desbloqueo (PIN o rostro). Puro (solo `time` + dataclass), sin numpy, para que
lo pueda usar tanto `vault/` como `face/`.

El estado se guarda en `header.json` (en claro): la biometría y la MK no están
disponibles antes de acertar el PIN, así que no se puede cifrar. Es un freno
para intentos en vivo en la UI y un disuasorio ("se borra tras N"), no una
defensa contra quien ya tiene acceso al sistema de archivos (ver el modelo de
amenaza en el README).
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class BackoffPolicy:
    base_delay_s: float = 2.0
    factor: float = 3.0
    max_delay_s: float = 900.0       # 15 min de tope por intento
    hard_limit: int | None = 15      # None = nunca borra; la bóveda decide qué hacer
    failures: int = 0
    locked_until: float = 0.0

    def register_failure(self, *, now: float | None = None) -> float:
        now = time.time() if now is None else now
        self.failures += 1
        delay = min(self.base_delay_s * (self.factor ** (self.failures - 1)), self.max_delay_s)
        self.locked_until = now + delay
        return self.locked_until

    def register_success(self) -> None:
        self.failures = 0
        self.locked_until = 0.0

    def remaining(self, *, now: float | None = None) -> float:
        now = time.time() if now is None else now
        return max(0.0, self.locked_until - now)

    @property
    def is_locked(self) -> bool:
        return self.remaining() > 0.0

    @property
    def wiped(self) -> bool:
        return self.hard_limit is not None and self.failures >= self.hard_limit

    def to_dict(self) -> dict:
        return {"failures": self.failures, "locked_until": self.locked_until}

    def load_state(self, d: dict | None) -> "BackoffPolicy":
        d = d or {}
        self.failures = int(d.get("failures", 0))
        self.locked_until = float(d.get("locked_until", 0.0))
        return self

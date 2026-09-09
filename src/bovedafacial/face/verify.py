"""Comparación de un embedding contra la plantilla enrolada + política de
reintentos (backoff exponencial) para frenar ataques por fuerza bruta.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

# Umbral por defecto de similitud coseno para antelopev2 (ResNet100 glint360k).
# Con embeddings L2-normalizados: >0.45 suele ser la misma persona; se puede
# subir a 0.5-0.55 para una bóveda si se prioriza rechazar impostores.
DEFAULT_THRESHOLD = 0.45


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float32).ravel()
    b = np.asarray(b, dtype=np.float32).ravel()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)


def score_against(embedding: np.ndarray, templates: np.ndarray, *, top_k: int = 3) -> float:
    """Similitud del embedding con la plantilla: media de las `top_k` mejores
    coincidencias (robusto a alguna foto de enrolado mala)."""
    templates = np.atleast_2d(np.asarray(templates, dtype=np.float32))
    e = np.asarray(embedding, dtype=np.float32).ravel()
    e = e / (np.linalg.norm(e) + 1e-9)
    t = templates / (np.linalg.norm(templates, axis=1, keepdims=True) + 1e-9)
    sims = t @ e
    k = min(top_k, sims.shape[0])
    return float(np.sort(sims)[-k:].mean())


@dataclass
class VerifyResult:
    matched: bool
    score: float
    threshold: float


def verify(embedding: np.ndarray, templates: np.ndarray, *,
           threshold: float = DEFAULT_THRESHOLD, top_k: int = 3) -> VerifyResult:
    s = score_against(embedding, templates, top_k=top_k)
    return VerifyResult(matched=s >= threshold, score=s, threshold=threshold)


@dataclass
class BackoffPolicy:
    """Bloqueo creciente tras fallos consecutivos. Serializable a dict para
    persistirlo junto a la bóveda (lo hará la Fase 3)."""

    base_delay_s: float = 2.0
    factor: float = 3.0
    max_delay_s: float = 900.0
    hard_limit: int | None = 15      # None = sin borrado; la Fase 3 puede actuar aquí
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

    def load_state(self, d: dict) -> "BackoffPolicy":
        self.failures = int(d.get("failures", 0))
        self.locked_until = float(d.get("locked_until", 0.0))
        return self

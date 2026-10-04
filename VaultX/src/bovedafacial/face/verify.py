"""Comparación de un embedding contra la plantilla enrolada + política de
reintentos (backoff exponencial) para frenar ataques por fuerza bruta.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Reexportado por compatibilidad: BackoffPolicy vive ahora en bovedafacial.throttle
from ..throttle import BackoffPolicy  # noqa: F401

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

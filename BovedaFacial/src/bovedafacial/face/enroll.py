"""Enrolado: convierte una tanda de frames buenos del usuario en una plantilla
(varios embeddings de 512-d) lista para guardarse cifrada dentro de la bóveda.
"""

from __future__ import annotations

import io
import time
from dataclasses import dataclass, field

import numpy as np

from .engine import EMBED_DIM, FaceEngine
from .quality import QualityGate, sharpness
from .types import FaceObs
from .verify import DEFAULT_THRESHOLD

TEMPLATE_MAGIC = b"BFTPL1\n"


class EnrollError(Exception):
    pass


@dataclass
class Template:
    embeddings: np.ndarray          # (M, 512) float32, cada fila L2-normalizada
    model_pack: str
    threshold: float = DEFAULT_THRESHOLD
    created: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        e = np.atleast_2d(np.asarray(self.embeddings, dtype=np.float32))
        e = e / (np.linalg.norm(e, axis=1, keepdims=True) + 1e-9)
        self.embeddings = e
        if e.shape[1] != EMBED_DIM:
            raise EnrollError(f"Embeddings con dimensión {e.shape[1]}, se esperaban {EMBED_DIM}.")

    @property
    def count(self) -> int:
        return int(self.embeddings.shape[0])

    @property
    def mean(self) -> np.ndarray:
        m = self.embeddings.mean(axis=0)
        return m / (np.linalg.norm(m) + 1e-9)

    def self_consistency(self) -> float:
        """Similitud coseno media entre las propias muestras (diagnóstico de
        calidad del enrolado; >0.6 es sano)."""
        if self.count < 2:
            return 1.0
        g = self.embeddings @ self.embeddings.T
        iu = np.triu_indices(self.count, k=1)
        return float(g[iu].mean())

    # --- serialización (va cifrada en faces.enc) ----------------------
    def to_bytes(self) -> bytes:
        buf = io.BytesIO()
        buf.write(TEMPLATE_MAGIC)
        meta = f"{self.model_pack}\x1f{self.threshold:.6f}\x1f{self.created:.3f}\n".encode()
        buf.write(len(meta).to_bytes(4, "big"))
        buf.write(meta)
        np.save(buf, self.embeddings.astype(np.float32), allow_pickle=False)
        return buf.getvalue()

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Template":
        buf = io.BytesIO(raw)
        if buf.read(len(TEMPLATE_MAGIC)) != TEMPLATE_MAGIC:
            raise EnrollError("Formato de plantilla facial no reconocido.")
        mlen = int.from_bytes(buf.read(4), "big")
        model_pack, threshold, created = buf.read(mlen).decode().strip().split("\x1f")
        embeddings = np.load(buf, allow_pickle=False)
        return cls(embeddings=embeddings, model_pack=model_pack,
                   threshold=float(threshold), created=float(created))


def enroll_from_frames(
    engine: FaceEngine,
    frames,
    *,
    target: int = 10,
    max_frames: int = 400,
    gate: QualityGate | None = None,
    model_pack: str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    min_self_consistency: float = 0.5,
) -> Template:
    """Recorre `frames` (iterable de imágenes BGR) y acumula hasta `target`
    embeddings que pasen el control de calidad."""
    gate = gate or QualityGate()
    embs: list[np.ndarray] = []
    seen = 0
    for frame in frames:
        seen += 1
        if seen > max_frames:
            break
        face = engine.primary_face(frame)
        problems = gate.check(frame.shape, face, sharpness(frame, face) if face is not None else None)
        if problems or face is None or face.embedding is None:
            continue
        embs.append(face.embedding)
        if len(embs) >= target:
            break

    if len(embs) < max(3, target // 2):
        raise EnrollError(
            f"Solo se consiguieron {len(embs)} muestras buenas. "
            "Mejora la luz, céntrate y mira de frente."
        )

    tpl = Template(
        embeddings=np.vstack(embs),
        model_pack=model_pack or engine.model_pack,
        threshold=threshold,
    )
    if tpl.self_consistency() < min_self_consistency:
        raise EnrollError(
            "Las muestras no son consistentes entre sí "
            f"(consistencia {tpl.self_consistency():.2f}). Repite el enrolado."
        )
    return tpl


@dataclass
class EnrollSession:
    """Versión incremental para la GUI: se le pasan frames uno a uno mientras
    muestra la vista de cámara y el reto de prueba de vida en curso."""

    engine: FaceEngine
    target: int = 10
    gate: QualityGate = field(default_factory=QualityGate)
    threshold: float = DEFAULT_THRESHOLD
    _embs: list = field(default_factory=list)
    last_problems: list = field(default_factory=list)

    @property
    def accepted(self) -> int:
        return len(self._embs)

    @property
    def done(self) -> bool:
        return self.accepted >= self.target

    def feed(self, frame_bgr) -> FaceObs | None:
        face = self.engine.primary_face(frame_bgr)
        sharp = sharpness(frame_bgr, face) if face is not None else None
        self.last_problems = self.gate.check(frame_bgr.shape, face, sharp)
        if not self.last_problems and face is not None and face.embedding is not None and not self.done:
            self._embs.append(face.embedding)
        return face

    def finish(self, *, min_self_consistency: float = 0.5) -> Template:
        if self.accepted < max(3, self.target // 2):
            raise EnrollError(f"Muestras insuficientes ({self.accepted}).")
        tpl = Template(np.vstack(self._embs), self.engine.model_pack, self.threshold)
        if tpl.self_consistency() < min_self_consistency:
            raise EnrollError("Muestras poco consistentes; repite el enrolado.")
        return tpl

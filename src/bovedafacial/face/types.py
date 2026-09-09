"""Observación de un rostro en un fotograma, normalizada a partir de la salida de
InsightFace para no arrastrar su objeto `Face` por todo el código."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FaceObs:
    bbox: np.ndarray                     # (4,)  x1, y1, x2, y2
    det_score: float
    kps: np.ndarray | None = None        # (5, 2) puntos clave del detector
    embedding: np.ndarray | None = None  # (512,) float32, L2-normalizado
    landmark_2d_106: np.ndarray | None = None
    pose: np.ndarray | None = None       # (3,) yaw, pitch, roll en grados

    @property
    def area(self) -> float:
        w = max(0.0, float(self.bbox[2] - self.bbox[0]))
        h = max(0.0, float(self.bbox[3] - self.bbox[1]))
        return w * h

    @property
    def width(self) -> float:
        return max(0.0, float(self.bbox[2] - self.bbox[0]))

    @property
    def center(self) -> tuple[float, float]:
        return (
            float(self.bbox[0] + self.bbox[2]) / 2.0,
            float(self.bbox[1] + self.bbox[3]) / 2.0,
        )

    # InsightFace entrega pose como [pitch, yaw, roll] en grados.
    @property
    def pitch(self) -> float | None:
        return None if self.pose is None else float(self.pose[0])

    @property
    def yaw(self) -> float | None:
        return None if self.pose is None else float(self.pose[1])

    @property
    def roll(self) -> float | None:
        return None if self.pose is None else float(self.pose[2])

    @classmethod
    def from_insightface(cls, f) -> "FaceObs":
        emb = getattr(f, "normed_embedding", None)
        if emb is None and getattr(f, "embedding", None) is not None:
            e = np.asarray(f.embedding, dtype=np.float32)
            emb = e / (np.linalg.norm(e) + 1e-9)
        return cls(
            bbox=np.asarray(f.bbox, dtype=np.float32),
            det_score=float(getattr(f, "det_score", 0.0)),
            kps=None if getattr(f, "kps", None) is None else np.asarray(f.kps, dtype=np.float32),
            embedding=None if emb is None else np.asarray(emb, dtype=np.float32),
            landmark_2d_106=(
                None if getattr(f, "landmark_2d_106", None) is None
                else np.asarray(f.landmark_2d_106, dtype=np.float32)
            ),
            pose=None if getattr(f, "pose", None) is None else np.asarray(f.pose, dtype=np.float32),
        )

"""Métricas de calidad de un frame para decidir si sirve para enrolar/verificar.

Todo son funciones puras sobre numpy (salvo `sharpness`, que usa OpenCV) para
poder probarlas sin cámara ni modelo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .types import FaceObs

# Índices del esquema de 106 puntos de InsightFace (2d106det).
# Contornos de cada ojo; se usan para el Eye Aspect Ratio (parpadeo).
LEFT_EYE_106 = [33, 34, 35, 36, 37, 38, 39, 40, 41, 42]
RIGHT_EYE_106 = [87, 88, 89, 90, 91, 92, 93, 94, 95, 96]
# 6 puntos para EAR: [esquina_ext, sup1, sup2, esquina_int, inf1, inf2]
LEFT_EAR_106 = [35, 37, 39, 40, 41, 33]
RIGHT_EAR_106 = [89, 91, 93, 94, 95, 87]


def _ear_from_points(p: np.ndarray) -> float:
    a = np.linalg.norm(p[1] - p[5])
    b = np.linalg.norm(p[2] - p[4])
    c = np.linalg.norm(p[0] - p[3])
    return float((a + b) / (2.0 * c + 1e-9))


def eye_aspect_ratio(landmark_2d_106: np.ndarray | None) -> float | None:
    """Media del EAR de ambos ojos. ~0.28-0.35 con ojos abiertos, <0.18 cerrados.
    Devuelve None si no hay landmarks."""
    if landmark_2d_106 is None or len(landmark_2d_106) < 106:
        return None
    lm = np.asarray(landmark_2d_106, dtype=np.float32)
    left = _ear_from_points(lm[LEFT_EAR_106])
    right = _ear_from_points(lm[RIGHT_EAR_106])
    return (left + right) / 2.0


def sharpness(bgr: np.ndarray, face: FaceObs | None = None) -> float:
    """Varianza del laplaciano (mayor = más nítido). Si se pasa `face`, se mide
    solo sobre el recorte del rostro."""
    import cv2

    img = bgr
    if face is not None:
        x1, y1, x2, y2 = (int(v) for v in face.bbox)
        x1, y1 = max(0, x1), max(0, y1)
        crop = bgr[y1:y2, x1:x2]
        if crop.size:
            img = crop
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


@dataclass
class QualityGate:
    min_det_score: float = 0.62
    min_face_ratio: float = 0.16     # ancho del rostro / ancho del frame
    max_face_ratio: float = 0.85
    max_center_offset: float = 0.28  # desviación del centro (fracción del frame)
    min_sharpness: float = 45.0
    max_abs_yaw: float = 22.0        # grados
    max_abs_pitch: float = 22.0

    def check(self, frame_shape: tuple[int, int], face: FaceObs | None, sharp: float | None) -> list[str]:
        """Devuelve la lista de motivos por los que el frame NO sirve (vacía = OK)."""
        h, w = frame_shape[:2]
        problems: list[str] = []
        if face is None:
            return ["no se detecta ningún rostro"]
        if face.det_score < self.min_det_score:
            problems.append("rostro poco claro")
        ratio = face.width / max(w, 1)
        if ratio < self.min_face_ratio:
            problems.append("acércate a la cámara")
        elif ratio > self.max_face_ratio:
            problems.append("aléjate un poco")
        cx, cy = face.center
        if abs(cx - w / 2) / w > self.max_center_offset or abs(cy - h / 2) / h > self.max_center_offset:
            problems.append("centra la cara")
        if sharp is not None and sharp < self.min_sharpness:
            problems.append("imagen borrosa, no te muevas")
        if face.yaw is not None and abs(face.yaw) > self.max_abs_yaw:
            problems.append("mira de frente")
        if face.pitch is not None and abs(face.pitch) > self.max_abs_pitch:
            problems.append("nivela la cabeza")
        return problems

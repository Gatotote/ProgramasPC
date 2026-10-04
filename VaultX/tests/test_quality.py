import pytest

np = pytest.importorskip("numpy")

from bovedafacial.face.quality import QualityGate, eye_aspect_ratio, sharpness
from bovedafacial.face.types import FaceObs


def _landmarks_with_ear(open_eyes: bool) -> np.ndarray:
    """106 puntos ficticios; solo importan los índices de ojos para el EAR.
    _ear_from_points usa p[0],p[3]=esquinas y (p[1],p[5]),(p[2],p[4])=pares
    verticales. EAR resultante = dy/5."""
    lm = np.zeros((106, 2), np.float32)
    dy = 3.0 if open_eyes else 0.4
    # ojo izquierdo: LEFT_EAR_106 = [35, 37, 39, 40, 41, 33]
    lm[35] = (0, 0);   lm[40] = (10, 0)              # esquinas
    lm[37] = (3, dy);  lm[33] = (3, -dy)             # par vertical 1
    lm[39] = (7, dy);  lm[41] = (7, -dy)             # par vertical 2
    # ojo derecho: RIGHT_EAR_106 = [89, 91, 93, 94, 95, 87]
    lm[89] = (20, 0);  lm[94] = (30, 0)
    lm[91] = (23, dy); lm[87] = (23, -dy)
    lm[93] = (27, dy); lm[95] = (27, -dy)
    return lm


def test_ear_open_vs_closed():
    open_ear = eye_aspect_ratio(_landmarks_with_ear(True))
    closed_ear = eye_aspect_ratio(_landmarks_with_ear(False))
    assert open_ear > closed_ear
    assert closed_ear < 0.19 < open_ear


def test_ear_none_without_landmarks():
    assert eye_aspect_ratio(None) is None
    assert eye_aspect_ratio(np.zeros((10, 2))) is None


def test_sharpness_drops_with_blur():
    cv2 = pytest.importorskip("cv2")
    rng = np.random.default_rng(0)
    sharp_img = rng.integers(0, 255, (120, 120, 3), dtype=np.uint8)
    blurred = cv2.GaussianBlur(sharp_img, (0, 0), 5)
    assert sharpness(sharp_img) > sharpness(blurred) * 3


def _face(w=1280, h=720, ratio=0.3, score=0.9, yaw=0.0, pitch=0.0, cx=None, cy=None):
    fw = ratio * w
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    bbox = np.array([cx - fw / 2, cy - fw / 2, cx + fw / 2, cy + fw / 2], np.float32)
    return FaceObs(bbox=bbox, det_score=score, pose=np.array([pitch, yaw, 0.0], np.float32))


def test_quality_gate_accepts_good_frame():
    gate = QualityGate()
    assert gate.check((720, 1280), _face(), sharp=200.0) == []


def test_quality_gate_flags_problems():
    gate = QualityGate()
    assert "no se detecta ningún rostro" in gate.check((720, 1280), None, None)
    assert "acércate a la cámara" in gate.check((720, 1280), _face(ratio=0.05), 200.0)
    assert "aléjate un poco" in gate.check((720, 1280), _face(ratio=0.95), 200.0)
    assert "mira de frente" in gate.check((720, 1280), _face(yaw=40.0), 200.0)
    assert "imagen borrosa, no te muevas" in gate.check((720, 1280), _face(), 5.0)
    assert "centra la cara" in gate.check((720, 1280), _face(cx=50), 200.0)

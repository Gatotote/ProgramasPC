"""Motor de reconocimiento facial (Fase 2).

InsightFace, pack `antelopev2` (SCRFD-10G + ResNet100 glint360k), onnxruntime-GPU.
La importación de insightface/onnxruntime/cv2 es perezosa: el núcleo de la
bóveda no depende de ellos. Requiere:  uv sync --extra face

    camera.py    fuente de vídeo (v4l2 / imagen / archivo)
    engine.py    carga del modelo + embeddings de 512-d
    quality.py   control de calidad del frame + EAR (parpadeo)
    liveness.py  retos de prueba de vida
    enroll.py    Template + enrolado (batch e incremental)
    verify.py    similitud coseno + umbral + backoff
    store.py     guardado cifrado de la plantilla en faces.enc
"""

from .camera import BaseCamera, CameraError, FileCamera, V4L2Camera, default_camera, list_v4l2_devices
from .engine import EngineError, FaceEngine, available_providers, models_present, pick_providers
from .enroll import EnrollError, EnrollSession, Template, enroll_from_frames
from .liveness import Challenge, LivenessSession
from .quality import QualityGate, eye_aspect_ratio, sharpness
from .store import has_template, load_template, save_template
from .types import FaceObs
from .verify import BackoffPolicy, VerifyResult, cosine, score_against, verify

__all__ = [
    "BaseCamera", "CameraError", "FileCamera", "V4L2Camera", "default_camera", "list_v4l2_devices",
    "EngineError", "FaceEngine", "available_providers", "models_present", "pick_providers",
    "EnrollError", "EnrollSession", "Template", "enroll_from_frames",
    "Challenge", "LivenessSession",
    "QualityGate", "eye_aspect_ratio", "sharpness",
    "has_template", "load_template", "save_template",
    "FaceObs",
    "BackoffPolicy", "VerifyResult", "cosine", "score_against", "verify",
]

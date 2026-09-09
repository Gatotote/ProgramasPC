"""Gate facial en vivo: cámara + motor + prueba de vida + verificación de
identidad. `open_vault()` de `vault/session.py` lo llama (vía `make_gate`) una
vez que el PIN ya recuperó la MK.

Prueba de vida (Fase 3): **liveness por movimiento**. En vez de retos guionados
(frágiles con solo la pose de la cabeza de este modelo), se exige que durante la
observación el rostro varíe de verdad — giro de la cabeza, cambio de distancia o
un parpadeo — además de una identidad fuerte en suficientes frames. El
anti-spoofing "de verdad" (modelo de textura/profundidad) queda para la Fase 5;
la `LivenessSession` guionada sigue disponible para el asistente de la GUI.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from .quality import eye_aspect_ratio
from .verify import verify

YAW_RANGE_MIN = 7.0     # grados de variación de yaw que cuentan como movimiento
WIDTH_CHANGE_MIN = 0.07  # cambio relativo del ancho del rostro (acercarse/alejarse)
BLINK_LO, BLINK_HI = 0.19, 0.26


@dataclass
class GateResult:
    ok: bool
    reason: str
    score: float = 0.0
    liveness_passed: bool = False
    frames: int = 0


def _best(scores) -> float:
    return max(scores) if scores else 0.0


def _motion_ok(yaws, widths, ear_lo: float, ear_hi: float) -> bool:
    yaw_range = (max(yaws) - min(yaws)) if len(yaws) >= 3 else 0.0
    w_change = (max(widths) / min(widths) - 1.0) if len(widths) >= 3 and min(widths) > 0 else 0.0
    blink = ear_lo < BLINK_LO and ear_hi > BLINK_HI
    return yaw_range >= YAW_RANGE_MIN or w_change >= WIDTH_CHANGE_MIN or blink


def verify_live(
    engine,
    camera,
    template,
    *,
    threshold: float | None = None,
    timeout: float = 20.0,
    min_match_frames: int = 6,
    window: int = 20,
    scripted=None,
    on_progress=None,
    on_frame=None,
) -> GateResult:
    """Devuelve GateResult. `scripted` opcional: una LivenessSession con retos
    guionados; si se pasa, su `.passed` sustituye a la liveness por movimiento.
    `on_frame(bgr)` recibe cada fotograma (para la vista previa de la GUI)."""
    thr = threshold if threshold is not None else template.threshold
    scores: deque = deque(maxlen=window)
    yaws: deque = deque(maxlen=window)
    widths: deque = deque(maxlen=window)
    ear_lo, ear_hi = 1.0, 0.0
    frames = 0
    t0 = time.monotonic()

    with camera:
        while time.monotonic() - t0 < timeout:
            frame = camera.read()
            if on_frame is not None:
                on_frame(frame)
            face = engine.primary_face(frame)
            frames += 1
            if scripted is not None:
                scripted.update(face)
            if face is not None:
                if face.yaw is not None:
                    yaws.append(face.yaw)
                widths.append(face.width)
                ear = eye_aspect_ratio(face.landmark_2d_106)
                if ear is not None:
                    ear_lo, ear_hi = min(ear_lo, ear), max(ear_hi, ear)
                if face.embedding is not None:
                    scores.append(verify(face.embedding, template.embeddings, threshold=thr).score)

            moved = _motion_ok(yaws, widths, ear_lo, ear_hi)
            good = sum(1 for s in scores if s >= thr)
            live_ok = scripted.passed if scripted is not None else moved
            if on_progress:
                on_progress(_best(scores), good, live_ok, frames)

            if live_ok and good >= min_match_frames:
                return GateResult(True, "ok", _best(scores), True, frames)
            if scripted is not None and scripted.failed:
                return GateResult(False, "liveness_timeout", _best(scores), False, frames)

    # agotado el tiempo: informar del motivo concreto
    good = sum(1 for s in scores if s >= thr)
    moved = _motion_ok(yaws, widths, ear_lo, ear_hi)
    if not good:
        return GateResult(False, "no_coincide", _best(scores), False, frames)
    if not moved:
        return GateResult(False, "sin_movimiento", _best(scores), False, frames)
    return GateResult(False, "pocos_frames", _best(scores), moved, frames)


def make_gate(engine=None, camera_factory=None, *, on_progress=None, on_frame=None, **verify_kw):
    """Devuelve un `face_gate(session) -> GateResult` para pasar a `open_vault`.
    Importa el motor y la cámara de forma perezosa."""
    from .camera import default_camera
    from .engine import FaceEngine
    from .store import load_template

    eng = engine or FaceEngine()

    def gate(session) -> GateResult:
        template = load_template(session.path, session.mk)
        if template is None:
            return GateResult(True, "sin_plantilla", liveness_passed=True)
        eng.load()
        cam = camera_factory() if camera_factory is not None else default_camera()
        return verify_live(eng, cam, template, on_progress=on_progress,
                           on_frame=on_frame, **verify_kw)

    return gate

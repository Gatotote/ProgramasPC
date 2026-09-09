"""Prueba de vida por retos activos.

No es anti-spoofing "de verdad" (para eso haría falta un modelo tipo
Silent-Face, previsto como mejora), pero obliga a un vídeo en directo que
responde a instrucciones aleatorias, lo que descarta una foto fija.

Retos disponibles: girar a la izquierda/derecha, volver al centro, parpadear y
acercarse. `LivenessSession` va pidiendo los retos en orden y se marca como
superada cuando se completan todos dentro del tiempo límite.

Todo es lógica pura sobre una secuencia de `FaceObs` -> testeable sin cámara.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from enum import Enum

from .quality import eye_aspect_ratio
from .types import FaceObs


class Challenge(str, Enum):
    TURN_LEFT = "gira la cabeza a tu izquierda"
    TURN_RIGHT = "gira la cabeza a tu derecha"
    CENTER = "vuelve a mirar de frente"
    BLINK = "parpadea"
    COME_CLOSER = "acércate un poco a la cámara"


DEFAULT_SEQUENCE_POOL = [
    Challenge.BLINK,
    Challenge.TURN_LEFT,
    Challenge.TURN_RIGHT,
    Challenge.COME_CLOSER,
]

YAW_TURN_DEG = 18.0        # giro mínimo para dar por válido TURN_*
YAW_CENTER_DEG = 10.0      # |yaw| por debajo de esto = "de frente"
BLINK_EAR_CLOSED = 0.19    # EAR por debajo = ojo cerrado
BLINK_EAR_OPEN = 0.26      # ...y hay que volver por encima para contar el parpadeo
CLOSER_RATIO = 1.18        # el rostro debe crecer este factor respecto al inicio


@dataclass
class LivenessSession:
    challenges: list[Challenge]
    timeout_s: float = 25.0          # por reto, no total
    _idx: int = 0
    _t0: float | None = None         # se fija con el primer frame
    _blink_seen_closed: bool = False
    _ref_width: float | None = None
    failed: bool = False

    @classmethod
    def random(cls, n: int = 2, *, pool: list[Challenge] | None = None,
               rng: random.Random | None = None, **kw) -> "LivenessSession":
        rng = rng or random.Random()
        pool = list(pool or DEFAULT_SEQUENCE_POOL)
        n = max(1, min(n, len(pool)))
        return cls(challenges=rng.sample(pool, n), **kw)

    # --- estado -------------------------------------------------------
    @property
    def current(self) -> Challenge | None:
        if self.failed or self._idx >= len(self.challenges):
            return None
        return self.challenges[self._idx]

    @property
    def passed(self) -> bool:
        return not self.failed and self._idx >= len(self.challenges)

    @property
    def progress(self) -> tuple[int, int]:
        return (self._idx, len(self.challenges))

    def reset(self) -> None:
        self._idx = 0
        self._t0 = None
        self._blink_seen_closed = False
        self._ref_width = None
        self.failed = False

    # --- avance -----------------------------------------------------
    def update(self, obs: FaceObs | None, *, now: float | None = None) -> Challenge | None:
        """Procesa un frame. Devuelve el reto actual (None si ya está superada
        o ha fallado por tiempo)."""
        if self.passed or self.failed:
            return None
        now = time.monotonic() if now is None else now
        if self._t0 is None:
            self._t0 = now
        if now - self._t0 > self.timeout_s:
            self.failed = True
            return None
        if obs is None:
            return self.current

        if self._ref_width is None:
            self._ref_width = obs.width

        ch = self.current
        if ch in (Challenge.TURN_LEFT, Challenge.TURN_RIGHT):
            yaw = obs.yaw
            if yaw is not None:
                # "izquierda del usuario" = giro que en yaw de InsightFace sale negativo
                if ch is Challenge.TURN_LEFT and yaw <= -YAW_TURN_DEG:
                    self._advance(now)
                elif ch is Challenge.TURN_RIGHT and yaw >= YAW_TURN_DEG:
                    self._advance(now)
        elif ch is Challenge.CENTER:
            if obs.yaw is not None and abs(obs.yaw) <= YAW_CENTER_DEG:
                self._advance(now)
        elif ch is Challenge.BLINK:
            ear = eye_aspect_ratio(obs.landmark_2d_106)
            if ear is not None:
                if ear < BLINK_EAR_CLOSED:
                    self._blink_seen_closed = True
                elif self._blink_seen_closed and ear > BLINK_EAR_OPEN:
                    self._advance(now)
        elif ch is Challenge.COME_CLOSER:
            if self._ref_width and obs.width >= self._ref_width * CLOSER_RATIO:
                self._advance(now)
        return self.current

    def _advance(self, now: float) -> None:
        self._idx += 1
        self._t0 = now                # cada reto tiene su propia ventana de tiempo
        self._blink_seen_closed = False
        self._ref_width = None

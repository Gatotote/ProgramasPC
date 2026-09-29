import random

import pytest

np = pytest.importorskip("numpy")

from bovedafacial.face.liveness import Challenge, LivenessSession
from bovedafacial.face.types import FaceObs


def _obs(yaw=0.0, width=200.0, ear=None):
    cx = cy = 360.0
    bbox = np.array([cx - width / 2, cy - width / 2, cx + width / 2, cy + width / 2], np.float32)
    lm = None
    if ear is not None:
        dy = ear * 5.0  # inverso de EAR = dy/5 del helper
        lm = np.zeros((106, 2), np.float32)
        lm[35] = (0, 0); lm[40] = (10, 0)
        lm[37] = (3, dy); lm[33] = (3, -dy)
        lm[39] = (7, dy); lm[41] = (7, -dy)
        lm[89] = (20, 0); lm[94] = (30, 0)
        lm[91] = (23, dy); lm[87] = (23, -dy)
        lm[93] = (27, dy); lm[95] = (27, -dy)
    return FaceObs(bbox=bbox, det_score=0.9,
                   pose=np.array([0.0, yaw, 0.0], np.float32), landmark_2d_106=lm)


def test_turn_left_then_right():
    s = LivenessSession([Challenge.TURN_LEFT, Challenge.TURN_RIGHT], timeout_s=1000)
    assert s.current is Challenge.TURN_LEFT
    s.update(_obs(yaw=-25), now=1)
    assert s.current is Challenge.TURN_RIGHT
    s.update(_obs(yaw=30), now=2)
    assert s.passed
    assert s.progress == (2, 2)


def test_turn_wrong_direction_does_not_advance():
    s = LivenessSession([Challenge.TURN_LEFT], timeout_s=1000)
    s.update(_obs(yaw=+25), now=1)
    assert not s.passed
    s.update(_obs(yaw=-25), now=2)
    assert s.passed


def test_blink_requires_close_then_open():
    s = LivenessSession([Challenge.BLINK], timeout_s=1000)
    s.update(_obs(ear=0.32), now=1)      # abierto
    assert not s.passed
    s.update(_obs(ear=0.10), now=2)      # cerrado
    assert not s.passed
    s.update(_obs(ear=0.32), now=3)      # abierto otra vez -> parpadeo
    assert s.passed


def test_come_closer():
    s = LivenessSession([Challenge.COME_CLOSER], timeout_s=1000)
    s.update(_obs(width=200), now=1)     # fija referencia
    assert not s.passed
    s.update(_obs(width=210), now=2)     # +5% insuficiente
    assert not s.passed
    s.update(_obs(width=260), now=3)     # +30%
    assert s.passed


def test_timeout_fails():
    s = LivenessSession([Challenge.BLINK], timeout_s=5.0)
    s.update(_obs(ear=0.3), now=0.0)
    out = s.update(_obs(ear=0.3), now=99.0)
    assert out is None
    assert s.failed and not s.passed


def test_none_obs_keeps_current_challenge():
    s = LivenessSession([Challenge.TURN_LEFT], timeout_s=1000)
    assert s.update(None, now=1) is Challenge.TURN_LEFT


def test_random_is_deterministic_with_seed():
    a = LivenessSession.random(n=2, rng=random.Random(42))
    b = LivenessSession.random(n=2, rng=random.Random(42))
    assert a.challenges == b.challenges
    assert len(a.challenges) == 2


def test_reset():
    s = LivenessSession([Challenge.TURN_LEFT], timeout_s=1000)
    s.update(_obs(yaw=-30), now=1)
    assert s.passed
    s.reset()
    assert not s.passed and s.progress == (0, 1)

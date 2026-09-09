import time

import pytest

np = pytest.importorskip("numpy")

from bovedafacial.face.verify import BackoffPolicy, cosine, score_against, verify


def _person(rng, n=10, spread=0.04):
    """Plantilla sintética de 'una persona': n embeddings cercanos a un eje base.
    spread≈0.04 da similitudes coseno intra-persona de ~0.7 (realista para
    antelopev2 entre sesiones distintas)."""
    base = rng.standard_normal(512).astype(np.float32)
    base /= np.linalg.norm(base)
    rows = base[None, :] + rng.standard_normal((n, 512)).astype(np.float32) * spread
    return base, rows


def test_cosine_bounds():
    v = np.array([1.0, 2.0, 3.0])
    assert cosine(v, v) == pytest.approx(1.0, abs=1e-6)
    assert cosine(v, -v) == pytest.approx(-1.0, abs=1e-6)
    assert cosine(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0, abs=1e-6)


def test_score_against_matches_own_sample():
    rng = np.random.default_rng(1)
    _, rows = _person(rng)
    rows /= np.linalg.norm(rows, axis=1, keepdims=True)
    assert score_against(rows[3], rows, top_k=1) == pytest.approx(1.0, abs=1e-5)


def test_score_impostor_is_low():
    rng = np.random.default_rng(7)
    _, rows = _person(rng)
    impostor = rng.standard_normal(512).astype(np.float32)
    assert score_against(impostor, rows) < 0.2


def test_verify_accepts_same_person_rejects_impostor():
    rng = np.random.default_rng(2)
    base, rows = _person(rng)
    probe_same = base + rng.standard_normal(512).astype(np.float32) * 0.04
    assert verify(probe_same, rows, threshold=0.45).matched

    probe_other = rng.standard_normal(512).astype(np.float32)
    assert not verify(probe_other, rows, threshold=0.45).matched


def test_backoff_exponential_delays():
    p = BackoffPolicy(base_delay_s=2.0, factor=3.0, max_delay_s=900.0)
    assert p.register_failure(now=0.0) == pytest.approx(2.0)
    assert p.register_failure(now=0.0) == pytest.approx(6.0)
    assert p.register_failure(now=0.0) == pytest.approx(18.0)
    assert p.failures == 3
    assert p.remaining(now=1.0) == pytest.approx(17.0)
    assert p.remaining(now=99.0) == 0.0


def test_backoff_is_locked_uses_walltime():
    p = BackoffPolicy(base_delay_s=30.0)
    p.register_failure()  # now = time.time()
    assert p.is_locked
    assert p.remaining() > 0.0


def test_backoff_capped():
    p = BackoffPolicy(base_delay_s=2.0, factor=10.0, max_delay_s=50.0)
    for _ in range(6):
        p.register_failure(now=0.0)
    assert p.locked_until == pytest.approx(50.0)


def test_backoff_success_resets():
    p = BackoffPolicy()
    p.register_failure()
    p.register_success()
    assert p.failures == 0
    assert not p.is_locked


def test_backoff_wipe_flag():
    p = BackoffPolicy(hard_limit=3)
    for _ in range(3):
        p.register_failure(now=0.0)
    assert p.wiped


def test_backoff_state_roundtrip():
    p = BackoffPolicy()
    p.register_failure(now=100.0)
    restored = BackoffPolicy().load_state(p.to_dict())
    assert restored.failures == p.failures
    assert restored.locked_until == pytest.approx(p.locked_until)

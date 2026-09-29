import pytest

from bovedafacial.throttle import BackoffPolicy


def test_reexported_from_face_verify():
    from bovedafacial.face.verify import BackoffPolicy as B2
    assert B2 is BackoffPolicy


def test_load_state_tolerates_none_and_missing_keys():
    p = BackoffPolicy().load_state(None)
    assert p.failures == 0 and p.locked_until == 0.0
    p.load_state({"failures": 4})
    assert p.failures == 4 and p.locked_until == 0.0


def test_exponential_then_reset():
    p = BackoffPolicy(base_delay_s=2.0, factor=3.0)
    assert p.register_failure(now=0.0) == pytest.approx(2.0)
    assert p.register_failure(now=0.0) == pytest.approx(6.0)
    assert p.remaining(now=1.0) == pytest.approx(5.0)
    p.register_success()
    assert p.failures == 0 and not p.is_locked


def test_wipe_flag():
    p = BackoffPolicy(hard_limit=3)
    for _ in range(3):
        p.register_failure(now=0.0)
    assert p.wiped

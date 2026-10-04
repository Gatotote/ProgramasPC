"""Fase 3: orquestación de open_vault() con un face_gate falso (sin cámara ni modelo)."""

from types import SimpleNamespace

import pytest

from bovedafacial.crypto import container as C
from bovedafacial.crypto.keyslots import WrongSecret
from bovedafacial.vault import (
    FaceRejected,
    VaultError,
    VaultLocked,
    create_vault,
    open_vault,
    vault_status,
)

_LIGHT = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}
PIN = "clave-larga"


@pytest.fixture
def vault(tmp_path):
    phrase, s = create_vault(tmp_path / "caja", PIN, kdf=_LIGHT)
    s.close()
    return tmp_path / "caja.vault", phrase


def _add_fake_face(vault_dir):
    C.write_secret(vault_dir, C.FACES_NAME, b"k" * 32, b"aad", b"plantilla-de-mentira")


# --- solo PIN --------------------------------------------------------------

def test_open_with_pin_no_face(vault):
    v, _ = vault
    with open_vault(v, pin=PIN) as s:
        assert s.list_dir("/") == []
    st = vault_status(v)
    assert st["failures"] == 0
    assert st["last_unlock"] is not None


def test_wrong_pin_increments_and_persists(vault):
    v, _ = vault
    with pytest.raises(WrongSecret):
        open_vault(v, pin="incorrecta", now=0.0)
    assert vault_status(v)["failures"] == 1
    assert C.read_header(v)["stats"]["failed_total"] == 1


def test_lockout_blocks_even_correct_pin(vault):
    v, _ = vault
    with pytest.raises(WrongSecret):
        open_vault(v, pin="incorrecta", now=1000.0)          # locked_until = 1002
    with pytest.raises(VaultLocked) as ei:
        open_vault(v, pin=PIN, now=1000.5)
    assert ei.value.retry_after == pytest.approx(1.5, abs=0.01)
    with open_vault(v, pin=PIN, now=1100.0):                  # ya pasó la ventana
        pass
    assert vault_status(v)["failures"] == 0                   # el éxito resetea


def test_backoff_grows(vault):
    v, _ = vault
    # cada reintento debe esperar a que pase su ventana: 0 -> 2 -> 8
    for i, (now, locked_until) in enumerate(
        [(0.0, 2.0), (2.0, 8.0), (8.0, 26.0)], start=1
    ):
        with pytest.raises(WrongSecret):
            open_vault(v, pin="incorrecta", now=now)
        assert vault_status(v)["failures"] == i
        assert C.read_header(v)["backoff"]["locked_until"] == pytest.approx(locked_until)


# --- recuperación -------------------------------------------------------

def test_recovery_bypasses_lock_and_face(vault):
    v, phrase = vault
    _add_fake_face(v)
    with pytest.raises(WrongSecret):
        open_vault(v, pin="incorrecta", now=0.0)              # deja la bóveda bloqueada
    with open_vault(v, phrase=phrase, now=0.1) as s:          # la frase entra igual
        assert s.list_dir("/") == []


def test_bad_recovery_phrase(vault):
    v, _ = vault
    from bovedafacial.crypto.keyslots import generate_recovery_phrase
    with pytest.raises(WrongSecret):
        open_vault(v, phrase=generate_recovery_phrase())


# --- gate facial ------------------------------------------------------

def test_face_gate_ok(vault):
    v, _ = vault
    _add_fake_face(v)
    seen = []

    def gate(session):
        seen.append(session)
        return SimpleNamespace(ok=True, reason="ok", score=0.83)

    with open_vault(v, pin=PIN, face_gate=gate) as s:
        assert s.list_dir("/") == []
    assert len(seen) == 1


def test_face_gate_rejects_counts_as_failure(vault):
    v, _ = vault
    _add_fake_face(v)

    def gate(session):
        return SimpleNamespace(ok=False, reason="no_coincide", score=0.21)

    with pytest.raises(FaceRejected) as ei:
        open_vault(v, pin=PIN, face_gate=gate, now=0.0)
    assert ei.value.score == pytest.approx(0.21)
    assert vault_status(v)["failures"] == 1


def test_face_required_but_no_gate(vault):
    v, _ = vault
    _add_fake_face(v)
    with pytest.raises(VaultError):
        open_vault(v, pin=PIN, face_gate=None)


def test_face_gate_exception_is_safe_and_not_penalised(vault):
    v, _ = vault
    _add_fake_face(v)

    def boom(session):
        raise RuntimeError("cámara desconectada")

    with pytest.raises(VaultError):
        open_vault(v, pin=PIN, face_gate=boom)
    assert vault_status(v)["failures"] == 0   # un fallo de hardware no es un intento


def test_policy_can_disable_face(vault):
    v, _ = vault
    _add_fake_face(v)
    header = C.read_header(v)
    header["policy"]["require_face"] = False
    C.save_header(v, header)

    called = []
    with open_vault(v, pin=PIN, face_gate=lambda s: called.append(1) or SimpleNamespace(ok=True)):
        pass
    assert not called


def test_no_pin_no_phrase(vault):
    v, _ = vault
    with pytest.raises(VaultError):
        open_vault(v)

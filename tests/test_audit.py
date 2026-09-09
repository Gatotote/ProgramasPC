import time

import pytest

from bovedafacial.crypto.keyslots import WrongSecret
from bovedafacial.vault import create_vault, open_vault, unlock_with_pin

_LIGHT = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}
PIN = "clave-larga"


def _vault(tmp_path):
    phrase, s = create_vault(tmp_path / "c", PIN, kdf=_LIGHT)
    s.close()
    return tmp_path / "c.vault", phrase


def test_records_newest_first(tmp_path):
    v, _ = _vault(tmp_path)
    with unlock_with_pin(v, PIN) as s:
        s.log_event("item_add", "password:X")
        s.log_event("file_open", "doc.pdf")
        r = s.activity(10)
    assert [e["kind"] for e in r[:2]] == ["file_open", "item_add"]


def test_audit_encrypted_on_disk(tmp_path):
    v, _ = _vault(tmp_path)
    with unlock_with_pin(v, PIN) as s:
        s.log_event("item_add", "MI-SECRETO-BUSCABLE")
    raw = (v / "audit.enc").read_bytes()
    assert b"MI-SECRETO-BUSCABLE" not in raw
    assert len(raw) > 12  # nonce + ciphertext


def test_summary_counts_today(tmp_path):
    v, _ = _vault(tmp_path)
    doc = tmp_path / "d.txt"
    doc.write_text("x")
    with unlock_with_pin(v, PIN) as s:
        s.add_item("/", "note", "n1", {"contenido": "hola"})
        s.import_path(doc, "/")
        summ = s.activity_summary()
    assert summ["items_added_today"] >= 1
    assert summ["files_added_today"] >= 1


def test_unlock_ok_is_logged(tmp_path):
    v, _ = _vault(tmp_path)
    with open_vault(v, pin=PIN) as s:
        assert any(e["kind"] == "unlock_ok" for e in s.activity(10))


def test_blocked_attempts_in_summary(tmp_path):
    v, _ = _vault(tmp_path)
    t = time.time()
    with pytest.raises(WrongSecret):
        open_vault(v, pin="incorrecta", now=t)          # queda en header["stats"]["fail_times"]
    with open_vault(v, pin=PIN, now=t + 5) as s:         # tras la ventana de 2 s
        summ = s.activity_summary()
    assert summ["blocked_attempts_24h"] == 1
    assert summ["failed_total"] == 1

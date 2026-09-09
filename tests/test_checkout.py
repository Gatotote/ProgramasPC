import tempfile

import pytest

from bovedafacial.vault import VaultError, create_vault, unlock_with_pin

_LIGHT = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}
PIN = "clave-larga"


def _vault(tmp_path):
    _, s = create_vault(tmp_path / "c", PIN, kdf=_LIGHT)
    return tmp_path / "c.vault", s


def test_checkout_decrypts_and_caches(tmp_path):
    v, s = _vault(tmp_path)
    src = tmp_path / "a.txt"
    src.write_text("contenido secreto")
    with s:
        s.import_path(src, "/")
        p = s.checkout("/a.txt")
        assert p.exists()
        assert p.read_text() == "contenido secreto"
        assert p.stat().st_mode & 0o777 == 0o600
        assert s.checkout("/a.txt") == p            # misma ruta en la 2ª llamada
        workarea = s._workarea
    assert not p.exists()                            # borrado al cerrar
    assert not workarea.exists()


def test_checkout_writes_back_changes(tmp_path):
    v, s = _vault(tmp_path)
    src = tmp_path / "nota.txt"
    src.write_text("v1")
    with s:
        s.import_path(src, "/")
        p = s.checkout("/nota.txt")
        p.write_text("v2 editado")                   # el usuario edita en su editor
    with unlock_with_pin(v, PIN) as s2:
        out = tmp_path / "restaurado.txt"
        s2.extract("/nota.txt", out)
        assert out.read_text() == "v2 editado"


def test_checkout_item_attachment(tmp_path):
    v, s = _vault(tmp_path)
    blob = tmp_path / "escritura.bin"
    blob.write_bytes(b"P" * 4096)
    with s:
        s.add_item("/", "will", "Testamento", {"albacea": "Ana"})
        s.attach_file("/Testamento", blob)
        p = s.checkout("/Testamento")
        assert p.read_bytes() == b"P" * 4096
        assert p.name.endswith("escritura.bin")


def test_checkout_dir_fails(tmp_path):
    _, s = _vault(tmp_path)
    with s:
        s.add_item("/Carpeta", "note", "n", {"contenido": "x"})
        with pytest.raises(VaultError):
            s.checkout("/Carpeta")


def test_workarea_in_ram_or_tmp(tmp_path):
    _, s = _vault(tmp_path)
    src = tmp_path / "f"
    src.write_bytes(b"z")
    with s:
        s.import_path(src, "/")
        p = str(s.checkout("/f"))
    assert p.startswith("/dev/shm/") or p.startswith(tempfile.gettempdir())

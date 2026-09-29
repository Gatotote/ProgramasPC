import os

import pytest

from bovedafacial.crypto.keyslots import WrongSecret
from bovedafacial.vault import (
    VaultError,
    create_vault,
    unlock_with_pin,
    unlock_with_recovery,
)


@pytest.fixture
def sample_tree(tmp_path):
    src = tmp_path / "origen"
    (src / "sub").mkdir(parents=True)
    (src / "raiz.txt").write_text("hola raíz")
    (src / "sub" / "nota.md").write_text("# secreto\ncontenido buscable")
    (src / "sub" / "bin.dat").write_bytes(os.urandom(9000))
    (src / "vacio.txt").write_bytes(b"")
    return src


def test_create_and_reopen(tmp_path):
    phrase, session = create_vault(tmp_path / "caja", "clave-larga", kdf=_LIGHT)
    session.close()
    assert (tmp_path / "caja.vault" / "header.json").exists()

    with unlock_with_pin(tmp_path / "caja.vault", "clave-larga") as s:
        assert s.list_dir("/") == []
    with unlock_with_recovery(tmp_path / "caja.vault", phrase) as s:
        assert s.list_dir("/") == []


def test_pin_too_short(tmp_path):
    with pytest.raises(VaultError):
        create_vault(tmp_path / "caja", "123", kdf=_LIGHT)


def test_wrong_pin(tmp_path):
    _, s = create_vault(tmp_path / "caja", "clave-larga", kdf=_LIGHT)
    s.close()
    with pytest.raises(WrongSecret):
        unlock_with_pin(tmp_path / "caja.vault", "otra-clave")


def test_import_list_extract_roundtrip(tmp_path, sample_tree):
    _, session = create_vault(tmp_path / "caja", "clave-larga", kdf=_LIGHT)
    with session as s:
        n = s.import_path(sample_tree, "/")
        assert n == 4
        names = {r["name"] for r in s.list_dir("/origen")}
        assert names == {"raiz.txt", "sub", "vacio.txt"}
        assert {r["name"] for r in s.list_dir("/origen/sub")} == {"nota.md", "bin.dat"}

    out = tmp_path / "restaurado"
    with unlock_with_pin(tmp_path / "caja.vault", "clave-larga") as s:
        s.extract("/origen", out)

    for rel in ["raiz.txt", "sub/nota.md", "sub/bin.dat", "vacio.txt"]:
        assert (out / rel).read_bytes() == (sample_tree / rel).read_bytes()


def test_content_not_discoverable_on_disk(tmp_path, sample_tree):
    """El objetivo del proyecto: nada del contenido ni de los nombres reales
    aparece al hurgar en el directorio .vault con herramientas normales."""
    _, session = create_vault(tmp_path / "caja", "clave-larga", kdf=_LIGHT)
    with session as s:
        s.import_path(sample_tree, "/")

    vault_dir = tmp_path / "caja.vault"
    needles = [b"contenido buscable", b"hola ra", b"nota.md", b"bin.dat", b"origen"]
    for path in vault_dir.rglob("*"):
        if path.is_file():
            blob = path.read_bytes()
            for needle in needles:
                assert needle not in blob, f"{needle!r} visible en {path.name}"

    # y los centinelas anti-indexado están puestos
    assert (vault_dir / ".noindex").exists()


def test_remove_deletes_objects(tmp_path, sample_tree):
    _, session = create_vault(tmp_path / "caja", "clave-larga", kdf=_LIGHT)
    with session as s:
        s.import_path(sample_tree, "/")
        before = _count_object_files(tmp_path / "caja.vault")
        s.remove("/origen/sub/bin.dat")
        after = _count_object_files(tmp_path / "caja.vault")
        assert after < before
        with pytest.raises(VaultError):
            s.list_dir("/origen/sub/bin.dat")  # ya no existe


def test_persistence_across_sessions(tmp_path, sample_tree):
    _, session = create_vault(tmp_path / "caja", "clave-larga", kdf=_LIGHT)
    with session as s:
        s.import_path(sample_tree / "raiz.txt", "/")
    with unlock_with_pin(tmp_path / "caja.vault", "clave-larga") as s:
        assert [r["name"] for r in s.list_dir("/")] == ["raiz.txt"]


def _count_object_files(vault_dir):
    return sum(1 for p in (vault_dir / "objects").rglob("*") if p.is_file())


_LIGHT = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}

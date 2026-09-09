import pytest

from bovedafacial.vault import VaultError, create_vault, unlock_with_pin

_LIGHT = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}
PIN = "clave-larga"


def _vault(tmp_path):
    _, s = create_vault(tmp_path / "c", PIN, kdf=_LIGHT)
    return tmp_path / "c.vault", s


def test_add_get_and_persist(tmp_path):
    v, s = _vault(tmp_path)
    with s:
        s.add_item("/Contraseñas", "password", "Correo",
                   {"usuario": "ana", "password": "secreta123", "basura": "x"})
        it = s.get_item("/Contraseñas/Correo")
        assert it["kind"] == "password"
        assert it["fields"]["usuario"] == "ana"
        assert "basura" not in it["fields"]          # clean_fields descarta lo desconocido
        assert it["created"] and it["modified"]
    with unlock_with_pin(v, PIN) as s2:
        assert s2.get_item("/Contraseñas/Correo")["fields"]["password"] == "secreta123"


def test_unknown_kind(tmp_path):
    _, s = _vault(tmp_path)
    with s, pytest.raises(ValueError):
        s.add_item("/", "banana", "x", {})


def test_update_merge_then_replace(tmp_path):
    _, s = _vault(tmp_path)
    with s:
        s.add_item("/", "password", "X", {"usuario": "a", "password": "p"})
        s.update_item("/X", {"url": "https://x"})
        f = s.get_item("/X")["fields"]
        assert f == {"usuario": "a", "password": "p", "url": "https://x"}
        s.update_item("/X", {"usuario": "b"}, replace=True)
        assert s.get_item("/X")["fields"] == {"usuario": "b"}


def test_list_items_and_kind_filter(tmp_path):
    _, s = _vault(tmp_path)
    with s:
        s.add_item("/Contraseñas", "password", "Correo", {"usuario": "a"})
        s.add_item("/Finanzas", "card", "Visa", {"numero": "4111"})
        s.add_item("/", "note", "Recordatorio", {"contenido": "algo"})
        assert len(s.list_items("/")) == 3
        cards = s.list_items("/", kind="card")
        assert [r["path"] for r in cards] == ["/Finanzas/Visa"]
        assert s.list_items("/Finanzas")[0]["name"] == "Visa"


def test_get_item_on_file_fails(tmp_path):
    _, s = _vault(tmp_path)
    f = tmp_path / "doc.txt"
    f.write_text("hola")
    with s:
        s.import_path(f, "/")
        with pytest.raises(VaultError):
            s.get_item("/doc.txt")


def test_attach_and_remove_cleans_objects(tmp_path):
    v, s = _vault(tmp_path)
    blob = tmp_path / "scan.bin"
    blob.write_bytes(b"Z" * 5000)
    with s:
        s.add_item("/", "will", "Testamento", {"albacea": "Ana"})
        s.attach_file("/Testamento", blob)
        it = s.get_item("/Testamento")
        assert it["attachments"][0]["name"] == "scan.bin"
        assert it["attachments"][0]["size"] == 5000
        before = _objs(v)
        s.remove("/Testamento")
        assert _objs(v) < before
        with pytest.raises(VaultError):
            s.get_item("/Testamento")


def _objs(vault_dir):
    return sum(1 for p in (vault_dir / "objects").rglob("*") if p.is_file())

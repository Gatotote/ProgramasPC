import json

import pytest

from bovedafacial.crypto import container as C
from bovedafacial.crypto.keyslots import new_master_key
from bovedafacial.vault import tree


def test_index_roundtrip(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = new_master_key()
    idx = tree.empty_root()
    tree.ensure_dir(idx, "/a/b")
    C.encrypt_index(vault, mk, idx)
    assert C.decrypt_index(vault, mk) == idx


def test_index_wrong_key_fails(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    C.encrypt_index(vault, new_master_key(), tree.empty_root())
    with pytest.raises(C.ContainerError):
        C.decrypt_index(vault, new_master_key())


def test_index_file_has_no_plaintext(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = new_master_key()
    idx = tree.empty_root()
    tree.add_file(idx, "/", "MI-DOCUMENTO-SECRETO.txt",
                  {"object_id": "00", "size": 0, "chunks": [0], "sha256": "x"}, 0.0)
    C.encrypt_index(vault, mk, idx)
    raw = (vault / C.INDEX_NAME).read_bytes()
    assert b"MI-DOCUMENTO-SECRETO" not in raw


def test_object_roundtrip_multichunk(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = new_master_key()
    data = b"A" * (10 * 1024 * 1024 + 7)   # >2 chunks de 4 MiB
    oid = C.new_object_id()
    desc = C.write_object(vault, mk, oid, data, chunk_size=4 * 1024 * 1024)
    assert desc["size"] == len(data)
    assert len(desc["chunks"]) == 3
    assert C.read_object(vault, mk, desc) == data


def test_object_empty_file(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = new_master_key()
    desc = C.write_object(vault, mk, C.new_object_id(), b"", chunk_size=4096)
    assert C.read_object(vault, mk, desc) == b""


def test_object_tamper_detected(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = new_master_key()
    desc = C.write_object(vault, mk, C.new_object_id(), b"hola mundo", chunk_size=4096)
    # corromper el primer (único) chunk
    chunk_dir = vault / C.OBJECTS_DIR
    chunk_file = next(p for p in chunk_dir.rglob("*") if p.is_file())
    b = bytearray(chunk_file.read_bytes())
    b[-1] ^= 0x01
    chunk_file.write_bytes(b)
    with pytest.raises(C.ContainerError):
        C.read_object(vault, mk, desc)


def test_chunk_names_are_opaque(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = new_master_key()
    C.write_object(vault, mk, C.new_object_id(), b"contenido buscable secreto", chunk_size=4096)
    for p in (vault / C.OBJECTS_DIR).rglob("*"):
        if p.is_file():
            assert all(ch in "0123456789abcdef" for ch in p.name)
            assert len(p.name) == 64  # hex de un HMAC-SHA256


def test_header_has_two_keyslots_and_no_mk(tmp_path):
    from bovedafacial.crypto.keyslots import wrap_pin_slot, wrap_recovery_slot, generate_recovery_phrase

    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = new_master_key()
    kdf = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}
    header = C.write_header(
        vault,
        pin_slot=wrap_pin_slot("123456", mk, kdf),
        recovery_slot=wrap_recovery_slot(generate_recovery_phrase(), mk),
        kdf=kdf,
    )
    on_disk = json.loads((vault / C.HEADER_NAME).read_bytes())
    assert set(on_disk["keyslots"]) == {"pin", "recovery"}
    assert mk.hex() not in json.dumps(on_disk)
    assert header == on_disk

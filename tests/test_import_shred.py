from bovedafacial.vault import create_vault

_LIGHT = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}


def _vault(tmp_path):
    _, s = create_vault(tmp_path / "c", "clave-larga", kdf=_LIGHT)
    return s


def test_import_shreds_single_file(tmp_path):
    s = _vault(tmp_path)
    f = tmp_path / "secreto.txt"
    f.write_text("dato sensible")
    with s:
        s.import_path(f, "/", secure_delete=True)
        assert not f.exists()
        assert [r["name"] for r in s.list_dir("/")] == ["secreto.txt"]


def test_import_no_shred_keeps_original(tmp_path):
    s = _vault(tmp_path)
    f = tmp_path / "doc.txt"
    f.write_text("x")
    with s:
        s.import_path(f, "/")
        assert f.exists()


def test_import_shreds_folder(tmp_path):
    s = _vault(tmp_path)
    src = tmp_path / "carpeta"
    (src / "sub").mkdir(parents=True)
    (src / "a.txt").write_text("a")
    (src / "sub" / "b.txt").write_text("b")
    with s:
        n = s.import_path(src, "/", secure_delete=True)
        assert n == 2
        assert not src.exists()
        assert {r["name"] for r in s.list_dir("/carpeta")} == {"a.txt", "sub"}

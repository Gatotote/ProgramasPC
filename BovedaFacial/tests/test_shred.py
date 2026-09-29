from bovedafacial.crypto.shred import shred_file, shred_tree


def test_shred_file_removes(tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"A" * 5000)
    shred_file(f)
    assert not f.exists()


def test_shred_missing_is_ok(tmp_path):
    shred_file(tmp_path / "no-existe")   # no debe lanzar


def test_shred_tree(tmp_path):
    root = tmp_path / "wa"
    (root / "sub").mkdir(parents=True)
    (root / "a").write_bytes(b"x" * 10)
    (root / "sub" / "b").write_bytes(b"y" * 10)
    shred_tree(root)
    assert not root.exists()

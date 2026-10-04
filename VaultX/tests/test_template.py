import os

import pytest

np = pytest.importorskip("numpy")

from bovedafacial.crypto import container as C
from bovedafacial.face.enroll import EnrollError, Template
from bovedafacial.face.store import has_template, load_template, save_template


def _template(rng, m=10):
    embs = rng.standard_normal((m, 512)).astype(np.float32)
    return Template(embeddings=embs, model_pack="antelopev2", threshold=0.45)


def test_template_normalizes_rows():
    rng = np.random.default_rng(0)
    tpl = _template(rng)
    norms = np.linalg.norm(tpl.embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_template_bad_dimension():
    with pytest.raises(EnrollError):
        Template(embeddings=np.zeros((3, 128), np.float32), model_pack="x")


def test_template_self_consistency():
    row = np.ones((1, 512), np.float32)
    tpl = Template(embeddings=np.repeat(row, 6, axis=0), model_pack="x")
    assert tpl.self_consistency() == pytest.approx(1.0, abs=1e-5)


def test_template_bytes_roundtrip():
    rng = np.random.default_rng(3)
    tpl = _template(rng, m=12)
    back = Template.from_bytes(tpl.to_bytes())
    assert back.model_pack == "antelopev2"
    assert back.threshold == pytest.approx(0.45)
    assert back.created == pytest.approx(tpl.created, abs=1e-3)
    assert np.allclose(back.embeddings, tpl.embeddings, atol=1e-6)


def test_store_roundtrip_encrypted(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    mk = os.urandom(32)
    rng = np.random.default_rng(4)
    tpl = _template(rng)

    assert not has_template(vault)
    assert load_template(vault, mk) is None

    save_template(vault, mk, tpl)
    assert has_template(vault)

    loaded = load_template(vault, mk)
    assert np.allclose(loaded.embeddings, tpl.embeddings, atol=1e-6)

    # el fichero en disco no revela los embeddings en claro
    raw = (vault / C.FACES_NAME).read_bytes()
    assert tpl.embeddings.tobytes()[:64] not in raw


def test_store_wrong_key_fails(tmp_path):
    vault = tmp_path / "v.vault"
    C.init_layout(vault)
    rng = np.random.default_rng(5)
    save_template(vault, os.urandom(32), _template(rng))
    with pytest.raises(C.ContainerError):
        load_template(vault, os.urandom(32))

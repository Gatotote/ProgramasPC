import pytest

from bovedafacial import desktop_integration as di


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    # forzar la ruta manual (sin balooctl / update-desktop-database del sistema)
    monkeypatch.setattr(di.shutil, "which", lambda name: None)
    return tmp_path


def test_baloo_manual_edit_is_idempotent(home):
    vault = home / "caja.vault"
    msg = di.exclude_from_baloo(vault)
    assert "baloofilerc" in msg or "Excluida" in msg
    rc = home / ".config" / "baloofilerc"
    txt = rc.read_text()
    assert "[General]" in txt
    assert str(vault.resolve()) + "/" in txt

    di.exclude_from_baloo(vault)  # otra vez
    assert rc.read_text().count(str(vault.resolve())) == 1


def test_baloo_appends_to_existing_key(home):
    rc = home / ".config" / "baloofilerc"
    rc.parent.mkdir(parents=True)
    rc.write_text("[General]\nexclude folders[$e]=/home/x/Downloads/\n"
                  "[Something Else]\nfoo=1\n")
    vault = home / "c.vault"
    di.exclude_from_baloo(vault)
    line = next(x for x in rc.read_text().splitlines() if x.startswith("exclude folders"))
    assert "/home/x/Downloads/" in line
    assert str(vault.resolve()) + "/" in line
    assert "foo=1" in rc.read_text()


def test_baloo_no_general_section(home):
    rc = home / ".config" / "baloofilerc"
    rc.parent.mkdir(parents=True)
    rc.write_text("[Basic Settings]\nIndexing-Enabled=true\n")
    vault = home / "c.vault"
    di.exclude_from_baloo(vault)
    txt = rc.read_text()
    assert "[General]" in txt
    assert "[Basic Settings]" in txt
    assert str(vault.resolve()) + "/" in txt


def test_install_desktop_entry(home):
    path = di.install_desktop_entry()
    assert path.exists()
    txt = path.read_text()
    assert "Name=Bóveda Inteligente" in txt
    assert txt.count("Exec=") == 1
    icon = home / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps" / "bovedafacial.svg"
    assert icon.exists()
    assert "<svg" in icon.read_text()

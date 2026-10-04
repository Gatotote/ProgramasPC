"""Configuración local de la GUI: qué bóveda abrir y preferencias sencillas.
Vive en ~/.config/bovedafacial/config.json (nada sensible)."""

from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP = "bovedafacial"
_CFG = Path(user_config_dir(APP)) / "config.json"


def default_vault_path() -> Path:
    return Path(user_data_dir(APP)) / "principal.vault"


def load() -> dict:
    try:
        return json.loads(_CFG.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save(data: dict) -> None:
    _CFG.parent.mkdir(parents=True, exist_ok=True)
    _CFG.write_text(json.dumps(data, indent=2), "utf-8")


def vault_path() -> Path:
    return Path(load().get("vault") or default_vault_path())


def set_vault_path(path: Path | str) -> None:
    data = load()
    data["vault"] = str(path)
    save(data)


def get(key: str, default=None):
    return load().get(key, default)


def set(key: str, value) -> None:  # noqa: A003
    data = load()
    data[key] = value
    save(data)

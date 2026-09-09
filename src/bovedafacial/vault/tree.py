"""Árbol lógico de la bóveda (lo que va cifrado dentro de index.enc).

Formato JSON-serializable:

    {"type": "dir", "entries": {
        "Documentos": {"type": "dir", "entries": {...}},
        "nota.txt":   {"type": "file", "size": 12, "mtime": 1.0,
                        "object_id": "…", "chunks": [12], "sha256": "…"}
    }}
"""

from __future__ import annotations

from typing import Iterator


class TreeError(Exception):
    pass


def empty_root() -> dict:
    return {"type": "dir", "entries": {}}


def split_path(path: str) -> list[str]:
    return [p for p in path.replace("\\", "/").split("/") if p not in ("", ".")]


def _dir_node(root: dict, parts: list[str], *, create: bool) -> dict:
    node = root
    for i, part in enumerate(parts):
        if node["type"] != "dir":
            raise TreeError(f"/{'/'.join(parts[:i])} no es una carpeta")
        child = node["entries"].get(part)
        if child is None:
            if not create:
                raise TreeError(f"No existe /{'/'.join(parts[:i + 1])}")
            child = {"type": "dir", "entries": {}}
            node["entries"][part] = child
        node = child
    if node["type"] != "dir":
        raise TreeError(f"/{'/'.join(parts)} no es una carpeta")
    return node


def ensure_dir(root: dict, path: str) -> dict:
    return _dir_node(root, split_path(path), create=True)


def get_node(root: dict, path: str) -> dict:
    parts = split_path(path)
    if not parts:
        return root
    parent = _dir_node(root, parts[:-1], create=False)
    node = parent["entries"].get(parts[-1])
    if node is None:
        raise TreeError(f"No existe /{'/'.join(parts)}")
    return node


def add_file(root: dict, dir_path: str, name: str, descriptor: dict, mtime: float) -> None:
    parent = ensure_dir(root, dir_path)
    entry = {"type": "file", "mtime": mtime}
    entry.update(descriptor)  # object_id, size, chunks, sha256
    parent["entries"][name] = entry


def remove(root: dict, path: str) -> list[dict]:
    """Quita una entrada. Devuelve los descriptores de archivo eliminados
    (para poder borrar sus objetos del disco)."""
    parts = split_path(path)
    if not parts:
        raise TreeError("No se puede eliminar la raíz")
    parent = _dir_node(root, parts[:-1], create=False)
    node = parent["entries"].pop(parts[-1], None)
    if node is None:
        raise TreeError(f"No existe /{'/'.join(parts)}")
    return list(iter_files(node))


def iter_files(node: dict) -> Iterator[dict]:
    if node["type"] == "file":
        yield node
    else:
        for child in node["entries"].values():
            yield from iter_files(child)


def listing(node: dict) -> list[dict]:
    if node["type"] != "dir":
        raise TreeError("No es una carpeta")
    out = []
    for name, child in sorted(node["entries"].items()):
        if child["type"] == "dir":
            out.append({"name": name, "type": "dir", "size": None})
        else:
            out.append({"name": name, "type": "file", "size": child["size"]})
    return out

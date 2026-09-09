"""Sesión de bóveda abierta: mantiene la MK y el índice en memoria y ofrece las
operaciones de alto nivel (importar, extraer, listar, eliminar).

`open_vault()` es el desbloqueo completo de la Fase 3: comprueba el bloqueo por
intentos fallidos, desenvuelve la MK con el PIN y, si hay plantilla facial y la
política lo exige, delega la verificación del rostro en un `face_gate` que
inyecta la capa de arriba (así `vault/` no depende de `face/`).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from ..crypto import container as C
from ..crypto.keyslots import (
    DEFAULT_KDF,
    KeySlot,
    WrongSecret,
    generate_recovery_phrase,
    new_master_key,
    unwrap_pin_slot,
    unwrap_recovery_slot,
    wrap_pin_slot,
    wrap_recovery_slot,
)
from ..throttle import BackoffPolicy
from . import audit, tree
from . import items as I

VAULT_SUFFIX = ".vault"
MIN_PIN_LEN = 6


class VaultError(Exception):
    pass


class VaultLocked(VaultError):
    """Demasiados intentos fallidos: hay que esperar."""

    def __init__(self, retry_after: float) -> None:
        self.retry_after = retry_after
        super().__init__(
            f"Bóveda bloqueada por intentos fallidos. Reintenta en {retry_after:.0f} s."
        )


class FaceRejected(VaultError):
    """PIN correcto pero el rostro no pasó la verificación / la prueba de vida."""

    def __init__(self, reason: str, score: float = 0.0) -> None:
        self.reason = reason
        self.score = score
        super().__init__(f"Rostro no verificado ({reason}).")


def _translate(fn):
    """Convierte errores internos (árbol/contenedor) en VaultError para la UI."""
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (tree.TreeError, C.ContainerError) as e:
            raise VaultError(str(e)) from e

    return wrapper


@dataclass
class Session:
    path: Path
    _mk: bytearray
    header: dict
    index: dict
    _dirty: bool = False
    _closed: bool = False

    # --- propiedades internas ---------------------------------------------
    @property
    def mk(self) -> bytes:
        if self._closed:
            raise VaultError("La sesión de bóveda ya está cerrada.")
        return bytes(self._mk)

    @property
    def chunk_size(self) -> int:
        return self.header["chunk_size"]

    # --- operaciones -----------------------------------------------------
    @_translate
    def import_path(self, src: Path, dest_dir: str = "/") -> int:
        """Importa un archivo o un árbol de carpetas. Devuelve nº de archivos."""
        src = Path(src)
        if not src.exists():
            raise VaultError(f"No existe el origen: {src}")
        count = 0
        if src.is_file():
            self._import_file(src, dest_dir, src.name)
            count = 1
        else:
            base = dest_dir.rstrip("/") + "/" + src.name
            tree.ensure_dir(self.index, base)
            for root, _dirs, files in os.walk(src):
                rel = Path(root).relative_to(src)
                vdir = base if rel == Path(".") else f"{base}/{rel.as_posix()}"
                tree.ensure_dir(self.index, vdir)
                for fname in sorted(files):
                    self._import_file(Path(root) / fname, vdir, fname)
                    count += 1
        self._dirty = True
        self.log_event(audit.FILE_IMPORT, f"{src.name} -> {dest_dir}", count=count)
        return count

    def _import_file(self, fpath: Path, vdir: str, name: str) -> None:
        data = fpath.read_bytes()
        object_id = C.new_object_id()
        descriptor = C.write_object(self.path, self.mk, object_id, data, self.chunk_size)
        tree.add_file(self.index, vdir, name, descriptor, fpath.stat().st_mtime)

    @_translate
    def list_dir(self, path: str = "/") -> list[dict]:
        return tree.listing(tree.get_node(self.index, path))

    @_translate
    def extract(self, vpath: str, dest: Path) -> Path:
        """Extrae un archivo o una carpeta a `dest` (en claro)."""
        dest = Path(dest)
        node = tree.get_node(self.index, vpath)
        if node["type"] == "file":
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(C.read_object(self.path, self.mk, node))
            os.utime(dest, (node["mtime"], node["mtime"]))
            return dest
        self._extract_dir(node, dest)
        return dest

    def _extract_dir(self, node: dict, dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        for name, child in node["entries"].items():
            target = dest / name
            if child["type"] == "dir":
                self._extract_dir(child, target)
            else:
                target.write_bytes(C.read_object(self.path, self.mk, child))
                os.utime(target, (child["mtime"], child["mtime"]))

    @_translate
    def remove(self, vpath: str) -> None:
        for descriptor in tree.remove(self.index, vpath):
            C.delete_object(self.path, self.mk, descriptor)
        self._dirty = True
        self.log_event(audit.ITEM_REMOVE, vpath)

    # --- elementos tipados (contraseñas, tarjetas, cuentas, ...) ----------
    @_translate
    def add_item(self, dir_path: str, kind, name: str, fields: dict) -> None:
        k = I.coerce_kind(kind)
        tree.add_item(self.index, dir_path, name, k.value,
                      I.clean_fields(k, fields), time.time())
        self._dirty = True
        self.log_event(audit.ITEM_ADD, f"{k.value}:{name}")

    @_translate
    def get_item(self, vpath: str) -> dict:
        node = tree.get_node(self.index, vpath)
        if node.get("type") != "item":
            raise VaultError(f"/{vpath.strip('/')} no es un elemento.")
        return {
            "kind": node["kind"],
            "fields": dict(node.get("fields", {})),
            "attachments": [dict(a) for a in node.get("attachments", [])],
            "created": node.get("created"),
            "modified": node.get("modified"),
        }

    @_translate
    def update_item(self, vpath: str, fields: dict, *, replace: bool = False) -> None:
        node = tree.get_node(self.index, vpath)
        if node.get("type") != "item":
            raise VaultError(f"/{vpath.strip('/')} no es un elemento.")
        clean = I.clean_fields(node["kind"], fields)
        node["fields"] = clean if replace else {**node.get("fields", {}), **clean}
        node["modified"] = time.time()
        self._dirty = True
        self.log_event(audit.ITEM_UPDATE, vpath)

    @_translate
    def list_items(self, dir_path: str = "/", kind=None) -> list[dict]:
        want = I.coerce_kind(kind).value if kind is not None else None
        start = tree.get_node(self.index, dir_path)
        out = []
        for path, node in tree.iter_items(start, dir_path.rstrip("/")):
            if want is None or node.get("kind") == want:
                out.append({
                    "path": path,
                    "name": path.rsplit("/", 1)[-1],
                    "kind": node.get("kind"),
                    "modified": node.get("modified"),
                    "attachments": len(node.get("attachments", [])),
                })
        return sorted(out, key=lambda r: r["path"])

    @_translate
    def attach_file(self, vpath: str, src: Path) -> None:
        node = tree.get_node(self.index, vpath)
        if node.get("type") != "item":
            raise VaultError(f"/{vpath.strip('/')} no es un elemento.")
        src = Path(src)
        data = src.read_bytes()
        descriptor = C.write_object(self.path, self.mk, C.new_object_id(), data, self.chunk_size)
        descriptor["name"] = src.name
        node.setdefault("attachments", []).append(descriptor)
        node["modified"] = time.time()
        self._dirty = True
        self.log_event(audit.FILE_IMPORT, f"adjunto:{src.name}")

    # --- registro de actividad -----------------------------------------
    def log_event(self, kind: str, detail: str = "", count: int = 1) -> None:
        if self._closed:
            return
        try:
            audit.record(self, kind, detail, count=count)
        except Exception:  # noqa: BLE001 - el log nunca debe tumbar una operación
            pass

    def activity(self, limit: int = 50, kind: str | None = None) -> list[dict]:
        return audit.recent(self, limit, kind)

    def activity_summary(self) -> dict:
        return audit.summary(self)

    # --- uso de espacio ---------------------------------------------
    def storage_stats(self) -> dict:
        files = items = attachments = 0
        file_bytes = attach_bytes = 0
        by_top: dict[str, int] = {}

        def walk(node, top):
            nonlocal files, items, attachments, file_bytes, attach_bytes
            t = node.get("type")
            if t == "file":
                files += 1
                file_bytes += node.get("size", 0)
                by_top[top] = by_top.get(top, 0) + node.get("size", 0)
            elif t == "item":
                items += 1
                for a in node.get("attachments", []):
                    attachments += 1
                    attach_bytes += a.get("size", 0)
                    by_top[top] = by_top.get(top, 0) + a.get("size", 0)
            elif t == "dir":
                for name, child in node["entries"].items():
                    walk(child, name if top is None else top)

        walk(self.index, None)
        objects_dir = self.path / C.OBJECTS_DIR
        on_disk = sum(p.stat().st_size for p in objects_dir.rglob("*") if p.is_file())
        return {
            "files": files,
            "items": items,
            "attachments": attachments,
            "plaintext_bytes": file_bytes + attach_bytes,
            "on_disk_bytes": on_disk,
            "by_category": by_top,
        }

    def save(self) -> None:
        if self._dirty and not self._closed:
            C.encrypt_index(self.path, self.mk, self.index)
            self._dirty = False

    def close(self) -> None:
        if self._closed:
            return
        self.save()
        for i in range(len(self._mk)):   # borrado best-effort (Python no garantiza)
            self._mk[i] = 0
        self._closed = True

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# --- creación y desbloqueo -------------------------------------------------

def _validate_pin(pin: str) -> None:
    if len(pin) < MIN_PIN_LEN:
        raise VaultError(f"El PIN debe tener al menos {MIN_PIN_LEN} caracteres.")


def create_vault(path: os.PathLike | str, pin: str, *, kdf: dict | None = None) -> tuple[str, Session]:
    """Crea una bóveda nueva. Devuelve (frase_de_recuperación, sesión abierta).
    La frase solo se devuelve aquí: hay que apuntarla en papel."""
    _validate_pin(pin)
    path = Path(path)
    if path.suffix != VAULT_SUFFIX:
        path = path.with_suffix(VAULT_SUFFIX)
    kdf = kdf or DEFAULT_KDF

    mk = new_master_key()
    phrase = generate_recovery_phrase()
    pin_slot = wrap_pin_slot(pin, mk, kdf)
    recovery_slot = wrap_recovery_slot(phrase, mk)

    C.init_layout(path)
    header = C.write_header(path, pin_slot=pin_slot, recovery_slot=recovery_slot, kdf=kdf)
    C.encrypt_index(path, mk, tree.empty_root())

    session = Session(path=path, _mk=bytearray(mk), header=header, index=tree.empty_root())
    return phrase, session


def _open(path: Path, mk: bytes, header: dict | None = None) -> Session:
    path = Path(path)
    header = header if header is not None else C.read_header(path)
    index = C.decrypt_index(path, mk)
    return Session(path=path, _mk=bytearray(mk), header=header, index=index)


@_translate
def unlock_with_pin(path: os.PathLike | str, pin: str) -> Session:
    """Desbloqueo de bajo nivel: solo PIN -> MK -> sesión. Sin backoff ni rostro.
    Lo usa el modo de recuperación interna y el enrolado. Para el desbloqueo
    normal usa `open_vault()`."""
    path = Path(path)
    header = C.read_header(path)
    slot = KeySlot.from_json(header["keyslots"]["pin"])
    mk = unwrap_pin_slot(pin, slot, header["kdf"])   # lanza WrongSecret si falla
    return _open(path, mk, header)


@_translate
def unlock_with_recovery(path: os.PathLike | str, phrase: str) -> Session:
    path = Path(path)
    header = C.read_header(path)
    slot = KeySlot.from_json(header["keyslots"]["recovery"])
    mk = unwrap_recovery_slot(phrase, slot)          # lanza WrongSecret si falla
    return _open(path, mk, header)


# --- desbloqueo completo (Fase 3) ---------------------------------------------

def _persist_failure(path: Path, header: dict, backoff: BackoffPolicy, now: float | None) -> None:
    backoff.register_failure(now=now)
    header["backoff"] = backoff.to_dict()
    stats = header.setdefault("stats", {})
    stats["failed_total"] = int(stats.get("failed_total", 0)) + 1
    times = stats.setdefault("fail_times", [])
    times.append(time.time() if now is None else now)
    stats["fail_times"] = times[-30:]
    C.save_header(path, header)


def _persist_success(path: Path, header: dict, backoff: BackoffPolicy | None) -> None:
    if backoff is not None:
        backoff.register_success()
        header["backoff"] = backoff.to_dict()
    header.setdefault("stats", {})["last_unlock"] = time.time()
    C.save_header(path, header)


def open_vault(
    path: os.PathLike | str,
    *,
    pin: str | None = None,
    phrase: str | None = None,
    face_gate=None,
    now: float | None = None,
) -> Session:
    """Desbloqueo normal de la bóveda.

    - `phrase`: modo recuperación — salta el bloqueo por intentos y el rostro.
    - `pin`: comprueba el bloqueo por intentos -> desenvuelve la MK -> si hay
      plantilla facial y la política lo exige, ejecuta `face_gate(session)`.

    `face_gate` es un callable que recibe la sesión ya abierta y devuelve un
    objeto con atributos `ok` (bool), `reason` (str) y `score` (float). Lo
    provee quien pueda importar `bovedafacial.face` (la CLI o la GUI).
    """
    path = Path(path)
    try:
        header = C.read_header(path)
    except C.ContainerError as e:
        raise VaultError(str(e)) from e

    # --- modo recuperación --------------------------------------------------
    if phrase is not None:
        try:
            slot = KeySlot.from_json(header["keyslots"]["recovery"])
            mk = unwrap_recovery_slot(phrase, slot)
        except C.ContainerError as e:
            raise VaultError(str(e)) from e
        session = _open(path, mk, header)
        _persist_success(path, header, backoff=None)
        session.log_event(audit.UNLOCK_OK, "recuperación")
        return session

    if pin is None:
        raise VaultError("Hace falta el PIN o la frase de recuperación.")

    # --- bloqueo por intentos fallidos -----------------------------------
    backoff = BackoffPolicy().load_state(header.get("backoff"))
    remaining = backoff.remaining(now=now)
    if remaining > 0:
        raise VaultLocked(remaining)

    # --- PIN -> MK ------------------------------------------------------
    try:
        slot = KeySlot.from_json(header["keyslots"]["pin"])
        mk = unwrap_pin_slot(pin, slot, header["kdf"])
    except WrongSecret:
        _persist_failure(path, header, backoff, now)
        raise
    except C.ContainerError as e:
        raise VaultError(str(e)) from e

    try:
        session = _open(path, mk, header)
    except C.ContainerError as e:
        raise VaultError(str(e)) from e

    # --- gate facial --------------------------------------------------
    require_face = header.get("policy", {}).get("require_face", True)
    if require_face and C.secret_exists(path, C.FACES_NAME):
        if face_gate is None:
            session.close()
            raise VaultError(
                "Esta bóveda exige reconocimiento facial. Instala el extra 'face' "
                "o entra con la frase de recuperación."
            )
        try:
            result = face_gate(session)
        except Exception as e:  # noqa: BLE001 - cualquier fallo del motor = rechazo seguro
            session.close()
            raise VaultError(f"Fallo en la verificación facial: {e}") from e
        if not getattr(result, "ok", False):
            session.close()
            _persist_failure(path, header, backoff, now)
            raise FaceRejected(getattr(result, "reason", "no coincide"),
                               float(getattr(result, "score", 0.0)))

    _persist_success(path, header, backoff)
    session.log_event(audit.UNLOCK_OK, "PIN + rostro" if require_face and C.secret_exists(path, C.FACES_NAME) else "PIN")
    return session


def vault_status(path: os.PathLike | str) -> dict:
    """Estado para la UI / el comando `status` (no descifra nada)."""
    path = Path(path)
    header = C.read_header(path)
    backoff = BackoffPolicy().load_state(header.get("backoff"))
    policy = header.get("policy", {})
    stats = header.get("stats", {})
    return {
        "vault_id": header.get("vault_id"),
        "has_face": C.secret_exists(path, C.FACES_NAME),
        "require_face": policy.get("require_face", True),
        "auto_lock_seconds": policy.get("auto_lock_seconds"),
        "failures": backoff.failures,
        "locked_for": backoff.remaining(),
        "wipe_flag": backoff.wiped,
        "last_unlock": stats.get("last_unlock"),
        "failed_total": stats.get("failed_total", 0),
    }

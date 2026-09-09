"""CLI de pruebas.

NO es el producto final (eso es la GUI PySide6 de la Fase 4). Ejercita el
núcleo + el desbloqueo completo (PIN + rostro + prueba de vida):

    bovedafacial init    ~/secreta.vault
    bovedafacial enroll  ~/secreta.vault           # enrola tu rostro
    bovedafacial status  ~/secreta.vault
    bovedafacial add     ~/secreta.vault ~/Documentos/contratos --dest /docs
    bovedafacial ls      ~/secreta.vault /docs
    bovedafacial get     ~/secreta.vault /docs/contratos/2025.pdf ./2025.pdf
    bovedafacial rm      ~/secreta.vault /docs/contratos/2025.pdf

Opciones de desbloqueo en add/ls/get/rm/enroll:
    --recovery    entrar con la frase de 24 palabras (salta el rostro)
    --pin-only    SOLO PRUEBAS: salta el bloqueo por intentos y el rostro
"""

from __future__ import annotations

from pathlib import Path

import click

from .crypto.keyslots import WrongSecret
from .vault import (
    FaceRejected,
    Session,
    VaultError,
    VaultLocked,
    create_vault,
    open_vault,
    unlock_with_pin,
    vault_status,
)


def _build_face_gate():
    try:
        from .face import make_gate
    except ImportError as e:  # pragma: no cover
        raise click.ClickException(
            "Esta bóveda exige rostro. Instala el extra facial: uv sync --extra face"
        ) from e

    def progress(best, good, live_ok, frames):
        mov = "movimiento ✓" if live_ok else "muévete un poco"
        click.echo(f"\r  {mov} · parecido {best:.2f} · coincidencias {good}    ", nl=False)

    return make_gate(on_progress=progress)


def _open(vault: Path, *, recovery: bool = False, pin_only: bool = False) -> Session:
    try:
        if recovery:
            phrase = click.prompt("Frase de recuperación (24 palabras)", hide_input=True)
            return open_vault(vault, phrase=phrase)

        pin = click.prompt("PIN", hide_input=True)
        if pin_only:
            click.secho("  (--pin-only: sin bloqueo ni rostro)", fg="yellow")
            return unlock_with_pin(vault, pin)

        st = vault_status(vault)
        gate = _build_face_gate() if (st["require_face"] and st["has_face"]) else None
        if gate:
            click.echo("Mírate a la cámara y muévete un poco: gira la cara, acércate o parpadea.")
        session = open_vault(vault, pin=pin, face_gate=gate)
        if gate:
            click.echo("\r  rostro verificado ✓                                          ")
        return session
    except VaultLocked as e:
        raise click.ClickException(str(e)) from e
    except FaceRejected as e:
        raise click.ClickException(f"{e}  (parecido {e.score:.2f})") from e
    except (WrongSecret, VaultError) as e:
        raise click.ClickException(str(e)) from e


def _unlock_opts(fn):
    fn = click.option("--recovery", is_flag=True,
                      help="Entrar con la frase de 24 palabras (salta el rostro).")(fn)
    fn = click.option("--pin-only", is_flag=True,
                      help="SOLO PRUEBAS: salta el bloqueo por intentos y el rostro.")(fn)
    return fn


@click.group()
@click.version_option(package_name="bovedafacial")
def main() -> None:
    """Bóveda de carpetas cifrada con desbloqueo por PIN + rostro."""


@main.command()
@click.argument("vault", type=click.Path(path_type=Path))
def init(vault: Path) -> None:
    """Crea una bóveda nueva."""
    pin = click.prompt("PIN nuevo (mín. 6)", hide_input=True, confirmation_prompt=True)
    try:
        phrase, session = create_vault(vault, pin)
    except VaultError as e:
        raise click.ClickException(str(e)) from e
    with session:
        pass
    click.secho("\n===== FRASE DE RECUPERACIÓN (24 palabras) =====", fg="yellow", bold=True)
    click.echo(phrase)
    click.secho(
        "Apúntala en papel y guárdala FUERA del equipo. No se volverá a mostrar.\n"
        "Es la única forma de entrar si falla la cámara o cambia tu aspecto.",
        fg="yellow",
    )
    click.echo(f"\nBóveda creada en: {session.path}")
    click.echo("Siguiente paso:  bovedafacial enroll " + str(session.path))


@main.command()
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.option("--frames", default=80, show_default=True, help="Máx. frames a capturar.")
@_unlock_opts
def enroll(vault: Path, frames: int, recovery: bool, pin_only: bool) -> None:
    """Enrola (o vuelve a enrolar) tu rostro en la bóveda."""
    try:
        from .face import EnrollSession, FaceEngine, default_camera, save_template
        from .face.enroll import EnrollError
    except ImportError as e:  # pragma: no cover
        raise click.ClickException("Falta el extra facial: uv sync --extra face") from e

    with _open(vault, recovery=recovery, pin_only=pin_only) as session:
        click.echo("Cargando motor facial (puede tardar la primera vez)…")
        engine = FaceEngine().load()
        click.echo(f"  motor listo · GPU={engine.on_gpu}")
        es = EnrollSession(engine, target=10)
        click.echo("Mira a la cámara, muévete un poco y varía la expresión:")
        seen = 0
        with default_camera() as cam:
            while not es.done and seen < frames:
                es.feed(cam.read())
                seen += 1
                bar = "█" * es.accepted + "·" * (es.target - es.accepted)
                hint = ", ".join(es.last_problems[:2]) if es.last_problems else "ok"
                click.echo(f"\r  [{bar}] {es.accepted}/{es.target}  {hint}          ", nl=False)
        click.echo()
        try:
            tpl = es.finish()
        except EnrollError as e:
            raise click.ClickException(str(e)) from e
        save_template(session.path, session.mk, tpl)
    click.secho(
        f"Rostro enrolado: {tpl.count} muestras · consistencia "
        f"{tpl.self_consistency():.2f} · umbral {tpl.threshold}",
        fg="green",
    )


@main.command()
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
def status(vault: Path) -> None:
    """Estado de la bóveda (sin descifrar nada)."""
    st = vault_status(vault)
    lock = f"{st['locked_for']:.0f} s" if st["locked_for"] > 0 else "no"
    last = st["last_unlock"]
    click.echo(f"  id bóveda          {st['vault_id']}")
    click.echo(f"  rostro enrolado    {'sí' if st['has_face'] else 'no'}"
               f"  (exigido: {'sí' if st['require_face'] else 'no'})")
    click.echo(f"  bloqueo automático {st['auto_lock_seconds']} s")
    click.echo(f"  intentos fallidos  {st['failures']}  (total histórico: {st['failed_total']})")
    click.echo(f"  bloqueada ahora    {lock}")
    if st["wipe_flag"]:
        click.secho("  ¡límite de intentos alcanzado! (la política de borrado la decide la GUI)",
                    fg="red")
    click.echo(f"  último desbloqueo  {last if last else '—'}")


@main.command()
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--dest", default="/", help="Carpeta destino dentro de la bóveda.")
@_unlock_opts
def add(vault: Path, src: Path, dest: str, recovery: bool, pin_only: bool) -> None:
    """Importa un archivo o una carpeta a la bóveda."""
    with _open(vault, recovery=recovery, pin_only=pin_only) as session:
        n = session.import_path(src, dest)
    click.echo(f"Importados {n} archivo(s) en {dest}")


@main.command(name="ls")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("path", default="/")
@_unlock_opts
def ls_(vault: Path, path: str, recovery: bool, pin_only: bool) -> None:
    """Lista el contenido de una carpeta de la bóveda."""
    with _open(vault, recovery=recovery, pin_only=pin_only) as session:
        rows = session.list_dir(path)
    for row in rows:
        if row["type"] == "dir":
            click.secho(f"  {row['name']}/", fg="blue")
        else:
            click.echo(f"  {row['name']}  ({row['size']} B)")
    if not rows:
        click.echo("  (vacío)")


@main.command()
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("vpath")
@click.argument("dest", type=click.Path(path_type=Path))
@_unlock_opts
def get(vault: Path, vpath: str, dest: Path, recovery: bool, pin_only: bool) -> None:
    """Extrae un archivo o carpeta de la bóveda a DEST (en claro)."""
    with _open(vault, recovery=recovery, pin_only=pin_only) as session:
        try:
            out = session.extract(vpath, dest)
        except VaultError as e:
            raise click.ClickException(str(e)) from e
    click.echo(f"Extraído en: {out}")


@main.command()
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("vpath")
@_unlock_opts
@click.confirmation_option(prompt="¿Eliminar de la bóveda de forma permanente?")
def rm(vault: Path, vpath: str, recovery: bool, pin_only: bool) -> None:
    """Elimina un archivo o carpeta de la bóveda."""
    with _open(vault, recovery=recovery, pin_only=pin_only) as session:
        try:
            session.remove(vpath)
        except VaultError as e:
            raise click.ClickException(str(e)) from e
    click.echo(f"Eliminado: {vpath}")


if __name__ == "__main__":
    main()

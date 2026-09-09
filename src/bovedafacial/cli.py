"""CLI de pruebas de la Fase 1.

NO es el producto final (eso es la GUI PySide6 de la Fase 4). Sirve para
ejercitar el núcleo cripto + contenedor sin cámara:

    bovedafacial init   ~/secreta.vault
    bovedafacial add    ~/secreta.vault ~/Documentos/contratos --dest /docs
    bovedafacial ls     ~/secreta.vault /docs
    bovedafacial get    ~/secreta.vault /docs/contratos/2025.pdf ./salida.pdf
    bovedafacial rm     ~/secreta.vault /docs/contratos/2025.pdf

El desbloqueo pide PIN por consola; con --recovery pide la frase de 24 palabras.
"""

from __future__ import annotations

from pathlib import Path

import click

from .crypto.keyslots import WrongSecret
from .vault import (
    Session,
    VaultError,
    create_vault,
    unlock_with_pin,
    unlock_with_recovery,
)


def _unlock(vault: Path, recovery: bool) -> Session:
    try:
        if recovery:
            phrase = click.prompt("Frase de recuperación (24 palabras)", hide_input=True)
            return unlock_with_recovery(vault, phrase)
        pin = click.prompt("PIN", hide_input=True)
        return unlock_with_pin(vault, pin)
    except (WrongSecret, VaultError) as e:
        raise click.ClickException(str(e)) from e


@click.group()
@click.version_option(package_name="bovedafacial")
def main() -> None:
    """Bóveda de carpetas cifrada (núcleo Fase 1)."""


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


@main.command()
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.option("--dest", default="/", help="Carpeta destino dentro de la bóveda.")
@click.option("--recovery", is_flag=True, help="Desbloquear con la frase en vez del PIN.")
def add(vault: Path, src: Path, dest: str, recovery: bool) -> None:
    """Importa un archivo o una carpeta a la bóveda."""
    with _unlock(vault, recovery) as session:
        n = session.import_path(src, dest)
    click.echo(f"Importados {n} archivo(s) en {dest}")


@main.command(name="ls")
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("path", default="/")
@click.option("--recovery", is_flag=True)
def ls_(vault: Path, path: str, recovery: bool) -> None:
    """Lista el contenido de una carpeta de la bóveda."""
    with _unlock(vault, recovery) as session:
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
@click.option("--recovery", is_flag=True)
def get(vault: Path, vpath: str, dest: Path, recovery: bool) -> None:
    """Extrae un archivo o carpeta de la bóveda a DEST (en claro)."""
    with _unlock(vault, recovery) as session:
        try:
            out = session.extract(vpath, dest)
        except VaultError as e:
            raise click.ClickException(str(e)) from e
    click.echo(f"Extraído en: {out}")


@main.command()
@click.argument("vault", type=click.Path(exists=True, path_type=Path))
@click.argument("vpath")
@click.option("--recovery", is_flag=True)
@click.confirmation_option(prompt="¿Eliminar de la bóveda de forma permanente?")
def rm(vault: Path, vpath: str, recovery: bool) -> None:
    """Elimina un archivo o carpeta de la bóveda."""
    with _unlock(vault, recovery) as session:
        try:
            session.remove(vpath)
        except VaultError as e:
            raise click.ClickException(str(e)) from e
    click.echo(f"Eliminado: {vpath}")


if __name__ == "__main__":
    main()

"""Lógica de escaneo y organización. Sin dependencias de Qt."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .categorias import CARPETAS, CARPETAS_CATEGORIA, categoria_de


@dataclass
class Opciones:
    carpeta: Path
    incluir_subcarpetas: bool = False   # recorrer también lo que hay dentro de subcarpetas
    mover: bool = True                  # False = copiar
    incluir_carpetas: bool = False      # subcarpetas sueltas -> carpeta "Carpetas"
    incluir_ocultos: bool = False       # archivos que empiezan por "."


@dataclass
class Accion:
    origen: Path
    categoria: str


@dataclass
class Plan:
    acciones: list[Accion] = field(default_factory=list)
    omitidos: list[tuple[Path, str]] = field(default_factory=list)  # (ruta, motivo)

    def por_categoria(self) -> dict[str, int]:
        conteo: dict[str, int] = {}
        for a in self.acciones:
            conteo[a.categoria] = conteo.get(a.categoria, 0) + 1
        return dict(sorted(conteo.items(), key=lambda kv: (-kv[1], kv[0])))


def _destino_libre(carpeta_cat: Path, nombre: str) -> Path:
    """Ruta de destino evitando pisar un archivo existente: 'foo.txt' -> 'foo (2).txt'."""
    destino = carpeta_cat / nombre
    if not destino.exists():
        return destino
    tallo, suf = destino.stem, destino.suffix
    i = 2
    while True:
        cand = carpeta_cat / f"{tallo} ({i}){suf}"
        if not cand.exists():
            return cand
        i += 1


def construir_plan(op: Opciones) -> Plan:
    """Recorre la carpeta y decide qué mover, sin tocar nada."""
    plan = Plan()
    raiz = op.carpeta.resolve()

    if not raiz.is_dir():
        raise NotADirectoryError(f"No es una carpeta: {raiz}")

    if op.incluir_subcarpetas:
        candidatos = raiz.rglob("*")
    else:
        candidatos = raiz.iterdir()

    for p in candidatos:
        rel = p.relative_to(raiz).parts
        # Nunca tocar lo que ya vive dentro de una carpeta de categoría.
        if rel and rel[0] in CARPETAS_CATEGORIA:
            continue

        nombre = p.name
        if p.is_symlink():
            plan.omitidos.append((p, "enlace simbólico"))
            continue
        if not op.incluir_ocultos and nombre.startswith("."):
            plan.omitidos.append((p, "oculto"))
            continue

        if p.is_dir():
            if op.incluir_subcarpetas:
                continue  # se recorre su contenido; la carpeta vacía se limpia al final
            if op.incluir_carpetas:
                plan.acciones.append(Accion(p, CARPETAS))
            else:
                plan.omitidos.append((p, "es carpeta"))
            continue

        if p.is_file():
            plan.acciones.append(Accion(p, categoria_de(nombre)))

    plan.acciones.sort(key=lambda a: (a.categoria, a.origen.name.lower()))
    return plan


def _limpiar_vacias(raiz: Path) -> list[Path]:
    """Borra subcarpetas que quedaron vacías tras mover su contenido."""
    eliminadas: list[Path] = []
    dirs = [d for d in raiz.rglob("*") if d.is_dir()]
    for p in sorted(dirs, key=lambda d: len(d.parts), reverse=True):
        rel = p.relative_to(raiz).parts
        if rel and rel[0] in CARPETAS_CATEGORIA:
            continue
        try:
            next(p.iterdir())
        except StopIteration:
            try:
                p.rmdir()
                eliminadas.append(p)
            except OSError:
                pass
    return eliminadas


def ejecutar(
    plan: Plan,
    op: Opciones,
    progreso: Callable[[int, int, Accion], None] | None = None,
) -> tuple[int, list[tuple[Path, str]], list[Path]]:
    """Aplica el plan. Devuelve (hechos, errores, carpetas_eliminadas)."""
    raiz = op.carpeta.resolve()
    hechos = 0
    errores: list[tuple[Path, str]] = []
    total = len(plan.acciones)

    for i, acc in enumerate(plan.acciones, 1):
        try:
            if not acc.origen.exists():
                errores.append((acc.origen, "ya no existe"))
            else:
                carpeta_cat = raiz / acc.categoria
                carpeta_cat.mkdir(parents=True, exist_ok=True)
                destino = _destino_libre(carpeta_cat, acc.origen.name)
                if op.mover:
                    shutil.move(str(acc.origen), str(destino))
                elif acc.origen.is_dir():
                    shutil.copytree(str(acc.origen), str(destino))
                else:
                    shutil.copy2(str(acc.origen), str(destino))
                hechos += 1
        except Exception as e:  # noqa: BLE001 - se reporta al usuario
            errores.append((acc.origen, str(e)))
        if progreso:
            progreso(i, total, acc)

    eliminadas: list[Path] = []
    if op.mover and op.incluir_subcarpetas:
        eliminadas = _limpiar_vacias(raiz)
    return hechos, errores, eliminadas

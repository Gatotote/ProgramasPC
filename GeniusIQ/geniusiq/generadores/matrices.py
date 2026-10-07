"""Matrices de figuras 3×3 (estilo Raven / Matrices de Wechsler).

Cada atributo de la celda sigue una regla por fila:
  * constante,
  * distribución de tres valores (cuadrado latino),
  * progresión (cantidad que aumenta, flecha que gira…).
Entre más atributos cambian, más difícil es la matriz (nivel 1 a 6).
"""

from __future__ import annotations

import random
from dataclasses import replace

from ..figuras import FORMAS, Celda, Matriz
from . import Item, mezclar, por_dificultad

DOMINIO = {
    "forma": FORMAS,
    "numero": [1, 2, 3, 4, 5],
    "tamano": [0, 1, 2],
    "relleno": [0, 1, 2],
    "rotacion": [0, 45, 90, 135, 180, 225, 270, 315],
}
B_NIVEL = {1: -2.3, 2: -1.3, 3: -0.4, 4: 0.4, 5: 1.1, 6: 1.8}
N_CAMBIAN = {1: 1, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4}


def _regla(rng: random.Random, atributo: str, nivel: int):
    """Devuelve f(fila, columna) → valor del atributo."""
    desp = rng.choice([1, 2]) if nivel >= 4 else 1
    if atributo == "forma":
        vals = rng.sample(FORMAS, 3)
        return lambda f, c: vals[(c + f * desp) % 3]
    if atributo in ("tamano", "relleno"):
        vals = rng.sample([0, 1, 2], 3)
        d = rng.choice([0, 1, 2]) if nivel >= 3 else rng.choice([0, 1])
        return lambda f, c: vals[(c + f * d) % 3]
    if atributo == "numero":
        if rng.random() < 0.6:
            inicio = rng.choice([1, 2]) if nivel < 4 else 1
            off = 1 if nivel >= 4 and rng.random() < 0.5 else 0
            return lambda f, c: inicio + c + f * off
        vals = rng.sample([1, 2, 3, 4], 3)
        return lambda f, c: vals[(c + f * desp) % 3]
    if atributo == "rotacion":
        paso = rng.choice([45, 90])
        off = rng.choice([0, 45]) if nivel >= 6 else 0
        return lambda f, c: (c * paso + f * off) % 360
    raise ValueError(atributo)


def _distractores(rng: random.Random, resp: Celda, celdas: list[Celda], cambian: list[str],
                  usar_rot: bool, cuantos: int) -> list[Celda]:
    atributos = ["numero", "tamano", "relleno"] + (["rotacion"] if usar_rot else ["forma"])
    vistos = {resp.firma()}
    elegidos: list[Celda] = []

    def agregar(c: Celda) -> None:
        if c.firma() not in vistos and len(elegidos) < cuantos:
            vistos.add(c.firma())
            elegidos.append(c)

    # 1) cambiar un atributo de los que varían, usando valores que sí aparecen en la matriz
    plausibles = []
    for at in cambian:
        presentes = {getattr(c, at) for c in celdas}
        plausibles += [replace(resp, **{at: v}) for v in presentes if v != getattr(resp, at)]
    rng.shuffle(plausibles)
    for c in plausibles:
        agregar(c)
    # 2) cambiar cualquier atributo
    otros = [replace(resp, **{at: v}) for at in atributos for v in DOMINIO[at] if v != getattr(resp, at)]
    rng.shuffle(otros)
    for c in otros[:cuantos]:
        agregar(c)
    # 3) cambiar dos atributos
    while len(elegidos) < cuantos:
        a1, a2 = rng.sample(atributos, 2)
        agregar(replace(resp, **{a1: rng.choice(DOMINIO[a1]), a2: rng.choice(DOMINIO[a2])}))
    return elegidos


def generar(rng: random.Random, nivel: int) -> Item:
    usar_rot = nivel >= 5 and rng.random() < 0.5
    candidatos = ["forma", "numero", "tamano", "relleno"]
    if usar_rot:
        candidatos.remove("forma")
    n = N_CAMBIAN[nivel] - (1 if usar_rot else 0)
    cambian = rng.sample(candidatos, n) + (["rotacion"] if usar_rot else [])

    base = {
        "forma": "flecha" if usar_rot else rng.choice(FORMAS),
        "numero": rng.choice([1, 2, 3]),
        "tamano": rng.choice([1, 2]),
        "relleno": rng.choice([0, 1, 2]),
        "rotacion": 0,
    }
    reglas = {at: _regla(rng, at, nivel) for at in cambian}
    celdas = []
    for f in range(3):
        for c in range(3):
            valores = dict(base)
            for at, regla in reglas.items():
                valores[at] = regla(f, c)
            celdas.append(Celda(**valores))

    resp = celdas[8]
    opciones, correcta = mezclar(rng, resp, _distractores(rng, resp, celdas, cambian, usar_rot, 7))
    return Item(
        clase="figura",
        pregunta="¿Qué figura completa la matriz?",
        b=B_NIVEL[nivel] + rng.uniform(-0.15, 0.15),
        correcta=correcta,
        opciones=opciones,
        figura=Matriz(celdas[:8] + [None]),
        a=1.5,
    )


def matrices(rng: random.Random) -> list[Item]:
    niveles = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6]
    return por_dificultad([generar(rng, n) for n in niveles])

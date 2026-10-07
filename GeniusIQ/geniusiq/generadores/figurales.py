"""Pruebas de figuras: series, clasificación, condiciones (topología) y rotación mental."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import replace

from ..figuras import FORMAS, Celda, Poliomino, SerieFiguras, Topologia, dentro
from . import Item, mezclar, por_dificultad

# ---------------------------------------------------------------- Series

B_SERIE = {1: -1.6, 2: -0.4, 3: 0.7, 4: 1.5}


def serie(rng: random.Random, nivel: int) -> Item:
    usar_rot = nivel >= 2 and rng.random() < 0.5
    candidatos = ["numero", "tamano", "relleno"] + (["rotacion"] if usar_rot else ["forma"])
    n = {1: 1, 2: 2, 3: 3, 4: 3}[nivel]
    cambian = rng.sample(candidatos, n)
    if usar_rot and "rotacion" not in cambian:
        cambian[-1] = "rotacion"

    reglas = {}
    for at in cambian:
        if at == "numero":
            reglas[at] = (lambda i: 1 + i) if rng.random() < 0.5 else (lambda i: 5 - i)
        elif at in ("tamano", "relleno"):
            ini, d = rng.randint(0, 2), (rng.choice([1, 2]) if nivel >= 3 else 1)
            reglas[at] = lambda i, ini=ini, d=d: (ini + d * i) % 3
        elif at == "forma":
            vals = rng.sample(FORMAS, 3)
            reglas[at] = lambda i, vals=vals: vals[i % 3]
        elif at == "rotacion":
            paso = rng.choice([135, 225]) if nivel >= 4 else rng.choice([45, 90])
            reglas[at] = lambda i, paso=paso: (i * paso) % 360

    base = Celda(forma="flecha" if usar_rot else rng.choice(FORMAS), numero=rng.choice([1, 2, 3]),
                 tamano=rng.choice([1, 2]), relleno=rng.choice([0, 1, 2]))
    celdas = [replace(base, **{at: f(i) for at, f in reglas.items()}) for i in range(5)]
    resp = celdas[4]

    dom = {"numero": [1, 2, 3, 4, 5], "tamano": [0, 1, 2], "relleno": [0, 1, 2],
           "forma": FORMAS, "rotacion": [0, 45, 90, 135, 180, 225, 270, 315]}
    vistos, distr = {resp.firma()}, []
    pool = [replace(resp, **{at: v}) for at in cambian for v in dom[at] if v != getattr(resp, at)]
    pool += [replace(resp, **{at: v}) for at in dom if at not in cambian
             and not (at == "rotacion" and not usar_rot) and not (at == "forma" and usar_rot)
             for v in dom[at] if v != getattr(resp, at)]
    rng.shuffle(pool)
    # primero los distractores en atributos que cambian (más tentadores)
    pool.sort(key=lambda c: 0 if any(getattr(c, at) != getattr(resp, at) for at in cambian) else 1)
    for c in pool:
        if c.firma() not in vistos and len(distr) < 4:
            vistos.add(c.firma())
            distr.append(c)
    opciones, correcta = mezclar(rng, resp, distr)
    return Item("figura", "¿Qué figura sigue en la serie?", B_SERIE[nivel] + rng.uniform(-.15, .15),
                correcta, opciones, SerieFiguras(celdas[:4]), a=1.4)


def series_figuras(rng: random.Random) -> list[Item]:
    return por_dificultad([serie(rng, n) for n in [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]])


# ---------------------------------------------------------------- Clasificación

B_CLASIF = {1: -2.0, 2: -0.9, 3: 0.1, 4: 0.9, 5: 1.6}
_ATR = ["forma", "tamano", "relleno", "numero"]


def _ambiguo(celdas: list[Celda], objetivo: str) -> bool:
    """¿Hay otro atributo que también deje a una sola figura fuera del grupo?"""
    for at in _ATR:
        if at == objetivo or (objetivo == "paridad" and at == "numero"):
            continue
        if max(Counter(getattr(c, at) for c in celdas).values()) == 4:
            return True
    if objetivo != "paridad":
        if max(Counter(c.numero % 2 for c in celdas).values()) == 4:
            return True
    return False


def clasificacion(rng: random.Random, nivel: int) -> Item:
    objetivos = {1: ["forma"], 2: ["forma", "relleno"], 3: ["tamano", "relleno"],
                 4: ["paridad", "tamano"], 5: ["paridad", "forma"]}[nivel]
    n_ruido = {1: 0, 2: 1, 3: 2, 4: 2, 5: 3}[nivel]
    dom = {"forma": FORMAS, "tamano": [0, 1, 2], "relleno": [0, 1, 2], "numero": [1, 2, 3, 4]}
    for _ in range(500):
        objetivo = rng.choice(objetivos)
        fijo = {at: rng.choice(v) for at, v in dom.items()}
        libres = [a for a in _ATR if a != objetivo and not (objetivo == "paridad" and a == "numero")]
        # con formas distintas el tamaño se aprecia mal: nunca mezclar forma y tamaño
        if objetivo == "tamano":
            libres.remove("forma")
        if objetivo == "forma":
            libres.remove("tamano")
        ruido = rng.sample(libres, min(n_ruido, len(libres)))
        if "forma" in ruido and "tamano" in ruido:
            continue
        celdas = []
        for _i in range(5):
            v = dict(fijo)
            for at in ruido:
                v[at] = rng.choice(dom[at])
            celdas.append(v)
        raro = rng.randrange(5)
        if objetivo == "paridad":
            pares = [rng.choice([2, 4]) for _ in range(4)]
            if len(set(pares)) == 1:
                pares[0] = 6 - pares[0]
            for i, c in enumerate(j for j in range(5) if j != raro):
                celdas[c]["numero"] = pares[i]
            celdas[raro]["numero"] = rng.choice([1, 3, 5])
        else:
            celdas[raro][objetivo] = rng.choice([x for x in dom[objetivo] if x != fijo[objetivo]])
        figuras = [Celda(**c) for c in celdas]
        if not _ambiguo(figuras, objetivo):
            return Item("figura", "¿Cuál figura NO pertenece al grupo?",
                        B_CLASIF[nivel] + rng.uniform(-.15, .15), raro, figuras, None, a=1.3)
    raise RuntimeError("no se pudo generar la clasificación")


def clasificaciones(rng: random.Random) -> list[Item]:
    return por_dificultad([clasificacion(rng, n) for n in [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]])


# ---------------------------------------------------------------- Condiciones (topología)

NOMBRES = {"circulo": "del círculo", "cuadrado": "del cuadrado", "triangulo": "del triángulo"}
_MARGEN = 0.015  # holgura para que «sí» y «no» se vean claros a simple vista
B_COND = {1: -0.9, 2: -0.2, 3: 0.5, 4: 1.2}
_LADO = 48
_MUESTRA = [((i + .5) / _LADO, (j + .5) / _LADO) for i in range(_LADO) for j in range(_LADO)]


def _diseno(rng: random.Random) -> list[tuple]:
    formas = []
    for tipo in ("circulo", "cuadrado", "triangulo"):
        s = rng.uniform(0.14, 0.27)
        m = s * 1.3 + 0.03
        formas.append((tipo, rng.uniform(m, 1 - m), rng.uniform(m, 1 - m), s))
    return formas


def _contenido(rng: random.Random, interior: str, exterior: str) -> list[tuple]:
    """Diseño donde `interior` queda completamente dentro de `exterior`."""
    formas = {f[0]: f for f in _diseno(rng)}
    _, cx, cy, s = formas[exterior]
    if exterior == "triangulo":
        cy += s * 0.2  # centro geométrico del triángulo
    formas[interior] = (interior, cx, cy, s * rng.uniform(0.3, 0.42))
    return list(formas.values())


def _mascara(forma: tuple, margen: float) -> int:
    """Entero cuyos bits marcan los puntos de muestra que caen dentro de la forma."""
    m = 0
    for i, (x, y) in enumerate(_MUESTRA):
        if dentro(forma, x, y, margen):
            m |= 1 << i
    return m


def _puntos(formas: list[tuple], dentro_de: list[str], fuera_de: list[str]) -> tuple[int, int]:
    """(puntos que cumplen con holgura, puntos que cumplen siendo generosos).

    Un dibujo «sí» debe cumplir aun achicando las formas de adentro; uno «no» no debe
    cumplir ni agrandándolas. Así nada depende de un roce de líneas.
    """
    por_tipo = {f[0]: f for f in formas}
    todos = (1 << len(_MUESTRA)) - 1
    estricto, generoso = todos, todos
    for t in dentro_de:
        estricto &= _mascara(por_tipo[t], -_MARGEN)
        generoso &= _mascara(por_tipo[t], _MARGEN)
    for t in fuera_de:
        estricto &= ~_mascara(por_tipo[t], _MARGEN)
        generoso &= ~_mascara(por_tipo[t], -_MARGEN)
    return estricto.bit_count(), generoso.bit_count()


def condicion(rng: random.Random, nivel: int) -> Item:
    tipos = ["circulo", "cuadrado", "triangulo"]
    for _ in range(50):
        rng.shuffle(tipos)
        dentro_de, fuera_de = {1: (tipos[:2], []), 2: (tipos[:1], tipos[1:2]),
                               3: (tipos[:3], []), 4: (tipos[:2], tipos[2:])}[nivel]
        si, no = None, []
        for _ in range(400):
            if nivel == 2 and len(no) < 4 and rng.random() < 0.5:
                d = _contenido(rng, dentro_de[0], fuera_de[0])
            else:
                d = _diseno(rng)
            estricto, generoso = _puntos(d, dentro_de, fuera_de)
            if estricto >= 20 and si is None:
                si = d
            elif generoso == 0 and len(no) < 4:
                no.append(d)
            if si and len(no) == 4:
                break
        if si and len(no) == 4:
            texto = "dentro " + " y ".join(NOMBRES[t] for t in dentro_de)
            if fuera_de:
                texto += ", pero fuera " + NOMBRES[fuera_de[0]]
            opciones, correcta = mezclar(rng, Topologia(si), [Topologia(x) for x in no])
            return Item("figura", f"¿En cuál dibujo se puede poner un punto que quede {texto}?",
                        B_COND[nivel] + rng.uniform(-.15, .15), correcta, opciones, None, a=1.3)
    raise RuntimeError("no se pudo generar la condición")


def condiciones(rng: random.Random) -> list[Item]:
    return por_dificultad([condicion(rng, n) for n in [1, 1, 2, 2, 3, 3, 4, 4]])


# ---------------------------------------------------------------- Rotación mental

B_ROT = {4: -1.6, 5: -0.7, 6: 0.1, 7: 0.8, 8: 1.5}


def _normalizar(celdas) -> frozenset:
    mx = min(x for x, _ in celdas)
    my = min(y for _, y in celdas)
    return frozenset((x - mx, y - my) for x, y in celdas)


def _girar(celdas, veces: int) -> frozenset:
    for _ in range(veces % 4):
        celdas = [(y, -x) for x, y in celdas]
    return _normalizar(celdas)


def _espejo(celdas) -> frozenset:
    return _normalizar([(-x, y) for x, y in celdas])


def _poliomino(rng: random.Random, n: int) -> frozenset:
    celdas = {(0, 0)}
    while len(celdas) < n:
        x, y = rng.choice(sorted(celdas))
        dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        celdas.add((x + dx, y + dy))
    return _normalizar(celdas)


def rotacion(rng: random.Random, n: int) -> Item:
    for _ in range(1000):
        P = _poliomino(rng, n)
        giros = {_girar(P, k) for k in range(4)}
        espejos = {_girar(_espejo(P), k) for k in range(4)}
        if giros & espejos or len(espejos) < 3:
            continue  # la figura es simétrica: el espejo no se distingue
        k0 = rng.randrange(4)
        modelo = _girar(P, k0)
        posibles = [g for g in giros if g != modelo]
        if not posibles:
            continue
        resp = rng.choice(posibles)
        distr = rng.sample(sorted(espejos, key=sorted), 3)
        opciones, correcta = mezclar(rng, Poliomino(resp), [Poliomino(d) for d in distr])
        return Item("figura", "¿Cuál es la MISMA figura de arriba, solo girada (sin voltearla como espejo)?",
                    B_ROT[n] + rng.uniform(-.15, .15), correcta, opciones, Poliomino(modelo), a=1.3)
    raise RuntimeError("no se pudo generar la rotación")


def rotaciones(rng: random.Random) -> list[Item]:
    return por_dificultad([rotacion(rng, n) for n in [4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8]])

"""Series numéricas, aritmética (problemas) y balanzas (pesos de figuras)."""

from __future__ import annotations

import random

from . import Item, mezclar, por_dificultad

PRIMOS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]

# ---------------------------------------------------------------- Series numéricas
#
# Cada tipo de patrón es una función rng → términos (el último es la respuesta).
# En cada test se eligen al azar unos cuantos tipos de cada banda de dificultad,
# así no sale siempre la misma secuencia de patrones.


def _aritmetica(s: int, d: int, n: int = 6) -> list[int]:
    return [s + d * i for i in range(n)]


def _acumular(inicio: int, saltos) -> list[int]:
    t = [inicio]
    for d in saltos:
        t.append(t[-1] + d)
    return t


def _recurrente(t: list[int], f, n: int = 6) -> list[int]:
    while len(t) < n:
        t.append(f(t))
    return t


def _intercaladas(rng: random.Random) -> list[int]:
    s1, d1 = rng.randint(1, 9), rng.randint(2, 5)
    s2, d2 = rng.randint(10, 30), rng.choice([-3, -2, 3, 4, 6])
    return [s1 + d1 * (i // 2) if i % 2 == 0 else s2 + d2 * (i // 2) for i in range(7)]


def _alterna_mult_suma(rng: random.Random) -> list[int]:
    k, m = rng.randint(1, 5), rng.choice([2, 3])
    t = [rng.randint(1, 4)]
    for i in range(5):
        t.append(t[-1] * m if i % 2 == 0 else t[-1] + k)
    return t


TIPOS_SERIE = [
    # (dificultad b, generador)
    # muy fáciles
    (-2.8, lambda r: _aritmetica(r.randint(1, 9), r.choice([1, 2]))),
    (-2.5, lambda r: _aritmetica(r.randint(1, 9), 10)),
    (-2.3, lambda r: _aritmetica(r.randint(1, 20), r.randint(3, 9))),
    (-2.0, lambda r: (lambda d: _aritmetica(d * 6 + r.randint(5, 20), -d))(r.randint(2, 7))),
    # fáciles
    (-1.4, lambda r: (lambda s: [s * 2 ** i for i in range(6)])(r.randint(1, 6))),
    (-1.2, lambda r: (lambda k: [k * 2 ** (5 - i) for i in range(6)])(r.randint(1, 3))),
    (-1.0, lambda r: (lambda s: [s * 3 ** i for i in range(6)])(r.randint(1, 4))),
    (-0.9, lambda r: _acumular(r.randint(1, 15), [r.randint(2, 4), r.randint(5, 8)] * 3)[:6]),
    (-0.8, lambda r: (lambda k: _acumular(r.randint(1, 10), [k + i for i in range(5)]))(r.randint(1, 3))),
    # medias
    (-0.5, lambda r: (lambda o: [(i + o) ** 2 for i in range(6)])(r.randint(1, 8))),
    (-0.3, lambda r: (lambda k: _acumular(r.randint(60, 90), [-(k + i) for i in range(5)]))(r.randint(1, 3))),
    (-0.1, lambda r: (lambda a: _acumular(r.randint(5, 20), [a, -r.randint(1, a - 1)] * 3)[:6])(r.randint(4, 9))),
    (0.2, lambda r: _recurrente([r.randint(1, 4), r.randint(2, 6)], lambda t: t[-1] + t[-2])),
    (0.4, lambda r: (lambda o, c: [(i + o) ** 2 + c for i in range(6)])(r.randint(1, 5), r.choice([-1, 1, 2]))),
    (0.6, lambda r: (lambda c: _recurrente([r.randint(2, 4)], lambda t: t[-1] * 2 + c))(r.choice([1, 2, -1]))),
    (0.7, lambda r: (lambda c: _recurrente([r.randint(1, 3)], lambda t: t[-1] * 3 + c))(r.choice([1, -1]))),
    # difíciles
    (0.8, _intercaladas),
    (0.9, lambda r: (lambda d: _acumular(r.randint(1, 10), [d * 2 ** i for i in range(5)]))(r.randint(1, 3))),
    (1.1, lambda r: (lambda o: [(i + o) * (i + o + 1) for i in range(6)])(r.randint(1, 5))),
    (1.2, lambda r: (lambda i: PRIMOS[i:i + 6])(r.randint(0, len(PRIMOS) - 6))),
    (1.2, lambda r: _acumular(r.randint(1, 10), [3 ** i for i in range(5)])),
    (1.3, lambda r: (lambda o: [(i + o) ** 3 for i in range(6)])(r.randint(1, 4))),
    (1.5, _alterna_mult_suma),
    # muy difíciles
    (1.6, lambda r: _recurrente([r.randint(1, 3)], lambda t: t[-1] * len(t))),
    (1.7, lambda r: (lambda o: _acumular(r.randint(1, 10), [(i + o) ** 2 for i in range(5)]))(r.randint(1, 3))),
    (2.0, lambda r: _acumular(r.randint(1, 10), [1, 1, 2, 3, 5])),
    (2.1, lambda r: _recurrente([r.randint(0, 2), r.randint(1, 2), r.randint(1, 3)],
                                lambda t: t[-1] + t[-2] + t[-3])),
    (2.2, lambda r: (lambda k: _recurrente([r.randint(1, 3), r.randint(2, 5)],
                                           lambda t: t[-1] + t[-2] + k))(r.randint(1, 3))),
]

# Cuántos tipos se toman de cada banda de dificultad.
BANDAS_SERIE = [(-9, -1.5, 2), (-1.5, -0.6, 3), (-0.6, 0.75, 3), (0.75, 1.55, 3), (1.55, 9, 2)]


def serie_numerica(rng: random.Random, b: float, generador) -> Item:
    t = generador(rng)
    return Item("numero", "¿Qué número sigue en la serie?", b + rng.uniform(-.1, .1),
                t[-1], texto_grande=",  ".join(map(str, t[:-1])) + ",  ?", a=1.5)


def series_numericas(rng: random.Random) -> list[Item]:
    items = []
    for lo, hi, cuantos in BANDAS_SERIE:
        banda = [(b, g) for b, g in TIPOS_SERIE if lo <= b < hi]
        for b, g in rng.sample(banda, min(cuantos, len(banda))):
            items.append(serie_numerica(rng, b, g))
    return por_dificultad(items)


# ---------------------------------------------------------------- Aritmética

def _problema(rng: random.Random, nivel: int) -> tuple[str, int, float]:
    if nivel == 1:
        a, b = rng.randint(2, 5), rng.randint(1, 4)
        return f"Tienes {a} canicas y te regalan {b}. ¿Cuántas canicas tienes ahora?", a + b, -2.8
    if nivel == 2:
        a, b = rng.randint(7, 12), rng.randint(2, 6)
        return f"Tenías {a} dulces y te comiste {b}. ¿Cuántos te quedan?", a - b, -2.2
    if nivel == 3:
        a, b = rng.randint(3, 9), rng.randint(3, 8)
        return f"Cada caja trae {a} lápices. ¿Cuántos lápices hay en {b} cajas?", a * b, -1.4
    if nivel == 4:
        a, b = rng.randint(3, 9), rng.randint(3, 8)
        return f"Se reparten {a * b} galletas entre {b} niños por partes iguales. ¿Cuántas le tocan a cada uno?", a, -0.9
    if nivel == 5:
        n, p = rng.randint(2, 5), rng.choice([12, 15, 18, 25, 35])
        billete = 100 if n * p < 100 else 200
        return (f"Compras {n} cuadernos de ${p} cada uno y pagas con un billete de ${billete}. "
                "¿Cuánto te dan de cambio?", billete - n * p, -0.4)
    if nivel == 6:
        v, h = rng.choice([40, 60, 80, 90, 120]), rng.randint(2, 4)
        return f"Un autobús va a {v} km por hora. ¿Cuántos kilómetros recorre en {h} horas y media?", v * h + v // 2, 0.1
    if nivel == 7:
        d = rng.choice([10, 20, 25, 50])
        p = rng.choice([80, 120, 160, 200, 240, 320, 400])
        return f"Unos tenis cuestan ${p} y tienen {d}% de descuento. ¿Cuánto pagas?", p * (100 - d) // 100, 0.6
    if nivel == 8:
        for _ in range(100):
            a, b, d = rng.randint(2, 8), rng.randint(2, 12), rng.randint(3, 24)
            if a != b and a * d % b == 0:
                return (f"{a} albañiles construyen una barda en {d} días. Trabajando al mismo ritmo, "
                        f"¿en cuántos días la construirían {b} albañiles?", a * d // b, 1.0)
        return "6 albañiles construyen una barda en 4 días. ¿En cuántos días la construirían 3?", 8, 1.0
    if nivel == 9:
        k = rng.randint(8, 15)
        return (f"Ana tiene el triple de la edad de su hijo. Dentro de {k} años tendrá el doble. "
                "¿Cuántos años tiene Ana hoy?", 3 * k, 1.5)
    if nivel == 10:
        a, b = rng.choice([(3, 6), (4, 12), (6, 12), (10, 15), (12, 24), (20, 30)])
        return (f"Una llave llena un tinaco en {a} horas y otra en {b} horas. "
                "Si se abren las dos juntas, ¿en cuántas horas lo llenan?", a * b // (a + b), 1.9)
    cabezas = rng.randint(12, 30)
    conejos = rng.randint(3, cabezas - 3)
    patas = 4 * conejos + 2 * (cabezas - conejos)
    return (f"En una granja hay gallinas y conejos. En total hay {cabezas} cabezas y {patas} patas. "
            "¿Cuántos conejos hay?", conejos, 2.3)


def aritmetica(rng: random.Random) -> list[Item]:
    items = []
    for nivel in range(1, 12):
        texto, resp, b = _problema(rng, nivel)
        items.append(Item("numero", texto, b + rng.uniform(-.1, .1), resp, a=1.5))
    return por_dificultad(items)


# ---------------------------------------------------------------- Balanzas

SIMBOLOS = ["▲", "■", "●", "◆", "★"]
B_BAL = {1: -1.8, 2: -0.9, 3: -0.1, 4: 0.7, 5: 1.4, 6: 2.0}


def _lado(cuantos: int, simbolo: str) -> str:
    return " ".join([simbolo] * cuantos) if cuantos <= 6 else f"{cuantos} × {simbolo}"


def balanza(rng: random.Random, nivel: int) -> Item:
    nsim = {1: 2, 2: 3, 3: 3, 4: 4, 5: 4, 6: 5}[nivel]
    pesos = [1]
    for _ in range(nsim - 1):
        pesos.append(pesos[-1] * rng.choice([2, 3]))
    simb = rng.sample(SIMBOLOS, nsim)
    lineas = []
    for i in range(1, nsim):
        razon = pesos[i] // pesos[i - 1]
        if nivel >= 4 and i >= 2 and rng.random() < 0.6:
            # combinación: pesado = (razón-1) del anterior + los ligeros que valen uno de él
            sub = pesos[i - 1] // pesos[i - 2]
            lineas.append(f"{simb[i]}  =  {_lado(razon - 1, simb[i - 1])}  {_lado(sub, simb[i - 2])}")
        elif nivel >= 3 and rng.random() < 0.5:
            m = rng.choice([2, 3])
            lineas.append(f"{_lado(m, simb[i])}  =  {_lado(m * razon, simb[i - 1])}")
        else:
            lineas.append(f"{simb[i]}  =  {_lado(razon, simb[i - 1])}")
    rng.shuffle(lineas)
    cuantos = rng.choice([1, 2]) if nivel >= 2 else 2
    resp = cuantos * pesos[-1]
    distr = {resp + 1, resp - 1, resp + pesos[1], resp - pesos[1], resp * 2, max(1, resp // 2), resp + 2}
    distr = sorted(d for d in distr if d > 0 and d != resp)
    distr = rng.sample(distr, 4)
    opciones, correcta = mezclar(rng, str(resp), [str(d) for d in distr])
    return Item("texto", f"Las balanzas están en equilibrio. ¿Cuántos {simb[0]} equilibran {_lado(cuantos, simb[-1])}?",
                B_BAL[nivel] + rng.uniform(-.15, .15), correcta, opciones,
                texto_grande="\n".join(lineas), a=1.5)


def balanzas(rng: random.Random) -> list[Item]:
    return por_dificultad([balanza(rng, n) for n in [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6]])

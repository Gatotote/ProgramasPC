"""Puntuación: teoría de respuesta al ítem (TRI) y normas aproximadas por edad.

Cada pregunta tiene una dificultad `b` en la escala «theta» de un adulto joven
(media 0, desviación 1). La capacidad de la persona se estima con EAP
(media a posteriori) usando el modelo logístico de 3 parámetros:

    P(acierto) = c + (1 - c) / (1 + exp(-a·(theta - b)))

donde `c` es la probabilidad de atinarle al azar (1 / número de opciones).

Las normas por edad son APROXIMADAS (curvas típicas de desarrollo y
envejecimiento cognitivo), no un baremo real: el resultado es una estimación.
"""

from __future__ import annotations

import math
from statistics import NormalDist

_NORMAL = NormalDist()
_MALLA = [-6 + i * 0.04 for i in range(301)]

# Correlación media supuesta entre subpruebas (para combinar puntajes).
R_DENTRO_INDICE = 0.60
R_TOTAL = 0.45

# Memoria (span): longitud media y desviación en adultos jóvenes.
SPAN = {"directo": (6.5, 1.2), "inverso": (4.9, 1.2), "corsi": (5.6, 1.1)}

# Velocidad: aciertos netos (aciertos - errores) de un adulto joven.
NORMAS_VELOCIDAD = {"busqueda": (48.0, 10.0), "claves": (52.0, 11.0)}


def prob(theta: float, a: float, b: float, c: float) -> float:
    return c + (1 - c) / (1 + math.exp(-a * (theta - b)))


def eap(respuestas: list, mu: float = 0.0, sd: float = 1.0) -> tuple[float, float]:
    """respuestas = [(a, b, c, acierto), ...] → (theta, error estándar)."""
    logs = []
    for t in _MALLA:
        lp = -0.5 * ((t - mu) / sd) ** 2
        for a, b, c, ok in respuestas:
            p = min(max(prob(t, a, b, c), 1e-9), 1 - 1e-9)
            lp += math.log(p if ok else 1 - p)
        logs.append(lp)
    m = max(logs)
    pesos = [math.exp(x - m) for x in logs]
    total = sum(pesos)
    media = sum(t * w for t, w in zip(_MALLA, pesos)) / total
    var = sum((t - media) ** 2 * w for t, w in zip(_MALLA, pesos)) / total
    return media, math.sqrt(var)


def b_span(tipo: str, longitud: int) -> float:
    media, sd = SPAN[tipo]
    return (longitud - media) / sd


def ref_edad(edad: float, norma: str) -> float:
    """Theta típico para esa edad (0 = adulto joven)."""
    if edad < 17:
        k = (17 - max(edad, 5)) / 11
        caida = {"cristalizado": 3.0, "fluido": 2.6, "memoria": 2.0, "visoespacial": 2.4}
        return -caida.get(norma, 2.5) * k
    if norma in ("fluido", "memoria", "visoespacial") and edad > 30:
        return -0.022 * (edad - 30)
    if norma == "cristalizado" and edad > 25:
        return 0.008 * (min(edad, 65) - 25)
    return 0.0


def factor_velocidad(edad: float) -> float:
    if edad < 17:
        return 0.4 + 0.6 * (max(edad, 5) - 5) / 12
    if edad > 30:
        return max(0.5, 1 - 0.009 * (edad - 30))
    return 1.0


def z_velocidad(clave: str, neto: float, edad: float) -> float:
    media, sd = NORMAS_VELOCIDAD[clave]
    f = factor_velocidad(edad)
    return (neto - media * f) / (sd * max(f, 0.6))


def compuesto(zs: list[float], r: float) -> float:
    k = len(zs)
    return sum(zs) / math.sqrt(k + k * (k - 1) * r) if k else 0.0


def error_compuesto(ses: list[float], r: float) -> float:
    k = len(ses)
    return math.sqrt(sum(s * s for s in ses)) / math.sqrt(k + k * (k - 1) * r) if k else 1.0


def percentil(z: float) -> float:
    return 100 * _NORMAL.cdf(z)


def escalar(z: float) -> int:
    """Puntuación escalar estilo Wechsler (media 10, DE 3, de 1 a 19)."""
    return max(1, min(19, round(10 + 3 * z)))


def acotar(z: float, lim: float = 4.0) -> float:
    return max(-lim, min(lim, z))


def clasificacion(z: float) -> str:
    ci = 100 + 15 * z
    if ci >= 130:
        return "Muy superior"
    if ci >= 120:
        return "Superior"
    if ci >= 110:
        return "Medio alto"
    if ci >= 90:
        return "Medio"
    if ci >= 80:
        return "Medio bajo"
    if ci >= 70:
        return "Limítrofe"
    return "Muy bajo"

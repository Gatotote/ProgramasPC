"""Calificación común de los cuestionarios por factores y facetas (Big Five, HEXACO).

dominios = {clave: (nombre, [(faceta, [(texto, +1 / -1), …]), …])}
normas   = {clave: (promedio, desviación)} por reactivo en escala 1–5, para el percentil.
descripcion = {clave: (qué mide, lectura si sale alto, lectura si sale bajo)}
"""

from __future__ import annotations

from statistics import NormalDist


def reactivos(dominios: dict, orden: list[str]) -> list[tuple]:
    """Lista intercalada (texto, dominio, faceta, signo): una de cada faceta por vuelta."""
    facetas = [(d, nombre, items) for d in orden for nombre, items in dominios[d][1]]
    vueltas = max(len(items) for _, _, items in facetas)
    return [(items[k][0], d, nombre, items[k][1]) for k in range(vueltas)
            for d, nombre, items in facetas if k < len(items)]


def nivel(percentil: float) -> str:
    return "Alto" if percentil >= 70 else "Bajo" if percentil < 30 else "Medio"


def calificar(lista: list[tuple], dominios: dict, orden: list[str], normas: dict, descripcion: dict,
              respuestas: list[int]) -> dict:
    por_faceta: dict[tuple, list[int]] = {}
    for (_, d, faceta, signo), r in zip(lista, respuestas):
        por_faceta.setdefault((d, faceta), []).append(r if signo > 0 else 6 - r)
    resultado = []
    for d in orden:
        nombre, facetas = dominios[d]
        valores = [v for f, _ in facetas for v in por_faceta[(d, f)]]
        media = sum(valores) / len(valores)
        m, sd = normas[d]
        pct = 100 * NormalDist().cdf((media - m) / sd)
        detalle = []
        for f, _ in facetas:
            mf = sum(por_faceta[(d, f)]) / len(por_faceta[(d, f)])
            detalle.append({"nombre": f, "puntos": round((mf - 1) / 4 * 100)})
        resultado.append({"clave": d, "nombre": nombre, "puntos": round((media - 1) / 4 * 100),
                          "percentil": pct, "nivel": nivel(pct), "facetas": detalle,
                          "descripcion": descripcion[d][0],
                          "lectura": descripcion[d][1] if pct >= 50 else descripcion[d][2]})
    resumen = " ".join(f"{x['clave']}{x['percentil']:.0f}" for x in resultado)   # p. ej. N74 E61 O38 A52 C54
    return {"dominios": resultado, "resumen": resumen}

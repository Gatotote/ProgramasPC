"""Generadores de preguntas. Cada pregunta es un `Item` con su dificultad `b`."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Item:
    clase: str               # "texto" (opciones de texto) | "figura" (opciones dibujadas) | "numero"
    pregunta: str
    b: float                 # dificultad en escala theta de adulto joven
    correcta: object         # índice de la opción correcta, o el número esperado
    opciones: list = field(default_factory=list)
    figura: object = None    # dibujo del enunciado (matriz, serie, polióminos…)
    texto_grande: str = ""   # serie numérica, ecuaciones de la balanza, etc.
    a: float = 1.4           # discriminación

    @property
    def c(self) -> float:
        """Probabilidad de atinarle al azar."""
        return 1 / len(self.opciones) if self.opciones else 0.0


def mezclar(rng: random.Random, correcta, distractores) -> tuple[list, int]:
    opciones = [correcta, *distractores]
    orden = list(range(len(opciones)))
    rng.shuffle(orden)
    return [opciones[i] for i in orden], orden.index(0)


def por_dificultad(items: list[Item]) -> list[Item]:
    return sorted(items, key=lambda it: it.b)

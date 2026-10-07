"""Pruebas de personalidad (cuestionarios de autoinforme)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

ESCALA_LIKERT = ["Nada", "Poco", "Ni sí ni no", "Bastante", "Totalmente"]
ESCALA_IMPORTANCIA = ["Nada importante", "Poco importante", "Algo importante", "Muy importante", "Esencial"]


@dataclass
class Cuestionario:
    clave: str
    nombre: str
    descripcion: str
    tipo: str                      # "likert" (1–5: ¿qué tanto te describe?) | "bipolar" (entre dos frases)
    preguntas: list                # likert: (texto, …)  ·  bipolar: (izquierda, derecha, …)
    calificar: Callable[[list[int], float], dict]   # respuestas (1 = primera opción) y edad → resultado
    edad_min: int = 14
    minutos: int = 10
    aviso: str = ""
    extra: dict = field(default_factory=dict)
    opciones: list[str] = field(default_factory=lambda: list(ESCALA_LIKERT))   # botones de respuesta (2–5)
    opciones_item: dict[int, list[str]] = field(default_factory=dict)   # índice → opciones propias de esa pregunta
    categoria: str = "personalidad"   # "personalidad" | "salud"

    def opciones_de(self, i: int) -> list[str]:
        return self.opciones_item.get(i, self.opciones)

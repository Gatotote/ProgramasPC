"""Valores: qué le importa a uno (interpersonales y personales), con preguntas propias.

Sigue las 12 escalas de los cuestionarios de valores de Gordon (SIV: interpersonales,
SPV: personales), que son de pago y usan elección forzada. Aquí se califica la importancia
de cada frase (1–5) y, como en el PVQ de Schwartz, se compara cada valor contra el
promedio de la misma persona: lo que cuenta es el orden de prioridades, no el número.
Preguntas propias, sin normas.
"""

from __future__ import annotations

from . import ESCALA_IMPORTANCIA, Cuestionario

# clave → (nombre, grupo, qué es, [frase ×4])
VALORES = {
    "apo": ("Apoyo", "interpersonal", "Ser tratado(a) con comprensión, recibir ánimo y amabilidad.",
            ["Que la gente me trate con comprensión y amabilidad.", "Recibir ánimo y apoyo de los demás.",
             "Tener a alguien que me escuche cuando lo necesito.", "Que los demás se preocupen por cómo me siento."]),
    "con": ("Conformidad", "interpersonal", "Hacer lo correcto y aceptado; seguir reglas y costumbres.",
            ["Hacer lo que es correcto y aceptado por la sociedad.", "Seguir las reglas al pie de la letra.",
             "Comportarme como se espera de mí.", "Respetar las costumbres y a la autoridad."]),
    "rec": ("Reconocimiento", "interpersonal", "Ser notado(a), admirado(a) y reconocido(a).",
            ["Que la gente reconozca mis logros.", "Ser admirado(a) por los demás.",
             "Que mi nombre sea conocido.", "Recibir elogios por lo que hago."]),
    "ind": ("Independencia", "interpersonal", "Decidir por cuenta propia y hacer las cosas a su manera.",
            ["Tomar mis propias decisiones sin pedir permiso.", "Hacer las cosas a mi manera.",
             "No depender de nadie.", "Tener libertad para organizar mi tiempo."]),
    "ben": ("Benevolencia", "interpersonal", "Ayudar, compartir y ser generoso(a) con los demás.",
            ["Ayudar a las personas que lo necesitan.", "Compartir lo que tengo con los demás.",
             "Hacer algo por mi comunidad.", "Ser generoso(a) aunque no me lo agradezcan."]),
    "lid": ("Liderazgo", "interpersonal", "Estar a cargo, tener autoridad e influencia sobre otros.",
            ["Estar a cargo de un grupo de personas.", "Tener autoridad para tomar decisiones que afectan a otros.",
             "Ser quien dirige un proyecto.", "Tener influencia sobre lo que hacen los demás."]),
    "pra": ("Sentido práctico", "personal", "Aprovechar el dinero, el tiempo y las cosas; lo útil.",
            ["Sacarle el máximo provecho a mi dinero y a mis cosas.", "Hacer lo que tiene una utilidad práctica.",
             "No desperdiciar tiempo ni recursos.", "Que lo que hago me deje un beneficio concreto."]),
    "log": ("Logro", "personal", "Enfrentar retos difíciles, superarse y lograr cosas importantes.",
            ["Hacer algo difícil y salir adelante.", "Trabajar en retos que exijan lo mejor de mí.",
             "Superarme y mejorar en lo que hago.", "Lograr algo importante en mi vida."]),
    "var": ("Variedad", "personal", "Cosas nuevas, viajes, emociones; evitar la rutina.",
            ["Hacer cosas nuevas y diferentes.", "Viajar y conocer lugares distintos.",
             "Tener experiencias emocionantes.", "Evitar la rutina."]),
    "dec": ("Decisión", "personal", "Tener convicciones firmes y decidir rápido.",
            ["Tener opiniones firmes.", "Ir directo al grano.",
             "No titubear al tomar una decisión.", "Defender mis posturas con firmeza."]),
    "ord": ("Orden", "personal", "Organización, rutina y método.",
            ["Tener mis cosas organizadas.", "Seguir una rutina ordenada.",
             "Que todo esté en su lugar.", "Trabajar con un método claro."]),
    "met": ("Metas", "personal", "Saber a dónde se va y perseguir objetivos claros.",
            ["Tener metas claras en la vida.", "Saber exactamente hacia dónde voy.",
             "Planear mi futuro a largo plazo.", "Concentrarme en un objetivo hasta lograrlo."]),
}

REACTIVOS = [(VALORES[c][3][k], c) for k in range(4) for c in VALORES]


def calificar(respuestas: list[int], edad: float) -> dict:
    por: dict[str, list[int]] = {}
    for (_, c), r in zip(REACTIVOS, respuestas):
        por.setdefault(c, []).append(r)
    general = sum(respuestas) / len(respuestas)
    lista = []
    for c, (nombre, grupo, que, _) in VALORES.items():
        media = sum(por[c]) / len(por[c])
        lista.append({"clave": c, "nombre": nombre, "grupo": grupo, "descripcion": que,
                      "puntos": round((media - 1) / 4 * 100), "relativo": round(media - general, 2)})
    orden = sorted(lista, key=lambda x: -x["relativo"])
    plano = orden[0]["relativo"] - orden[-1]["relativo"] < 0.5   # casi todo calificado igual
    return {"valores": lista, "general": round(general, 2), "plano": plano, "mas": [x["nombre"] for x in orden[:3]],
            "menos": [x["nombre"] for x in orden[-3:]][::-1],
            "resumen": "Prioriza: " + ", ".join(x["nombre"] for x in orden[:3])}


VALORES_CUESTIONARIO = Cuestionario(
    "valores", "Valores",
    "Qué te mueve: 6 valores interpersonales (apoyo, conformidad, reconocimiento, independencia, benevolencia, "
    "liderazgo) y 6 personales (sentido práctico, logro, variedad, decisión, orden, metas). Da tu orden de "
    "prioridades. Inspirado en los cuestionarios de valores de Gordon (SIV/SPV); preguntas propias. "
    "Unos 7 minutos.",
    "likert", [r[0] for r in REACTIVOS], calificar, edad_min=14, minutos=7,
    aviso="¿Qué tan importante es para ti…?  Todo puede parecer importante: trata de distinguir lo que de "
          "verdad pesa más.",
    opciones=list(ESCALA_IMPORTANCIA))

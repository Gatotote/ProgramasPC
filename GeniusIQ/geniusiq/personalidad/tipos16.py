"""16 tipos (estilo MBTI) con un cuestionario libre.

Basado en las Open Extended Jungian Type Scales (OEJTS 1.2, Eric Jorgenson, licencia
Creative Commons): 32 pares de frases opuestas, se marca de 1 a 5 hacia cuál se inclina uno.
Traducción propia. Cada par cuenta para una de las 4 dimensiones:
E/I (energía), S/N (información), T/F (decisiones), J/P (estilo de vida).

El MBTI® original es una marca registrada y de pago; esto NO es el MBTI.
"""

from __future__ import annotations

from . import Cuestionario

# (frase izquierda, frase derecha, dimensión, letra que gana si se elige la derecha)
PARES = [
    ("Hago listas.", "Confío en mi memoria.", "JP", "P"),
    ("Soy escéptico(a).", "Quiero creer.", "TF", "F"),
    ("Me aburro si paso mucho tiempo solo(a).", "Necesito tiempo a solas.", "EI", "I"),
    ("Acepto las cosas como son.", "Me inconformo con cómo son las cosas.", "SN", "N"),
    ("Mantengo mi cuarto limpio.", "Dejo las cosas donde caigan.", "JP", "P"),
    ("Que me digan «robot» me parece un insulto.", "Busco tener una mente lógica, como una máquina.", "TF", "T"),
    ("Soy enérgico(a).", "Soy tranquilo(a).", "EI", "I"),
    ("Prefiero exámenes de opción múltiple.", "Prefiero exámenes de desarrollar respuestas.", "SN", "N"),
    ("Soy caótico(a).", "Soy organizado(a).", "JP", "J"),
    ("Me hieren con facilidad.", "Tengo la piel dura.", "TF", "T"),
    ("Trabajo mejor en grupo.", "Trabajo mejor solo(a).", "EI", "I"),
    ("Me enfoco en el presente.", "Me enfoco en el futuro.", "SN", "N"),
    ("Planeo con mucha anticipación.", "Planeo a última hora.", "JP", "P"),
    ("Quiero que la gente me respete.", "Quiero que la gente me quiera.", "TF", "F"),
    ("Las fiestas me agotan.", "Las fiestas me cargan de energía.", "EI", "E"),
    ("Me integro con los demás.", "Sobresalgo de los demás.", "SN", "N"),
    ("Dejo mis opciones abiertas.", "Me comprometo.", "JP", "J"),
    ("Quiero ser bueno(a) arreglando cosas.", "Quiero ser bueno(a) ayudando a las personas.", "TF", "F"),
    ("Hablo más de lo que escucho.", "Escucho más de lo que hablo.", "EI", "I"),
    ("Al contar algo, digo lo que pasó.", "Al contar algo, digo lo que significó.", "SN", "N"),
    ("Hago el trabajo de inmediato.", "Dejo el trabajo para después.", "JP", "P"),
    ("Sigo al corazón.", "Sigo a la cabeza.", "TF", "T"),
    ("Me quedo en casa.", "Salgo a divertirme.", "EI", "E"),
    ("Quiero el panorama general.", "Quiero los detalles.", "SN", "S"),
    ("Improviso.", "Me preparo.", "JP", "J"),
    ("Mi idea de lo correcto se basa en la justicia.", "Mi idea de lo correcto se basa en la compasión.", "TF", "F"),
    ("Me cuesta trabajo gritar muy fuerte.", "Me sale natural gritarle a alguien que está lejos.", "EI", "E"),
    ("Soy teórico(a).", "Soy práctico(a), de lo que se comprueba.", "SN", "S"),
    ("Trabajo duro.", "Me divierto en grande.", "JP", "P"),
    ("Me incomodan las emociones.", "Valoro las emociones.", "TF", "F"),
    ("Me gusta presentarme frente a la gente.", "Evito hablar en público.", "EI", "I"),
    ("Me gusta saber «quién», «qué» y «cuándo».", "Me gusta saber «por qué».", "SN", "N"),
]

DIMENSIONES = {
    "EI": ("Extraversión", "Introversión", "De dónde saca la energía: de la gente y la acción, o de su mundo interior."),
    "SN": ("Sensación", "Intuición", "Cómo toma la información: datos concretos y presentes, o patrones e ideas."),
    "TF": ("Pensamiento", "Sentimiento", "Cómo decide: con lógica y criterios objetivos, o con valores y empatía."),
    "JP": ("Juicio", "Percepción", "Cómo organiza su vida: planeado y cerrado, o flexible y abierto."),
}

TIPOS = {
    "ISTJ": "Responsable y metódico(a). Cumple su palabra, valora el orden, la tradición y los hechos.",
    "ISFJ": "Protector(a) y atento(a). Cuida a los suyos con lealtad, paciencia y gran memoria para los detalles.",
    "INFJ": "Visionario(a) y reservado(a). Busca sentido y propósito; muy intuitivo(a) con las personas.",
    "INTJ": "Estratega independiente. Hace planes a largo plazo, piensa en sistemas y exige competencia.",
    "ISTP": "Práctico(a) y analítico(a). Le gusta entender cómo funcionan las cosas y resolver problemas con las manos.",
    "ISFP": "Sensible y tranquilo(a). Vive el presente, aprecia la belleza y es fiel a sus valores.",
    "INFP": "Idealista y creativo(a). Guiado(a) por sus valores, empático(a), busca autenticidad.",
    "INTP": "Pensador(a) curioso(a). Ama las ideas, las teorías y encontrar fallas lógicas.",
    "ESTP": "Enérgico(a) y directo(a). Le gusta la acción, el riesgo y resolver sobre la marcha.",
    "ESFP": "Alegre y espontáneo(a). Disfruta la gente, la diversión y hacer pasar un buen rato a los demás.",
    "ENFP": "Entusiasta e inspirador(a). Ve posibilidades en todo, conecta con la gente y odia la rutina.",
    "ENTP": "Ingenioso(a) y debatidor(a). Le encantan los retos intelectuales y las ideas nuevas.",
    "ESTJ": "Organizador(a) y decidido(a). Pone orden, dirige y hace que las cosas se cumplan.",
    "ESFJ": "Cálido(a) y servicial. Pendiente de los demás, busca armonía y cuida las tradiciones.",
    "ENFJ": "Líder carismático(a). Motiva a los demás, piensa en el bien del grupo y sabe comunicar.",
    "ENTJ": "Comandante decidido(a). Visión a largo plazo, eficiencia y gusto por dirigir.",
}


def calificar(respuestas: list[int], edad: float) -> dict:
    # puntos > 0 favorece la primera letra (E, S, T, J); < 0 la segunda (I, N, F, P)
    puntos = {dim: 0 for dim in DIMENSIONES}
    for (_, _, dim, letra_der), r in zip(PARES, respuestas):
        hacia_derecha = r - 3                     # -2 … +2
        puntos[dim] += hacia_derecha if letra_der == dim[0] else -hacia_derecha
    dims, codigo = [], ""
    for dim, (n1, n2, desc) in DIMENSIONES.items():
        p = puntos[dim]
        letra = dim[0] if p > 0 else dim[1]       # empate → segunda letra, como en el MBTI
        codigo += letra
        dims.append({"clave": dim, "izquierda": n1, "derecha": n2, "letra": letra,
                     "claridad": min(100, round(abs(p) / 16 * 100)), "puntos": p, "descripcion": desc})
    return {"tipo16": codigo, "dimensiones": dims, "descripcion_tipo": TIPOS[codigo], "resumen": codigo}


TIPOS_16 = Cuestionario(
    "tipos16", "16 tipos (estilo MBTI)",
    "Clasifica en uno de 16 tipos según 4 preferencias: Extraversión/Introversión, Sensación/Intuición, "
    "Pensamiento/Sentimiento y Juicio/Percepción. Cuestionario libre OEJTS (no es el MBTI® oficial). "
    "Es popular y divertido, pero tiene menos respaldo científico que el Big Five. Unos 5 minutos.",
    "bipolar", [(a, b) for a, b, _, _ in PARES], calificar, edad_min=12, minutos=5,
    aviso="En cada par, elige hacia qué frase te inclinas más (1 = totalmente la de la izquierda, "
          "5 = totalmente la de la derecha).")

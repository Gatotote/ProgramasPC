"""Eneagrama (9 tipos) con preguntas propias.

No existe una versión libre y validada; estas 45 frases (5 por tipo) se escribieron para
este programa a partir de las descripciones generales de cada tipo. Es para curiosidad
y autoconocimiento, NO tiene respaldo científico.
"""

from __future__ import annotations

from . import Cuestionario

TIPOS = {
    1: ("El Perfeccionista",
        "Busca hacer lo correcto y mejorar las cosas. Responsable, con principios firmes y ojo para los errores; "
        "puede ser muy exigente consigo y con los demás.",
        ["Me molesta mucho cuando las cosas no se hacen como deben hacerse.",
         "Tengo una voz interna que me critica cuando cometo errores.",
         "Prefiero hacer las cosas bien a hacerlas rápido.",
         "Me cuesta relajarme si sé que algo quedó mal hecho.",
         "Tengo reglas claras sobre lo que está bien y lo que está mal."]),
    2: ("El Ayudador",
        "Generoso(a), cálido(a) y atento(a) a lo que necesitan los demás. Le importa sentirse querido(a) y "
        "necesario(a); a veces olvida sus propias necesidades.",
        ["Me doy cuenta enseguida de lo que necesitan los demás.",
         "Me cuesta decir que no cuando alguien me pide ayuda.",
         "Me siento bien cuando la gente me necesita.",
         "Suelo poner las necesidades de otros antes que las mías.",
         "Me duele cuando no me agradecen lo que hago por los demás."]),
    3: ("El Triunfador",
        "Orientado(a) a metas, eficiente y adaptable. Quiere destacar y ser reconocido(a) por sus logros; "
        "puede confundir lo que hace con lo que es.",
        ["Me importa mucho tener éxito y que se note.",
         "Me adapto a lo que se espera de mí para causar buena impresión.",
         "Me siento valioso(a) cuando logro mis metas.",
         "Soy muy competitivo(a).",
         "Detesto perder el tiempo en cosas que no llevan a ningún resultado."]),
    4: ("El Individualista",
        "Sensible, creativo(a) y en busca de autenticidad. Siente las emociones con profundidad y quiere "
        "ser único(a); a veces se siente incomprendido(a).",
        ["Siento que soy diferente a la mayoría de la gente.",
         "Mis emociones son muy intensas y profundas.",
         "Me atrae la melancolía, el arte y lo que tiene significado.",
         "A veces siento que a los demás les falta algo que yo no tengo.",
         "Es muy importante para mí ser auténtico(a) y original."]),
    5: ("El Investigador",
        "Observador(a), curioso(a) e independiente. Necesita entender cómo funcionan las cosas y cuidar su "
        "energía y su privacidad; puede aislarse.",
        ["Necesito entender a fondo las cosas antes de actuar.",
         "Cuido mucho mi tiempo, mi energía y mi espacio personal.",
         "Prefiero observar a participar.",
         "Disfruto pasar horas investigando un tema que me interesa.",
         "Me agotan las personas que me exigen mucho emocionalmente."]),
    6: ("El Leal",
        "Comprometido(a), responsable y atento(a) a los riesgos. Busca seguridad y apoyo; puede dudar mucho "
        "o anticipar lo que podría salir mal.",
        ["Suelo imaginar lo que podría salir mal para estar preparado(a).",
         "Soy muy leal con mi familia, mis amigos y mi trabajo.",
         "Me cuesta confiar en alguien hasta que me demuestra que es confiable.",
         "Antes de decidir, pido opinión a personas en las que confío.",
         "Me dan seguridad las reglas claras y saber con quién cuento."]),
    7: ("El Entusiasta",
        "Optimista, espontáneo(a) y con muchas ideas. Busca experiencias nuevas y evitar el dolor o el "
        "aburrimiento; le cuesta comprometerse con una sola cosa.",
        ["Siempre tengo muchos planes y proyectos emocionantes.",
         "Me aburro fácilmente con la rutina.",
         "Prefiero ver el lado positivo y no quedarme en lo negativo.",
         "Me gusta tener muchas opciones abiertas.",
         "Empiezo muchas cosas, pero me cuesta terminarlas."]),
    8: ("El Desafiador",
        "Fuerte, directo(a) y protector(a). Quiere tener el control de su vida y defender a los suyos; "
        "puede intimidar o chocar con la autoridad.",
        ["Digo las cosas de frente aunque incomoden.",
         "No me gusta que nadie me controle.",
         "Defiendo con fuerza a las personas que quiero.",
         "Me cuesta mostrarme vulnerable.",
         "Cuando algo me parece injusto, me enfrento sin dudarlo."]),
    9: ("El Pacificador",
        "Tranquilo(a), paciente y conciliador(a). Busca la armonía y evita los conflictos; a veces deja de "
        "lado lo que quiere para no causar problemas.",
        ["Hago lo posible por evitar los conflictos.",
         "Me es fácil ver el punto de vista de todos.",
         "A veces dejo para después lo importante por hacer cosas más cómodas.",
         "Prefiero adaptarme a los demás que imponer lo que yo quiero.",
         "La gente dice que soy una persona tranquila y fácil de llevar."]),
}

# orden intercalado: una frase de cada tipo por vuelta
REACTIVOS = [(TIPOS[t][2][k], t) for k in range(5) for t in range(1, 10)]


def calificar(respuestas: list[int], edad: float) -> dict:
    suma = {t: 0 for t in TIPOS}
    for (_, t), r in zip(REACTIVOS, respuestas):
        suma[t] += r
    puntos = {t: round((suma[t] - 5) / 20 * 100) for t in TIPOS}     # 0–100
    orden = sorted(TIPOS, key=lambda t: -puntos[t])
    principal = orden[0]
    vecinas = [principal - 1 or 9, principal % 9 + 1]
    ala = max(vecinas, key=lambda t: puntos[t])
    return {"eneatipo": principal, "ala": ala, "nombre_tipo": TIPOS[principal][0],
            "descripcion_tipo": TIPOS[principal][1],
            "tipos": [{"tipo": t, "nombre": TIPOS[t][0], "puntos": puntos[t]} for t in TIPOS],
            "siguientes": orden[1:3], "resumen": f"Tipo {principal}w{ala}"}


ENEAGRAMA = Cuestionario(
    "eneagrama", "Eneagrama (9 tipos)",
    "Describe 9 maneras de ver el mundo y lo que motiva a cada una. Da el tipo principal y su «ala» "
    "(el tipo vecino que más influye). Preguntas propias: es para curiosidad y autoconocimiento, sin "
    "respaldo científico. Unos 6 minutos.",
    "likert", [r[0] for r in REACTIVOS], calificar, edad_min=12, minutos=6,
    aviso="Contesta cómo has sido la mayor parte de tu vida, no solo en las últimas semanas.")

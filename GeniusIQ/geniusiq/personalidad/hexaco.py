"""HEXACO (6 factores) con preguntas propias.

El modelo HEXACO (Ashton y Lee) agrega al Big Five un sexto factor, Honestidad-Humildad,
y reacomoda Amabilidad y Emocionalidad. El inventario oficial (HEXACO-PI-R) solo se permite
para investigación sin fines de lucro, así que estas 72 frases se escribieron para este
programa siguiendo las 24 facetas del modelo (4 por factor, 3 frases por faceta).
NO es el HEXACO-PI-R: las normas son aproximadas y falta validarlo.
"""

from __future__ import annotations

from . import Cuestionario, factores

DOMINIOS = {
    "H": ("Honestidad-Humildad", [
        ("Sinceridad", [("Le hago la barba a la gente cuando quiero conseguir algo.", -1),
                        ("No finjo que alguien me cae bien solo para sacar un favor.", 1),
                        ("Uso halagos para conseguir lo que quiero.", -1)]),
        ("Justicia", [("Nunca aceptaría un soborno, aunque fuera mucho dinero.", 1),
                      ("Me quedaría con dinero ajeno si supiera que nadie se va a enterar.", -1),
                      ("Haría trampa si eso me ayudara a salir adelante sin consecuencias.", -1)]),
        ("Desinterés por la riqueza", [("Tener mucho dinero no es algo que me importe demasiado.", 1),
                                       ("Me gustaría tener cosas de lujo para que la gente lo note.", -1),
                                       ("Me gustaría vivir en una zona exclusiva y cara.", -1)]),
        ("Modestia", [("Creo que merezco más respeto que una persona promedio.", -1),
                      ("Me considero una persona común, ni mejor ni peor que los demás.", 1),
                      ("Quiero que la gente sepa que soy alguien importante.", -1)]),
    ]),
    "E": ("Emocionalidad", [
        ("Miedo", [("Me dan miedo las situaciones en las que me podría lastimar.", 1),
                   ("Haría algo peligroso, como un deporte extremo, sin sentir miedo.", -1),
                   ("Los temblores o las tormentas fuertes me asustan más que a la mayoría.", 1)]),
        ("Ansiedad", [("Me preocupo de más por cosas pequeñas.", 1),
                      ("Duermo tranquilo(a) aunque tenga problemas pendientes.", -1),
                      ("Me pongo nervioso(a) cuando tengo que tomar una decisión importante.", 1)]),
        ("Dependencia", [("Cuando tengo un problema, necesito que alguien me apoye.", 1),
                         ("Puedo superar las dificultades sin ayuda de nadie.", -1),
                         ("Cuando paso por un mal momento, busco a alguien que me consuele.", 1)]),
        ("Sentimentalismo", [("Me pongo muy sentimental cuando me despido de alguien querido.", 1),
                             ("Lloro con facilidad en las películas tristes.", 1),
                             ("Me afecta poco cuando alguien cercano está sufriendo.", -1)]),
    ]),
    "X": ("Extraversión", [
        ("Autoestima social", [("Creo que le caigo bien a la mayoría de la gente.", 1),
                               ("Siento que no le agrado a los demás.", -1),
                               ("En general, estoy satisfecho(a) conmigo mismo(a).", 1)]),
        ("Audacia social", [("Me siento cómodo(a) hablando frente a un grupo.", 1),
                            ("En las reuniones prefiero que hablen los demás.", -1),
                            ("Me animo a dar mi opinión aunque no conozca a nadie.", 1)]),
        ("Sociabilidad", [("Disfruto platicar con gente que acabo de conocer.", 1),
                          ("Preferiría un trabajo en el que casi no trate con gente.", -1),
                          ("Me gustan las reuniones con muchos amigos.", 1)]),
        ("Vivacidad", [("Normalmente me siento con buen ánimo y energía.", 1),
                       ("La mayoría de los días me siento animado(a) y optimista.", 1),
                       ("Siento que tengo menos energía que la mayoría de la gente.", -1)]),
    ]),
    "A": ("Amabilidad", [
        ("Perdón", [("Me cuesta mucho perdonar a quien me hizo daño.", -1),
                    ("Le doy otra oportunidad a quien me falló.", 1),
                    ("Guardo rencor por mucho tiempo.", -1)]),
        ("Gentileza", [("Suelo ser comprensivo(a) con los errores de los demás.", 1),
                       ("Critico con dureza a quien hace mal las cosas.", -1),
                       ("Trato a la gente con amabilidad aunque se equivoque.", 1)]),
        ("Flexibilidad", [("Cedo con facilidad para llegar a un acuerdo.", 1),
                          ("Cuando creo tener la razón, no cambio de opinión aunque insistan.", -1),
                          ("Discuto mucho cuando no están de acuerdo conmigo.", -1)]),
        ("Paciencia", [("Rara vez me enojo, aunque me traten mal.", 1),
                       ("Pierdo la paciencia con facilidad.", -1),
                       ("Me cuesta mantener la calma cuando algo me molesta.", -1)]),
    ]),
    "C": ("Responsabilidad", [
        ("Organización", [("Planeo con anticipación y organizo mis cosas.", 1),
                          ("Mis cosas suelen estar desordenadas.", -1),
                          ("Me gusta tener un lugar para cada cosa.", 1)]),
        ("Diligencia", [("Me esfuerzo mucho para lograr mis metas.", 1),
                        ("Cuando algo cuesta trabajo, lo dejo a medias.", -1),
                        ("Me pongo metas exigentes y trabajo duro para cumplirlas.", 1)]),
        ("Perfeccionismo", [("Reviso mi trabajo varias veces para no dejar errores.", 1),
                            ("Me conformo con que las cosas queden más o menos.", -1),
                            ("Cuido mucho los detalles.", 1)]),
        ("Prudencia", [("Pienso bien las cosas antes de decidir.", 1),
                       ("Hago las cosas por impulso.", -1),
                       ("Actúo sin medir las consecuencias.", -1)]),
    ]),
    "O": ("Apertura a la experiencia", [
        ("Apreciación estética", [("Disfruto mucho la belleza de la naturaleza o del arte.", 1),
                                  ("Me aburriría ir a un museo o a una galería de arte.", -1),
                                  ("La música o la pintura me pueden conmover mucho.", 1)]),
        ("Curiosidad", [("Me interesa aprender sobre la historia y la cultura de otros países.", 1),
                        ("Me gusta leer o ver documentales sobre temas nuevos.", 1),
                        ("No me interesan los temas que no me sirven en el día a día.", -1)]),
        ("Creatividad", [("Se me ocurren ideas originales.", 1),
                         ("Me gustaría crear algo artístico, como escribir, pintar o componer.", 1),
                         ("No me considero una persona creativa.", -1)]),
        ("Poco convencional", [("Me atraen las ideas que a otros les parecen raras.", 1),
                               ("Me cae bien la gente con opiniones poco comunes.", 1),
                               ("Prefiero hacer las cosas como siempre se han hecho.", -1)]),
    ]),
}

ORDEN = ["H", "E", "X", "A", "C", "O"]

# Promedio y desviación aproximados por reactivo (escala 1–5) en adultos, tomados de lo
# típico del HEXACO-60 en autoinforme. Solo orientativos: estas frases no tienen normas propias.
NORMAS = {"H": (3.30, 0.60), "E": (3.20, 0.60), "X": (3.40, 0.60), "A": (3.05, 0.60), "C": (3.50, 0.55),
          "O": (3.35, 0.65)}

DESCRIPCION = {
    "H": ("Sinceridad, juego limpio, poco interés en el lujo y en sentirse superior. Es el factor que el "
          "Big Five no tiene.",
          "Alto: sincero(a) y justo(a); no manipula, no le atrae el estatus ni romper las reglas para ganar.",
          "Bajo: usa el halago o la astucia para conseguir cosas, le atraen el dinero y el estatus, se "
          "siente con derecho a más."),
    "E": ("Miedo al peligro, preocupación, necesidad de apoyo y apego emocional.",
          "Alto: sensible, se preocupa, busca apoyo en otros y se conmueve con facilidad.",
          "Bajo: valiente e independiente, poco preocupado(a); puede parecer frío(a) o distante."),
    "X": ("Seguridad en sí mismo(a) frente a los demás, gusto por la gente y energía.",
          "Alto: seguro(a) en lo social, platicador(a), animado(a) y con energía.",
          "Bajo: reservado(a), prefiere poca compañía, más callado(a) en grupo."),
    "A": ("Perdonar, ser tolerante y paciente; no enojarse con facilidad.",
          "Alto: perdona, es tolerante, cede para llegar a acuerdos y mantiene la calma.",
          "Bajo: guarda rencor, es crítico(a) y terco(a); se enoja con facilidad."),
    "C": ("Organización, esfuerzo, cuidado de los detalles y prudencia.",
          "Alto: ordenado(a), trabajador(a), detallista y prudente.",
          "Bajo: flexible y espontáneo(a), pero puede ser desordenado(a), impulsivo(a) o conformarse."),
    "O": ("Gusto por el arte, curiosidad, creatividad e ideas fuera de lo común.",
          "Alto: curioso(a), creativo(a), sensible al arte y abierto(a) a lo poco convencional.",
          "Bajo: práctico(a) y tradicional; le interesan más las cosas concretas."),
}

REACTIVOS = factores.reactivos(DOMINIOS, ORDEN)


def calificar(respuestas: list[int], edad: float) -> dict:
    return factores.calificar(REACTIVOS, DOMINIOS, ORDEN, NORMAS, DESCRIPCION, respuestas)


HEXACO = Cuestionario(
    "hexaco", "HEXACO (6 factores)",
    "Como el Big Five, pero con un sexto factor: Honestidad-Humildad (sinceridad, juego limpio, modestia). "
    "Mide Honestidad-Humildad, Emocionalidad, Extraversión, Amabilidad, Responsabilidad y Apertura, con 4 "
    "facetas cada uno. Preguntas propias basadas en el modelo de Ashton y Lee (no es el HEXACO-PI-R oficial). "
    "Unos 12 minutos.",
    "likert", [r[0] for r in REACTIVOS], calificar, edad_min=14, minutos=12,
    aviso="Contesta cómo eres normalmente, no cómo te gustaría ser. No hay respuestas buenas ni malas.")

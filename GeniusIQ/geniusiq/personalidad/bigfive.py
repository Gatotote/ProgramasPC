"""Big Five (OCEAN) con los 120 reactivos del IPIP-NEO-120 (Johnson, 2014).

Los reactivos del International Personality Item Pool (ipip.ori.org) son de dominio
público. Traducción y adaptación al español propias (el de «liberalismo» se adaptó a
México: en vez de votar por candidatos liberales/conservadores, apoyar ideas
progresistas/conservadoras).

Cada faceta tiene 4 reactivos; cada dominio, 6 facetas (24 reactivos).
"""

from __future__ import annotations

from . import Cuestionario, factores

# dominio → (nombre, [(faceta, [(texto, +1 / -1), ×4]), ×6])
DOMINIOS = {
    "N": ("Neuroticismo", [
        ("Ansiedad", [("Me preocupo por las cosas.", 1), ("Temo que pase lo peor.", 1),
                      ("Le tengo miedo a muchas cosas.", 1), ("Me estreso con facilidad.", 1)]),
        ("Enojo", [("Me enojo con facilidad.", 1), ("Me irrito con facilidad.", 1),
                   ("Pierdo los estribos.", 1), ("No me molesto fácilmente.", -1)]),
        ("Desánimo", [("Con frecuencia me siento triste.", 1), ("No me caigo bien a mí mismo(a).", 1),
                      ("Seguido ando decaído(a).", 1), ("Me siento a gusto conmigo mismo(a).", -1)]),
        ("Inhibición social", [("Me cuesta trabajo acercarme a los demás.", 1),
                               ("Me da miedo llamar la atención.", 1),
                               ("Solo me siento cómodo(a) con mis amigos.", 1),
                               ("Las situaciones sociales difíciles no me incomodan.", -1)]),
        ("Inmoderación", [("Me doy atracones (de comida, compras, etc.).", 1), ("Rara vez me excedo.", -1),
                          ("Resisto fácilmente las tentaciones.", -1), ("Puedo controlar mis antojos.", -1)]),
        ("Vulnerabilidad", [("Entro en pánico con facilidad.", 1), ("Los acontecimientos me rebasan.", 1),
                            ("Siento que no puedo con las cosas.", 1), ("Mantengo la calma bajo presión.", -1)]),
    ]),
    "E": ("Extraversión", [
        ("Cordialidad", [("Hago amigos con facilidad.", 1), ("Me siento a gusto entre la gente.", 1),
                         ("Evito el contacto con los demás.", -1), ("Mantengo a los demás a distancia.", -1)]),
        ("Sociabilidad", [("Me encantan las fiestas grandes.", 1),
                          ("En las fiestas platico con muchas personas distintas.", 1),
                          ("Prefiero estar solo(a).", -1), ("Evito las multitudes.", -1)]),
        ("Asertividad", [("Tomo el mando.", 1), ("Trato de dirigir a los demás.", 1),
                         ("Tomo el control de las cosas.", 1), ("Espero a que otros tomen la iniciativa.", -1)]),
        ("Nivel de actividad", [("Siempre estoy ocupado(a).", 1), ("Siempre ando de un lado a otro.", 1),
                                ("Hago muchas cosas en mi tiempo libre.", 1), ("Me gusta tomarme las cosas con calma.", -1)]),
        ("Búsqueda de emociones", [("Me encanta la emoción.", 1), ("Busco aventuras.", 1),
                                   ("Disfruto hacer cosas arriesgadas.", 1), ("Me pongo loco(a) y desenfrenado(a).", 1)]),
        ("Alegría", [("Irradio alegría.", 1), ("Me divierto mucho.", 1), ("Amo la vida.", 1),
                     ("Veo el lado bueno de la vida.", 1)]),
    ]),
    "O": ("Apertura a la experiencia", [
        ("Imaginación", [("Tengo una imaginación muy viva.", 1), ("Disfruto dejar volar la fantasía.", 1),
                         ("Me encanta soñar despierto(a).", 1), ("Me gusta perderme en mis pensamientos.", 1)]),
        ("Interés artístico", [("Creo que el arte es importante.", 1),
                               ("Veo belleza en cosas que otros no notan.", 1),
                               ("No me gusta la poesía.", -1), ("No disfruto ir a museos de arte.", -1)]),
        ("Emotividad", [("Vivo mis emociones con intensidad.", 1), ("Siento las emociones de los demás.", 1),
                        ("Rara vez noto mis reacciones emocionales.", -1),
                        ("No entiendo a la gente que se emociona.", -1)]),
        ("Gusto por la novedad", [("Prefiero la variedad a la rutina.", 1),
                                  ("Prefiero quedarme con lo que ya conozco.", -1),
                                  ("No me gustan los cambios.", -1), ("Me apego a las formas tradicionales.", -1)]),
        ("Intelecto", [("Me encanta leer material que me reta.", 1), ("Evito las discusiones filosóficas.", -1),
                       ("Me cuesta trabajo entender ideas abstractas.", -1),
                       ("No me interesan las discusiones teóricas.", -1)]),
        ("Apertura en valores", [("Apoyo ideas políticas progresistas.", 1),
                                 ("Creo que no existe un bien y un mal absolutos.", 1),
                                 ("Apoyo ideas políticas conservadoras.", -1),
                                 ("Creo que hay que ser muy duros con el crimen.", -1)]),
    ]),
    "A": ("Amabilidad", [
        ("Confianza", [("Confío en los demás.", 1), ("Creo que los demás tienen buenas intenciones.", 1),
                       ("Confío en lo que la gente dice.", 1), ("Desconfío de la gente.", -1)]),
        ("Rectitud", [("Uso a los demás para mis propios fines.", -1), ("Hago trampa para salir adelante.", -1),
                      ("Me aprovecho de los demás.", -1), ("Le pongo obstáculos a los planes de otros.", -1)]),
        ("Altruismo", [("Me encanta ayudar a los demás.", 1), ("Me preocupo por los demás.", 1),
                       ("Me son indiferentes los sentimientos de los demás.", -1),
                       ("No le dedico tiempo a los demás.", -1)]),
        ("Cooperación", [("Me encanta una buena pelea.", -1), ("Le grito a la gente.", -1),
                         ("Insulto a la gente.", -1), ("Me desquito con los demás.", -1)]),
        ("Modestia", [("Creo que soy mejor que los demás.", -1), ("Me tengo en muy alta estima.", -1),
                      ("Tengo una opinión muy alta de mí mismo(a).", -1), ("Presumo mis virtudes.", -1)]),
        ("Compasión", [("Me identifico con las personas sin hogar.", 1),
                       ("Siento compasión por quienes están peor que yo.", 1),
                       ("No me interesan los problemas de otras personas.", -1),
                       ("Trato de no pensar en los necesitados.", -1)]),
    ]),
    "C": ("Responsabilidad", [
        ("Autoeficacia", [("Termino las tareas con éxito.", 1), ("Destaco en lo que hago.", 1),
                          ("Manejo las tareas sin problemas.", 1), ("Sé cómo sacar las cosas adelante.", 1)]),
        ("Orden", [("Me gusta ordenar.", 1), ("Seguido olvido regresar las cosas a su lugar.", -1),
                   ("Dejo desordenado mi cuarto.", -1), ("Dejo mis cosas tiradas por ahí.", -1)]),
        ("Sentido del deber", [("Cumplo mis promesas.", 1), ("Digo la verdad.", 1),
                               ("Rompo las reglas.", -1), ("No cumplo mis promesas.", -1)]),
        ("Afán de logro", [("Trabajo duro.", 1), ("Hago más de lo que se espera de mí.", 1),
                           ("Hago solo lo mínimo para salir del paso.", -1),
                           ("Le dedico poco tiempo y esfuerzo a mi trabajo.", -1)]),
        ("Autodisciplina", [("Hago mis pendientes de inmediato.", 1), ("Siempre estoy preparado(a).", 1),
                            ("Empiezo las tareas en cuanto puedo.", 1), ("Pierdo el tiempo.", -1)]),
        ("Prudencia", [("Me lanzo a hacer cosas sin pensarlo.", -1), ("Tomo decisiones precipitadas.", -1),
                       ("Hago las cosas a la carrera.", -1), ("Actúo sin pensar.", -1)]),
    ]),
}

ORDEN = ["N", "E", "O", "A", "C"]

# Promedio y desviación aproximados por reactivo (escala 1–5) en adultos (referencia:
# muestras del IPIP-NEO-120). Solo para dar un percentil orientativo.
NORMAS = {"N": (2.75, 0.65), "E": (3.35, 0.55), "O": (3.45, 0.50), "A": (3.80, 0.50), "C": (3.65, 0.55)}

DESCRIPCION = {
    "N": ("Qué tan seguido se sienten emociones negativas (preocupación, enojo, tristeza) y qué tan "
          "fácil se pierde la calma.",
          "Alto: se preocupa, se estresa o se desanima con facilidad; vive las emociones negativas con intensidad.",
          "Bajo: emocionalmente estable y tranquilo(a); se repone rápido de los problemas."),
    "E": ("Cuánta energía se obtiene de la gente y de la actividad.",
          "Alto: sociable, enérgico(a), le gusta estar con gente, tomar la iniciativa y la emoción.",
          "Bajo: reservado(a), prefiere grupos pequeños o estar a solas, más tranquilo(a)."),
    "O": ("Curiosidad intelectual, imaginación y gusto por lo nuevo, el arte y las ideas.",
          "Alto: curioso(a), imaginativo(a), le atraen las ideas, el arte y la variedad.",
          "Bajo: práctico(a) y concreto(a), prefiere lo conocido y lo tradicional."),
    "A": ("Cómo se trata a los demás: confianza, honradez, ayuda y trato amable.",
          "Alto: confiado(a), servicial, compasivo(a), evita los conflictos.",
          "Bajo: directo(a), escéptico(a), competitivo(a); pone sus intereses primero."),
    "C": ("Organización, disciplina y constancia para cumplir metas.",
          "Alto: ordenado(a), cumplido(a), disciplinado(a) y prudente.",
          "Bajo: espontáneo(a) y flexible, pero puede ser desordenado(a) o dejar las cosas para después."),
}


REACTIVOS = factores.reactivos(DOMINIOS, ORDEN)


def calificar(respuestas: list[int], edad: float) -> dict:
    return factores.calificar(REACTIVOS, DOMINIOS, ORDEN, NORMAS, DESCRIPCION, respuestas)


BIG_FIVE = Cuestionario(
    "bigfive", "Big Five (OCEAN)",
    "El modelo de personalidad con más respaldo científico. Mide cinco grandes rasgos — Apertura, "
    "Responsabilidad, Extraversión, Amabilidad y Neuroticismo — y 6 facetas de cada uno (30 en total). "
    "Preguntas del IPIP-NEO-120 (dominio público). Unos 15 minutos.",
    "likert", [r[0] for r in REACTIVOS], calificar, edad_min=14, minutos=15,
    aviso="Contesta cómo eres normalmente, no cómo te gustaría ser. No hay respuestas buenas ni malas.")

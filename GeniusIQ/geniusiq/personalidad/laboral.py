"""Perfil laboral: rasgos para el trabajo y riesgos bajo presión, con preguntas propias.

Alternativa libre a pruebas comerciales de selección de personal:
- Rasgos (8): siguen los del Perfil e Inventario de Personalidad de Gordon (ascendencia,
  responsabilidad, estabilidad emocional, sociabilidad, cautela, originalidad, relaciones
  personales y vigor), que junto con los valores forman el SOSIE.
- Riesgos bajo presión (8): siguen la idea del Hogan Development Survey ("descarriladores":
  conductas que estorban cuando hay estrés, cansancio o mucha confianza).
Las preguntas son propias, NO son las de Gordon, SOSIE ni Hogan, y no tienen normas: el
resultado es un puntaje 0–100 (qué tanto se describe uno así), no un percentil.
"""

from __future__ import annotations

from . import Cuestionario

# clave → (nombre, qué mide, alto, bajo, [(texto, ±1), ×5])
RASGOS = {
    "lid": ("Liderazgo", "Tomar la iniciativa, decidir y dirigir a otros.",
            "Toma el mando con naturalidad, decide y da instrucciones sin problema.",
            "Prefiere seguir indicaciones y aportar desde su lugar, sin dirigir.",
            [("Me gusta tomar decisiones por el grupo.", 1),
             ("Cuando nadie organiza, yo tomo la iniciativa.", 1),
             ("Me siento cómodo(a) dando instrucciones a otros.", 1),
             ("Prefiero que otro dirija y yo seguir indicaciones.", -1),
             ("Me incomoda tener que corregir a un compañero.", -1)]),
    "res": ("Responsabilidad", "Cumplir lo que se promete, con constancia y puntualidad.",
            "Cumple sus compromisos y es constante aunque nadie lo supervise.",
            "Necesita seguimiento y fechas claras para cumplir.",
            [("Termino lo que empiezo aunque sea aburrido.", 1),
             ("Si me comprometo a una fecha, la cumplo.", 1),
             ("Llego puntual a mis compromisos.", 1),
             ("Se me olvidan tareas que me encargaron.", -1),
             ("Si nadie me supervisa, bajo el ritmo.", -1)]),
    "est": ("Estabilidad emocional", "Mantener la calma y el rendimiento con presión o críticas.",
            "Trabaja tranquilo(a) bajo presión y se repone rápido de los tropiezos.",
            "La presión y las críticas le afectan; rinde mejor en ambientes tranquilos.",
            [("Mantengo la calma cuando hay mucha presión en el trabajo.", 1),
             ("Las críticas a mi trabajo me afectan por días.", -1),
             ("Me repongo rápido de un mal día.", 1),
             ("Me pongo tenso(a) cuando las cosas no salen como las planeé.", -1),
             ("Puedo trabajar bien aunque tenga problemas personales.", 1)]),
    "soc": ("Sociabilidad", "Gusto por trabajar con gente y tratar con desconocidos.",
            "Disfruta el trabajo en equipo y el trato con clientes.",
            "Prefiere trabajar solo(a) o con poca gente.",
            [("Disfruto trabajar rodeado(a) de gente.", 1),
             ("Me es fácil platicar con clientes o desconocidos.", 1),
             ("Me gusta convivir con mis compañeros fuera del trabajo.", 1),
             ("Prefiero trabajar solo(a) que en equipo.", -1),
             ("Las juntas y reuniones me cansan.", -1)]),
    "cau": ("Cautela", "Pensar antes de actuar y evitar riesgos innecesarios.",
            "Revisa las opciones, sigue instrucciones y evita riesgos.",
            "Decide rápido y se arriesga; útil en lo urgente, pero puede precipitarse.",
            [("Antes de decidir, reviso bien las opciones.", 1),
             ("Evito arriesgarme sin necesidad.", 1),
             ("Leo las instrucciones antes de empezar algo nuevo.", 1),
             ("Tomo decisiones rápido aunque me falte información.", -1),
             ("Me gusta apostar por lo arriesgado si la ganancia es grande.", -1)]),
    "ori": ("Originalidad", "Gusto por las ideas nuevas y los problemas difíciles.",
            "Propone formas nuevas de hacer las cosas y disfruta resolver problemas.",
            "Prefiere procedimientos probados y trabajo concreto.",
            [("Me gusta encontrar formas nuevas de hacer el trabajo.", 1),
             ("Se me ocurren soluciones que a otros no.", 1),
             ("Disfruto los problemas que nadie ha resuelto.", 1),
             ("Prefiero seguir el procedimiento de siempre.", -1),
             ("Me aburre pensar en ideas o teorías.", -1)]),
    "tra": ("Trato con la gente", "Paciencia, confianza y respeto con compañeros y clientes.",
            "Paciente y respetuoso(a) aun con gente difícil; confía en su equipo.",
            "Se impacienta o desconfía con facilidad; puede generar roces.",
            [("Tengo paciencia con la gente difícil.", 1),
             ("Confío en mis compañeros de trabajo.", 1),
             ("Trato con respeto incluso a quien no me cae bien.", 1),
             ("Me irrita la gente que trabaja más despacio que yo.", -1),
             ("Hablo mal de los compañeros a sus espaldas.", -1)]),
    "ene": ("Energía", "Ritmo de trabajo y aguante en jornadas intensas.",
            "Trabaja a buen ritmo, aguanta jornadas largas y le gusta estar ocupado(a).",
            "Prefiere un ritmo tranquilo y constante, sin presión de tiempo.",
            [("Trabajo a buen ritmo durante todo el día.", 1),
             ("Me gusta tener muchas cosas que hacer.", 1),
             ("Aguanto jornadas largas sin bajar el rendimiento.", 1),
             ("Me canso rápido cuando el trabajo es intenso.", -1),
             ("Prefiero un trabajo tranquilo, sin prisas.", -1)]),
}

# clave → (nombre, cómo se ve, [texto ×3]) — todas cuentan a favor del riesgo
RIESGOS = {
    "vol": ("Volatilidad", "Explota o se desanima de golpe; su humor afecta al equipo.",
            ["Cuando estoy bajo presión, exploto con la gente.",
             "Mi entusiasmo por un proyecto se me pasa rápido.",
             "Mis cambios de humor afectan mi trabajo."]),
    "des": ("Desconfianza", "Ve malas intenciones en los demás y toma las críticas como algo personal.",
            ["Sospecho que los demás tienen intenciones ocultas.",
             "Cuando me critican, pienso que es algo personal.",
             "Me cuesta creer en las promesas de mis jefes."]),
    "mie": ("Miedo a equivocarse", "Pospone decisiones y evita proponer cosas nuevas.",
            ["Prefiero no decidir para no equivocarme.",
             "Me da miedo proponer cosas nuevas por si fallan.",
             "Pospongo las decisiones importantes hasta el último momento."]),
    "arr": ("Arrogancia", "Se siente con la razón y con derecho a más; le cuesta admitir errores.",
            ["Creo que casi siempre tengo la razón.",
             "Me cuesta aceptar que cometí un error.",
             "Pienso que merezco un puesto más alto del que tengo."]),
    "ata": ("Atajos y reglas", "Prueba los límites, promete de más y se arriesga por diversión.",
            ["Me gusta probar qué tanto puedo romper las reglas.",
             "Prometo cosas que sé que no voy a cumplir para salir del paso.",
             "Me aburro rápido y tomo riesgos para divertirme."]),
    "mic": ("Control excesivo", "No delega, revisa de más y quiere todo a su manera.",
            ["Me cuesta delegar porque nadie lo hace tan bien como yo.",
             "Reviso de más el trabajo de los demás.",
             "Me estreso si las cosas no se hacen exactamente a mi manera."]),
    "pro": ("Protagonismo", "Busca ser el centro de atención y empieza más de lo que termina.",
            ["Me gusta ser el centro de atención.",
             "Interrumpo a los demás para contar lo mío.",
             "Empiezo muchas cosas para impresionar, pero me cuesta terminarlas."]),
    "pas": ("Resistencia pasiva", "Dice que sí, pero hace las cosas a su modo y a su tiempo.",
            ["Digo que sí a lo que me piden, pero lo hago a mi modo y a mi tiempo.",
             "Me molesta en silencio que me pidan más de lo justo.",
             "Cuando no estoy de acuerdo no lo digo, pero lo hago más lento."]),
}


def _reactivos() -> list[tuple]:
    """(texto, grupo, clave, signo), intercalados: una frase de cada escala por vuelta."""
    rasgos = [(t, "rasgo", c, s) for k in range(5) for c, (*_, items) in RASGOS.items() for t, s in [items[k]]]
    riesgos = [(items[k], "riesgo", c, 1) for k in range(3) for c, (*_, items) in RIESGOS.items()]
    # se reparten los riesgos entre los rasgos para que no queden todos juntos al final
    lista, paso = [], len(rasgos) / len(riesgos)
    j = 0
    for i, r in enumerate(rasgos):
        lista.append(r)
        while j < len(riesgos) and (j + 1) * paso <= i + 1:
            lista.append(riesgos[j])
            j += 1
    return lista + riesgos[j:]


REACTIVOS = _reactivos()


def _puntos(valores: list[int]) -> int:
    return round((sum(valores) / len(valores) - 1) / 4 * 100)


def calificar(respuestas: list[int], edad: float) -> dict:
    por: dict[str, list[int]] = {}
    for (_, _, c, s), r in zip(REACTIVOS, respuestas):
        por.setdefault(c, []).append(r if s > 0 else 6 - r)
    rasgos = []
    for c, (nombre, mide, alto, bajo, _) in RASGOS.items():
        p = _puntos(por[c])
        rasgos.append({"clave": c, "nombre": nombre, "puntos": p, "descripcion": mide,
                       "nivel": "Alto" if p >= 70 else "Bajo" if p <= 40 else "Medio",
                       "lectura": alto if p >= 70 else bajo if p <= 40 else
                       "Término medio: depende de la situación."})
    riesgos = []
    for c, (nombre, como, _) in RIESGOS.items():
        p = _puntos(por[c])
        riesgos.append({"clave": c, "nombre": nombre, "puntos": p, "descripcion": como,
                        "nivel": "Alto" if p >= 75 else "Moderado" if p >= 55 else "Bajo"})
    fuertes = [x["nombre"] for x in sorted(rasgos, key=lambda x: -x["puntos"]) if x["puntos"] >= 60][:3]
    cuidar = [x["nombre"] for x in sorted(riesgos, key=lambda x: -x["puntos"]) if x["nivel"] != "Bajo"]
    resumen = "Fuerte: " + (", ".join(fuertes) or "—")
    if cuidar:
        resumen += " · Cuidar: " + ", ".join(cuidar[:2])
    return {"rasgos": rasgos, "riesgos": riesgos, "fortalezas": fuertes, "a_cuidar": cuidar, "resumen": resumen}


PERFIL_LABORAL = Cuestionario(
    "laboral", "Perfil laboral",
    "Cómo es uno en el trabajo: 8 rasgos (liderazgo, responsabilidad, estabilidad emocional, sociabilidad, "
    "cautela, originalidad, trato con la gente y energía) y 8 riesgos bajo presión (conductas que estorban "
    "con estrés o cansancio). Alternativa libre inspirada en Gordon/SOSIE y Hogan; preguntas propias, sin "
    "normas. Para autoconocimiento, NO para decidir contrataciones. Unos 11 minutos.",
    "likert", [r[0] for r in REACTIVOS], calificar, edad_min=16, minutos=11,
    aviso="Piensa en cómo eres en el trabajo (o en la escuela, si no trabajas). Contesta cómo eres, no cómo "
          "debería ser un buen empleado.")

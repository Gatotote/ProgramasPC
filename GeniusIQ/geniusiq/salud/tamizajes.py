"""Los tamizajes y su calificación oficial.

Todos se pueden usar sin pagar ni pedir permiso para uso clínico o personal:
- PHQ-9 y GAD-7 (Spitzer, Kroenke, Williams y Löwe; Pfizer los liberó al dominio público).
- ASRS v1.1, 18 preguntas (Organización Mundial de la Salud y Kessler; uso libre).
- SNAP-IV-26 (Swanson, Nolan y Pelham; se distribuye libremente).
- AUDIT (Organización Mundial de la Salud, 2001; uso libre).
- PCL-5 (National Center for PTSD de EE. UU.; dominio público).
Traducción propia al español de México. Las respuestas llegan como 1 = primera opción.
"""

from __future__ import annotations

from ..personalidad import Cuestionario
from . import CRISIS

FRECUENCIA_2SEM = ["Nunca", "Varios días", "Más de la mitad de los días", "Casi todos los días"]
FRECUENCIA_ASRS = ["Nunca", "Rara vez", "Algunas veces", "Con frecuencia", "Muy seguido"]
INTENSIDAD = ["Nada", "Un poco", "Moderadamente", "Bastante", "Extremadamente"]


def _nivel(total: int, cortes: list[tuple]) -> tuple[int, str, str]:
    """cortes = [(desde, nivel, lectura), …] de menor a mayor → (índice, nivel, lectura)."""
    i = max(k for k, (desde, *_) in enumerate(cortes) if total >= desde)
    return i, cortes[i][1], cortes[i][2]


def _resultado(total: int, maximo: int, cortes: list[tuple], corte_positivo: int, recomendacion: str,
               nombre_corto: str, **extra) -> dict:
    i, nivel, lectura = _nivel(total, cortes)
    positivo = total >= corte_positivo
    return {"puntaje": total, "maximo": maximo, "nivel": nivel, "gravedad": i, "lectura": lectura,
            "positivo": positivo, "corte": corte_positivo,
            "cortes": [{"desde": d, "nivel": n} for d, n, _ in cortes],
            "recomendacion": recomendacion if positivo else
            "Por ahora no sale una señal de alerta. Si algo te sigue preocupando, coméntalo con tu médico.",
            "subescalas": [], "alertas": [], "notas": [], "urgente": False,
            "resumen": f"{nombre_corto} {total}/{maximo} · {nivel}", **extra}


# ------------------------------------------------------------------ PHQ-9 (depresión)

PHQ9_PREGUNTAS = [
    "Poco interés o gusto por hacer las cosas.",
    "Sentirte decaído(a), deprimido(a) o sin esperanza.",
    "Problemas para dormirte o para seguir dormido(a), o dormir demasiado.",
    "Sentirte cansado(a) o con poca energía.",
    "Poco apetito o comer en exceso.",
    "Sentirte mal contigo mismo(a): que eres un fracaso o que les has fallado a ti o a tu familia.",
    "Dificultad para concentrarte en cosas como leer o ver la televisión.",
    "Moverte o hablar tan despacio que otras personas lo notaron; o lo contrario: estar tan inquieto(a) "
    "que te has movido mucho más de lo normal.",
    "Pensar que estarías mejor muerto(a) o que quieres hacerte daño de alguna manera.",
]


def _phq9(respuestas: list[int], edad: float) -> dict:
    v = [r - 1 for r in respuestas]
    res = _resultado(sum(v), 27, [
        (0, "Mínima", "Síntomas de depresión mínimos o ausentes."),
        (5, "Leve", "Síntomas leves de depresión."),
        (10, "Moderada", "Síntomas moderados de depresión."),
        (15, "Moderadamente grave", "Síntomas de depresión moderadamente graves."),
        (20, "Grave", "Síntomas graves de depresión."),
    ], 10, "Conviene una valoración con un médico o psicólogo en las próximas semanas; con puntajes de 15 o "
           "más, lo antes posible. La depresión tiene tratamiento y suele mejorar.", "PHQ-9")
    if v[8] > 0:
        res["urgente"] = True
        res["alertas"].append("Marcaste que has tenido pensamientos de muerte o de hacerte daño. Eso es "
                              "importante aunque el resto del puntaje sea bajo: platícalo hoy con alguien de "
                              "confianza y con un profesional.\n\n" + CRISIS)
        res["recomendacion"] = ("Busca hoy a un profesional o llama a la Línea de la Vida (800 911 2000), "
                                "aunque el resto del puntaje sea bajo.")
    return res


PHQ9 = Cuestionario(
    "phq9", "PHQ-9 (depresión)",
    "Detecta síntomas de depresión de las últimas 2 semanas y su intensidad. Es el cuestionario más usado en "
    "consultorios de todo el mundo (Patient Health Questionnaire, dominio público). 9 preguntas, 2 minutos.",
    "likert", PHQ9_PREGUNTAS, _phq9, edad_min=12, minutos=2,
    aviso="Durante las últimas 2 semanas, ¿con qué frecuencia te han molestado estos problemas?",
    opciones=FRECUENCIA_2SEM, categoria="salud")


# ------------------------------------------------------------------ GAD-7 (ansiedad)

GAD7_PREGUNTAS = [
    "Sentirte nervioso(a), ansioso(a) o con los nervios de punta.",
    "No poder dejar de preocuparte o no poder controlar la preocupación.",
    "Preocuparte demasiado por diferentes cosas.",
    "Dificultad para relajarte.",
    "Estar tan inquieto(a) que te cuesta quedarte quieto(a).",
    "Molestarte o irritarte con facilidad.",
    "Sentir miedo, como si algo terrible fuera a pasar.",
]


def _gad7(respuestas: list[int], edad: float) -> dict:
    return _resultado(sum(r - 1 for r in respuestas), 21, [
        (0, "Mínima", "Ansiedad mínima o ausente."),
        (5, "Leve", "Síntomas leves de ansiedad."),
        (10, "Moderada", "Síntomas moderados de ansiedad."),
        (15, "Grave", "Síntomas graves de ansiedad."),
    ], 10, "Conviene una valoración con un médico o psicólogo: a partir de 10 puntos es probable un trastorno "
           "de ansiedad (generalizada, pánico, social o estrés postraumático). Tiene tratamiento.", "GAD-7")


GAD7 = Cuestionario(
    "gad7", "GAD-7 (ansiedad)",
    "Detecta síntomas de ansiedad de las últimas 2 semanas (Generalized Anxiety Disorder-7, dominio público). "
    "7 preguntas, 2 minutos.",
    "likert", GAD7_PREGUNTAS, _gad7, edad_min=12, minutos=2,
    aviso="Durante las últimas 2 semanas, ¿con qué frecuencia te han molestado estos problemas?",
    opciones=FRECUENCIA_2SEM, categoria="salud")


# ------------------------------------------------------------------ ASRS v1.1 completo (TDAH en adultos)

# (pregunta, grupo D = desatención / H = hiperactividad-impulsividad, desde qué respuesta cuenta: 3 =
# «Algunas veces», 4 = «Con frecuencia»; son las casillas sombreadas del formato oficial)
ASRS_PREGUNTAS = [
    # parte A: las 6 que mejor predicen el diagnóstico
    ("¿Con qué frecuencia te cuesta terminar los detalles finales de un proyecto, una vez que ya hiciste "
     "las partes difíciles?", "D", 3),
    ("¿Con qué frecuencia te cuesta poner las cosas en orden cuando haces una tarea que requiere "
     "organización?", "D", 3),
    ("¿Con qué frecuencia tienes problemas para acordarte de citas u obligaciones?", "D", 3),
    ("Cuando tienes una tarea que requiere pensar mucho, ¿con qué frecuencia evitas empezarla o la "
     "retrasas?", "D", 4),
    ("¿Con qué frecuencia mueves o retuerces las manos o los pies cuando tienes que estar sentado(a) mucho "
     "tiempo?", "H", 4),
    ("¿Con qué frecuencia te sientes demasiado activo(a) y con necesidad de hacer cosas, como si tuvieras "
     "un motor por dentro?", "H", 4),
    # parte B
    ("¿Con qué frecuencia cometes errores por descuido cuando trabajas en algo aburrido o difícil?", "D", 4),
    ("¿Con qué frecuencia te cuesta mantener la atención cuando haces un trabajo aburrido o repetitivo?",
     "D", 4),
    ("¿Con qué frecuencia te cuesta concentrarte en lo que te dicen, aun cuando te hablan directamente?",
     "D", 3),
    ("¿Con qué frecuencia pierdes cosas o te cuesta encontrarlas en la casa o en el trabajo?", "D", 4),
    ("¿Con qué frecuencia te distraen la actividad o el ruido a tu alrededor?", "D", 4),
    ("¿Con qué frecuencia te levantas de tu lugar en juntas u otras situaciones en las que se espera que "
     "sigas sentado(a)?", "H", 3),
    ("¿Con qué frecuencia te sientes intranquilo(a) o inquieto(a)?", "H", 4),
    ("¿Con qué frecuencia te cuesta calmarte y relajarte cuando tienes tiempo para ti?", "H", 4),
    ("¿Con qué frecuencia hablas de más en reuniones con otras personas?", "H", 4),
    ("Cuando platicas con alguien, ¿con qué frecuencia terminas sus frases antes de que lo haga la otra "
     "persona?", "H", 3),
    ("¿Con qué frecuencia te cuesta esperar tu turno en situaciones en las que hay que hacerlo?", "H", 4),
    ("¿Con qué frecuencia interrumpes a otros cuando están ocupados?", "H", 3),
]


def _asrs(respuestas: list[int], edad: float) -> dict:
    zona = [r >= desde for r, (_, _, desde) in zip(respuestas, ASRS_PREGUNTAS)]
    senales = sum(zona[:6])
    res = _resultado(senales, 6, [
        (0, "Sin señal", "Pocas señales de TDAH en adultos en las 6 preguntas de detección."),
        (4, "Señal positiva", "El patrón de respuestas es compatible con TDAH en adultos."),
    ], 4, "Conviene una evaluación con un psiquiatra o neuropsicólogo. El TDAH en adultos es frecuente, a "
          "menudo no se detectó en la infancia y tiene tratamiento.", "ASRS")
    res["resumen"] = f"ASRS {senales}/6 señales · {res['nivel']}"
    res["explicacion_total"] = ("El resultado oficial sale de la parte A (preguntas 1–6): se cuentan las "
                                "respuestas en zona de alerta. 4 o más = señal positiva.")
    sintomas = {}
    for g, nombre in (("D", "Desatención"), ("H", "Hiperactividad / impulsividad")):
        idx = [i for i, (_, gi, _) in enumerate(ASRS_PREGUNTAS) if gi == g]
        sintomas[g] = sum(zona[i] for i in idx)
        res["subescalas"].append({"nombre": nombre, "puntos": sum(respuestas[i] - 1 for i in idx),
                                  "maximo": 4 * len(idx)})
    d, h = sintomas["D"], sintomas["H"]
    presentacion = ("combinada" if d >= 5 and h >= 5 else "predominantemente con desatención" if d >= 5 else
                    "predominantemente hiperactiva/impulsiva" if h >= 5 else "")
    res["notas"] = [f"Síntomas en zona de alerta (las 18 preguntas): desatención {d} de 9, hiperactividad/"
                    f"impulsividad {h} de 9.",
                    "Como referencia, en adultos el DSM-5 pide 5 o más síntomas en un grupo, que hayan empezado "
                    "antes de los 12 años y que estorben en dos o más ámbitos (casa, trabajo, escuela, pareja). "
                    "Eso solo lo puede confirmar un profesional."]
    if presentacion:
        res["notas"].append(f"El número de síntomas se parece a la presentación {presentacion}.")
    res["sintomas"] = sintomas
    return res


ASRS = Cuestionario(
    "asrs", "ASRS (TDAH en adultos)",
    "Escala de Autoinforme de TDAH en Adultos de la OMS (ASRS v1.1) completa: las 18 preguntas siguen los "
    "18 síntomas del DSM. La parte A (6 preguntas) da el resultado de detección; la parte B completa el "
    "perfil de desatención e hiperactividad/impulsividad. 5 minutos.",
    "likert", [p for p, _, _ in ASRS_PREGUNTAS], _asrs, edad_min=18, minutos=5,
    aviso="Piensa en los últimos 6 meses, en el trabajo, la escuela o la casa.",
    opciones=FRECUENCIA_ASRS, categoria="salud")


# ------------------------------------------------------------------ SNAP-IV (TDAH en niños y adolescentes)

SNAP_INFORMANTE = ["Papá, mamá o tutor", "Maestro(a)"]
SNAP_ESCALA = ["Nada", "Un poco", "Bastante", "Mucho"]

SNAP_PREGUNTAS = [
    # desatención (1–9)
    "A menudo no pone atención a los detalles o comete errores por descuido en sus tareas o trabajos.",
    "A menudo le cuesta mantener la atención en tareas o juegos.",
    "A menudo parece no escuchar cuando se le habla directamente.",
    "A menudo no sigue las instrucciones y no termina las tareas de la escuela, los encargos o sus "
    "obligaciones.",
    "A menudo le cuesta organizar tareas y actividades.",
    "A menudo evita, le disgustan o hace de mala gana las tareas que requieren esfuerzo mental sostenido.",
    "A menudo pierde cosas que necesita (juguetes, tareas, lápices, libros…).",
    "A menudo se distrae con cualquier cosa a su alrededor.",
    "A menudo es olvidadizo(a) en las actividades diarias.",
    # hiperactividad / impulsividad (10–18)
    "A menudo mueve las manos o los pies, o se retuerce en el asiento.",
    "A menudo se levanta de su lugar en el salón o en otras situaciones en que debe quedarse sentado(a).",
    "A menudo corre o se trepa en exceso en situaciones en que no es apropiado.",
    "A menudo le cuesta jugar o hacer actividades de tiempo libre en silencio.",
    "A menudo está «en movimiento» o actúa como si tuviera «un motor».",
    "A menudo habla en exceso.",
    "A menudo suelta las respuestas antes de que terminen de hacerle la pregunta.",
    "A menudo le cuesta esperar su turno.",
    "A menudo interrumpe o se mete en lo que hacen otros (conversaciones, juegos).",
    # oposicionismo (19–26)
    "A menudo pierde los estribos.",
    "A menudo discute con los adultos.",
    "A menudo desafía o se niega a cumplir lo que piden los adultos o las reglas.",
    "A menudo hace cosas a propósito para molestar a los demás.",
    "A menudo culpa a otros de sus errores o de su mal comportamiento.",
    "A menudo es susceptible o se molesta fácilmente con los demás.",
    "A menudo está enojado(a) o resentido(a).",
    "A menudo es rencoroso(a) o vengativo(a).",
]

# Puntos de corte del promedio por grupo (Swanson; ~5 % más alto de la población), según quién contesta
SNAP_CORTES = {
    "padres": {"D": 1.78, "H": 1.44, "O": 1.88, "TDAH": 1.67},
    "maestro": {"D": 2.56, "H": 1.78, "O": 1.38, "TDAH": 2.00},
}
_SNAP_GRUPOS = [("D", "Desatención (1–9)", 0, 9), ("H", "Hiperactividad / impulsividad (10–18)", 9, 18),
                ("O", "Oposicionismo (19–26)", 18, 26)]


def _snap(respuestas: list[int], edad: float) -> dict:
    quien = "maestro" if respuestas[0] == 2 else "padres"
    v = [r - 1 for r in respuestas[1:]]          # 0–3
    cortes = SNAP_CORTES[quien]
    suma_tdah = sum(v[:18])
    corte_tdah = round(cortes["TDAH"] * 18)
    res = _resultado(suma_tdah, 54, [
        (0, "Por debajo del corte", "Los síntomas de TDAH no destacan frente a lo típico de su edad."),
        (corte_tdah, "Arriba del corte", "Los síntomas de TDAH están en el 5 % más alto: conviene evaluarlo."),
    ], corte_tdah, "Conviene una evaluación con un paidopsiquiatra, neuropediatra o psicólogo infantil. "
                   "Ayuda mucho que también lo conteste un maestro (o los papás, si lo contestó el maestro): "
                   "el TDAH se nota en más de un lugar.", "SNAP-IV")
    res["informante"] = quien
    res["explicacion_total"] = (f"Suma de las 18 preguntas de TDAH (0–54). Contestó: "
                                f"{'maestro(a)' if quien == 'maestro' else 'papá, mamá o tutor'}; corte para "
                                f"ese informante: promedio {cortes['TDAH']:.2f} = {corte_tdah} puntos.")
    arriba, notas = [], []
    for g, nombre, a, b in _SNAP_GRUPOS:
        grupo = v[a:b]
        prom = sum(grupo) / len(grupo)
        presentes = sum(1 for x in grupo if x >= 2)       # «Bastante» o «Mucho»
        res["subescalas"].append({"nombre": nombre, "puntos": sum(grupo), "maximo": 3 * len(grupo),
                                  "texto": f"prom. {prom:.2f} (corte {cortes[g]:.2f})"})
        if prom >= cortes[g]:
            arriba.append(g)
        notas.append(f"{nombre}: promedio {prom:.2f} (corte {cortes[g]:.2f}), {presentes} de {len(grupo)} "
                     f"conductas en «Bastante» o «Mucho».")
        res[f"sintomas_{g}"] = presentes
    if ("D" in arriba or "H" in arriba) and not res["positivo"]:
        res["positivo"] = True
        res["recomendacion"] = ("Uno de los grupos de TDAH pasa su corte aunque la suma total no: conviene "
                                "una evaluación con un paidopsiquiatra, neuropediatra o psicólogo infantil.")
    if "O" in arriba:
        res["alertas"].append("El oposicionismo (enojo, desafío, discusiones) pasa el corte. Suele acompañar "
                              "al TDAH; coméntenlo también en la evaluación.")
    d, h = res["sintomas_D"], res["sintomas_H"]
    if d >= 6 or h >= 6:
        tipo = ("combinada" if d >= 6 and h >= 6 else "predominantemente con desatención" if d >= 6
                else "predominantemente hiperactiva/impulsiva")
        notas.append(f"Hay 6 o más conductas frecuentes en un grupo (criterio de síntomas del DSM para niños): "
                     f"se parece a la presentación {tipo}. Solo un profesional puede confirmarlo.")
    if edad >= 18 or edad < 6:
        res["alertas"].append(f"El SNAP-IV está hecho para niños y adolescentes de 6 a 17 años; con "
                              f"{edad:.0f} años el resultado no aplica bien.")
    res["notas"] = notas
    res["resumen"] = f"SNAP-IV {suma_tdah}/54 · {res['nivel']}" + (" · oposicionismo" if "O" in arriba else "")
    return res


SNAP_IV = Cuestionario(
    "snap", "SNAP-IV (TDAH en niños)",
    "Escala de Swanson, Nolan y Pelham (SNAP-IV-26, uso libre) para niños y adolescentes de 6 a 17 años. "
    "La contesta un adulto que lo conozca bien (papá, mamá, tutor o maestro). Mide desatención, "
    "hiperactividad/impulsividad y oposicionismo. Elige a la persona del NIÑO antes de empezar. 6 minutos.",
    "likert", ["¿Quién contesta este cuestionario?"] + SNAP_PREGUNTAS, _snap, edad_min=6, minutos=6,
    aviso="Lo contesta un adulto que conozca bien al niño o adolescente, pensando en cómo se ha comportado "
          "en los últimos 6 meses.",
    opciones=SNAP_ESCALA, opciones_item={0: SNAP_INFORMANTE}, categoria="salud", edad_max=17, informante=True)


# ------------------------------------------------------------------ AUDIT (alcohol)

_FREC_AUDIT = ["Nunca", "Menos de una vez al mes", "Una vez al mes", "Cada semana", "Diario o casi diario"]
_SI_NO_AUDIT = ["No", "Sí, pero no en el último año", "Sí, en el último año"]

AUDIT_PREGUNTAS = [
    ("¿Con qué frecuencia tomas alguna bebida que contenga alcohol?",
     ["Nunca", "Una vez al mes o menos", "2 a 4 veces al mes", "2 o 3 veces a la semana", "4 o más veces a la semana"]),
    ("Los días que tomas, ¿cuántas bebidas estándar sueles tomar?", ["No tomo, o 1 o 2", "3 o 4", "5 o 6", "7 a 9",
                                                                    "10 o más"]),
    ("¿Con qué frecuencia tomas 6 o más bebidas estándar en una sola ocasión?", _FREC_AUDIT),
    ("En el último año, ¿con qué frecuencia no pudiste parar de beber una vez que empezaste?", _FREC_AUDIT),
    ("En el último año, ¿con qué frecuencia dejaste de hacer lo que se esperaba de ti por haber bebido?",
     _FREC_AUDIT),
    ("En el último año, ¿con qué frecuencia necesitaste beber en la mañana para sentirte bien después de haber "
     "bebido mucho el día anterior?", _FREC_AUDIT),
    ("En el último año, ¿con qué frecuencia te sentiste culpable o con remordimiento después de beber?",
     _FREC_AUDIT),
    ("En el último año, ¿con qué frecuencia no pudiste recordar lo que pasó la noche anterior porque habías "
     "bebido?", _FREC_AUDIT),
    ("¿Tú u otra persona han resultado heridos porque habías bebido?", _SI_NO_AUDIT),
    ("¿Algún familiar, amigo, médico u otro profesional de la salud se ha preocupado por tu forma de beber o te "
     "ha sugerido que tomes menos?", _SI_NO_AUDIT),
]


def _audit(respuestas: list[int], edad: float) -> dict:
    v = [r - 1 for r in respuestas[:8]] + [(r - 1) * 2 for r in respuestas[8:]]   # 9 y 10 valen 0, 2 o 4
    res = _resultado(sum(v), 40, [
        (0, "Zona I · Bajo riesgo", "Consumo de bajo riesgo o abstinencia."),
        (8, "Zona II · Consumo de riesgo", "Consumo que aumenta el riesgo de problemas de salud o accidentes."),
        (16, "Zona III · Consumo perjudicial", "Consumo que probablemente ya está causando daño."),
        (20, "Zona IV · Posible dependencia", "Patrón compatible con dependencia al alcohol."),
    ], 8, "Conviene reducir el consumo y platicarlo con un médico. En zona III o IV, buscar valoración "
          "especializada (Centros de Integración Juvenil o Línea de la Vida: 800 911 2000).", "AUDIT")
    res["subescalas"] = [{"nombre": "Consumo (1–3)", "puntos": sum(v[0:3]), "maximo": 12},
                         {"nombre": "Señales de dependencia (4–6)", "puntos": sum(v[3:6]), "maximo": 12},
                         {"nombre": "Daños por el alcohol (7–10)", "puntos": sum(v[6:10]), "maximo": 16}]
    if sum(v[3:6]) >= 4:
        res["alertas"].append("Las preguntas 4 a 6 (señales de dependencia) suman 4 o más. Esto merece una "
                              "valoración médica sin importar el total.")
    if 5 <= res["puntaje"] < 8:
        res["alertas"].append("En mujeres y en mayores de 65 años muchos usan un corte más bajo (7 o incluso "
                              "5): tómalo en cuenta.")
    return res


AUDIT = Cuestionario(
    "audit", "AUDIT (alcohol)",
    "Prueba de la OMS para detectar consumo de riesgo, consumo perjudicial y posible dependencia al alcohol "
    "(Alcohol Use Disorders Identification Test). 10 preguntas, 3 minutos.",
    "likert", [p for p, _ in AUDIT_PREGUNTAS], _audit, edad_min=18, minutos=3,
    aviso="Una bebida estándar = una cerveza de 355 ml, una copa de vino de 140 ml o un caballito de 45 ml de "
          "tequila, mezcal, ron, etc. Si no tomas, contesta «Nunca» y la primera opción.",
    opciones_item={i: ops for i, (_, ops) in enumerate(AUDIT_PREGUNTAS)}, categoria="salud")


# ------------------------------------------------------------------ PCL-5 (estrés postraumático)

PCL5_PREGUNTAS = [
    "Recuerdos repetidos, perturbadores e involuntarios de la experiencia estresante.",
    "Sueños repetidos y perturbadores sobre la experiencia estresante.",
    "Sentir o actuar de repente como si la experiencia estresante estuviera pasando otra vez (como si "
    "estuvieras ahí reviviéndola).",
    "Sentirte muy alterado(a) cuando algo te recordó la experiencia estresante.",
    "Tener reacciones físicas fuertes cuando algo te recordó la experiencia (por ejemplo, el corazón "
    "acelerado, dificultad para respirar, sudor).",
    "Evitar recuerdos, pensamientos o sentimientos relacionados con la experiencia.",
    "Evitar cosas que te la recuerdan (por ejemplo, personas, lugares, conversaciones, actividades, objetos "
    "o situaciones).",
    "Dificultad para recordar partes importantes de la experiencia.",
    "Tener creencias negativas fuertes sobre ti, los demás o el mundo (por ejemplo: «soy malo(a)», «algo "
    "está muy mal en mí», «no se puede confiar en nadie», «el mundo es muy peligroso»).",
    "Culparte a ti o a alguien más por la experiencia o por lo que pasó después.",
    "Tener sentimientos negativos fuertes, como miedo, horror, enojo, culpa o vergüenza.",
    "Perder el interés en actividades que antes disfrutabas.",
    "Sentirte distante o aislado(a) de otras personas.",
    "Dificultad para sentir emociones positivas (por ejemplo, no poder sentir alegría o cariño por las "
    "personas cercanas).",
    "Estar irritable, tener arranques de enojo o actuar de forma agresiva.",
    "Arriesgarte demasiado o hacer cosas que te podrían hacer daño.",
    "Estar «en alerta», vigilante o en guardia.",
    "Sentirte nervioso(a) o asustarte con facilidad.",
    "Dificultad para concentrarte.",
    "Problemas para dormirte o seguir dormido(a).",
]

_GRUPOS_PCL5 = [("B. Recuerdos que regresan (1–5)", 0, 5, 1), ("C. Evitación (6–7)", 5, 7, 1),
                ("D. Pensamientos y ánimo negativos (8–14)", 7, 14, 2), ("E. Alerta y reactividad (15–20)", 14, 20, 2)]


def _pcl5(respuestas: list[int], edad: float) -> dict:
    v = [r - 1 for r in respuestas]
    res = _resultado(sum(v), 80, [
        (0, "Bajo", "Pocas molestias relacionadas con la experiencia estresante."),
        (20, "Moderado", "Molestias notables, por debajo del corte de probable estrés postraumático."),
        (33, "Probable TEPT", "Puntaje compatible con trastorno de estrés postraumático."),
    ], 33, "Conviene una valoración con un psicólogo o psiquiatra con experiencia en trauma. El estrés "
           "postraumático tiene tratamientos eficaces (terapias centradas en el trauma).", "PCL-5")
    # patrón del DSM-5: síntoma presente si vale 2 («Moderadamente») o más
    cumple = True
    for nombre, a, b, minimo in _GRUPOS_PCL5:
        presentes = sum(1 for x in v[a:b] if x >= 2)
        cumple &= presentes >= minimo
        res["subescalas"].append({"nombre": nombre, "puntos": sum(v[a:b]), "maximo": 4 * (b - a)})
    res["patron_dsm5"] = cumple
    if cumple and not res["positivo"]:
        res["alertas"].append("Aunque el total no llega a 33, los síntomas cumplen el patrón de grupos del "
                              "DSM-5 (al menos 1 de B, 1 de C, 2 de D y 2 de E en «Moderadamente» o más). "
                              "Conviene una valoración.")
    if v[15] >= 2:
        res["alertas"].append("Marcaste que te arriesgas o haces cosas que te podrían hacer daño. Platícalo "
                              "con alguien de confianza y menciónalo en la valoración.")
    return res


PCL5 = Cuestionario(
    "pcl5", "PCL-5 (estrés postraumático)",
    "Lista de 20 síntomas de estrés postraumático del DSM-5 (PTSD Checklist, National Center for PTSD, "
    "dominio público), relacionados con la peor experiencia estresante que hayas vivido. 5 minutos.",
    "likert", PCL5_PREGUNTAS, _pcl5, edad_min=18, minutos=5,
    aviso="Piensa en la experiencia más estresante que hayas vivido (accidente, violencia, desastre, muerte "
          "repentina de alguien cercano…). En el ÚLTIMO MES, ¿cuánto te molestó cada problema?",
    opciones=INTENSIDAD, categoria="salud")


TAMIZAJES = [PHQ9, GAD7, ASRS, SNAP_IV, AUDIT, PCL5]

"""Los cinco tamizajes y su calificación oficial.

Todos se pueden usar sin pagar ni pedir permiso para uso clínico o personal:
- PHQ-9 y GAD-7 (Spitzer, Kroenke, Williams y Löwe; Pfizer los liberó al dominio público).
- ASRS v1.1, parte A (Organización Mundial de la Salud y Kessler; uso libre).
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
            "subescalas": [], "alertas": [], "urgente": False,
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


# ------------------------------------------------------------------ ASRS v1.1 parte A (TDAH en adultos)

ASRS_PREGUNTAS = [
    "¿Con qué frecuencia te cuesta terminar los detalles finales de un proyecto, una vez que ya hiciste las "
    "partes difíciles?",
    "¿Con qué frecuencia te cuesta poner las cosas en orden cuando haces una tarea que requiere organización?",
    "¿Con qué frecuencia tienes problemas para acordarte de citas u obligaciones?",
    "Cuando tienes una tarea que requiere pensar mucho, ¿con qué frecuencia evitas empezarla o la retrasas?",
    "¿Con qué frecuencia mueves o retuerces las manos o los pies cuando tienes que estar sentado(a) mucho "
    "tiempo?",
    "¿Con qué frecuencia te sientes demasiado activo(a) y con necesidad de hacer cosas, como si tuvieras un "
    "motor por dentro?",
]


def _asrs(respuestas: list[int], edad: float) -> dict:
    # cuenta como señal: preguntas 1–3 desde «Algunas veces», 4–6 desde «Con frecuencia» (casillas sombreadas)
    senales = sum(1 for i, r in enumerate(respuestas) if r >= (3 if i < 3 else 4))
    res = _resultado(senales, 6, [
        (0, "Sin señal", "Pocas señales de TDAH en adultos."),
        (4, "Señal positiva", "El patrón de respuestas es compatible con TDAH en adultos."),
    ], 4, "Conviene una evaluación con un psiquiatra o neuropsicólogo. El TDAH en adultos es frecuente, a "
          "menudo no se detectó en la infancia y tiene tratamiento.", "ASRS",
        puntaje_frecuencia=sum(r - 1 for r in respuestas))
    res["resumen"] = f"ASRS {senales}/6 señales · {res['nivel']}"
    res["explicacion_total"] = ("Se cuentan las respuestas que caen en la zona de alerta (preguntas 1–3 desde "
                                "«Algunas veces»; 4–6 desde «Con frecuencia»). 4 o más = señal positiva.")
    return res


ASRS = Cuestionario(
    "asrs", "ASRS (TDAH en adultos)",
    "Las 6 preguntas de detección de la Escala de Autoinforme de TDAH en Adultos de la OMS (ASRS v1.1, "
    "parte A). Detecta desatención e hiperactividad de los últimos 6 meses. 2 minutos.",
    "likert", ASRS_PREGUNTAS, _asrs, edad_min=18, minutos=2,
    aviso="Piensa en los últimos 6 meses, en el trabajo, la escuela o la casa.",
    opciones=FRECUENCIA_ASRS, categoria="salud")


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


TAMIZAJES = [PHQ9, GAD7, ASRS, AUDIT, PCL5]

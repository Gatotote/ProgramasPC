"""Subpruebas, baterías (modos de test) y cálculo de resultados."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import irt
from .generadores import figurales, matrices, numericos, verbal


@dataclass
class Subprueba:
    clave: str
    nombre: str
    instrucciones: str
    tipo: str = "items"          # items | digitos_directo | digitos_inverso | corsi | busqueda | claves
    generar: Callable | None = None
    norma: str = "fluido"        # fluido | cristalizado | memoria | visoespacial | velocidad
    verbal: bool = False         # para el CI verbal / no verbal (estilo Stanford-Binet)
    tiempo_item: int = 0         # segundos por pregunta (0 = sin límite)
    discontinuar: int = 3        # termina tras N errores seguidos (0 = nunca)
    max_items: int = 14
    minutos: float = 4           # duración aproximada, para mostrarla


SUBPRUEBAS = {s.clave: s for s in [
    Subprueba("matrices", "Matrices de figuras",
              "Verás una cuadrícula de 3×3 con una casilla vacía. Fíjate cómo cambian las figuras "
              "a lo largo de las filas y columnas, y elige la opción que completa la cuadrícula.",
              generar=matrices.matrices, tiempo_item=90, max_items=14, minutos=8),
    Subprueba("series_num", "Series numéricas",
              "Escribe el número que sigue en cada serie y presiona Enter.",
              generar=numericos.series_numericas, tiempo_item=60, max_items=12, minutos=6),
    Subprueba("analogias", "Analogías verbales",
              "Completa la relación: «A es a B como C es a…». Elige la palabra que mejor la completa.",
              generar=verbal.analogias, norma="cristalizado", verbal=True, tiempo_item=40, minutos=4),
    Subprueba("semejanzas", "Semejanzas",
              "Elige en qué se parecen las dos cosas. Busca lo más importante que tienen en común.",
              generar=verbal.semejanzas, norma="cristalizado", verbal=True, tiempo_item=40, minutos=4),
    Subprueba("vocabulario", "Vocabulario",
              "Elige la palabra que significa lo mismo que la palabra entre comillas.",
              generar=verbal.vocabulario, norma="cristalizado", verbal=True, tiempo_item=30, minutos=4),
    Subprueba("informacion", "Información general",
              "Preguntas de cultura general. Elige la respuesta correcta.",
              generar=verbal.informacion, norma="cristalizado", verbal=True, tiempo_item=30, minutos=4),
    Subprueba("aritmetica", "Aritmética",
              "Resuelve cada problema mentalmente (sin papel) y escribe el resultado. Tienes 45 segundos "
              "por problema.",
              generar=numericos.aritmetica, norma="memoria", verbal=True, tiempo_item=45, minutos=6),
    Subprueba("balanzas", "Balanzas",
              "Las balanzas están en equilibrio: lo de la izquierda pesa lo mismo que lo de la derecha. "
              "Usa esa información para encontrar la respuesta.",
              generar=numericos.balanzas, tiempo_item=60, max_items=12, minutos=6),
    Subprueba("rotacion", "Rotación mental",
              "Arriba hay una figura hecha de cuadritos. Elige cuál de las opciones es la MISMA figura, "
              "solo girada. Cuidado: las demás están volteadas como en un espejo.",
              generar=figurales.rotaciones, norma="visoespacial", tiempo_item=40, max_items=12, minutos=5),
    Subprueba("condiciones", "Condiciones (topología)",
              "Cada dibujo tiene un círculo, un cuadrado y un triángulo. Elige el único dibujo donde se "
              "puede poner un punto que cumpla la condición.",
              generar=figurales.condiciones, norma="visoespacial", tiempo_item=60, max_items=8, minutos=4),
    Subprueba("series_fig", "Series de figuras",
              "Las figuras cambian de una casilla a la siguiente siguiendo una regla. Elige la que sigue.",
              generar=figurales.series_figuras, tiempo_item=45, max_items=12, minutos=5),
    Subprueba("clasificacion", "Clasificación",
              "Cuatro de las cinco figuras tienen algo en común. Elige la que NO pertenece al grupo.",
              generar=figurales.clasificaciones, tiempo_item=45, max_items=12, minutos=5),
    Subprueba("digitos", "Retención de dígitos",
              "Verás una serie de números, uno por uno. Primero escríbelos en el MISMO orden; después, "
              "en una segunda parte, al REVÉS. Cada vez la serie es más larga.",
              tipo="digitos", norma="memoria", verbal=True, discontinuar=0, minutos=6),
    Subprueba("corsi", "Memoria espacial (bloques)",
              "Se iluminarán algunos cuadros uno por uno. Cuando termine, haz clic en ellos en el mismo "
              "orden. Cada vez la secuencia es más larga.",
              tipo="corsi", norma="memoria", discontinuar=0, minutos=5),
    Subprueba("busqueda", "Búsqueda de símbolos",
              "A la izquierda hay dos símbolos objetivo. Di si ALGUNO de ellos aparece en el grupo de la "
              "derecha. Responde lo más rápido que puedas sin equivocarte: tienes 2 minutos.\n\n"
              "Teclas: S o ← = Sí está · N o → = No está.",
              tipo="busqueda", norma="velocidad", discontinuar=0, minutos=2.5),
    Subprueba("claves", "Claves",
              "Arriba está la clave: cada símbolo tiene un número. Cuando aparezca un símbolo, presiona "
              "su número (con el teclado o con los botones). Tienes 90 segundos.",
              tipo="claves", norma="velocidad", discontinuar=0, minutos=2),
]}


@dataclass
class Bateria:
    clave: str
    nombre: str
    descripcion: str
    edad_min: int
    edad_max: int
    subpruebas: list[str]
    indices: dict[str, tuple[str, list[str]]]   # clave → (nombre, subpruebas)
    sd: float = 15.0
    verbal_noverbal: bool = False


BATERIAS = [
    Bateria("rapido", "Rápido (mixto)",
            "Una muestra corta de cada habilidad: razonamiento con figuras, números, palabras, "
            "memoria y rapidez. Unos 20 minutos.",
            6, 99, ["matrices", "series_num", "analogias", "digitos", "busqueda"],
            {"RF": ("Razonamiento", ["matrices", "series_num"]),
             "VB": ("Verbal", ["analogias"]),
             "MT": ("Memoria de trabajo", ["digitos"]),
             "VP": ("Velocidad", ["busqueda"])}),
    Bateria("wais", "Estilo WAIS-IV (adultos)",
            "Inspirado en la Escala Wechsler para adultos (16 a 90 años): cuatro índices — "
            "Comprensión verbal, Razonamiento perceptivo, Memoria de trabajo y Velocidad de "
            "procesamiento — y un CI total. Preguntas propias, no las originales. Unos 55 minutos.",
            16, 99,
            ["semejanzas", "vocabulario", "informacion", "matrices", "rotacion", "balanzas",
             "digitos", "aritmetica", "busqueda", "claves"],
            {"ICV": ("Comprensión verbal", ["semejanzas", "vocabulario", "informacion"]),
             "IRP": ("Razonamiento perceptivo", ["matrices", "rotacion", "balanzas"]),
             "IMT": ("Memoria de trabajo", ["digitos", "aritmetica"]),
             "IVP": ("Velocidad de procesamiento", ["busqueda", "claves"])}),
    Bateria("wisc", "Estilo WISC-V (niños de 6 a 16)",
            "Inspirado en la Escala Wechsler para niños (6 a 16 años): cinco índices — Comprensión "
            "verbal, Visoespacial, Razonamiento fluido, Memoria de trabajo y Velocidad de "
            "procesamiento. Las preguntas empiezan según la edad. Unos 50 minutos.",
            6, 16,
            ["semejanzas", "vocabulario", "rotacion", "condiciones", "matrices", "balanzas",
             "digitos", "corsi", "claves", "busqueda"],
            {"ICV": ("Comprensión verbal", ["semejanzas", "vocabulario"]),
             "IVE": ("Visoespacial", ["rotacion", "condiciones"]),
             "IRF": ("Razonamiento fluido", ["matrices", "balanzas"]),
             "IMT": ("Memoria de trabajo", ["digitos", "corsi"]),
             "IVP": ("Velocidad de procesamiento", ["claves", "busqueda"])}),
    Bateria("binet", "Estilo Stanford-Binet 5",
            "Inspirado en la Stanford-Binet (2 a 85+ años): cinco factores, cada uno con una parte "
            "verbal y otra no verbal, más CI verbal y CI no verbal. Unos 50 minutos.",
            6, 99,
            ["matrices", "analogias", "informacion", "vocabulario", "series_num", "aritmetica",
             "rotacion", "condiciones", "corsi", "digitos"],
            {"RF": ("Razonamiento fluido", ["matrices", "analogias"]),
             "CO": ("Conocimiento", ["informacion", "vocabulario"]),
             "RC": ("Razonamiento cuantitativo", ["series_num", "aritmetica"]),
             "VE": ("Procesamiento visoespacial", ["rotacion", "condiciones"]),
             "MT": ("Memoria de trabajo", ["corsi", "digitos"])},
            verbal_noverbal=True),
    Bateria("cattell", "Estilo Cattell Culture Fair",
            "Inspirado en el Test de Factor «g» de Cattell: solo figuras, sin palabras ni cultura "
            "escolar. Cuatro partes — Series, Clasificación, Matrices y Condiciones. El CI se reporta "
            "con desviación 24, como el original (también se muestra su equivalente en escala 15). "
            "Unos 25 minutos.",
            8, 99, ["series_fig", "clasificacion", "matrices", "condiciones"],
            {"G": ("Factor g (inteligencia fluida)", ["series_fig", "clasificacion", "matrices", "condiciones"])},
            sd=24.0),
]
BATERIAS_POR_CLAVE = {b.clave: b for b in BATERIAS}


def punto_inicio(items: list, edad: float, norma: str) -> int:
    """Primera pregunta adecuada para la edad (las anteriores se omiten)."""
    objetivo = irt.ref_edad(edad, norma) - 1.2
    for i, it in enumerate(items):
        if it.b >= objetivo:
            return i
    return 0


def calcular(bateria: Bateria, edad: float, resultados: dict) -> dict:
    """resultados[clave] = {"respuestas": [(a,b,c,ok)...]} o {"aciertos": n, "errores": m}."""
    subs = []
    for clave, res in resultados.items():
        sp = SUBPRUEBAS[clave]
        if sp.norma == "velocidad":
            neto = res["aciertos"] - res["errores"]
            z, se = irt.z_velocidad(clave, neto, edad), 0.35
            detalle = f"{res['aciertos']} aciertos, {res['errores']} errores"
        else:
            mu = irt.ref_edad(edad, sp.norma)
            theta, se = irt.eap(res["respuestas"], mu, 1.0)
            z = theta - mu
            ok = sum(1 for r in res["respuestas"] if r[3])
            detalle = f"{ok} de {len(res['respuestas'])} correctas"
            if res.get("span"):
                detalle += f" · span máximo {res['span']}"
        z = irt.acotar(z)
        subs.append({"clave": clave, "nombre": sp.nombre, "z": z, "se": se,
                     "escalar": irt.escalar(z), "detalle": detalle, "verbal": sp.verbal})
    por_clave = {s["clave"]: s for s in subs}

    def combinar(claves: list[str], r: float) -> dict | None:
        zs = [por_clave[c]["z"] for c in claves if c in por_clave]
        if not zs:
            return None
        ses = [por_clave[c]["se"] for c in claves if c in por_clave]
        if len(zs) == 1:
            zc, sec = zs[0], ses[0]
        else:
            zc, sec = irt.compuesto(zs, r), irt.error_compuesto(ses, r)
        zc = irt.acotar(zc)
        sec = max(sec, 0.15)
        ci = 100 + bateria.sd * zc
        return {"z": zc, "ci": round(ci), "percentil": irt.percentil(zc),
                "rango": [round(ci - 1.645 * bateria.sd * sec), round(ci + 1.645 * bateria.sd * sec)],
                "clasificacion": irt.clasificacion(zc)}

    indices = []
    for ic, (nombre, claves) in bateria.indices.items():
        comb = combinar(claves, irt.R_DENTRO_INDICE)
        if comb:
            indices.append({"clave": ic, "nombre": nombre, **comb})
    if len(indices) == 1 and len(bateria.indices) == 1:
        total = {k: v for k, v in indices[0].items() if k not in ("clave", "nombre")}  # un solo factor
    else:
        total = combinar(list(por_clave), irt.R_TOTAL)
    extras = []
    if bateria.verbal_noverbal:
        for nombre, es_verbal in (("CI verbal", True), ("CI no verbal", False)):
            comb = combinar([s["clave"] for s in subs if s["verbal"] == es_verbal], irt.R_TOTAL)
            if comb:
                extras.append({"nombre": nombre, **comb})
    return {"bateria": bateria.clave, "nombre_bateria": bateria.nombre, "edad": edad,
            "sd": bateria.sd, "subpruebas": subs, "indices": indices, "total": total,
            "extras": extras, "equivalente_15": round(100 + 15 * total["z"]) if total else None}

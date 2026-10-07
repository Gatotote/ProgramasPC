"""Pruebas verbales: vocabulario, analogías, semejanzas e información general.

Bancos propios (no son preguntas de ningún test comercial).
Formato de cada entrada: (enunciado, correcta, distractor, distractor, distractor, dificultad).
"""

from __future__ import annotations

import random

from . import Item, mezclar, por_dificultad

VOCABULARIO = [
    ("contento", "feliz", "triste", "cansado", "enojado", -3.0),
    ("grande", "enorme", "pequeño", "rápido", "suave", -2.8),
    ("comenzar", "empezar", "terminar", "olvidar", "correr", -2.4),
    ("cansado", "fatigado", "despierto", "alegre", "limpio", -2.2),
    ("veloz", "rápido", "lento", "fuerte", "alto", -2.0),
    ("hermoso", "bello", "feo", "frío", "duro", -2.0),
    ("pedir", "solicitar", "dar", "negar", "ocultar", -1.8),
    ("antiguo", "viejo", "nuevo", "roto", "lindo", -1.6),
    ("escaso", "poco", "mucho", "caro", "lejano", -1.5),
    ("obstinado", "terco", "amable", "flojo", "tímido", -0.8),
    ("lúgubre", "sombrío", "alegre", "ruidoso", "húmedo", -0.3),
    ("mesurado", "moderado", "desmedido", "furioso", "torpe", -0.2),
    ("sosegado", "tranquilo", "inquieto", "sediento", "sucio", 0.0),
    ("efímero", "pasajero", "eterno", "pequeño", "frágil", 0.2),
    ("perspicaz", "agudo", "torpe", "lento", "callado", 0.3),
    ("dádiva", "regalo", "deuda", "duda", "castigo", 0.4),
    ("diáfano", "transparente", "opaco", "oscuro", "pesado", 0.6),
    ("prolijo", "minucioso", "descuidado", "breve", "sencillo", 0.8),
    ("inefable", "indescriptible", "evidente", "común", "inútil", 0.9),
    ("ubicuo", "omnipresente", "escaso", "oculto", "inmóvil", 1.0),
    ("sempiterno", "eterno", "pasajero", "antiguo", "sereno", 1.0),
    ("acérrimo", "tenaz", "tibio", "ácido", "amargo", 1.1),
    ("exiguo", "insuficiente", "abundante", "exagerado", "ágil", 1.2),
    ("pusilánime", "cobarde", "valiente", "generoso", "orgulloso", 1.3),
    ("incólume", "ileso", "herido", "incómodo", "inculto", 1.4),
    ("conspicuo", "ilustre", "oscuro", "dudoso", "ordinario", 1.5),
    ("fatuo", "presuntuoso", "humilde", "sabio", "fatigado", 1.5),
    ("abyecto", "vil", "noble", "abierto", "tranquilo", 1.6),
    ("pertinaz", "obstinado", "breve", "pertinente", "débil", 1.7),
    ("procaz", "desvergonzado", "educado", "tímido", "pacífico", 1.8),
    ("inicuo", "injusto", "justo", "inicial", "inútil", 1.9),
    ("baladí", "insignificante", "importante", "bailable", "valioso", 2.0),
]

ANALOGIAS = [
    ("Perro es a ladrar como gato es a…", "maullar", "correr", "dormir", "comer", -2.8),
    ("Día es a noche como blanco es a…", "negro", "gris", "luz", "sol", -2.6),
    ("Lápiz es a escribir como tijeras es a…", "cortar", "papel", "coser", "pegar", -2.0),
    ("Pie es a zapato como mano es a…", "guante", "dedo", "brazo", "anillo", -2.0),
    ("Ojo es a ver como oído es a…", "oír", "ruido", "oreja", "música", -1.8),
    ("Pájaro es a nido como abeja es a…", "colmena", "flor", "miel", "árbol", -1.6),
    ("Médico es a hospital como maestro es a…", "escuela", "libro", "alumno", "pizarrón", -1.6),
    ("Lunes es a martes como enero es a…", "febrero", "diciembre", "mes", "año", -1.4),
    ("Agua es a sed como comida es a…", "hambre", "plato", "cocina", "sabor", -1.2),
    ("Pez es a agua como ave es a…", "aire", "pluma", "nido", "ala", -1.2),
    ("Reloj es a tiempo como termómetro es a…", "temperatura", "fiebre", "mercurio", "clima", -0.8),
    ("Libro es a autor como cuadro es a…", "pintor", "museo", "marco", "color", -0.6),
    ("Capitán es a barco como piloto es a…", "avión", "aeropuerto", "pasajero", "cielo", -0.6),
    ("Oruga es a mariposa como renacuajo es a…", "rana", "pez", "huevo", "charco", -0.4),
    ("Caliente es a frío como áspero es a…", "suave", "duro", "rugoso", "seco", -0.4),
    ("Semilla es a árbol como huevo es a…", "ave", "nido", "cáscara", "yema", -0.3),
    ("Kilómetro es a distancia como kilogramo es a…", "masa", "báscula", "gramo", "volumen", 0.0),
    ("Estrofa es a poema como capítulo es a…", "novela", "página", "autor", "párrafo", 0.2),
    ("Poeta es a verso como compositor es a…", "melodía", "piano", "orquesta", "canto", 0.3),
    ("Sequía es a agua como hambruna es a…", "alimento", "hambre", "pobreza", "campo", 0.4),
    ("Herbívoro es a plantas como piscívoro es a…", "peces", "carne", "insectos", "frutas", 0.6),
    ("Cobarde es a valor como ignorante es a…", "conocimiento", "escuela", "estupidez", "error", 0.8),
    ("Arquitecto es a plano como cocinero es a…", "receta", "cocina", "sartén", "mesero", 0.9),
    ("Mapa es a territorio como partitura es a…", "música", "papel", "director", "orquesta", 1.0),
    ("Agua es a hielo como lava es a…", "roca", "volcán", "fuego", "ceniza", 1.0),
    ("Milímetro es a metro como miligramo es a…", "gramo", "kilogramo", "litro", "tonelada", 1.1),
    ("Prólogo es a libro como obertura es a…", "ópera", "teatro", "telón", "final", 1.3),
    ("Miope es a lejos como présbita es a…", "cerca", "lentes", "ojo", "anciano", 1.6),
]

SEMEJANZAS = [
    ("un perro y un gato", "Son animales", "Ladran", "Tienen plumas", "Son plantas", -3.0),
    ("una manzana y un plátano", "Son frutas", "Son amarillos", "Son redondos", "Crecen bajo tierra", -2.8),
    ("una camisa y un pantalón", "Son ropa", "Tienen botones", "Son de lana", "Se usan en los pies", -2.4),
    ("un coche y una bicicleta", "Son medios de transporte", "Tienen motor", "Usan gasolina",
     "Tienen cuatro ruedas", -2.0),
    ("un piano y una guitarra", "Son instrumentos musicales", "Tienen teclas", "Se tocan soplando",
     "Son pequeños", -1.8),
    ("el ojo y el oído", "Son órganos de los sentidos", "Son redondos", "Tienen pestañas",
     "Sirven para comer", -1.2),
    ("el cobre y el hierro", "Son metales", "Son líquidos", "Son piedras preciosas", "Son de color rojo", -1.0),
    ("el norte y el oeste", "Son puntos cardinales", "Hace frío", "Son países", "Son opuestos", -0.8),
    ("una mosca y un árbol", "Son seres vivos", "Vuelan", "Tienen hojas", "Son insectos", -0.6),
    ("un reloj y una regla", "Son instrumentos de medición", "Tienen manecillas", "Son de madera",
     "Sirven para escribir", -0.4),
    ("un huevo y una semilla", "De ellos nace un nuevo ser vivo", "Son comida", "Tienen cáscara",
     "Son blancos", 0.0),
    ("un poema y una estatua", "Son obras de arte", "Están hechos de piedra", "Riman", "Están en museos", 0.3),
    ("el vapor y la niebla", "Son agua en el aire", "Son contaminación", "Son gases tóxicos",
     "Solo aparecen de noche", 0.5),
    ("la democracia y la monarquía", "Son formas de gobierno", "Tienen rey", "En ambas se vota",
     "Son países", 0.6),
    ("un amigo y un enemigo", "Son personas con las que tenemos una relación", "Se pelean con nosotros",
     "Nos ayudan", "Son familiares", 0.8),
    ("el elogio y el castigo", "Son respuestas a la conducta de alguien", "Son agradables", "Son regalos",
     "Son leyes", 1.0),
    ("la venganza y el perdón", "Son formas de responder a una ofensa", "Son sentimientos alegres",
     "Son delitos", "Son leyes", 1.2),
    ("la libertad y la justicia", "Son valores de la sociedad", "Son leyes escritas", "Son edificios",
     "Son lo mismo", 1.3),
    ("una hipótesis y una teoría", "Son explicaciones que intentan dar cuenta de los hechos",
     "Son leyes ya comprobadas", "Son experimentos", "Son opiniones sin fundamento", 1.5),
    ("el espacio y el tiempo", "Son dimensiones en las que ocurren los hechos", "Son planetas",
     "Se pueden comprar", "Solo existen en los libros", 1.8),
]

INFORMACION = [
    ("¿De qué color se ve el cielo en un día despejado?", "Azul", "Verde", "Rojo", "Café", -3.2),
    ("¿Qué animal da leche y hace «muu»?", "La vaca", "La cabra", "El caballo", "La oveja", -3.2),
    ("¿Cuántos días tiene una semana?", "7", "5", "10", "6", -3.0),
    ("¿Cuántos meses tiene un año?", "12", "10", "11", "13", -2.6),
    ("¿En qué estación del año hace más frío?", "Invierno", "Verano", "Primavera", "Otoño", -2.2),
    ("¿Qué órgano bombea la sangre?", "El corazón", "El pulmón", "El hígado", "El riñón", -2.0),
    ("¿Cuál es la capital de México?", "Ciudad de México", "Guadalajara", "Monterrey", "Puebla", -2.0),
    ("¿Cuántos lados tiene un hexágono?", "6", "5", "7", "8", -1.0),
    ("¿Qué planeta es conocido como el planeta rojo?", "Marte", "Venus", "Júpiter", "Saturno", -0.8),
    ("¿A qué temperatura hierve el agua a nivel del mar?", "100 °C", "50 °C", "80 °C", "120 °C", -0.8),
    ("¿Quién pintó la Mona Lisa?", "Leonardo da Vinci", "Pablo Picasso", "Vincent van Gogh",
     "Miguel Ángel", -0.6),
    ("¿Cuál es el océano más grande?", "Pacífico", "Atlántico", "Índico", "Ártico", -0.6),
    ("¿En qué año inició la Independencia de México?", "1810", "1910", "1821", "1492", -0.4),
    ("¿Quién escribió «Don Quijote de la Mancha»?", "Miguel de Cervantes", "Gabriel García Márquez",
     "Lope de Vega", "Octavio Paz", -0.2),
    ("¿Qué gas absorben las plantas para hacer la fotosíntesis?", "Dióxido de carbono", "Oxígeno",
     "Nitrógeno", "Helio", 0.0),
    ("¿Quién propuso la teoría de la relatividad?", "Albert Einstein", "Isaac Newton", "Galileo Galilei",
     "Charles Darwin", 0.0),
    ("¿En qué continente está Egipto?", "África", "Asia", "Europa", "Oceanía", 0.2),
    ("¿Cuál es el símbolo químico del oro?", "Au", "Ag", "Or", "Fe", 0.4),
    ("¿Quién propuso la evolución de las especies por selección natural?", "Charles Darwin",
     "Gregor Mendel", "Louis Pasteur", "Isaac Newton", 0.5),
    ("¿Quién escribió «Cien años de soledad»?", "Gabriel García Márquez", "Mario Vargas Llosa",
     "Julio Cortázar", "Jorge Luis Borges", 0.5),
    ("¿Qué presidente de México fue de origen zapoteco y promulgó las Leyes de Reforma?", "Benito Juárez",
     "Porfirio Díaz", "Lázaro Cárdenas", "Vicente Guerrero", 0.6),
    ("¿Cuál es el río más largo de América?", "Amazonas", "Misisipi", "Bravo", "Paraná", 0.6),
    ("¿Qué partícula del átomo tiene carga negativa?", "Electrón", "Protón", "Neutrón", "Núcleo", 0.8),
    ("¿Cuál es el hueso más largo del cuerpo humano?", "Fémur", "Tibia", "Húmero", "Peroné", 0.9),
    ("¿Qué obra escribió Homero?", "La Odisea", "La Eneida", "La Divina Comedia", "Hamlet", 1.0),
    ("¿Qué obra compuso Beethoven?", "La Novena Sinfonía", "Las cuatro estaciones", "La flauta mágica",
     "El lago de los cisnes", 1.1),
    ("¿Cuántos huesos tiene aproximadamente un adulto?", "206", "150", "312", "98", 1.2),
    ("¿Cuál es la capital de Australia?", "Canberra", "Sídney", "Melbourne", "Perth", 1.4),
    ("¿Qué filósofo fue maestro de Alejandro Magno?", "Aristóteles", "Platón", "Sócrates", "Pitágoras", 1.6),
    ("¿En qué siglo cayó Constantinopla en manos de los otomanos?", "XV", "XIII", "XVII", "X", 1.8),
]


def _items(rng: random.Random, banco: list, plantilla: str) -> list[Item]:
    items = []
    for enunciado, correcta, *distr, b in banco:
        opciones, idx = mezclar(rng, correcta, distr)
        items.append(Item("texto", plantilla.format(enunciado), b, idx, opciones, a=1.3))
    return por_dificultad(items)


def vocabulario(rng: random.Random) -> list[Item]:
    return _items(rng, VOCABULARIO, "¿Qué palabra significa lo mismo que «{}»?")


def analogias(rng: random.Random) -> list[Item]:
    return _items(rng, ANALOGIAS, "{}")


def semejanzas(rng: random.Random) -> list[Item]:
    return _items(rng, SEMEJANZAS, "¿En qué se parecen {}?")


def informacion(rng: random.Random) -> list[Item]:
    return _items(rng, INFORMACION, "{}")

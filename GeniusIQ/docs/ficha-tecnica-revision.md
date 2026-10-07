# GeniusIQ — Ficha técnica para revisión profesional

6 de octubre de 2026 · Preparada por Genaro Velasco · GeniusIQ v0.4.0

## Propósito y alcance

GeniusIQ es un programa de escritorio de uso **familiar y no clínico** que estima el CI, describe rasgos de personalidad y aplica tamizajes de salud mental. Antes de usarlo con mi familia (adolescentes y adultos) pido a un psicólogo o psiquiatra que revise su contenido, su calificación y sus avisos.

- **Autor:** Genaro Velasco (ingeniero mecatrónico, sin formación en psicología).
- **Versión revisada:** 0.4.0, programa en Python 3.13 + PySide6 para Linux. Funciona sin internet; los datos quedan solo en la computadora.
- **Uso previsto:** autoconocimiento y curiosidad en casa. **No** se usa para diagnóstico, para tomar decisiones escolares ni para contratar personal.
- **Usuarios:** adultos de la familia y menores de 6 a 17 años, siempre acompañados de un adulto.

El programa tiene tres módulos: inteligencia (5 baterías, 16 subpruebas), personalidad (6 cuestionarios) y tamizaje de salud mental (6 instrumentos). Este último **está bloqueado** con un aviso de «En revisión» hasta recibir su visto bueno.

## Qué pido revisar

Lo más urgente son los tamizajes de salud mental. Pueden marcar cada punto al terminarlo y anotar sus opiniones y correcciones directamente sobre este documento.

**Tamizaje de salud mental (prioridad)**

- [ ] Comparar mis traducciones del Anexo con las versiones oficiales en español (PHQ-9, GAD-7, ASRS, SNAP-IV, AUDIT, PCL-5). ¿Conviene sustituirlas por las validadas en México?
- [ ] Confirmar los puntos de corte y las reglas de calificación de la sección de tamizaje.
- [ ] Revisar el protocolo de la pregunta 9 del PHQ-9 y los teléfonos de crisis.
- [ ] Decidir edades mínimas: PHQ-9 y GAD-7 desde 12 años, ¿o usar versiones para adolescentes (PHQ-A, GAD-7 adolescente)?
- [ ] Revisar la redacción de resultados y recomendaciones: que no alarmen ni tranquilicen de más.

**Personalidad**

- [ ] HEXACO, Perfil laboral y Valores usan frases propias, sin validar: ¿claridad, carga de cada factor, sesgo de deseabilidad social?
- [ ] Las normas aproximadas del Big Five y del HEXACO: ¿son razonables para adultos mexicanos?
- [ ] ¿Es adecuado mostrar el Eneagrama y los 16 tipos con la advertencia de bajo respaldo científico, o conviene quitarlos?

**Inteligencia**

- [ ] Bancos verbales (vocabulario, analogías, semejanzas, información): adecuación cultural y dificultad para niños.
- [ ] Las curvas de normas por edad y las correlaciones supuestas entre subpruebas.
- [ ] Clasificaciones del CI y la forma de comunicarlas a un menor.

## Módulo de inteligencia

El CI se estima con teoría de respuesta al ítem y se compara con normas por edad **supuestas**, no con un baremo real. Las preguntas son propias; ninguna se copió de WAIS, WISC, Stanford-Binet ni Cattell.

**Baterías**

| Batería | Edades | Subpruebas | Índices |
| --- | --- | --- | --- |
| Rápido (mixto) | 6+ | 5 | Razonamiento, Verbal, Memoria de trabajo, Velocidad |
| Estilo WAIS-IV | 16–90 | 10 | Comprensión verbal, Razonamiento perceptivo, Memoria de trabajo, Velocidad de procesamiento |
| Estilo WISC-V | 6–16 | 10 | Comprensión verbal, Visoespacial, Razonamiento fluido, Memoria de trabajo, Velocidad |
| Estilo Stanford-Binet 5 | 6+ | 10 | 5 factores + CI verbal y CI no verbal |
| Estilo Cattell Culture Fair | 8+ | 4 | Factor g, con DE 24 como el original (y equivalente en DE 15) |

**Subpruebas y origen de los reactivos**

| Subprueba | Reactivos | Origen | Límite por reactivo |
| --- | --- | --- | --- |
| Vocabulario | 32 | Banco fijo propio | 30 s |
| Información general | 30 | Banco fijo propio | 30 s |
| Analogías verbales | 28 | Banco fijo propio | 40 s |
| Semejanzas | 20 | Banco fijo propio, opción múltiple | 40 s |
| Matrices de figuras | 17 | Generadas al azar | 90 s |
| Rotación mental | 14 | Generadas al azar | 40 s |
| Clasificación | 14 | Generadas al azar | 45 s |
| Series numéricas | 13 | Generadas al azar | 60 s |
| Balanzas | 12 | Generadas al azar | 60 s |
| Series de figuras | 12 | Generadas al azar | 45 s |
| Aritmética (mental) | 11 | Generadas al azar | 45 s |
| Condiciones (topología) | 8 | Generadas al azar | 60 s |
| Dígitos (directo e inverso) | Span creciente | Al azar | — |
| Bloques de Corsi | Span creciente | Al azar | — |
| Búsqueda de símbolos | Tiempo fijo | Al azar | 2 min en total |
| Claves | Tiempo fijo | Al azar | 90 s en total |

**Calificación**

1. Cada reactivo tiene una dificultad *b* asignada a mano en la escala de un adulto joven (media 0, DE 1), de −3.2 a +2.3. La discriminación *a* es fija por subprueba (1.3 a 1.5). El parámetro de azar *c* es 1 / número de opciones.
2. Los reactivos van de fácil a difícil; el inicio depende de la edad y la subprueba se suspende tras 3 errores seguidos.
3. La capacidad θ se estima por EAP con el modelo logístico de 3 parámetros y una a priori normal centrada en lo típico para la edad: **P(acierto | θ) = c + (1 − c) / (1 + e^(−a·(θ − b)))**.
4. **Normas por edad (supuestas):** de 5 a 17 años, θ típico sube linealmente hasta el adulto joven (de −3.0 en conocimiento a −2.0 en memoria a los 5 años). Después de los 30, razonamiento, memoria y visoespacial bajan 0.022 DE por año. El conocimiento sube 0.008 DE por año de 25 a 65.
5. Memoria: span medio de adulto joven de 6.5 (directo), 4.9 (inverso) y 5.6 (Corsi), con DE de 1.1 a 1.2. Velocidad: aciertos netos contra una media supuesta (48 y 52) con un factor de edad.
6. Puntuación escalar = 10 + 3z, acotada de 1 a 19. Índices y CI total combinan las z suponiendo una correlación r de 0.60 dentro de un índice y de 0.45 entre todas: **z compuesto = Σ zᵢ / √(k + k·(k − 1)·r)**.
7. CI = 100 + 15z (24 en Cattell), con percentil e intervalo del 90 %. Clasificación: ≥130 Muy superior, 120 Superior, 110 Medio alto, 90 Medio, 80 Medio bajo, 70 Limítrofe, <70 Muy bajo.

## Módulo de personalidad

Dos cuestionarios vienen de bancos libres (Big Five y 16 tipos); los otros cuatro usan frases que escribí yo y **no tienen validación ni normas propias**. Todos son de autoinforme en escala de 1 a 5 y la persona puede regresar a corregir respuestas.

| Cuestionario | Reactivos | Fuente de los reactivos | Edad | Resultado |
| --- | --- | --- | --- | --- |
| Big Five (OCEAN) | 120 (24 por dominio, 4 por faceta) | IPIP-NEO-120 (Johnson, 2014), dominio público; traducción propia | 14+ | 5 dominios con percentil + 30 facetas (0–100) |
| HEXACO | 72 (12 por factor, 3 por faceta) | Frases propias sobre el modelo de Ashton y Lee; no es el HEXACO-PI-R | 14+ | 6 factores con percentil + 24 facetas |
| 16 tipos (estilo MBTI) | 32 pares bipolares | OEJTS 1.2 (Jorgenson), Creative Commons; traducción propia | 12+ | Código de 4 letras + claridad de cada preferencia |
| Eneagrama | 45 (5 por tipo) | Frases propias; sin respaldo científico, se avisa | 12+ | Tipo principal, ala y puntaje de los 9 tipos |
| Perfil laboral | 64 (8 rasgos × 5 + 8 riesgos × 3) | Frases propias; rasgos al estilo Gordon/SOSIE y riesgos al estilo Hogan HDS | 16+ | Puntaje 0–100 por escala, sin normas |
| Valores | 48 (12 valores × 4) | Frases propias; escalas de Gordon SIV/SPV | 14+ | Orden de prioridades (ipsativo) |

**Calificación**

- **Big Five y HEXACO:** promedio por dominio (con reactivos inversos), convertido a percentil con una media y DE supuestas por reactivo. Big Five: N 2.75/0.65, E 3.35/0.55, O 3.45/0.50, A 3.80/0.50, C 3.65/0.55. HEXACO: H 3.30/0.60, E 3.20/0.60, X 3.40/0.60, A 3.05/0.60, C 3.50/0.55, O 3.35/0.65. Nivel: Bajo < 30, Medio 30–69, Alto ≥ 70.
- **16 tipos:** cada par suma de −2 a +2 hacia un polo; 8 pares por dimensión. La claridad es |suma| / 16. Un empate da la segunda letra.
- **Eneagrama:** suma por tipo; el ala es el tipo vecino con más puntos.
- **Perfil laboral:** promedio por escala llevado a 0–100. Rasgo Alto ≥ 70 y Bajo ≤ 40. Riesgo Alto ≥ 75 y Moderado ≥ 55.
- **Valores:** promedio de importancia por valor menos el promedio general de la persona (como en el PVQ de Schwartz). Si la diferencia entre el valor más alto y el más bajo es menor de 0.5, el programa avisa que el orden no es interpretable.

## Tamizaje de salud mental

Se usan los seis instrumentos reales, todos de uso libre, con sus reglas de calificación publicadas. Lo único propio es la traducción al español de México (texto completo en el Anexo). Respuestas sin omitir: el programa no avanza hasta contestar.

| Instrumento | Licencia | Reactivos y escala | Periodo | Edad en el programa | Cortes usados | Positivo si |
| --- | --- | --- | --- | --- | --- | --- |
| PHQ-9 (depresión) | Dominio público (Pfizer) | 9, de 0 a 3 | Últimas 2 semanas | 12+ | 0 Mínima, 5 Leve, 10 Moderada, 15 Moderadamente grave, 20 Grave | Total ≥ 10, o pregunta 9 > 0 (alerta aparte) |
| GAD-7 (ansiedad) | Dominio público (Pfizer) | 7, de 0 a 3 | Últimas 2 semanas | 12+ | 0 Mínima, 5 Leve, 10 Moderada, 15 Grave | Total ≥ 10 |
| ASRS v1.1 completo (TDAH, adultos) | OMS, uso libre | 18, de 0 a 4 | Últimos 6 meses | 18+ | Parte A: casillas sombreadas | 4 o más de las 6 de la parte A |
| SNAP-IV-26 (TDAH, niños) | Distribución libre (Swanson) | 1 de informante + 26, de 0 a 3 | Últimos 6 meses | 6–17, lo contesta un adulto | Promedios de Swanson por informante (abajo) | Suma TDAH ≥ corte, o desatención o hiperactividad ≥ su corte |
| AUDIT (alcohol) | OMS, uso libre | 10; 1–8 de 0 a 4, 9–10 valen 0, 2 o 4 | Último año | 18+ | Zona I 0, II 8, III 16, IV 20 | Total ≥ 8 |
| PCL-5 (estrés postraumático) | Dominio público (National Center for PTSD) | 20, de 0 a 4 | Último mes | 18+ | 0 Bajo, 20 Moderado, 33 Probable TEPT | Total ≥ 33 |

**Reglas adicionales**

- **ASRS:** cuentan desde «Algunas veces» las preguntas 1, 2, 3, 9, 12, 16 y 18; las demás, desde «Con frecuencia». Las 18 se agrupan en desatención (1–4, 7–11) e hiperactividad/impulsividad (5–6, 12–18). El programa informa cuántos síntomas de cada grupo caen en zona de alerta y menciona el umbral de 5 del DSM-5 solo como referencia.
- **SNAP-IV:** la primera pregunta registra quién contesta. Cortes del promedio por grupo: padres — desatención 1.78, hiperactividad 1.44, oposicionismo 1.88, TDAH combinado 1.67 (suma ≥ 30 de 54); maestro — 2.56, 1.78, 1.38 y 2.00 (suma ≥ 36). Una conducta cuenta como presente en «Bastante» o «Mucho»; con 6 o más en un grupo se menciona la presentación probable.
- **AUDIT:** alerta aparte si las preguntas 4 a 6 (dependencia) suman 4 o más. Con 5 a 7 puntos se avisa que en mujeres y mayores de 65 años suele usarse un corte más bajo. Bebida estándar definida como cerveza de 355 ml, copa de vino de 140 ml o caballito de 45 ml.
- **PCL-5:** grupos B (1–5), C (6–7), D (8–14) y E (15–20). Se informa si se cumple el patrón del DSM-5 (síntoma presente ≥ 2: al menos 1 B, 1 C, 2 D y 2 E) aunque el total no llegue a 33. Si la pregunta 16 (conductas de riesgo) vale 2 o más, sale un aviso para mencionarlo en la valoración.

**Pantalla de resultado:** puntaje, nivel, una barra por zonas (verde a rojo), la recomendación, las alertas, los subtotales por grupo y el aviso de que un tamizaje no es un diagnóstico.

## Salvaguardas

El módulo de salud mental queda bloqueado hasta que ustedes lo aprueben; el resto lleva avisos de que no es un diagnóstico.

- **Candado de revisión:** mientras no haya visto bueno, cada tamizaje muestra «En revisión: no lo uses con la familia» y pide confirmación antes de empezar. Se quita cambiando un solo valor en el código.
- **Crisis (PHQ-9, pregunta 9 > 0):** aunque el total sea bajo, el resultado muestra hasta arriba la Línea de la Vida (800 911 2000, 24 horas), SAPTEL (55 5259 8121) y el 911, y recomienda buscar ayuda ese mismo día.
- **Menores de edad:** antes de un tamizaje, el programa pide que un adulto de confianza acompañe y vea el resultado. El SNAP-IV lo contesta el adulto, no el niño.
- **Fuera de rango de edad:** se avisa en la pantalla de inicio, en la confirmación y en el resultado.
- **Avisos permanentes:** el CI se presenta como «estimación casera, no diagnóstico»; la personalidad, como «estilos sin resultados buenos ni malos»; los tamizajes, como «detección: un puntaje alto indica platicarlo con un profesional; uno bajo no descarta un problema».
- **Privacidad:** respuestas y resultados se guardan solo en la computadora (base SQLite local), sin internet ni cuentas. Cualquier sesión se puede borrar desde el historial.

## Limitaciones conocidas y decisiones abiertas

La limitación principal es que nada está normado ni validado en población mexicana: los números sirven para comparar a una persona consigo misma, no para clasificarla.

- **CI:** las dificultades *b*, las curvas por edad y las correlaciones entre subpruebas son estimaciones mías, no datos. Sin calibración, el error real es mayor que el intervalo del 90 % que se muestra.
- **Bancos verbales:** son pequeños (20 a 32 reactivos) y fijos, así que se pueden aprender si se repite la prueba. Pueden tener sesgo cultural o escolar.
- **Personalidad:** las normas del Big Five y del HEXACO son aproximadas y de adultos, aunque se aplican desde los 14 años. Las escalas propias no tienen confiabilidad medida.
- **Tamizajes:** las traducciones no son las validadas en español. El ASRS y el AUDIT se limitan a 18+ aunque existen usos en adolescentes. No hay versión para adolescentes del PHQ-9 ni del GAD-7.
- **Historial sin contraseña:** quien use la computadora puede ver los resultados de los menores.

**Decisiones que quiero tomar con ustedes**

1. ¿Usar las versiones oficiales en español de los tamizajes en lugar de mis traducciones?
2. ¿Qué instrumentos permitir en menores de edad y con qué acompañamiento?
3. ¿Mostrar el número de CI a un menor, o solo una descripción cualitativa?
4. ¿Proteger el historial con contraseña o esconder los tamizajes de los menores?
5. ¿Qué hacer en casa ante un resultado positivo: a quién acudir y en cuánto tiempo?

## Anexo: reactivos de los tamizajes

Texto exacto que ve la persona, en el orden en que aparece. Entre paréntesis, el valor de cada opción.

### PHQ-9 (depresión)

*Instrucción:* Durante las últimas 2 semanas, ¿con qué frecuencia te han molestado estos problemas?

*Opciones:* Nunca (0) · Varios días (1) · Más de la mitad de los días (2) · Casi todos los días (3)

1. Poco interés o gusto por hacer las cosas.
2. Sentirte decaído(a), deprimido(a) o sin esperanza.
3. Problemas para dormirte o para seguir dormido(a), o dormir demasiado.
4. Sentirte cansado(a) o con poca energía.
5. Poco apetito o comer en exceso.
6. Sentirte mal contigo mismo(a): que eres un fracaso o que les has fallado a ti o a tu familia.
7. Dificultad para concentrarte en cosas como leer o ver la televisión.
8. Moverte o hablar tan despacio que otras personas lo notaron; o lo contrario: estar tan inquieto(a) que te has movido mucho más de lo normal.
9. Pensar que estarías mejor muerto(a) o que quieres hacerte daño de alguna manera.

### GAD-7 (ansiedad)

*Instrucción:* Durante las últimas 2 semanas, ¿con qué frecuencia te han molestado estos problemas?

*Opciones:* Nunca (0) · Varios días (1) · Más de la mitad de los días (2) · Casi todos los días (3)

1. Sentirte nervioso(a), ansioso(a) o con los nervios de punta.
2. No poder dejar de preocuparte o no poder controlar la preocupación.
3. Preocuparte demasiado por diferentes cosas.
4. Dificultad para relajarte.
5. Estar tan inquieto(a) que te cuesta quedarte quieto(a).
6. Molestarte o irritarte con facilidad.
7. Sentir miedo, como si algo terrible fuera a pasar.

### ASRS (TDAH en adultos)

*Instrucción:* Piensa en los últimos 6 meses, en el trabajo, la escuela o la casa.

*Opciones:* Nunca (0) · Rara vez (1) · Algunas veces (2) · Con frecuencia (3) · Muy seguido (4)

1. ¿Con qué frecuencia te cuesta terminar los detalles finales de un proyecto, una vez que ya hiciste las partes difíciles?
2. ¿Con qué frecuencia te cuesta poner las cosas en orden cuando haces una tarea que requiere organización?
3. ¿Con qué frecuencia tienes problemas para acordarte de citas u obligaciones?
4. Cuando tienes una tarea que requiere pensar mucho, ¿con qué frecuencia evitas empezarla o la retrasas?
5. ¿Con qué frecuencia mueves o retuerces las manos o los pies cuando tienes que estar sentado(a) mucho tiempo?
6. ¿Con qué frecuencia te sientes demasiado activo(a) y con necesidad de hacer cosas, como si tuvieras un motor por dentro?
7. ¿Con qué frecuencia cometes errores por descuido cuando trabajas en algo aburrido o difícil?
8. ¿Con qué frecuencia te cuesta mantener la atención cuando haces un trabajo aburrido o repetitivo?
9. ¿Con qué frecuencia te cuesta concentrarte en lo que te dicen, aun cuando te hablan directamente?
10. ¿Con qué frecuencia pierdes cosas o te cuesta encontrarlas en la casa o en el trabajo?
11. ¿Con qué frecuencia te distraen la actividad o el ruido a tu alrededor?
12. ¿Con qué frecuencia te levantas de tu lugar en juntas u otras situaciones en las que se espera que sigas sentado(a)?
13. ¿Con qué frecuencia te sientes intranquilo(a) o inquieto(a)?
14. ¿Con qué frecuencia te cuesta calmarte y relajarte cuando tienes tiempo para ti?
15. ¿Con qué frecuencia hablas de más en reuniones con otras personas?
16. Cuando platicas con alguien, ¿con qué frecuencia terminas sus frases antes de que lo haga la otra persona?
17. ¿Con qué frecuencia te cuesta esperar tu turno en situaciones en las que hay que hacerlo?
18. ¿Con qué frecuencia interrumpes a otros cuando están ocupados?

### SNAP-IV (TDAH en niños)

*Instrucción:* Lo contesta un adulto que conozca bien al niño o adolescente, pensando en cómo se ha comportado en los últimos 6 meses.

*Pregunta inicial:* ¿Quién contesta este cuestionario? [Papá, mamá o tutor · Maestro(a)]

*Opciones:* Nada (0) · Un poco (1) · Bastante (2) · Mucho (3)

1. A menudo no pone atención a los detalles o comete errores por descuido en sus tareas o trabajos.
2. A menudo le cuesta mantener la atención en tareas o juegos.
3. A menudo parece no escuchar cuando se le habla directamente.
4. A menudo no sigue las instrucciones y no termina las tareas de la escuela, los encargos o sus obligaciones.
5. A menudo le cuesta organizar tareas y actividades.
6. A menudo evita, le disgustan o hace de mala gana las tareas que requieren esfuerzo mental sostenido.
7. A menudo pierde cosas que necesita (juguetes, tareas, lápices, libros…).
8. A menudo se distrae con cualquier cosa a su alrededor.
9. A menudo es olvidadizo(a) en las actividades diarias.
10. A menudo mueve las manos o los pies, o se retuerce en el asiento.
11. A menudo se levanta de su lugar en el salón o en otras situaciones en que debe quedarse sentado(a).
12. A menudo corre o se trepa en exceso en situaciones en que no es apropiado.
13. A menudo le cuesta jugar o hacer actividades de tiempo libre en silencio.
14. A menudo está «en movimiento» o actúa como si tuviera «un motor».
15. A menudo habla en exceso.
16. A menudo suelta las respuestas antes de que terminen de hacerle la pregunta.
17. A menudo le cuesta esperar su turno.
18. A menudo interrumpe o se mete en lo que hacen otros (conversaciones, juegos).
19. A menudo pierde los estribos.
20. A menudo discute con los adultos.
21. A menudo desafía o se niega a cumplir lo que piden los adultos o las reglas.
22. A menudo hace cosas a propósito para molestar a los demás.
23. A menudo culpa a otros de sus errores o de su mal comportamiento.
24. A menudo es susceptible o se molesta fácilmente con los demás.
25. A menudo está enojado(a) o resentido(a).
26. A menudo es rencoroso(a) o vengativo(a).

### AUDIT (alcohol)

*Instrucción:* Una bebida estándar = una cerveza de 355 ml, una copa de vino de 140 ml o un caballito de 45 ml de tequila, mezcal, ron, etc. Si no tomas, contesta «Nunca» y la primera opción.

1. ¿Con qué frecuencia tomas alguna bebida que contenga alcohol?  [Nunca (0) · Una vez al mes o menos (1) · 2 a 4 veces al mes (2) · 2 o 3 veces a la semana (3) · 4 o más veces a la semana (4)]
2. Los días que tomas, ¿cuántas bebidas estándar sueles tomar?  [No tomo, o 1 o 2 (0) · 3 o 4 (1) · 5 o 6 (2) · 7 a 9 (3) · 10 o más (4)]
3. ¿Con qué frecuencia tomas 6 o más bebidas estándar en una sola ocasión?  [Nunca (0) · Menos de una vez al mes (1) · Una vez al mes (2) · Cada semana (3) · Diario o casi diario (4)]
4. En el último año, ¿con qué frecuencia no pudiste parar de beber una vez que empezaste?  [Nunca (0) · Menos de una vez al mes (1) · Una vez al mes (2) · Cada semana (3) · Diario o casi diario (4)]
5. En el último año, ¿con qué frecuencia dejaste de hacer lo que se esperaba de ti por haber bebido?  [Nunca (0) · Menos de una vez al mes (1) · Una vez al mes (2) · Cada semana (3) · Diario o casi diario (4)]
6. En el último año, ¿con qué frecuencia necesitaste beber en la mañana para sentirte bien después de haber bebido mucho el día anterior?  [Nunca (0) · Menos de una vez al mes (1) · Una vez al mes (2) · Cada semana (3) · Diario o casi diario (4)]
7. En el último año, ¿con qué frecuencia te sentiste culpable o con remordimiento después de beber?  [Nunca (0) · Menos de una vez al mes (1) · Una vez al mes (2) · Cada semana (3) · Diario o casi diario (4)]
8. En el último año, ¿con qué frecuencia no pudiste recordar lo que pasó la noche anterior porque habías bebido?  [Nunca (0) · Menos de una vez al mes (1) · Una vez al mes (2) · Cada semana (3) · Diario o casi diario (4)]
9. ¿Tú u otra persona han resultado heridos porque habías bebido?  [No (0) · Sí, pero no en el último año (2) · Sí, en el último año (4)]
10. ¿Algún familiar, amigo, médico u otro profesional de la salud se ha preocupado por tu forma de beber o te ha sugerido que tomes menos?  [No (0) · Sí, pero no en el último año (2) · Sí, en el último año (4)]

### PCL-5 (estrés postraumático)

*Instrucción:* Piensa en la experiencia más estresante que hayas vivido (accidente, violencia, desastre, muerte repentina de alguien cercano…). En el ÚLTIMO MES, ¿cuánto te molestó cada problema?

*Opciones:* Nada (0) · Un poco (1) · Moderadamente (2) · Bastante (3) · Extremadamente (4)

1. Recuerdos repetidos, perturbadores e involuntarios de la experiencia estresante.
2. Sueños repetidos y perturbadores sobre la experiencia estresante.
3. Sentir o actuar de repente como si la experiencia estresante estuviera pasando otra vez (como si estuvieras ahí reviviéndola).
4. Sentirte muy alterado(a) cuando algo te recordó la experiencia estresante.
5. Tener reacciones físicas fuertes cuando algo te recordó la experiencia (por ejemplo, el corazón acelerado, dificultad para respirar, sudor).
6. Evitar recuerdos, pensamientos o sentimientos relacionados con la experiencia.
7. Evitar cosas que te la recuerdan (por ejemplo, personas, lugares, conversaciones, actividades, objetos o situaciones).
8. Dificultad para recordar partes importantes de la experiencia.
9. Tener creencias negativas fuertes sobre ti, los demás o el mundo (por ejemplo: «soy malo(a)», «algo está muy mal en mí», «no se puede confiar en nadie», «el mundo es muy peligroso»).
10. Culparte a ti o a alguien más por la experiencia o por lo que pasó después.
11. Tener sentimientos negativos fuertes, como miedo, horror, enojo, culpa o vergüenza.
12. Perder el interés en actividades que antes disfrutabas.
13. Sentirte distante o aislado(a) de otras personas.
14. Dificultad para sentir emociones positivas (por ejemplo, no poder sentir alegría o cariño por las personas cercanas).
15. Estar irritable, tener arranques de enojo o actuar de forma agresiva.
16. Arriesgarte demasiado o hacer cosas que te podrían hacer daño.
17. Estar «en alerta», vigilante o en guardia.
18. Sentirte nervioso(a) o asustarte con facilidad.
19. Dificultad para concentrarte.
20. Problemas para dormirte o seguir dormido(a).


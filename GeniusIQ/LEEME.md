# GeniusIQ

Estimación **casera y no clínica** del cociente intelectual (CI). Programa de escritorio
(Python 3.13 + PySide6), hecho por Genaro Velasco.

> Los tests reales (WAIS, WISC, Stanford-Binet, Cattell) los aplica un psicólogo con material
> y baremos oficiales, y sus preguntas tienen derechos de autor. Aquí las preguntas son
> **propias** (generadas por el programa o de bancos escritos para él) y las normas por edad
> son **aproximadas**. Sirve para curiosidad y práctica, no para diagnóstico ni contratación.

## Abrir

- Icono «GeniusIQ» en el escritorio, o `./ejecutar.sh` (usa `uv`).
- `./ejecutar.sh --version` muestra la versión.

## Modos (baterías)

| Modo | Edades | Índices |
|---|---|---|
| Rápido (mixto) | 6+ | Razonamiento, Verbal, Memoria de trabajo, Velocidad |
| Estilo WAIS-IV | 16–90 | Comprensión verbal, Razonamiento perceptivo, Memoria de trabajo, Velocidad de procesamiento |
| Estilo WISC-V | 6–16 | Comprensión verbal, Visoespacial, Razonamiento fluido, Memoria de trabajo, Velocidad |
| Estilo Stanford-Binet 5 | 6+ | 5 factores + CI verbal y CI no verbal |
| Estilo Cattell Culture Fair | 8+ | Factor g (solo figuras). CI con desviación 24, como el original, y su equivalente en escala 15 |

Al elegir un modo se pueden quitar subpruebas. El historial queda por persona.

## Personalidad (desde v0.2.0)

| Cuestionario | Preguntas | Qué da | Fuente |
|---|---|---|---|
| Big Five (OCEAN) | 120 | 5 rasgos con percentil aproximado + 30 facetas | IPIP-NEO-120 (Johnson 2014), dominio público; traducción propia |
| 16 tipos (estilo MBTI) | 32 pares | Código de 4 letras + claridad de cada preferencia | OEJTS 1.2 (Jorgenson), Creative Commons; NO es el MBTI® |
| Eneagrama | 45 | Tipo principal + ala + puntaje de los 9 tipos | Preguntas propias, sin respaldo científico |

Desde v0.3.0 (etapa 2):

| Cuestionario | Preguntas | Qué da | Fuente |
|---|---|---|---|
| HEXACO | 72 | 6 factores (incluye Honestidad-Humildad) con percentil aproximado + 24 facetas | Preguntas propias sobre el modelo de Ashton y Lee; NO es el HEXACO-PI-R |
| Perfil laboral | 64 | 8 rasgos para el trabajo + 8 riesgos bajo presión (0–100, sin normas) | Preguntas propias; inspirado en Gordon/SOSIE y Hogan (HDS) |
| Valores | 48 | Orden de prioridades de 12 valores (6 interpersonales, 6 personales) | Preguntas propias; escalas de Gordon SIV/SPV, calificación ipsativa como el PVQ de Schwartz |

Se contestan con botones o las teclas 1–N (cada cuestionario define sus opciones; en el AUDIT
cambian por pregunta); «← Anterior» (o ←) para corregir. El historial guarda las respuestas y el
resultado. Los percentiles del Big Five y del HEXACO usan promedios aproximados de adultos
(`NORMAS` en cada archivo).

## Salud mental: tamizaje (desde v0.3.0, etapa 3)

| Cuestionario | Preguntas | Corte | Edad |
|---|---|---|---|
| PHQ-9 (depresión) | 9 | 5/10/15/20; positivo ≥10; pregunta 9 > 0 → aviso de crisis | 12+ |
| GAD-7 (ansiedad) | 7 | 5/10/15; positivo ≥10 | 12+ |
| ASRS v1.1 parte A (TDAH adultos) | 6 | 4+ respuestas en zona sombreada | 18+ |
| AUDIT (alcohol) | 10 | Zonas 8/16/20; aviso si 4–6 suman ≥4 | 18+ |
| PCL-5 (estrés postraumático) | 20 | ≥33 + patrón de grupos DSM-5 (B1, C1, D2, E2) | 18+ |

Todos son de uso libre (dominio público u OMS). Traducción propia: **falta que la revisen
psicólogos/psiquiatras** contra las versiones oficiales en español. Mientras tanto
`salud/__init__.py` tiene `REVISADO = False` y el programa muestra «En revisión» y pide
confirmación antes de empezar. Si alguien marca la pregunta 9 del PHQ-9, el resultado muestra la
Línea de la Vida (800 911 2000), SAPTEL y el 911.

## Subpruebas

Matrices, series numéricas, analogías, semejanzas, vocabulario, información general,
aritmética, balanzas, rotación mental, condiciones (topología), series de figuras,
clasificación, retención de dígitos (directo e inverso), bloques de Corsi, búsqueda de
símbolos y claves.

Las de figuras y números se **generan al azar** cada vez (no se repiten), con nivel de
dificultad controlado. Las verbales salen de bancos fijos en `geniusiq/generadores/verbal.py`.

## Cómo calcula el CI

1. Cada pregunta tiene una dificultad `b` (escala de un adulto joven: media 0, desviación 1).
2. Las preguntas se aplican de fácil a difícil, empezando según la edad, y la subprueba se
   suspende tras 3 errores seguidos (como en Wechsler).
3. La capacidad se estima con **teoría de respuesta al ítem** (modelo logístico de 3
   parámetros, estimación EAP); el parámetro de azar es 1/número de opciones.
4. Se compara con lo típico para la edad (`irt.ref_edad`: desarrollo en niños, leve
   descenso de razonamiento/memoria/velocidad después de los 30) → puntuación z.
5. Subprueba → puntuación escalar 1–19 (media 10). Índices y CI total combinan las z
   considerando la correlación entre subpruebas → CI = 100 + 15·z (24 en Cattell).
6. Se muestran percentil, clasificación y un rango probable del 90 %.

Las velocidades (búsqueda, claves) usan aciertos − errores contra una media supuesta.

## Archivos

- `geniusiq/irt.py` — modelo estadístico y normas por edad.
- `geniusiq/baterias.py` — subpruebas, baterías y cálculo de resultados.
- `geniusiq/generadores/` — preguntas (matrices, figurales, numéricos, verbal).
- `geniusiq/figuras.py` — dibujo de figuras (QPainter).
- `geniusiq/personalidad/` — cuestionarios de personalidad y su calificación (`factores.py`: común a Big Five y HEXACO).
- `geniusiq/salud/` — tamizajes de salud mental (`tamizajes.py`) y avisos de crisis.
- `geniusiq/ui/` — interfaz.
- Datos: `~/.local/share/geniusiq/geniusiq.db` (SQLite). La variable `GENIUSIQ_DB` cambia la ruta
  (útil para pruebas).

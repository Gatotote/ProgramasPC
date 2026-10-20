# Teclado Mágico

Programa para bebés (hecho para mi hijo pequeño). Pantalla completa: cada tecla hace
aparecer algo con su sonido.

- **Letras** → la letra gigante + un animal o cosa que empieza con ella y la palabra
  (G 🐱 gato, Ñ 🦬 ñu…). Si aprieta la misma letra seguida
  va en ciclos de 6: cinco veces su nota musical (siempre la misma por letra) y la sexta una voz dice «¡Ge!… gato».
- **Números** → el número + esa cantidad de animalitos para contar (0 = 10) y la voz dice
  «¡Tres!», con el mismo ciclo de 6 que las letras.
- **Espacio / Enter** → lluvia de confeti con arpegio.
- **Cualquier otra tecla** → figura con carita o un animal/cosa al azar con «boing».
- **Ratón** → estela de colores; clic = confeti.

Las notas son de la escala pentatónica (nunca suena feo aunque aplaste todo el
teclado) y se limitan a 3 sonidos cada 0.12 s para que no truene.

## Cerrar

Escribir **`salir`** en el teclado. Alt+F4 y la «X» no lo cierran a propósito.

## Bloqueo de atajos

- El programa aparta el teclado (SDL en Wayland nativo → KWin respeta el «keyboard shortcuts
  inhibit»). Se pide cada vez que la ventana recibe el foco; antes de eso KWin lo ignora.
- `SDL_ALLOW_ALT_TAB_WHILE_GRABBED=0`: si no, **SDL mismo minimiza la ventana con Alt+Tab**, y la
  **F3 del Logitech K400 Plus manda Alt+Tab** (macro del teclado: Alt abajo, Tab, Alt arriba ~1 s después).
- Además `ejecutar.sh` apaga los atajos globales (`blockGlobalShortcuts`) y la tecla Meta sola
  (`kwinrc [ModifierOnlyShortcuts] Meta=`), y al salir lo regresa todo como estaba.
  Si se cerró de golpe, `herramientas/restaurar-al-iniciar.sh` (autoarranque de KDE) regresa la tecla Meta.

Diagnóstico:
- Registro de la última sesión (teclas, foco, cierre): `~/.cache/tecladomagico/ultima-sesion.log`.
- Qué manda de verdad un teclado: `sudo python3 herramientas/escuchar_teclado.py 20`.

## Uso

```sh
./ejecutar.sh             # pantalla completa
./ejecutar.sh --ventana   # en ventana, sin bloquear el teclado (pruebas)
./ejecutar.sh --version
```

Lanzador: `tecladomagico.desktop` (copiado al Escritorio).
Sin imágenes: todo se dibuja (emojis de Noto Color Emoji). Las notas se sintetizan; la voz son
WAV en `tecladomagico/voz/` hechos con Piper (voz `es_MX-claude-high`, sin internet) por
`herramientas/generar_voz.py` — el modelo se baja a `herramientas/modelos/` (no va al repo).

## Licencia

[MIT](LICENSE) — se puede usar, copiar, modificar y compartir libremente, siempre que se conserve la mención del autor. Este programa fue realizado por **Genaro Velasco**.

Dependencias: pygame-ce (LGPL-2.1) y numpy (BSD). Las voces de Piper tienen cada una su propia licencia (ver la ficha de cada voz) y piper-tts solo se usa para generarlas.

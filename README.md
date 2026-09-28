# EstrésPC

Pruebas de estrés para Linux con ventana gráfica: CPU, RAM, GPU, video 4K y disco, con
gráficas en vivo, límites de temperatura y detección de errores.

## Uso

    ./ejecutar.sh            # o el icono «EstrésPC» del escritorio / menú
    ./ejecutar.sh --version

Requisitos del sistema: `stress-ng`, `nvidia-smi` (opcional, para leer la GPU
NVIDIA), un driver OpenCL (`opencl-nvidia`), `7zip` (benchmark) y `glmark2`
(opcional, en las filas). Dependencias de Python con `uv` (incluye `moderngl` para el render 3D).

## Qué hace cada prueba

| Prueba | Motor | Cómo detecta errores |
|---|---|---|
| CPU | `stress-ng --cpu` (matrices, FFT, primos o mixto) | `--verify`: revisa cada resultado |
| RAM | `stress-ng --vm --vm-method all` sobre un % de la RAM libre | `--verify`: escribe patrones y los relee |
| GPU | `estrespc/gpu_trabajador.py` (OpenCL, mapa logístico con `fma`) | Elementos gemelos deben dar los mismos bits; el caos amplifica cualquier bit volteado (cómputo o VRAM) |
| Video 4K | `estrespc/video_trabajador.py`: varios `ffmpeg` decodificando 4K 60 fps en bucle con NVDEC, lo más rápido posible (opcional: recodificar con NVENC y ver uno en `mpv`) | Errores de decodificación que reporta `ffmpeg` |
| Disco | `stress-ng --hdd` con E/S directa (sin caché) | `--verify`: relee lo escrito; borra sus archivos al terminar |

Protección: si la CPU, GPU o un SSD pasan su límite 3 segundos seguidos, se
detiene todo. Avisa si el equipo está con batería.

## Videos 4K (sin derechos de autor)

Se guardan en `~/.local/share/estrespc/videos/` (puedes poner los tuyos ahí):

- **Generados en tu equipo** (botón «Generar videos 4K de prueba»): 15 s de
  4K 60 fps con mucho detalle en H.264, HEVC 10 bits y AV1 (~450 MB en total).
  Los hizo tu propio equipo, así que no tienen derechos de autor de nadie.
- **Big Buck Bunny 4K 60 fps** (672 MB), de la Blender Foundation, con licencia
  CC BY 3.0: se puede usar libremente dando crédito (queda en `CREDITOS.txt`).

Cada video 4K ocupa ~600 MB de VRAM (~1 GB si se recodifica, ~1.6 GB la
ventana de mpv). Si corre junto con la prueba GPU, esta usa menos VRAM
automáticamente para que quepan los videos.

## Fila de tareas (desde v0.4.0)

En vez de una sola carga fija, una **secuencia de pasos que se repite** hasta cumplir la
duración. Muchas fallas no salen con carga constante sino en los **cambios** de carga
(de reposo a máximo el voltaje salta de golpe), con cargas de distinto tipo, o en la
parte **gráfica** de la GPU, que es distinta de la de cálculo.

Cada paso tiene una duración, una carga de CPU y una de GPU:

| CPU | Qué hace | GPU | Qué hace |
|---|---|---|---|
| Pesada | matrices, todos los hilos (máximo calor) | Cálculo | OpenCL con verificación |
| Ligera | enteros, 2 hilos | Render 3D | escena 3D en 4K propia (`render_trabajador.py`) con **imagen de control** |
| Ráfagas | todos los hilos 1 s sí / 1 s no | glmark2 | escenas de glmark2 en 4K (solo rendimiento) |
| Mixta | mitad FFT, mitad compresión zlib | Video 4K | 4 videos a la vez (NVDEC) |
| Un hilo | un hilo al máximo (frecuencia y voltaje más altos) | Cálculo + render | las dos partes a la vez |
| Reposo | nada (para el salto de reposo a máximo) | Reposo | nada |

Todas las cargas de CPU usan `stress-ng --verify`. El **render 3D** dibuja cada 4 s una
imagen de control con los mismos datos y la compara píxel por píxel con la primera: un
píxel distinto = artefacto (error). Se dibuja con EGL directo sobre la NVIDIA (sin
ventana); glmark2 usa PRIME (`__NV_PRIME_RENDER_OFFLOAD=1`).

Perfiles de fábrica: **CPU · carga variable**, **GPU · mixta**, **Todo el equipo**.
«Editar / copiar…» y «Nueva…» abren el editor (agregar, duplicar, quitar y ordenar pasos);
las filas propias se guardan en `~/.local/share/estrespc/filas/`. El informe incluye la
lista de pasos con los errores acumulados en cada uno.

## Escenas 3D reales (desde v0.6.0)

Tipo de carga GPU **«Escena 3D»** en las filas: dibuja escenas glTF reales en 4K como un juego
moderno — sombras de 4096 px (la escena se dibuja 2 veces por cuadro), antialiasing 4×,
texturas con transparencia recortada, y un HDRI 360° de fondo que además ilumina y se refleja.
La cámara recorre cada escena (círculo o ruta propia) y se verifica con la misma imagen de
control píxel a píxel. Cada paso «Escena 3D» usa la siguiente escena del catálogo.

| Escena | Triángulos | fps aprox. (RTX 3060, 4K) | Licencia |
|---|---|---|---|
| Bistro (Amazon Lumberyard) | 2.8 M | 60–115 | CC BY 4.0 |
| Sponza (Intel 2022) | 3.7 M | ~90 | **solo uso local** (ver CREDITOS) |
| Jungle Ruins (Intel 2024) | 6.0 M | — | CC BY 4.0 |
| Vehículo / torre (Cesium) | ligeros | ~300 | Apache 2.0 / CC BY 3.0 |

- Catálogo: `medios/modelos3d/escenas.json` (archivo, HDRI, cámara `dentro`/`fuera`, `ruta` en
  metros, exposición, `solo_local`). Créditos en `medios/modelos3d/CREDITOS.txt`.
- **Convertir escenas nuevas** (FBX, glTF, USD o .blend → .glb) con Blender:
  `blender --background --factory-startup --python herramientas/convertir_escena.py -- ORIGEN DESTINO.glb 1024 [MAX_TRIS]`
  (texturas a 1024 px para caber en 6 GB de VRAM; MAX_TRIS simplifica con Decimate).
  Ojo: escenas gigantes (Jungle Ruins sin tope: 12.5 M) pueden agotar 22 GB de RAM al exportar.
- **HDRIs** (.exr/.hdr → .npy): `herramientas/convertir_hdri.py`, salida en `medios/hdri/listos/`.

## Benchmark (pestaña «Benchmark», desde v0.3.0)

Mide el rendimiento con una **carga fija** (~3 min) y guarda el resultado para
comparar: el mismo equipo antes y después de un mantenimiento (pasta térmica,
limpieza), o contra otro equipo. Hazlo con cargador, el mismo perfil de energía
y el equipo en reposo. Cada corrida lleva una nota (p. ej. «antes de la pasta»).

| Medida | Cómo | Unidad |
|---|---|---|
| CPU 1 hilo / todos los hilos | `7z b -mmt1` / `7z b -mmtN` (7-Zip; comparable con los resultados publicados de 7-Zip) | MIPS |
| Memoria RAM | copia de bloques de 256 MB en 4 procesos, mejor de 3 rondas | GB/s |
| GPU | el trabajador OpenCL de la prueba de estrés, 20 s, mediana sin los primeros 5 s | TFLOPS |
| Video 4K | decodificación NVDEC, 4 flujos, 20 s (si hay videos) | fps |
| Disco | 2 GB directo (sin caché): secuencial 4×8 MB en paralelo + lectura aleatoria 4K de a una | MB/s, IOPS |

También guarda la **temperatura máxima y la frecuencia promedio** de CPU y GPU
durante cada paso: es lo que más cambia con una pasta nueva. La tabla compara dos
corridas y colorea el cambio (verde = mejor; en temperaturas, menos es mejor).
Si una temperatura pasa su límite, el benchmark se cancela.

Resultados en `~/.local/share/estrespc/benchmarks/<fecha_hora>.json`.
Requiere `7zip` (`sudo pacman -S 7zip`).

## Registros

Cada corrida guarda `sensores.csv` (un renglón por segundo) e `informe.txt`
(resultado, mín/máx de cada sensor y el registro) en
`~/.local/share/estrespc/registros/<fecha_hora>/`.

## Notas

- La potencia de la CPU (RAPL) no se muestra: el kernel solo la deja leer a root.
- La GPU NVIDIA solo se consulta mientras se prueba o si se marca «Vigilar»,
  porque consultarla la despierta y gasta batería.

Este programa fue realizado por Genaro Velasco.

# Medios incluidos con EstrésPC

Todo lo que se ponga aquí viaja **dentro del programa** (y del instalador): no hay que descargarlo.

## `videos/` — videos 4K para la prueba «Video 4K»
EstrésPC usa automáticamente cualquier `.mp4`, `.mkv`, `.mov` o `.webm` de esta carpeta
(además de los de `~/.local/share/estrespc/videos/`).

- Ideal: **4K (3840×2160) a 60 fps**, 15 s a 2 min, en códecs distintos (H.264, HEVC/H.265, AV1)
  para cargar el decodificador de varias formas.
- **Licencia (importante, GatoTec es un negocio):** solo videos que permitan uso comercial y
  redistribución, y anotar el crédito en `videos/CREDITOS.txt`. Fuentes seguras:
  - Películas abiertas de la **Blender Foundation** (CC BY): Big Buck Bunny, Sintel,
    Tears of Steel, Spring — https://studio.blender.org/films/
  - **Pexels** / **Pixabay** (licencia propia: uso comercial sin atribución obligatoria).
  - Los generados por el propio programa (botón «Generar videos 4K de prueba»).
- **No** usar trailers, videos de YouTube ni películas comerciales.

## `hdri/` — ambientes de 360° para el render 3D (pendiente de integrar)
Imágenes HDR panorámicas (`.exr` o `.hdr`, equirectangulares 2:1): sirven de fondo y de
iluminación/reflejos (IBL) para la escena. Fuente recomendada: **Poly Haven** (CC0).
- `historic_cloister_passage_4k.exr` — claustro gótico (4096×2048)
- `industrial_pipe_and_valve_01_4k.exr` — bodega industrial (4096×2048)

## `modelos3d/` — escenas para el render 3D (pendiente de integrar)
Formato recomendado: **glTF 2.0** (`.glb` / `.gltf`). Solo modelos con licencia libre, p. ej.:
- **Khronos glTF Sample Assets**: *Sponza* (Crytek, CC BY 3.0), *Flight Helmet*, etc.
  — https://github.com/KhronosGroup/glTF-Sample-Assets
- **Kenney** (CC0, dominio público) — https://kenney.nl/assets
- **Poly Haven** (CC0: modelos, texturas y HDRIs) — https://polyhaven.com
- **NVIDIA ORCA** (Amazon Lumberyard *Bistro*, CC BY 4.0) — escena pesada ideal para estrés.

Los archivos extraídos de **juegos comerciales** no se pueden redistribuir ni usar en una
herramienta de un negocio aunque se tengan comprados.

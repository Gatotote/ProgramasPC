# BóvedaFacial

Bóveda de carpetas **cifrada** con desbloqueo por **reconocimiento facial**
(InsightFace / ArcFace, pack `antelopev2`) **+ PIN**. El contenido queda
inaccesible por búsquedas del sistema y por el explorador de archivos: dentro
del `.vault` solo hay blobs cifrados con nombres HMAC, sin extensiones.

## Modelo de seguridad (resumen)

- Clave maestra aleatoria de 256 bits (`MK`) cifra todo el contenido (AES-256-GCM).
- `MK` se guarda en **dos keyslots** estilo LUKS:
  - **PIN** → `Argon2id` → KEK → envuelve `MK`.
  - **Frase de recuperación** de 24 palabras (BIP39) → HKDF → KEK → envuelve `MK`.
- Desbloqueo normal = **PIN correcto Y coincidencia facial** (Fase 3). El rostro
  es una puerta de autenticación *después* de recuperar la `MK` con el PIN;
  la biometría nunca es material de clave (no es secreta ni estable).
- La **frase de recuperación** salta el paso facial (cámara averiada, cambio de
  aspecto). Guárdala en **papel, fuera del equipo**: es el punto único de
  compromiso total.

### Qué protege / qué no

Protege: equipo robado o apagado, otros usuarios de la máquina, copias del
`.vault` en la nube, navegación casual, indexadores de escritorio.
**No** protege contra root/malware con la bóveda ya abierta, keyloggers, ni
desbloqueo forzado.

## Estado

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Núcleo cripto + contenedor + CLI de pruebas + tests | ✅ |
| 2 | Motor facial (antelopev2): cámara, embeddings, enrolado, liveness | ✅ |
| 3 | Integración de desbloqueo: PIN → MK → gate facial, rate-limiting | ⏳ |
| 4 | GUI PySide6: asistente, ventana principal, vista de desbloqueo | ⏳ |
| 5 | Auto-bloqueo, exclusión Baloo, `shred` del original, empaquetado | ⏳ |

### Motor facial (Fase 2)

```bash
uv sync --extra face          # instala insightface + onnxruntime-gpu + wheels CUDA 13
uv run --extra face python scripts/face_smoke.py           # prueba con la webcam
uv run --extra face python scripts/face_smoke.py --enroll  # enrola y se verifica
```

- Pack `antelopev2` (SCRFD-10G + ResNet100 glint360k); se descarga solo a
  `~/.insightface/` en el primer uso (~260 MB). El motor corrige el zip anidado.
- GPU: `onnxruntime-gpu[cuda,cudnn]` trae los wheels `nvidia-*-cu13`, así que la
  RTX 3060 acelera sin instalar el toolkit CUDA en el sistema (~2 GB en `.venv`).
  Medido: `primary_face` ~40-100 ms en GPU vs ~2.3 s en CPU. Si faltan las libs
  CUDA, cae a CPU con aviso.
- `insightface` arrastra `onnxruntime` (CPU) que choca con `onnxruntime-gpu`;
  se anula en `[tool.uv] override-dependencies`.

## Uso (CLI de pruebas — Fase 1)

```bash
uv sync
uv run bovedafacial init   ~/secreta.vault
uv run bovedafacial add    ~/secreta.vault ~/Documentos/contratos --dest /docs
uv run bovedafacial ls     ~/secreta.vault /docs
uv run bovedafacial get    ~/secreta.vault /docs/contratos/2025.pdf ./2025.pdf
uv run bovedafacial rm     ~/secreta.vault /docs/contratos/2025.pdf
```

`--recovery` en cualquier comando pide la frase de 24 palabras en vez del PIN.

## Desarrollo

```bash
uv sync
uv run pytest
```

## Estructura

```
src/bovedafacial/
  cli.py            CLI de pruebas (Fase 1)
  crypto/
    keyslots.py     Argon2id + BIP39, envolver/desenvolver MK
    subkeys.py      subclaves HKDF por dominio
    container.py    header.json, index.enc, objects/ (chunks cifrados)
  vault/
    tree.py         árbol lógico de carpetas/archivos
    session.py      sesión abierta: importar / extraer / listar / eliminar
  face/
    camera.py       fuente de vídeo (v4l2 / imagen)
    engine.py       InsightFace antelopev2 + embeddings 512-d (carga perezosa)
    quality.py      control de calidad del frame + EAR (parpadeo)
    liveness.py     retos de prueba de vida (girar / parpadear / acercarse)
    enroll.py       Template + enrolado (batch e incremental)
    verify.py       similitud coseno + umbral + backoff exponencial
    store.py        guardado cifrado de la plantilla en faces.enc
  ui/               Fase 4  (uv sync --extra gui)
scripts/face_smoke.py   prueba manual del motor con la webcam
```

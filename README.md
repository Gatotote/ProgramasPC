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
| 3 | Desbloqueo completo: `open_vault` (PIN → MK → gate facial), backoff | ✅ |
| 4a | Modelo de datos: elementos tipados + registro de actividad + generador | ✅ |
| 4b | GUI PySide6: asistente, ventana principal, vista de desbloqueo | ⏳ |
| 5 | Auto-bloqueo, exclusión Baloo, `shred` del original, empaquetado | ⏳ |

### Elementos tipados y actividad (Fase 4a)

Además de archivos, la bóveda guarda **elementos** (`vault/items.py`):
`password · card · account · contact · will · insurance · note`. Cada uno es una
entrada del índice con `fields` (dict pequeño, cifrado dentro de `index.enc`) y
`attachments` opcionales (archivos troceados). Los campos `secret` los enmascara
la UI.

- `Session.add_item / get_item / update_item / list_items / attach_file`
- `vault/audit.py`: registro cifrado (`audit.enc`) → `session.activity()`,
  `activity_summary()` (para el panel: último acceso, añadidos hoy, intentos
  bloqueados 24 h, uso de disco). Los intentos fallidos de PIN viven en
  `header["stats"]["fail_times"]` (en claro, no hay MK aún).
- `bovedafacial/pwgen.py`: generador de contraseñas (`secrets`).

```bash
uv run bovedafacial gen -n 24
uv run bovedafacial item add  V.vault password "Banco" --dir /Finanzas -f usuario=x -f password=y
uv run bovedafacial item list V.vault
uv run bovedafacial item show V.vault /Finanzas/Banco [--reveal]
uv run bovedafacial activity  V.vault
```

### Desbloqueo (Fase 3)

`vault.open_vault(path, pin=…, phrase=…, face_gate=…)`:

1. Lee el bloqueo por intentos del `header.json` (en claro; no hay MK antes del
   PIN). Si está dentro de la ventana → `VaultLocked(retry_after)`.
2. `Argon2id(PIN)` desenvuelve la MK. Si falla → `BackoffPolicy.register_failure`
   (2 s → 6 s → 18 s …, tope 15 min) y se persiste en el header.
3. Si hay `faces.enc` y la política lo exige, ejecuta `face_gate(session)`:
   cámara → **liveness por movimiento** (giro de cabeza / acercarse / parpadeo)
   + similitud coseno ≥ umbral en ≥ 6 frames. Rechazo → cuenta como intento.
4. `phrase` (24 palabras) salta el bloqueo y el rostro — es la vía de escape.

`vault/` no importa `face/`: el `face_gate` lo inyecta la CLI/GUI vía
`face.make_gate()`. `BackoffPolicy` vive en `bovedafacial/throttle.py`.

```bash
uv run bovedafacial init   ~/secreta.vault
uv run --extra face bovedafacial enroll ~/secreta.vault
uv run bovedafacial status ~/secreta.vault
uv run --extra face bovedafacial ls ~/secreta.vault /      # pide PIN + rostro
uv run bovedafacial ls ~/secreta.vault / --recovery        # frase, sin rostro
uv run bovedafacial ls ~/secreta.vault / --pin-only        # SOLO pruebas
```

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
  throttle.py       BackoffPolicy (bloqueo por intentos, sin numpy)
  pwgen.py          generador de contraseñas
  vault/
    tree.py         árbol lógico: carpetas / archivos / elementos tipados
    items.py        tipos de elemento + campos (password, card, account, …)
    audit.py        registro de actividad cifrado (audit.enc)
    session.py      sesión abierta + open_vault() (PIN → MK → gate facial)
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

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
| 2 | Motor facial (antelopev2): cámara, embeddings, enrolado, liveness | ⏳ |
| 3 | Integración de desbloqueo: PIN → MK → gate facial, rate-limiting | ⏳ |
| 4 | GUI PySide6: asistente, ventana principal, vista de desbloqueo | ⏳ |
| 5 | Auto-bloqueo, exclusión Baloo, `shred` del original, empaquetado | ⏳ |

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
  face/             Fase 2  (uv sync --extra face)
  ui/               Fase 4  (uv sync --extra gui)
```

# BóvedaFacial · «Bóveda Inteligente» — bitácora de la sesión (2026-09-09)

Resumen de lo que hicimos hoy y **qué falta probar para continuar en casa**.

---

## Qué es

Caja fuerte de escritorio (Linux/KDE, PySide6) que guarda **carpetas cifradas**
y **elementos con estructura** (contraseñas, tarjetas, cuentas, contactos,
testamentos, seguros, notas). Se abre con **PIN + rostro** (InsightFace
antelopev2 en GPU) y hay **frase de recuperación** de 24 palabras.
Cifrado AES-256-GCM, clave maestra envuelta por PIN (Argon2id) y por la frase.
Nada del contenido aparece en el explorador ni en las búsquedas del sistema.

- Repo **solo local**: `~/Proyectos/BovedaFacial/`, rama `main`, sin remoto.
- **99 tests** (`uv run pytest`).
- Se lanza con `bovedafacial-gui` (icono en el menú de KDE y en el Escritorio).

## Fases completadas hoy (1 → 5 + GUI)

| Commit | Contenido |
|--------|-----------|
| `1b3cf36` | Fase 1 · núcleo cripto + contenedor `.vault` (chunks HMAC, index.enc) |
| `098b206` | Fase 2 · motor facial antelopev2 (GPU vía wheels `nvidia-*-cu13`) |
| `f862b05` | Fase 3 · `open_vault` (PIN → MK → gate facial + liveness), backoff |
| `e0eaae1` | Fase 4a · elementos tipados + registro de actividad + generador |
| `fc367bb` | Fase 4b·1 · GUI: tema, asistente de 1er arranque, ventana de desbloqueo |
| `4fbea22` | Fase 4b·2 · ventana principal (barra lateral, tarjetas, actividad, FAB) |
| `cf0511a` | Fase 4b·3 · vistas Archivos y Fotografías + `Session.checkout` (a RAM) |
| `84edfba` | Fase 5 · exclusión de Baloo, `shred` del original al importar, lanzador |
| `d4528b8` | fix · fantasmas entre tarjetas (sub-layouts huérfanos en `refresh`) |
| `79e8937`→`87714cd` | icono (elegido V2, luego el de VaultXAndroid sin fondo) |
| `d85d05d` | ventana de progreso en abrir/importar/exportar/eliminar |
| `2d31f1c` | editor: botones con texto (no emoji) + medidor de fortaleza |

## Estado en la máquina

- Bóveda real creada: `~/.local/share/bovedafacial/principal.vault`
  (con **rostro enrolado**; ya se ha desbloqueado con éxito).
- Lanzador: `~/.local/share/applications/bovedafacial.desktop` + `~/Escritorio/`.
- Icono nuevo (sin fondo) instalado; Plasma reiniciado.
- Baloo: la bóveda quedó excluida del índice al crearla.

---

## ⏳ Qué falta probar (en casa)

Marca según vayas comprobando:

- [ ] **Icono nuevo** visible en el menú de KDE y en el Escritorio
      (si no, F5 en el escritorio o cerrar/abrir sesión).
- [ ] **Desbloqueo por rostro** desde la GUI: abrir con el icono → meter PIN →
      «Entrar» → la vista previa de la cámara + progreso → abre la bóveda.
- [ ] **Frase de recuperación**: en la pantalla de desbloqueo, «Usar la frase de
      recuperación» → entrar con las 24 palabras (¿las tienes apuntadas?).
- [ ] **Cámara desconectada**: desenchufar la webcam y comprobar que el
      desbloqueo lo dice y ofrece la frase (no se cuelga).
- [ ] **Importar** un archivo y una carpeta desde *Archivos* → aparece la
      ventana «Cifrando e importando…».
- [ ] **Abrir** un archivo desde *Archivos* → se descifra y lo abre el programa
      del sistema. Luego **Bloquear ahora** y comprobar que
      `ls /dev/shm/bovedafacial-*` ya no existe.
- [ ] **Fotografías**: importar 2-3 imágenes y ver las miniaturas.
- [ ] **Contraseñas**: crear una con el editor → botones «Ver / Copiar /
      Generar», el **medidor de fortaleza** (rojo/amarillo/verde) en vivo, y la
      columna «Fortaleza» en la lista.
- [ ] **Finanzas**: crear una cuenta y una tarjeta; ver los números enmascarados.
- [ ] **Bloqueo por inactividad**: dejar la ventana 3 min sin tocar → vuelve a la
      pantalla de desbloqueo. (Ajustable en Configuración.)
- [ ] **Reportes / indicador 🟢🟡🔴**: que refleje contraseñas débiles, respaldo
      antiguo, intentos bloqueados.
- [ ] **Configuración**: cambiar tema (claro/oscuro), cambiar el tiempo de
      auto-bloqueo, «Volver a enrolar rostro», «Marcar respaldo hecho ahora».
- [ ] **CLI opcional**: `uv run bovedafacial add <vault> <archivo> --shred`
      (pide confirmación y borra el original de forma segura).

## Pendientes conocidos (no bloquean, para más adelante)

- Icono **sin fondo**: poco contraste sobre superficies claras del escritorio.
  Si molesta, se le puede poner un disco de fondo oscuro semitransparente.
- En Configuración, **«Cambiar PIN»** y **«Mostrar frase de recuperación»** son
  botones informativos todavía (sin implementar).
- **Anti-spoofing real** (foto vs. cara): ahora la prueba de vida es por
  movimiento; falta un modelo de textura/profundidad (Silent-Face) — opcional.
- **`locate`/plocate**: para excluir la bóveda hay que añadir `.vault` a
  `PRUNENAMES` en `/etc/updatedb.conf` (con sudo). Baloo ya está cubierto.
- **GitHub**: sigue sin subir; se decide cuando Genaro quiera.
- Al correr `uv sync` **sin** `--extra face`, `onnxruntime` (CPU) intenta
  colarse; el `override-dependencies` de `pyproject.toml` lo neutraliza — usar
  siempre `uv sync --extra face --extra gui`.

## Cómo retomar

```bash
cd ~/Proyectos/BovedaFacial
uv sync --extra face --extra gui
uv run pytest -q            # 99 verdes
uv run bovedafacial-gui     # o el icono del escritorio
uv run bovedafacial-gui --demo   # bóveda temporal con datos de ejemplo
```

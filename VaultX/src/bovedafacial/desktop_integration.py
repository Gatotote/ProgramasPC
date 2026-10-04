"""Integración con el escritorio (Fase 5):

- `exclude_from_baloo()`: saca el `.vault` del indexador de archivos de KDE para
  que no aparezca en Dolphin / KRunner / la búsqueda del sistema.
- `install_desktop_entry()`: instala el lanzador «VaultX» y su icono
  en ~/.local/share, para abrirla desde el menú de KDE.

Todo es best-effort: si no hay KDE o falta una herramienta, se informa y ya.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Mismo icono que la app Android (VaultXAndroid) pero SIN fondo: círculo +
# fractal hexagonal + candado en trazo blanco, anillos decorativos en morado.
# Se ve para superficies oscuras; sobre fondo claro los trazos blancos pierden
# contraste (el panel/menú de KDE suele ser oscuro).
ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108">
  <g fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M54,54 m-26,0 a26,26 0 1,1 52,0 a26,26 0 1,1 -52,0" stroke="#FFFFFF" stroke-width="1.7"/>
    <path d="M 54,28 L 76.52,41 L 76.52,67 L 54,80 L 31.48,67 L 31.48,41 Z" stroke="#FFFFFF" stroke-width="1.7"/>
    <path d="M 54,43.08 L 63.46,48.54 L 63.46,59.46 L 54,64.92 L 44.54,59.46 L 44.54,48.54 Z" stroke="#FFFFFF" stroke-width="1.5"/>
    <path d="M54,28L54,43.08 M76.52,41L63.46,48.54 M76.52,67L63.46,59.46 M54,80L54,64.92 M31.48,67L44.54,59.46 M31.48,41L44.54,48.54 M31.48,41L76.52,41 M31.48,67L76.52,67" stroke="#FFFFFF" stroke-width="1.5"/>
    <path d="M49,53.2 h10 v8.4 h-10 z" stroke="#FFFFFF" stroke-width="1.7"/>
    <path d="M51.1,53.2 v-2.4 a2.9,2.9 0 0,1 5.8,0 v2.4" stroke="#FFFFFF" stroke-width="1.7"/>
    <path d="M54,22.7L54,20.5 M59.44,23.18L59.82,21.01 M64.71,24.59L65.46,22.52 M69.65,26.89L70.75,24.99 M74.12,30.02L75.53,28.34 M77.98,33.88L79.66,32.47 M81.11,38.35L83.01,37.25 M83.41,43.29L85.48,42.54 M84.82,48.56L86.99,48.18 M85.3,54L87.5,54 M84.82,59.44L86.99,59.82 M83.41,64.71L85.48,65.46 M81.11,69.65L83.01,70.75 M77.98,74.12L79.66,75.53 M74.12,77.98L75.53,79.66 M69.65,81.11L70.75,83.01 M64.71,83.41L65.46,85.48 M59.44,84.82L59.82,86.99 M54,85.3L54,87.5 M48.56,84.82L48.18,86.99 M43.29,83.41L42.54,85.48 M38.35,81.11L37.25,83.01 M33.88,77.98L32.47,79.66 M30.02,74.12L28.34,75.53 M26.89,69.65L24.99,70.75 M24.59,64.71L22.52,65.46 M23.18,59.44L21.01,59.82 M22.7,54L20.5,54 M23.18,48.56L21.01,48.18 M24.59,43.29L22.52,42.54 M26.89,38.35L24.99,37.25 M30.02,33.88L28.34,32.47 M33.88,30.02L32.47,28.34 M38.35,26.89L37.25,24.99 M43.29,24.59L42.54,22.52 M48.56,23.18L48.18,21.01" stroke="#7C3AED" stroke-width="1.35"/>
    <path d="M54,18.6L57.39,18.76L60.75,19.25L64.05,20.06L67.26,21.18 M79.03,28.97L81.32,31.48L83.35,34.2L85.11,37.11L86.59,40.17 M89.4,54L89.24,57.39L88.75,60.75L87.94,64.05L86.82,67.26 M79.03,79.03L76.52,81.32L73.8,83.35L70.89,85.11L67.83,86.59 M54,89.4L50.61,89.24L47.25,88.75L43.95,87.94L40.74,86.82 M28.97,79.03L26.68,76.52L24.65,73.8L22.89,70.89L21.41,67.83 M18.6,54L18.76,50.61L19.25,47.25L20.06,43.95L21.18,40.74 M28.97,28.97L31.48,26.68L34.2,24.65L37.11,22.89L40.17,21.41" stroke="#A78BFA" stroke-width="1.5"/>
  </g>
  <path fill="#A78BFA" d="M54,24.8m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M61.56,25.79m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M68.6,28.71m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M74.65,33.35m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M79.29,39.4m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M82.21,46.44m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M83.2,54m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M82.21,61.56m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M79.29,68.6m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M74.65,74.65m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M68.6,79.29m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M61.56,82.21m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M54,83.2m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M46.44,82.21m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M39.4,79.29m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M33.35,74.65m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M28.71,68.6m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M25.79,61.56m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M24.8,54m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M25.79,46.44m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M28.71,39.4m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M33.35,33.35m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M39.4,28.71m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0 M46.44,25.79m-1.05,0a1.05,1.05 0 1,1 2.1,0a1.05,1.05 0 1,1 -2.1,0"/>
  <path fill="#A78BFA" d="M71.7,23.34m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0 M88.19,44.84m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0 M84.66,71.7m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0 M63.16,88.19m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0 M36.3,84.66m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0 M19.81,63.16m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0 M23.34,36.3m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0 M44.84,19.81m-0.95,0a0.95,0.95 0 1,1 1.9,0a0.95,0.95 0 1,1 -1.9,0"/>
</svg>
"""


# --- Baloo -----------------------------------------------------------------

def exclude_from_baloo(vault_path: Path | str) -> str:
    p = Path(vault_path).expanduser().resolve()
    entry = str(p) + "/"

    for tool in ("balooctl6", "balooctl"):
        exe = shutil.which(tool)
        if not exe:
            continue
        try:
            subprocess.run([exe, "config", "add", "excludeFolders", str(p)],
                           check=True, capture_output=True, timeout=15)
            return f"Excluida del índice (vía {tool})."
        except (subprocess.SubprocessError, OSError):
            pass

    rc = Path.home() / ".config" / "baloofilerc"
    text = rc.read_text("utf-8") if rc.exists() else ""
    if entry in text:
        return "Ya estaba excluida del índice."

    key = "exclude folders[$e]="
    lines = text.splitlines()
    out: list[str] = []
    in_general = False
    done = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            if in_general and not done:
                out.append(key + entry)
                done = True
            in_general = stripped == "[General]"
            out.append(line)
            continue
        if in_general and not done and line.startswith(key):
            val = line[len(key):].strip()
            out.append(key + (val + "," + entry if val else entry))
            done = True
            continue
        out.append(line)
    if not done:
        if in_general:
            out.append(key + entry)
        else:
            out = ["[General]", key + entry, ""] + out

    rc.parent.mkdir(parents=True, exist_ok=True)
    rc.write_text("\n".join(out).rstrip("\n") + "\n", "utf-8")
    return "Añadida a ~/.config/baloofilerc (aplica al reiniciar la sesión o Baloo)."


# --- lanzador .desktop --------------------------------------------------

def _gui_executable() -> str:
    exe = shutil.which("bovedafacial-gui")
    if exe:
        return exe
    cand = Path(sys.executable).parent / "bovedafacial-gui"
    if cand.exists():
        return str(cand)
    return f'"{sys.executable}" -m bovedafacial.ui.app'


def _icon_svg_path() -> Path:
    return (Path.home() / ".local" / "share" / "icons" / "hicolor"
            / "scalable" / "apps" / "bovedafacial.svg")


def _write_icons() -> Path:
    svg_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps"
    svg_dir.mkdir(parents=True, exist_ok=True)
    svg = svg_dir / "bovedafacial.svg"
    svg.write_text(ICON_SVG, "utf-8")
    # PNG en varios tamaños (algunos contextos de KDE los prefieren)
    rsvg = shutil.which("rsvg-convert")
    if rsvg:
        for size in (16, 22, 24, 32, 48, 64, 128, 256):
            d = Path.home() / ".local" / "share" / "icons" / "hicolor" / f"{size}x{size}" / "apps"
            d.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run([rsvg, "-w", str(size), "-h", str(size), str(svg),
                                "-o", str(d / "bovedafacial.png")],
                               check=True, capture_output=True, timeout=15)
            except (subprocess.SubprocessError, OSError):
                pass
    return svg


def install_desktop_entry() -> Path:
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    _write_icons()

    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=VaultX\n"
        "GenericName=Caja fuerte cifrada\n"
        "Comment=Documentos, contraseñas y finanzas con desbloqueo por rostro y PIN\n"
        f"Exec={_gui_executable()}\n"
        "Icon=bovedafacial\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
        "Keywords=boveda;vault;contraseñas;password;caja fuerte;cifrado;\n"
        "StartupNotify=true\n"
    )
    dpath = apps / "bovedafacial.desktop"
    dpath.write_text(entry, "utf-8")
    os.chmod(dpath, 0o755)

    _refresh_desktop_caches(apps)
    return dpath


def _refresh_desktop_caches(apps: Path) -> None:
    for tool, args in (
        ("update-desktop-database", [str(apps)]),
        ("kbuildsycoca6", ["--noincremental"]),
        ("gtk-update-icon-cache", ["-f", "-t",
                                   str(Path.home() / ".local" / "share" / "icons" / "hicolor")]),
    ):
        exe = shutil.which(tool)
        if exe:
            try:
                subprocess.run([exe, *args], capture_output=True, timeout=30)
            except (subprocess.SubprocessError, OSError):
                pass
    for cache in ("icon-cache.kcache", "plasma-svgelements"):
        try:
            (Path.home() / ".cache" / cache).unlink(missing_ok=True)
        except OSError:
            pass


def place_on_desktop() -> Path | None:
    """Copia el lanzador al Escritorio con `Icon=` en ruta absoluta (más fiable
    para la vista de carpeta que el nombre de icono del tema)."""
    src = install_desktop_entry()
    try:
        out = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True,
                              text=True, timeout=5).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        out = ""
    desk = Path(out) if out else Path.home() / "Desktop"
    if not desk.is_dir():
        desk = Path.home() / "Escritorio"
    if not desk.is_dir():
        return None
    text = src.read_text("utf-8").replace("Icon=bovedafacial", f"Icon={_icon_svg_path()}")
    dst = desk / "bovedafacial.desktop"
    dst.write_text(text, "utf-8")
    os.chmod(dst, 0o755)
    return dst

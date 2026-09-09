"""Integración con el escritorio (Fase 5):

- `exclude_from_baloo()`: saca el `.vault` del indexador de archivos de KDE para
  que no aparezca en Dolphin / KRunner / la búsqueda del sistema.
- `install_desktop_entry()`: instala el lanzador «Bóveda Inteligente» y su icono
  en ~/.local/share, para abrirla desde el menú de KDE.

Todo es best-effort: si no hay KDE o falta una herramienta, se informa y ya.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect x="6" y="6" width="116" height="116" rx="24" fill="#1b1e23"/>
  <rect x="6" y="6" width="116" height="116" rx="24" fill="none" stroke="#2d323b" stroke-width="2"/>
  <circle cx="64" cy="60" r="34" fill="none" stroke="#c6903f" stroke-width="7"/>
  <circle cx="64" cy="60" r="9" fill="#c6903f"/>
  <rect x="60" y="60" width="8" height="24" rx="4" fill="#c6903f"/>
  <path d="M64 20a40 40 0 0 1 40 40" fill="none" stroke="#c6903f" stroke-width="7"
        stroke-linecap="round" opacity="0.5"/>
  <rect x="30" y="98" width="68" height="12" rx="6" fill="#c6903f"/>
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


def install_desktop_entry() -> Path:
    apps = Path.home() / ".local" / "share" / "applications"
    icons = Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps"
    apps.mkdir(parents=True, exist_ok=True)
    icons.mkdir(parents=True, exist_ok=True)

    (icons / "bovedafacial.svg").write_text(ICON_SVG, "utf-8")

    entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Bóveda Inteligente\n"
        "GenericName=Caja fuerte cifrada\n"
        "Comment=Documentos, contraseñas y finanzas con desbloqueo por rostro y PIN\n"
        f"Exec={_gui_executable()}\n"
        "Icon=bovedafacial\n"
        "Terminal=false\n"
        "Categories=Utility;Security;\n"
        "Keywords=boveda;vault;contraseñas;password;caja fuerte;cifrado;\n"
        "StartupNotify=true\n"
    )
    dpath = apps / "bovedafacial.desktop"
    dpath.write_text(entry, "utf-8")
    os.chmod(dpath, 0o755)

    upd = shutil.which("update-desktop-database")
    if upd:
        subprocess.run([upd, str(apps)], capture_output=True, timeout=15)
    return dpath

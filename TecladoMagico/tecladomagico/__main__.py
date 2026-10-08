import argparse
import os

from . import VERSION


def main():
    parser = argparse.ArgumentParser(prog="tecladomagico", description="Teclado Mágico para bebés")
    parser.add_argument("--version", action="version", version=f"Teclado Mágico {VERSION}")
    parser.add_argument("--ventana", action="store_true", help="abrir en ventana (para pruebas), sin bloquear el teclado")
    args = parser.parse_args()

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    os.environ.setdefault("SDL_VIDEO_WAYLAND_WMCLASS", "tecladomagico")
    os.environ.setdefault("SDL_VIDEO_X11_WMCLASS", "tecladomagico")
    # Nombre propio en el mezclador de sonido (si no, sale como «python3.13» y comparte silencio/volumen
    # con cualquier otro programa de Python).
    os.environ.setdefault("SDL_APP_NAME", "Teclado Mágico")
    os.environ.setdefault("SDL_AUDIO_DEVICE_APP_NAME", "Teclado Mágico")
    # Que SIGTERM (apagar la PC, kill) lo cierre: si SDL lo convierte en QUIT, se ignoraría como Alt+F4.
    os.environ.setdefault("SDL_NO_SIGNAL_HANDLERS", "1")
    if os.environ.get("WAYLAND_DISPLAY"):
        # En Wayland nativo KWin sí respeta el bloqueo de atajos; por XWayland no.
        os.environ.setdefault("SDL_VIDEODRIVER", "wayland,x11")
    if not args.ventana:
        # Pide al compositor que no procese atajos (Super, Alt+Tab…) mientras tenga el foco.
        os.environ.setdefault("SDL_GRAB_KEYBOARD", "1")
        # Con el teclado apartado, SDL mismo minimiza la ventana al ver Alt+Tab (salida de emergencia de SDL).
        # La F3 del Logitech K400 Plus manda justo Alt+Tab, así que se apaga.
        os.environ.setdefault("SDL_ALLOW_ALT_TAB_WHILE_GRABBED", "0")

    from .juego import Juego

    Juego(ventana=args.ventana).correr()


if __name__ == "__main__":
    main()

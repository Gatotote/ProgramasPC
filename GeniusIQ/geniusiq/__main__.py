import sys

from . import VERSION


def main() -> int:
    if "--version" in sys.argv:
        print(f"GeniusIQ {VERSION}")
        return 0
    from .ui.ventana import ejecutar
    return ejecutar()


if __name__ == "__main__":
    sys.exit(main())

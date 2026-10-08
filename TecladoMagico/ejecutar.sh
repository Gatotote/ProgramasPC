#!/bin/sh
# Lanza Teclado Mágico con el entorno del proyecto.
# En pantalla completa apaga los atajos globales de KDE mientras corre (Meta, Meta+P de
# «proyectar pantalla», Alt+Espacio de KRunner, Ctrl+Alt+Supr…) y SIEMPRE los regresa al salir.
cd "$(dirname "$(readlink -f "$0")")" || exit 1

case " $* " in
    *" --ventana "*|*" --version "*|*" -h "*|*" --help "*) exec uv run --quiet python -m tecladomagico "$@" ;;
esac

KWINRC="$HOME/.config/kwinrc"
META_ANTES=$(kreadconfig6 --file "$KWINRC" --group ModifierOnlyShortcuts --key Meta --default __sin_valor__)

restaurar() {
    qdbus6 org.kde.kglobalaccel /kglobalaccel org.kde.KGlobalAccel.blockGlobalShortcuts false >/dev/null 2>&1
    if [ "$META_ANTES" = "__sin_valor__" ]; then
        kwriteconfig6 --file "$KWINRC" --group ModifierOnlyShortcuts --key Meta --delete
    else
        kwriteconfig6 --file "$KWINRC" --group ModifierOnlyShortcuts --key Meta "$META_ANTES"
    fi
    qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1
}
trap restaurar EXIT
trap 'exit 130' INT TERM HUP

qdbus6 org.kde.kglobalaccel /kglobalaccel org.kde.KGlobalAccel.blockGlobalShortcuts true >/dev/null 2>&1
# La tecla Meta sola (abrir el menú) la maneja KWin aparte de kglobalaccel.
kwriteconfig6 --file "$KWINRC" --group ModifierOnlyShortcuts --key Meta ""
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1

uv run --quiet python -m tecladomagico "$@"

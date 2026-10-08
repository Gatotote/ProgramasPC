#!/bin/sh
# Autoarranque de KDE (~/.config/autostart/tecladomagico-restaurar-atajos.desktop): si el Teclado Mágico
# se cerró de golpe (apagón, kill -9), regresa los atajos globales y la tecla Meta. Si no, no hace nada.
cd "$(dirname "$(readlink -f "$0")")/.." || exit 1
qdbus6 org.kde.kglobalaccel /kglobalaccel org.kde.KGlobalAccel.blockGlobalShortcuts false >/dev/null 2>&1
if grep -q '^Meta=$' "$HOME/.config/kwinrc"; then
    kwriteconfig6 --file kwinrc --group ModifierOnlyShortcuts --key Meta --delete
    qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1
fi

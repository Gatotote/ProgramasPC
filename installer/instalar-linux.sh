#!/usr/bin/env bash
# Instalador de "Descargador y Conversor" para Linux.
# Ejecutar desde la carpeta donde se descomprimió el paquete: ./instalar-linux.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

DESTINO="$HOME/.local/share/DescargadorYConversor"
BIN_ESCRITORIO="$HOME/.local/share/applications"
ICONOS="$HOME/.local/share/icons"

echo "=== Instalador Descargador y Conversor (Linux) ==="

echo "-- Copiando programa a $DESTINO --"
rm -rf "$DESTINO"
mkdir -p "$DESTINO"
cp -r DescargadorYConversor/. "$DESTINO/"
chmod +x "$DESTINO/DescargadorYConversor"

echo "-- Instalando ícono y acceso directo --"
mkdir -p "$ICONOS" "$BIN_ESCRITORIO"
cp icono.png "$ICONOS/descargador-y-conversor.png"

cat > "$BIN_ESCRITORIO/descargador-y-conversor.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Descargador y Conversor
Comment=Descarga videos/audio y convierte imágenes
Exec=$DESTINO/DescargadorYConversor
Icon=$ICONOS/descargador-y-conversor.png
Terminal=false
Categories=AudioVideo;Utility;
EOF
chmod +x "$BIN_ESCRITORIO/descargador-y-conversor.desktop"

echo
echo "=== Listo ==="
echo "Programa instalado en: $DESTINO"
echo "Búscalo como 'Descargador y Conversor' en el menú de aplicaciones."

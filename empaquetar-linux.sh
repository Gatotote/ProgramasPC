#!/usr/bin/env bash
# Construye el ejecutable con PyInstaller y arma el paquete .tar.gz para Linux.
#   ./empaquetar-linux.sh
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

VERSION="$(cat VERSION)"
SALIDA="Output"
PKG="$SALIDA/DescargadorYConversor"

echo "== 1/2  PyInstaller =="
.venv/bin/python -m PyInstaller DescargadorYConversor.spec --noconfirm --clean

echo "== 2/2  Empaquetando =="
rm -rf "$PKG"
mkdir -p "$PKG"
cp -r dist/DescargadorYConversor "$PKG/DescargadorYConversor"
cp assets/logo_azul.png "$PKG/icono.png"
cp LEEME.md "$PKG/LEEME.md"
cp installer/instalar-linux.sh "$PKG/instalar-linux.sh"
chmod +x "$PKG/instalar-linux.sh" "$PKG/DescargadorYConversor/DescargadorYConversor"

TARBALL="$SALIDA/DescargadorYConversor-${VERSION}-Linux.tar.gz"
tar -czf "$TARBALL" -C "$PKG" .
rm -rf "$PKG"

echo
echo "Listo: $TARBALL"
du -h "$TARBALL"

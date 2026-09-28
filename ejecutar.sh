#!/bin/sh
# Lanza EstrésPC con el entorno del proyecto.
cd "$(dirname "$(readlink -f "$0")")" && exec uv run --quiet python -m estrespc "$@"

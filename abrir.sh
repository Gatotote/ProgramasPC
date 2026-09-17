#!/usr/bin/env bash
# Lanza el Descargador y Conversor con su venv.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
exec .venv/bin/python main.py "$@"

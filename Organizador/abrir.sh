#!/usr/bin/env bash
# Lanza el Organizador de Archivos con su venv.
cd "$(dirname "$(readlink -f "$0")")" || exit 1
exec .venv/bin/python main.py "$@"

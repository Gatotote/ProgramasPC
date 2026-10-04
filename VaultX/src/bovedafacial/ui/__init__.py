"""Interfaz PySide6 «VaultX».

Pieza 1 (hecha): tema, asistente de primer arranque, ventana de desbloqueo
(PIN + rostro con vista previa), enrolado.
Pieza 2 (pendiente): ventana principal — barra lateral, tarjetas por categoría,
panel de actividad, editor de elementos, botón «Agregar».

Requiere:  uv sync --extra gui --extra face
Se lanza con:  bovedafacial-gui
"""

from .app import main

__all__ = ["main"]

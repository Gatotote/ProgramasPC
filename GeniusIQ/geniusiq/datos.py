"""Historial: personas y sesiones en SQLite (~/.local/share/geniusiq/geniusiq.db)."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path

RUTA = Path(os.environ.get("GENIUSIQ_DB", Path.home() / ".local/share/geniusiq/geniusiq.db"))
RUTA_VIEJA = Path.home() / ".local/share/testiq/testiq.db"   # cuando el programa se llamaba TestIQ


def edad(nacimiento: str, hoy: date | None = None) -> float:
    """Edad en años (con decimales)."""
    return ((hoy or date.today()) - date.fromisoformat(nacimiento)).days / 365.25


def _json(resultado: dict) -> str:
    """El resultado sin las llaves de uso interno (las que empiezan con «_», como _id)."""
    return json.dumps({k: v for k, v in resultado.items() if not k.startswith("_")}, ensure_ascii=False)


class BaseDatos:
    def __init__(self, ruta: Path = RUTA):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if "GENIUSIQ_DB" not in os.environ and not ruta.exists() and RUTA_VIEJA.exists():
            shutil.move(RUTA_VIEJA, ruta)  # trae el historial de cuando se llamaba TestIQ
        self.con = sqlite3.connect(ruta)
        self.con.row_factory = sqlite3.Row
        self.con.executescript("""
            CREATE TABLE IF NOT EXISTS personas (
                id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, nacimiento TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY, persona_id INTEGER NOT NULL REFERENCES personas(id),
                fecha TEXT NOT NULL, bateria TEXT NOT NULL, ci INTEGER, resultado TEXT NOT NULL);
        """)

    def personas(self) -> list[sqlite3.Row]:
        return self.con.execute("SELECT * FROM personas ORDER BY nombre").fetchall()

    def agregar_persona(self, nombre: str, nacimiento: str) -> int:
        with self.con:
            return self.con.execute("INSERT INTO personas (nombre, nacimiento) VALUES (?, ?)",
                                    (nombre, nacimiento)).lastrowid

    def guardar_sesion(self, persona_id: int, resultado: dict) -> int:
        ci = resultado["total"]["ci"] if resultado.get("total") else None
        with self.con:
            return self.con.execute(
                "INSERT INTO sesiones (persona_id, fecha, bateria, ci, resultado) VALUES (?, ?, ?, ?, ?)",
                (persona_id, datetime.now().isoformat(timespec="minutes"), resultado["nombre_bateria"],
                 ci, _json(resultado))).lastrowid

    def actualizar_resultado(self, sesion_id: int, resultado: dict) -> None:
        """Reescribe el resultado guardado (p. ej. al añadir el análisis de reacciones)."""
        with self.con:
            self.con.execute("UPDATE sesiones SET resultado = ? WHERE id = ?", (_json(resultado), sesion_id))

    def sesiones(self) -> list[sqlite3.Row]:
        return self.con.execute("""
            SELECT s.*, p.nombre FROM sesiones s JOIN personas p ON p.id = s.persona_id
            ORDER BY s.fecha DESC""").fetchall()

    def borrar_sesion(self, sesion_id: int) -> None:
        with self.con:
            self.con.execute("DELETE FROM sesiones WHERE id = ?", (sesion_id,))

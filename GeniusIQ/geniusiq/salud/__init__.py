"""Tamizaje de salud mental con cuestionarios validados de uso libre (PHQ-9, GAD-7, ASRS, AUDIT, PCL-5).

Un tamizaje NO es un diagnóstico: solo indica si conviene una evaluación profesional.
Las traducciones son propias; antes de usarlo con la familia lo deben revisar
psicólogos o psiquiatras (comparar contra las versiones oficiales en español).
"""

from __future__ import annotations

# Cambiar a True solo cuando un profesional haya revisado las traducciones y los textos.
REVISADO = False

AVISO_SALUD = ("⚠ Esto es un tamizaje (detección), NO un diagnóstico. Un puntaje alto solo indica que conviene "
               "platicarlo con un médico, psicólogo o psiquiatra. Un puntaje bajo no descarta un problema si "
               "algo te preocupa.")

AVISO_REVISION = ("🔒 En revisión: las traducciones todavía no las revisa un profesional. "
                  "No lo uses con la familia hasta entonces.")

CRISIS = ("Si piensas en hacerte daño o en quitarte la vida, no estás solo(a) y hay ayuda ahora mismo:\n"
          "• Línea de la Vida: 800 911 2000 (gratis, 24 horas, todo México)\n"
          "• SAPTEL: 55 5259 8121 (24 horas)\n"
          "• Emergencias: 911\n"
          "Habla también con alguien de confianza hoy mismo.")

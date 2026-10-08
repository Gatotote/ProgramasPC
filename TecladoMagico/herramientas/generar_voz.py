"""Genera tecladomagico/voz/<letra>.wav y <número>.wav (1 a 10) con Piper (voz es_MX-claude-high).

Solo se corre al cambiar textos o voz; el programa usa los WAV ya hechos (no necesita Piper).
Modelo en herramientas/modelos/ (no va al repo):
  https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_MX/claude/high
Uso: uv run python herramientas/generar_voz.py
"""

import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig

from tecladomagico.juego import LETRAS

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "herramientas" / "modelos" / "es_MX-claude-high.onnx"
SALIDA = RAIZ / "tecladomagico" / "voz"

NOMBRES = {
    "a": "a", "b": "be", "c": "ce", "d": "de", "e": "e", "f": "efe", "g": "ge", "h": "hache",
    "i": "i", "j": "jota", "k": "ka", "l": "ele", "m": "eme", "n": "ene", "ñ": "eñe", "o": "o",
    "p": "pe", "q": "cu", "r": "erre", "s": "ese", "t": "te", "u": "u", "v": "uve", "w": "doble uve",
    "x": "equis", "y": "ye", "z": "zeta",
}

NUMEROS = ["uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez"]


def main():
    voz = PiperVoice.load(MODELO)
    config = SynthesisConfig(length_scale=1.15)  # un poquito más lento, para bebé
    SALIDA.mkdir(exist_ok=True)
    for letra, (_dibujo, palabra) in LETRAS.items():
        texto = f"¡{NOMBRES[letra].capitalize()}! ... {palabra}."
        with wave.open(str(SALIDA / f"{letra}.wav"), "wb") as wav:
            voz.synthesize_wav(texto, wav, syn_config=config)
        print(letra, "→", texto)
    for n, nombre in enumerate(NUMEROS, start=1):
        texto = f"¡{nombre.capitalize()}!"
        with wave.open(str(SALIDA / f"{n}.wav"), "wb") as wav:
            voz.synthesize_wav(texto, wav, syn_config=config)
        print(n, "→", texto)


if __name__ == "__main__":
    main()

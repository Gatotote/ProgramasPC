"""Sonidos sintetizados al vuelo (notas tipo marimba, «boing», arpegios) y la voz de las letras (WAV)."""

from pathlib import Path

import numpy as np
import pygame

TASA = 44100
VOLUMEN = 0.35
CARPETA_VOZ = Path(__file__).resolve().parent / "voz"  # WAV hechos con herramientas/generar_voz.py

# Escala pentatónica de Do: nunca suena feo, aunque apriete diez teclas a la vez.
_PENTA = [261.63, 293.66, 329.63, 392.00, 440.00]
ESCALA = [f * o for o in (1, 2, 4) for f in _PENTA]


def _a_sonido(onda):
    onda = np.clip(onda, -1, 1)
    datos = (onda * 32767 * VOLUMEN).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([datos, datos]))


def _envolvente(n, ataque=0.005, caida=5.0):
    t = np.arange(n) / TASA
    env = np.exp(-t * caida)
    na = int(ataque * TASA)
    env[:na] *= np.linspace(0, 1, na)
    return env


def nota(freq, dur=0.9):
    n = int(TASA * dur)
    t = np.arange(n) / TASA
    onda = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return _a_sonido(onda / 1.5 * _envolvente(n))


def boing(dur=0.55):
    n = int(TASA * dur)
    t = np.arange(n) / TASA
    freq = 220 + 380 * (t / dur) + 25 * np.sin(2 * np.pi * 9 * t)
    fase = 2 * np.pi * np.cumsum(freq) / TASA
    return _a_sonido(np.sin(fase) * _envolvente(n, caida=4.0))


def arpegio(dur=0.7):
    paso = int(TASA * 0.07)
    total = np.zeros(int(TASA * dur) + paso * 5)
    for i, f in enumerate(ESCALA[5:11]):
        n = int(TASA * 0.45)
        t = np.arange(n) / TASA
        trozo = np.sin(2 * np.pi * f * t) * _envolvente(n, caida=7.0)
        total[i * paso:i * paso + n] += trozo * 0.6
    return _a_sonido(total)


class Sonidos:
    def __init__(self):
        self.ok = pygame.mixer.get_init() is not None
        if not self.ok:
            return
        pygame.mixer.set_num_channels(16)
        self.notas = [nota(f) for f in ESCALA]
        self.boing = boing()
        self.arpegio = arpegio()
        self.voces = {}
        for wav in CARPETA_VOZ.glob("*.wav"):
            self.voces[wav.stem] = pygame.mixer.Sound(wav)
        pygame.mixer.set_reserved(1)  # el canal 0 queda solo para la voz
        self.canal_voz = pygame.mixer.Channel(0)
        self.canal_voz.set_volume(0.8)
        self._ultimos = []  # momentos de los últimos sonidos, para no saturar si aplasta todo el teclado

    def _permitido(self, ahora):
        self._ultimos = [t for t in self._ultimos if ahora - t < 0.12]
        if len(self._ultimos) >= 3:
            return False
        self._ultimos.append(ahora)
        return True

    def tocar(self, sonido, ahora):
        if self.ok and self._permitido(ahora):
            sonido.play()

    def decir(self, clave):
        """Dice la letra (con su palabra) o el número; si ya estaba hablando, lo corta (no se encima una voz con otra)."""
        if not self.ok or clave not in self.voces:
            return False
        self.canal_voz.play(self.voces[clave])
        return True

    def tocar_nota(self, indice, ahora):
        if self.ok:
            self.tocar(self.notas[indice % len(self.notas)], ahora)

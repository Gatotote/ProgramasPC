"""Escucha lo que mandan de verdad los teclados (a nivel del kernel) durante unos segundos.

Necesita sudo (los /dev/input/event* son del grupo input):
  sudo python3 herramientas/escuchar_teclado.py [segundos]
Deja el resultado en /tmp/escucha-teclado.txt (y lo muestra).
"""

import select
import sys
import time

from evdev import InputDevice, categorize, ecodes, list_devices

segundos = float(sys.argv[1]) if len(sys.argv) > 1 else 20
teclados = [d for d in map(InputDevice, list_devices()) if ecodes.EV_KEY in d.capabilities()]
print(f"Escuchando {len(teclados)} dispositivos {segundos:.0f} s… aprieta la F3 del Logitech", flush=True)
lineas = []
fin = time.time() + segundos
while time.time() < fin:
    listos, _, _ = select.select(teclados, [], [], 0.5)
    for d in listos:
        for ev in d.read():
            if ev.type in (ecodes.EV_KEY, ecodes.EV_MSC):
                linea = f"{ev.timestamp():.3f}  {d.name}  {categorize(ev)}"
                print(linea, flush=True)
                lineas.append(linea)
with open("/tmp/escucha-teclado.txt", "w") as f:
    f.write("\n".join(lineas) + "\n")
print("Listo.")

"""Convierte un HDRI (.exr o .hdr, equirectangular 2:1) a un arreglo numpy float16 para el render.

    blender --background --factory-startup --python convertir_hdri.py -- ORIGEN DESTINO.npy [ANCHO]

El render lo carga directo (sin librerías de EXR). ANCHO por defecto 2048 (alto = ANCHO/2).
"""
import os
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
origen, destino = os.path.abspath(args[0]), os.path.abspath(args[1])
ancho = int(args[2]) if len(args) > 2 else 2048
img = bpy.data.images.load(origen)
img.scale(ancho, ancho // 2)
px = np.empty(ancho * (ancho // 2) * 4, dtype=np.float32)
img.pixels.foreach_get(px)
rgb = px.reshape(ancho // 2, ancho, 4)[:, :, :3]          # filas de abajo hacia arriba (como OpenGL)
os.makedirs(os.path.dirname(destino), exist_ok=True)
np.save(destino, np.clip(rgb, 0, 65000).astype(np.float16))
print(f"[hdri] {origen} -> {destino} {ancho}x{ancho // 2} máx={rgb.max():.1f} prom={rgb.mean():.3f}", flush=True)

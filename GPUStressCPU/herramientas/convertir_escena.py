"""Convierte una escena 3D (FBX, glTF o USD) a un solo .glb listo para el render de GPUStressCPU.
Se corre con Blender en segundo plano:

    blender --background --factory-startup --python convertir_escena.py -- ORIGEN DESTINO.glb [MAX_PX] [MAX_TRIS]

- Reduce cada textura a MAX_PX (2048 por defecto) en su lado mayor: las escenas de 4K no caben en
  6 GB de VRAM, y a 2K la GPU sigue trabajando al máximo.
- Si la escena pasa de MAX_TRIS triángulos (0 = sin tope), simplifica cada malla ORIGINAL una sola vez
  (Decimate): sus copias/instancias quedan simplificadas igual, sin gastar memoria de más.
- Aplica las transformaciones y exporta un GLB con Y hacia arriba (convención glTF).
"""
import os
import sys
import time

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
origen, destino = os.path.abspath(args[0]), os.path.abspath(args[1])
max_px = int(args[2]) if len(args) > 2 else 2048
max_tris = int(args[3]) if len(args) > 3 else 0
t0 = time.time()


def log(*a):
    print(f"[convertir {time.time() - t0:6.1f}s]", *a, flush=True)


ext = origen.lower().rsplit(".", 1)[-1]
log("importando", origen)
if ext == "blend":
    bpy.ops.wm.open_mainfile(filepath=origen)
    # Instancias de colecciones / partículas → objetos reales, para que el glTF las incluya.
    bpy.ops.object.select_all(action="SELECT")
    try:
        bpy.ops.object.duplicates_make_real()
    except Exception as e:
        log("sin instancias que convertir:", e)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
if ext == "blend":
    pass
elif ext == "fbx":
    bpy.ops.import_scene.fbx(filepath=origen, use_image_search=True)
elif ext in ("gltf", "glb"):
    bpy.ops.import_scene.gltf(filepath=origen)
elif ext in ("usd", "usda", "usdc", "usdz"):
    bpy.ops.wm.usd_import(filepath=origen)
else:
    sys.exit(f"formato no soportado: {ext}")

mallas = [o for o in bpy.context.scene.objects if o.type == "MESH"]
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in mallas)
log(f"{len(mallas)} mallas · ~{tris:,} triángulos · {len(bpy.data.images)} imágenes · "
    f"{len(bpy.data.materials)} materiales")

if max_tris and tris > max_tris:
    factor = max_tris / tris
    grafo = bpy.context.evaluated_depsgraph_get()
    usuarios = {}
    for o in mallas:
        usuarios.setdefault(o.data, []).append(o)
    simplificadas = 0
    for malla, objs in usuarios.items():
        n = sum(len(p.vertices) - 2 for p in malla.polygons)
        if n < 500:               # piezas chicas: no vale la pena
            continue
        o = objs[0]
        mod = o.modifiers.new("simplificar", "DECIMATE")
        mod.ratio = max(0.02, factor)
        grafo.update()
        nueva = bpy.data.meshes.new_from_object(o.evaluated_get(grafo))
        o.modifiers.remove(mod)
        for u in objs:
            u.data = nueva
        simplificadas += 1
    bpy.data.orphans_purge(do_recursive=True)   # libera las mallas originales ya reemplazadas
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in mallas)
    log(f"simplificadas {simplificadas} mallas originales (factor {factor:.2f}) → ~{tris:,} triángulos")

reducidas = faltan = 0
for img in bpy.data.images:
    if img.source != "FILE":
        continue
    # (No leer img.pixels desde Python: copia la imagen entera como flotantes y agota la RAM.)
    w, h = img.size
    if w == 0 or h == 0:
        faltan += 1
        continue
    if max(w, h) > max_px:
        f = max_px / max(w, h)
        img.scale(max(1, int(w * f)), max(1, int(h * f)))
        reducidas += 1
log(f"texturas reducidas a {max_px}px: {reducidas} · sin cargar: {faltan}")

os.makedirs(os.path.dirname(destino), exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.data.orphans_purge(do_recursive=True)
import resource
log(f"memoria antes de exportar: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20:.1f} GB (pico)")
bpy.ops.export_scene.gltf(filepath=destino, export_format="GLB", export_yup=True,
                          export_apply=True, export_image_format="AUTO",
                          export_jpeg_quality=90, export_animations=False,
                          export_cameras=False, export_lights=False)
log(f"listo: {destino} ({os.path.getsize(destino) / 2**20:.0f} MB)")

"""Proceso aparte que estresa la GPU por OpenCL y verifica los resultados.

Cada elemento calcula varias cadenas caóticas (mapa logístico con fma). Los
elementos con el mismo índice módulo 1024 deben dar exactamente los mismos
bits; cualquier diferencia es un error de cómputo o de VRAM. El caos amplifica
cualquier bit volteado, así que un error no pasa desapercibido.

Salida: una línea JSON por evento en stdout.
"""

import argparse
import json
import signal
import sys
import time
import warnings

import numpy as np
import pyopencl as cl

warnings.filterwarnings("ignore", category=cl.CompilerWarning)

KERNEL = r"""
#define CADENAS 8
__kernel void quemar(__global float *salida, const int vueltas) {
    size_t gid = get_global_id(0);
    uint s = (uint)(gid & 1023u);
    float x[CADENAS];
    for (int k = 0; k < CADENAS; k++)
        x[k] = 0.1f + 0.8f * (float)(s * CADENAS + k) / (1024.0f * CADENAS);
    const float r = 3.9f;
    for (int i = 0; i < vueltas; i++) {
        #pragma unroll
        for (int k = 0; k < CADENAS; k++) {
            float rx = x[k] * r;
            x[k] = fma(rx, -x[k], rx);
        }
    }
    float suma = 0.0f;
    for (int k = 0; k < CADENAS; k++) suma += x[k];
    salida[gid] = suma;
}

__kernel void verificar(__global const float *salida, __global uint *errores) {
    size_t gid = get_global_id(0);
    if (as_uint(salida[gid]) != as_uint(salida[gid & 1023u]))
        atomic_inc(errores);
}
"""
FLOPS_POR_VUELTA = 8 * 3  # CADENAS × (mul + fma)
OBJETIVO_SEG = 0.15  # duración deseada de cada lanzamiento


def emitir(**datos):
    print(json.dumps(datos), flush=True)


def dispositivos():
    lista = []
    for p, plataforma in enumerate(cl.get_platforms()):
        try:
            devs = plataforma.get_devices(device_type=cl.device_type.GPU)
        except cl.Error:
            continue
        for d, dev in enumerate(devs):
            lista.append({"id": f"{p}:{d}", "nombre": dev.name.strip(),
                          "plataforma": plataforma.name.strip(),
                          "memoria": dev.global_mem_size})
    return lista


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--dispositivo", default="")
    ap.add_argument("--memoria", type=float, default=0.7, help="fracción de VRAM a usar")
    args = ap.parse_args()

    if args.listar:
        emitir(tipo="dispositivos", lista=dispositivos())
        return 0

    parar = False

    def al_senal(*_):
        nonlocal parar
        parar = True

    signal.signal(signal.SIGINT, al_senal)
    signal.signal(signal.SIGTERM, al_senal)

    lista = dispositivos()
    if not lista:
        emitir(tipo="error", mensaje="No se encontró ninguna GPU con OpenCL")
        return 1
    elegido = next((x for x in lista if x["id"] == args.dispositivo), lista[0])
    p, d = map(int, elegido["id"].split(":"))
    dev = cl.get_platforms()[p].get_devices(device_type=cl.device_type.GPU)[d]
    ctx = cl.Context([dev])
    cola = cl.CommandQueue(ctx)
    prog = cl.Program(ctx, KERNEL).build()
    quemar = cl.Kernel(prog, "quemar")
    verificar = cl.Kernel(prog, "verificar")

    # Reparte la VRAM pedida en búferes del tamaño máximo permitido.
    total = int(dev.global_mem_size * min(max(args.memoria, 0.05), 0.9))
    max_bufer = dev.max_mem_alloc_size
    bufs = []
    try:
        while total >= 64 << 20:
            tam = min(total, max_bufer) // (4 * 1024) * (4 * 1024)
            b = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, tam)
            # Tocar el búfer para que el driver lo reserve de verdad.
            cl.enqueue_fill_buffer(cola, b, np.float32(0), 0, tam)
            cola.finish()
            bufs.append((b, tam // 4))
            total -= tam
    except cl.Error as e:
        if not bufs:
            emitir(tipo="error", mensaje=f"No se pudo reservar VRAM: {e}")
            return 1
    usados = sum(n for _, n in bufs) * 4
    errores_buf = cl.Buffer(ctx, cl.mem_flags.READ_WRITE, 4)
    cl.enqueue_fill_buffer(cola, errores_buf, np.uint32(0), 0, 4)
    emitir(tipo="inicio", dispositivo=elegido["nombre"], vram_mb=usados >> 20)

    vueltas = 16
    errores = np.zeros(1, dtype=np.uint32)
    flops = 0
    t_reporte = time.monotonic()
    while not parar:
        for b, n in bufs:
            if parar:
                break
            t0 = time.monotonic()
            quemar(cola, (n,), None, b, np.int32(vueltas))
            verificar(cola, (n,), None, b, errores_buf)
            cola.finish()
            dt = time.monotonic() - t0
            flops += n * vueltas * FLOPS_POR_VUELTA
            # Ajusta el trabajo para que cada lanzamiento dure ~OBJETIVO_SEG.
            if dt > 0:
                vueltas = int(min(max(vueltas * OBJETIVO_SEG / dt, 1), 4096))
        ahora = time.monotonic()
        if ahora - t_reporte >= 1.0:
            cl.enqueue_copy(cola, errores, errores_buf)
            emitir(tipo="progreso", gflops=round(flops / (ahora - t_reporte) / 1e9, 1),
                   errores=int(errores[0]))
            flops = 0
            t_reporte = ahora

    cl.enqueue_copy(cola, errores, errores_buf)
    emitir(tipo="fin", errores=int(errores[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

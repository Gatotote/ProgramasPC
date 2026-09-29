"""Proceso aparte para las mediciones del benchmark que no tienen herramienta externa.

    python -m estrespc.bench_trabajador ram   [--procesos 4] [--segundos 3]
    python -m estrespc.bench_trabajador disco --carpeta RUTA [--mb 1024] [--segundos 8]

Salida: una línea JSON por evento en stdout (igual que los otros trabajadores).
"""

import argparse
import json
import mmap
import multiprocessing as mp
import os
import random
import sys
import time

MB = 1 << 20


def emitir(**datos):
    print(json.dumps(datos), flush=True)


# ------------------------------------------------------------------ RAM
def _copiar(segundos, cola):
    import numpy as np
    a = np.ones(256 * MB // 8)  # 256 MB: mucho más grande que la caché
    b = np.empty_like(a)
    np.copyto(b, a)             # calentar (reservar páginas)
    n, t0 = 0, time.perf_counter()
    while time.perf_counter() - t0 < segundos:
        np.copyto(b, a)
        n += 1
    # Cada copia lee a y escribe b: 2 × tamaño de tráfico de memoria.
    cola.put(n * 2 * a.nbytes / (time.perf_counter() - t0))


def ram(procesos, segundos):
    mejor = 0.0
    for ronda in range(3):
        cola = mp.Queue()
        ps = [mp.Process(target=_copiar, args=(segundos, cola)) for _ in range(procesos)]
        for p in ps:
            p.start()
        total = sum(cola.get() for _ in ps)
        for p in ps:
            p.join()
        emitir(tipo="progreso", ronda=ronda + 1, gbs=round(total / 1e9, 2))
        mejor = max(mejor, total)
    emitir(tipo="resultado", gbs=round(mejor / 1e9, 2))


# ------------------------------------------------------------------ disco
def _bufer(tam):
    """Búfer alineado a página (O_DIRECT lo exige) con datos aleatorios
    (así la compresión del sistema de archivos no infla el resultado)."""
    b = mmap.mmap(-1, tam)
    b.write(os.urandom(tam))
    return b


def _en_paralelo(fd, mb, escribir, hilos=4, tam_bloque=8 * MB):
    """Reparte el archivo en `hilos` tramos y los lee/escribe a la vez con
    bloques de 8 MB (como hacen los benchmarks secuenciales conocidos)."""
    from concurrent.futures import ThreadPoolExecutor
    por_hilo = mb * MB // hilos

    def tramo(i):
        buf = _bufer(tam_bloque)
        inicio = i * por_hilo
        for off in range(inicio, inicio + por_hilo, tam_bloque):
            if escribir:
                os.pwritev(fd, [buf], off)
            else:
                os.preadv(fd, [buf], off)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(hilos) as ex:
        list(ex.map(tramo, range(hilos)))
    if escribir:
        os.fsync(fd)
    return mb / (time.perf_counter() - t0)


def disco(carpeta, mb, segundos):
    ruta = os.path.join(carpeta, f".estrespc-benchmark-{os.getpid()}.tmp")
    mb = max(64, mb // 32 * 32)  # múltiplo de 4 hilos × 8 MB
    try:
        # Escritura y lectura secuencial directas (sin caché del sistema).
        fd = os.open(ruta, os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_DIRECT, 0o600)
        os.ftruncate(fd, mb * MB)
        esc = _en_paralelo(fd, mb, escribir=True)
        emitir(tipo="progreso", paso="escritura", mbs=round(esc))
        lee = _en_paralelo(fd, mb, escribir=False)
        emitir(tipo="progreso", paso="lectura", mbs=round(lee))

        # Lectura aleatoria de 4 KB, una a la vez (QD1): la que se siente al abrir programas.
        chico = mmap.mmap(-1, 4096)
        bloques = mb * MB // 4096
        n, t0 = 0, time.perf_counter()
        while time.perf_counter() - t0 < segundos:
            os.preadv(fd, [chico], random.randrange(bloques) * 4096)
            n += 1
        iops = n / (time.perf_counter() - t0)
        os.close(fd)
        emitir(tipo="resultado", escritura_mbs=round(esc), lectura_mbs=round(lee),
               aleatoria_iops=round(iops))
    except OSError as e:
        emitir(tipo="error", mensaje=f"Disco: {e}")
        return 1
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prueba", choices=["ram", "disco"])
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--segundos", type=float, default=0)
    ap.add_argument("--carpeta", default=os.path.expanduser("~"))
    ap.add_argument("--mb", type=int, default=1024)
    args = ap.parse_args()
    if args.prueba == "ram":
        ram(args.procesos, args.segundos or 3)
        return 0
    return disco(args.carpeta, args.mb, args.segundos or 8)


if __name__ == "__main__":
    sys.exit(main())

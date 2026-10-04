"""Prueba manual del motor facial con la webcam real.

    uv run --extra face python scripts/face_smoke.py            # info + 1 captura
    uv run --extra face python scripts/face_smoke.py --enroll   # enrola y se verifica

La primera ejecución descarga el pack antelopev2 (~260 MB) a ~/.insightface/.
No abre ventanas: usa la cámara, imprime métricas y termina.
"""

from __future__ import annotations

import argparse
import sys
import time

from bovedafacial.face import (
    FaceEngine,
    available_providers,
    default_camera,
    enroll_from_frames,
    list_v4l2_devices,
    models_present,
    verify,
)
from bovedafacial.face.quality import QualityGate, sharpness


def _frames(cam, n, delay=0.06):
    for _ in range(n):
        yield cam.read()
        time.sleep(delay)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enroll", action="store_true", help="enrola y luego se verifica")
    ap.add_argument("--frames", type=int, default=60)
    args = ap.parse_args()

    print("Providers onnxruntime:", available_providers())
    print("Cámaras:", list_v4l2_devices() or "ninguna")
    print("Modelo antelopev2 presente:", models_present())

    print("\nCargando motor (puede tardar / descargar la primera vez)...")
    t0 = time.time()
    engine = FaceEngine().load()
    print(f"  motor listo en {time.time() - t0:.1f}s | GPU={engine.on_gpu} | {engine.providers}")

    try:
        cam = default_camera()
    except Exception as e:  # noqa: BLE001
        print("No hay cámara utilizable:", e)
        return 1

    with cam:
        frame = cam.read()
        print(f"\nFrame: {frame.shape[1]}x{frame.shape[0]}")
        t0 = time.time()
        face = engine.primary_face(frame)
        dt = (time.time() - t0) * 1000
        if face is None:
            print(f"  sin rostro ({dt:.0f} ms). Ponte frente a la cámara con buena luz.")
            return 1
        gate = QualityGate()
        print(f"  rostro: det_score={face.det_score:.3f} inferencia={dt:.0f} ms")
        print(f"  bbox={face.bbox.astype(int).tolist()} ancho_rel={face.width / frame.shape[1]:.2f}")
        print(f"  pose(pitch,yaw,roll)={None if face.pose is None else face.pose.round(1).tolist()}")
        print(f"  nitidez={sharpness(frame, face):.0f}")
        print(f"  embedding={None if face.embedding is None else face.embedding.shape} "
              f"norma={None if face.embedding is None else round(float((face.embedding**2).sum()**0.5), 3)}")
        problems = gate.check(frame.shape, face, sharpness(frame, face))
        print("  calidad:", "OK" if not problems else problems)

        if args.enroll:
            print(f"\nEnrolando con ~{args.frames} frames, mira a la cámara y muévete un poco...")
            tpl = enroll_from_frames(engine, _frames(cam, args.frames), target=10)
            print(f"  plantilla: {tpl.count} muestras | consistencia={tpl.self_consistency():.3f}")
            time.sleep(0.5)
            probe = None
            for _ in range(20):
                probe = engine.embedding(cam.read())
                if probe is not None:
                    break
            res = verify(probe, tpl.embeddings, threshold=tpl.threshold)
            print(f"  verificación: score={res.score:.3f} umbral={res.threshold} -> "
                  f"{'ACEPTADO' if res.matched else 'RECHAZADO'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

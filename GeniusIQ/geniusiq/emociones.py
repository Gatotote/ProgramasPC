"""Análisis de reacciones: emoción aparente de la cara en un video, alineada con las marcas de la prueba.

Modelo: HSEmotion «enet_b2_8» (Savchenko, Apache 2.0), entrenado con AffectNet; 8 expresiones,
63 % de acierto en AffectNet-8 (el más preciso de los gratuitos; las personas coinciden ~60 % en esas fotos).
Cara: YuNet (OpenCV Zoo, MIT), el detector de caras moderno de OpenCV.
Todo corre local, en el procesador; nada sale de la computadora.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import numpy as np

MODELO = Path(__file__).resolve().parent / "modelos" / "enet_b2_8.onnx"
LADO = 260   # tamaño de entrada del enet_b2 (el b0 usaba 224)
DETECTOR = Path(__file__).resolve().parent / "modelos" / "face_detection_yunet_2023mar.onnx"
NOMBRE_MODELO = "HSEmotion enet_b2_8 (AffectNet)"
EMOCIONES = ["Enojo", "Desprecio", "Asco", "Miedo", "Alegría", "Neutral", "Tristeza", "Sorpresa"]
NEUTRAL = EMOCIONES.index("Neutral")
MUESTRAS_POR_SEG = 3
CORTES = ("instrucciones", "inicio", "pregunta", "fin")   # tipos de marca que abren un tramo nuevo

AVISO = ("ℹ La emoción se estima solo por la expresión de la cara (sonrisa, ceño, cejas…), no por lo que la "
         "persona siente por dentro. Es aproximada: la luz, los lentes o voltear la cara la confunden.")


class Analizador:
    def __init__(self):
        import cv2
        import onnxruntime as ort
        self.cv2 = cv2
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        self.sesion = ort.InferenceSession(str(MODELO), providers=["CPUExecutionProvider"])
        self.caras = cv2.FaceDetectorYN.create(str(DETECTOR), "", (320, 320), 0.8)

    def cara(self, cuadro: np.ndarray) -> np.ndarray | None:
        """Recorta la cara más grande del cuadro (BGR); None si no hay."""
        cv2 = self.cv2
        alto, ancho = cuadro.shape[:2]
        escala = 640 / max(alto, ancho) if max(alto, ancho) > 640 else 1.0
        chico = cv2.resize(cuadro, None, fx=escala, fy=escala) if escala < 1 else cuadro
        self.caras.setInputSize((chico.shape[1], chico.shape[0]))
        _, encontradas = self.caras.detect(chico)
        if encontradas is None or len(encontradas) == 0:
            return None
        x, y, w, h = (float(v) / escala for v in max(encontradas, key=lambda r: r[2] * r[3])[:4])
        m = 0.12 * w
        x0, y0 = int(max(0, x - m)), int(max(0, y - m))
        x1, y1 = int(min(ancho, x + w + m)), int(min(alto, y + h + m))
        return cuadro[y0:y1, x0:x1]

    def probabilidades(self, cara_bgr: np.ndarray) -> np.ndarray:
        cv2 = self.cv2
        x = cv2.resize(cv2.cvtColor(cara_bgr, cv2.COLOR_BGR2RGB), (LADO, LADO)).astype(np.float32) / 255
        x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
        logits = self.sesion.run(None, {"input": x.transpose(2, 0, 1)[np.newaxis].astype(np.float32)})[0][0]
        e = np.exp(logits - logits.max())
        return e / e.sum()


def analizar(video: str | Path, progreso: Callable[[float], None] | None = None,
             cancelado: Callable[[], bool] | None = None) -> list[list]:
    """Recorre el video y regresa muestras [segundo, p0..p7] (sin probabilidades si no se vio la cara).

    Regresa None si se canceló.
    """
    an = Analizador()
    cap = an.cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video:\n{video}")
    total = cap.get(an.cv2.CAP_PROP_FRAME_COUNT) or 0
    muestras: list[list] = []
    siguiente = 0.0
    n = 0
    while True:
        if not cap.grab():
            break
        n += 1
        t = cap.get(an.cv2.CAP_PROP_POS_MSEC) / 1000
        if t + 1e-6 < siguiente:
            continue
        siguiente = t + 1 / MUESTRAS_POR_SEG
        ok, cuadro = cap.retrieve()
        if not ok:
            continue
        cara = an.cara(cuadro)
        muestras.append([round(t, 2)] + ([] if cara is None or cara.size == 0
                                         else [round(float(v), 4) for v in an.probabilidades(cara)]))
        if progreso and total:
            progreso(min(1.0, n / total))
        if cancelado and cancelado():
            cap.release()
            return None
    cap.release()
    return muestras


def _media(filas: list[list]) -> list[float] | None:
    con = [m[1:] for m in filas if len(m) > 1]
    return [round(float(v), 4) for v in np.mean(con, axis=0)] if con else None


def _porcentajes(filas: list[list]) -> dict:
    """% del tiempo con cara en que cada emoción fue la principal."""
    con = [int(np.argmax(m[1:])) for m in filas if len(m) > 1]
    return {EMOCIONES[i]: round(100 * con.count(i) / len(con), 1) for i in range(len(EMOCIONES))} if con else {}


def resumir(muestras: list[list], eventos: list[dict]) -> dict:
    """Reparte las muestras en tramos (de una marca a la siguiente) y saca la emoción de cada uno."""
    fin = max([m[0] for m in muestras] + [e["t"] for e in eventos] + [0]) + 0.01
    cortes = [e for e in eventos if e["tipo"] in CORTES]
    tramos = []
    for k, e in enumerate(cortes):
        t0, t1 = e["t"], cortes[k + 1]["t"] if k + 1 < len(cortes) else fin
        if e["tipo"] == "fin" or t1 - t0 < 0.3:
            continue
        dentro = [m for m in muestras if t0 <= m[0] < t1]
        resp = [r for r in eventos if r["tipo"] == "respuesta" and t0 <= r["t"] < t1 + 0.05]
        media = _media(dentro)
        tramo = {"t0": round(t0, 1), "t1": round(t1, 1), "tipo": e["tipo"], "texto": e["texto"],
                 "respuesta": resp[-1]["texto"] if resp else "", "correcta": resp[-1].get("ok") if resp else None,
                 "cara": round(100 * sum(len(m) > 1 for m in dentro) / len(dentro)) if dentro else 0,
                 "media": media}
        if media:
            tramo["emocion"] = EMOCIONES[int(np.argmax(media))]
            otras = [(v, i) for i, v in enumerate(media) if i != NEUTRAL]
            v, i = max(otras)
            tramo["reaccion"] = EMOCIONES[i] if v >= 0.25 else ""
            tramo["fuerza"] = round(v, 2)
        tramos.append(tramo)

    comparacion = {}
    for clave, nombre in ((True, "Al acertar"), (False, "Al fallar")):
        filas = [m for tr in tramos if tr["correcta"] is clave for m in muestras if tr["t0"] <= m[0] < tr["t1"]]
        if filas:
            comparacion[nombre] = _porcentajes(filas)

    linea = []   # emoción principal de cada segundo (-1 = no se vio la cara)
    for s in range(int(fin) + 1):
        media = _media([m for m in muestras if s <= m[0] < s + 1])
        linea.append(int(np.argmax(media)) if media else -1)

    return {"modelo": NOMBRE_MODELO, "duracion": round(fin, 1),
            "cara": round(100 * sum(len(m) > 1 for m in muestras) / len(muestras)) if muestras else 0,
            "distribucion": _porcentajes(muestras), "comparacion": comparacion, "linea": linea,
            "tramos": tramos}


def guardar_muestras(video: str | Path, muestras: list[list]) -> Path:
    ruta = Path(video).with_suffix(".emociones.json")
    ruta.write_text(json.dumps({"modelo": NOMBRE_MODELO, "emociones": EMOCIONES, "muestras": muestras}))
    return ruta

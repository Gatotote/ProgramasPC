"""Motor de reconocimiento facial (Fase 2).

Se implementará sobre InsightFace con el pack `antelopev2` (ResNet100 glint360k,
la mayor precisión disponible) + onnxruntime-GPU. Módulos previstos:

    camera.py  -> abstracción de la fuente de vídeo (v4l2 / cámara IP / archivo)
    engine.py  -> carga del modelo y cálculo de embeddings de 512-d
    enroll.py  -> captura de N frames + liveness (parpadeo/giro) + plantillas
    verify.py  -> coincidencia por similitud coseno + umbral + rate-limiting

Requiere:  uv sync --extra face
"""

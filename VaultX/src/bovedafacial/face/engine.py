"""Motor de reconocimiento facial sobre InsightFace.

Pack por defecto: `antelopev2` (detector SCRFD-10G + ResNet100 glint360k), la
mayor precisión disponible en InsightFace. Los modelos se descargan solos a
`~/.insightface/models/antelopev2/` en el primer uso (~260 MB).

La importación de `insightface`/`onnxruntime` es perezosa: el núcleo de la
bóveda (crypto + contenedor) no depende de ellos.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import numpy as np

from .types import FaceObs

log = logging.getLogger(__name__)

DEFAULT_PACK = "antelopev2"
DEFAULT_DET_SIZE = (640, 640)
EMBED_DIM = 512


class EngineError(Exception):
    pass


def available_providers() -> list[str]:
    try:
        import onnxruntime as ort
    except ImportError as e:  # pragma: no cover
        raise EngineError("Falta onnxruntime. Instala con: uv sync --extra face") from e
    return list(ort.get_available_providers())


def pick_providers(prefer_gpu: bool = True) -> list[str]:
    """Lista de ExecutionProviders en orden de preferencia. CUDA primero si está;
    TensorRT se evita (compilación lenta en el primer arranque)."""
    have = set(available_providers())
    order: list[str] = []
    if prefer_gpu and "CUDAExecutionProvider" in have:
        order.append("CUDAExecutionProvider")
    order.append("CPUExecutionProvider")
    return order


class FaceEngine:
    def __init__(
        self,
        model_pack: str = DEFAULT_PACK,
        *,
        root: str | os.PathLike | None = None,
        det_size: tuple[int, int] = DEFAULT_DET_SIZE,
        prefer_gpu: bool = True,
        det_thresh: float = 0.5,
    ) -> None:
        self.model_pack = model_pack
        self.root = str(root) if root else None
        self.det_size = det_size
        self.prefer_gpu = prefer_gpu
        self.det_thresh = det_thresh
        self._app = None
        self._providers: list[str] = []

    # --- carga perezosa -------------------------------------------------
    def load(self) -> "FaceEngine":
        if self._app is not None:
            return self
        try:
            from insightface.app import FaceAnalysis
        except ImportError as e:  # pragma: no cover
            raise EngineError("Falta insightface. Instala con: uv sync --extra face") from e

        _flatten_model_dir(self.model_pack, self.root)  # corrige el zip anidado de antelopev2

        if self.prefer_gpu:
            try:  # onnxruntime>=1.29: precarga CUDA/cuDNN desde los wheels nvidia-*
                import onnxruntime as ort

                if hasattr(ort, "preload_dlls"):
                    ort.preload_dlls()
            except Exception:  # pragma: no cover
                pass

        def _build(providers: list[str]):
            kwargs = {"name": self.model_pack, "providers": providers}
            if self.root:
                kwargs["root"] = self.root
            app = FaceAnalysis(**kwargs)
            app.prepare(
                ctx_id=0 if "CUDAExecutionProvider" in providers else -1,
                det_size=self.det_size,
                det_thresh=self.det_thresh,
            )
            return app

        requested = pick_providers(self.prefer_gpu)
        try:
            app = _build(requested)
        except Exception as e:
            if requested == ["CPUExecutionProvider"]:
                raise EngineError(
                    f"No se pudo iniciar el motor facial: {type(e).__name__}: {e}"
                ) from e
            log.warning("Fallo al iniciar en GPU (%s: %s); reintento en CPU.", type(e).__name__, e)
            try:
                app = _build(["CPUExecutionProvider"])
            except Exception as e2:
                raise EngineError(
                    f"No se pudo iniciar el motor facial ni en GPU ni en CPU: "
                    f"{type(e2).__name__}: {e2}"
                ) from e2

        self._app = app
        self._providers = _session_providers(app) or ["CPUExecutionProvider"]
        if "CUDAExecutionProvider" in requested and not self.on_gpu:
            log.warning(
                "Se pidió GPU pero onnxruntime corre en CPU (faltan librerías CUDA). "
                "Inferencia ~10x más lenta."
            )
        log.info("FaceEngine listo (pack=%s, providers=%s)", self.model_pack, self._providers)
        return self

    @property
    def providers(self) -> list[str]:
        return list(self._providers)

    @property
    def on_gpu(self) -> bool:
        return "CUDAExecutionProvider" in self._providers

    # --- inferencia ---------------------------------------------------
    def analyze(self, bgr: np.ndarray) -> list[FaceObs]:
        self.load()
        faces = self._app.get(bgr)
        return [FaceObs.from_insightface(f) for f in faces]

    def primary_face(self, bgr: np.ndarray, min_det_score: float | None = None) -> FaceObs | None:
        """El rostro más grande por encima del umbral de confianza, o None."""
        thr = self.det_thresh if min_det_score is None else min_det_score
        candidates = [f for f in self.analyze(bgr) if f.det_score >= thr]
        if not candidates:
            return None
        return max(candidates, key=lambda f: f.area)

    def embedding(self, bgr: np.ndarray) -> np.ndarray | None:
        face = self.primary_face(bgr)
        return None if face is None else face.embedding


def _session_providers(app) -> list[str]:
    """Providers REALES en uso por las sesiones de onnxruntime (onnxruntime hace
    fallback silencioso a CPU si no encuentra las librerías CUDA)."""
    for model in getattr(app, "models", {}).values():
        sess = getattr(model, "session", None)
        if sess is not None:
            try:
                return list(sess.get_providers())
            except Exception:  # pragma: no cover
                pass
    return []


def _model_dir(model_pack: str, root: str | os.PathLike | None) -> Path:
    base = Path(root) if root else Path.home() / ".insightface"
    return base / "models" / model_pack


def _flatten_model_dir(model_pack: str = DEFAULT_PACK, root: str | os.PathLike | None = None) -> None:
    """El auto-descargador de InsightFace deja antelopev2 en un subdirectorio
    anidado (`antelopev2/antelopev2/*.onnx`). Lo aplana in situ."""
    pack_dir = _model_dir(model_pack, root)
    nested = pack_dir / model_pack
    if not pack_dir.is_dir():
        return
    if any(pack_dir.glob("*.onnx")):
        return
    if nested.is_dir() and any(nested.glob("*.onnx")):
        for f in nested.iterdir():
            shutil.move(str(f), str(pack_dir / f.name))
        try:
            nested.rmdir()
        except OSError:
            pass
        log.info("Modelos de %s aplanados en %s", model_pack, pack_dir)


def models_present(model_pack: str = DEFAULT_PACK, root: str | os.PathLike | None = None) -> bool:
    pack_dir = _model_dir(model_pack, root)
    return any(pack_dir.glob("*.onnx")) or (pack_dir / model_pack).is_dir()

"""Widget de enrolado facial: vista de cámara + barra de progreso. Emite
`enrolled(Template)` al terminar o `failed(str)` si algo va mal."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from .widgets import VideoView


class _EnrollWorker(QThread):
    preview = Signal(object)
    progress = Signal(int, int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, target: int = 10, max_frames: int = 400) -> None:
        super().__init__()
        self.target = target
        self.max_frames = max_frames
        self._alive = True

    def run(self) -> None:
        try:
            from ..face import EnrollSession, FaceEngine, default_camera
            from ..face.enroll import EnrollError
        except ImportError as e:  # pragma: no cover
            self.failed.emit(f"Falta el extra facial: {e}")
            return
        try:
            engine = FaceEngine().load()
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"Motor facial: {e}")
            return
        es = EnrollSession(engine, target=self.target)
        try:
            with default_camera() as cam:
                seen = 0
                while self._alive and not es.done and seen < self.max_frames:
                    frame = cam.read()
                    seen += 1
                    self.preview.emit(frame)
                    es.feed(frame)
                    hint = ", ".join(es.last_problems[:2]) if es.last_problems else "perfecto"
                    self.progress.emit(es.accepted, es.target, hint)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))
            return
        if not self._alive:
            return
        try:
            self.done.emit(es.finish())
        except EnrollError as e:
            self.failed.emit(str(e))

    def stop(self) -> None:
        self._alive = False
        self.wait(3000)


class EnrollWidget(QWidget):
    enrolled = Signal(object)   # Template
    failed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._worker: _EnrollWorker | None = None
        self.template = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.video = VideoView(420, 300)
        self.bar = QProgressBar()
        self.bar.setRange(0, 10)
        self.status = QLabel("Pulsa «Empezar» y mira a la cámara.")
        self.status.setProperty("role", "dim")
        self.status.setWordWrap(True)
        self.btn = QPushButton("Empezar enrolado")
        self.btn.setObjectName("primary")
        self.btn.clicked.connect(self.start)

        lay.addWidget(self.video)
        lay.addWidget(self.bar)
        lay.addWidget(self.status)
        lay.addWidget(self.btn)

    def start(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self.btn.setEnabled(False)
        self.btn.setText("Cargando motor…")
        self.status.setText("Muévete un poco y varía la expresión.")
        w = _EnrollWorker()
        w.preview.connect(self.video.set_frame)
        w.progress.connect(self._on_progress)
        w.done.connect(self._on_done)
        w.failed.connect(self._on_failed)
        w.finished.connect(lambda: self.btn.setText("Volver a enrolar"))
        self._worker = w
        w.start()

    def _on_progress(self, accepted: int, target: int, hint: str) -> None:
        self.bar.setRange(0, target)
        self.bar.setValue(accepted)
        self.status.setText(f"{accepted}/{target} muestras · {hint}")

    def _on_done(self, template) -> None:
        self.template = template
        self.bar.setValue(self.bar.maximum())
        self.status.setText(
            f"Rostro enrolado: {template.count} muestras · "
            f"consistencia {template.self_consistency():.2f}")
        self.btn.setEnabled(True)
        self.enrolled.emit(template)

    def _on_failed(self, msg: str) -> None:
        self.status.setText(f"No se pudo enrolar: {msg}")
        self.btn.setEnabled(True)
        self.failed.emit(msg)

    def shutdown(self) -> None:
        if self._worker:
            self._worker.stop()

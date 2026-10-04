"""Ventana de desbloqueo: PIN + rostro (con vista previa y progreso) y, como
alternativa, la frase de recuperación."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..vault import open_vault, vault_status
from ..vault.session import FaceRejected, VaultLocked
from .widgets import VideoView, hline


class _UnlockWorker(QThread):
    status = Signal(str)
    preview = Signal(object)
    ok = Signal(object)      # Session
    fail = Signal(str)

    def __init__(self, vault_path: Path, *, pin: str | None = None,
                 phrase: str | None = None, need_face: bool = False) -> None:
        super().__init__()
        self.vault_path = vault_path
        self.pin = pin
        self.phrase = phrase
        self.need_face = need_face

    def run(self) -> None:
        gate = None
        if self.pin is not None and self.need_face:
            try:
                from ..face import make_gate
            except ImportError as e:  # pragma: no cover
                self.fail.emit(f"Falta el extra facial: {e}")
                return

            def prog(best, good, live_ok, frames):
                mv = "movimiento ✓" if live_ok else "muévete un poco"
                self.status.emit(f"{mv} · parecido {best:.0%} · coincidencias {good}")

            gate = make_gate(on_progress=prog, on_frame=self.preview.emit)
            self.status.emit("Cargando motor facial…")
        try:
            session = open_vault(self.vault_path, pin=self.pin, phrase=self.phrase,
                                 face_gate=gate)
        except VaultLocked as e:
            self.fail.emit(str(e))
        except FaceRejected as e:
            self.fail.emit(f"{e} (parecido {e.score:.0%})")
        except Exception as e:  # noqa: BLE001
            self.fail.emit(str(e))
        else:
            self.ok.emit(session)


class UnlockWindow(QWidget):
    unlocked = Signal(object)   # Session

    def __init__(self, vault_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.vault_path = Path(vault_path)
        self.setWindowTitle("VaultX")
        self.resize(720, 480)
        self._worker: _UnlockWorker | None = None
        self._recovery = False

        st = vault_status(self.vault_path)
        self._need_face = bool(st["require_face"] and st["has_face"])

        # --- izquierda: cámara ---
        self.video = VideoView(380, 300)
        left = QVBoxLayout()
        left.addWidget(self.video, 1)

        # --- derecha: acceso ---
        title = QLabel("VaultX")
        title.setProperty("role", "h1")
        self.sub = QLabel(str(self.vault_path))
        self.sub.setProperty("role", "dim")
        self.sub.setWordWrap(True)

        self.field = QLineEdit()
        self.field.setEchoMode(QLineEdit.EchoMode.Password)
        self.field.setPlaceholderText("PIN")
        self.field.returnPressed.connect(self._go)

        self.enter = QPushButton("Entrar")
        self.enter.setObjectName("primary")
        self.enter.clicked.connect(self._go)

        self.switch = QPushButton("Usar la frase de recuperación")
        self.switch.setProperty("role", "link")
        self.switch.clicked.connect(self._toggle_recovery)

        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.hide()
        self.msg = QLabel(" ")
        self.msg.setWordWrap(True)
        self.msg.setProperty("role", "dim")

        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(title)
        right.addWidget(self.sub)
        right.addWidget(hline())
        right.addStretch(1)
        right.addWidget(self.field)
        right.addWidget(self.enter)
        right.addWidget(self.switch, 0, Qt.AlignmentFlag.AlignLeft)
        right.addWidget(self.bar)
        right.addWidget(self.msg)
        right.addStretch(2)

        root = QHBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(20)
        root.addLayout(left, 1)
        root.addLayout(right, 1)

        if not self._need_face:
            self.video.setText("(sin rostro enrolado)")
        self._tick_lock()
        self._locktimer = QTimer(self)
        self._locktimer.timeout.connect(self._tick_lock)
        self._locktimer.start(1000)

    # ---------- lock countdown ----------
    def _tick_lock(self) -> None:
        rem = vault_status(self.vault_path)["locked_for"]
        if rem > 0 and not self._recovery:
            self.enter.setEnabled(False)
            self.field.setEnabled(False)
            self.msg.setText(f"Bloqueada por intentos fallidos. Reintenta en {rem:.0f} s "
                             f"(o usa la frase de recuperación).")
        elif self._worker is None or not self._worker.isRunning():
            self.enter.setEnabled(True)
            self.field.setEnabled(True)
            if self.msg.text().startswith("Bloqueada"):
                self.msg.setText(" ")

    # ---------- recovery toggle ----------
    def _toggle_recovery(self) -> None:
        self._recovery = not self._recovery
        if self._recovery:
            self.field.setEchoMode(QLineEdit.EchoMode.Normal)
            self.field.setPlaceholderText("24 palabras de recuperación")
            self.switch.setText("Volver al PIN")
            self.video.hide()
        else:
            self.field.setEchoMode(QLineEdit.EchoMode.Password)
            self.field.setPlaceholderText("PIN")
            self.switch.setText("Usar la frase de recuperación")
            self.video.show()
        self.field.clear()
        self._tick_lock()

    # ---------- go ----------
    def _go(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        text = self.field.text().strip()
        if not text:
            return
        self.enter.setEnabled(False)
        self.field.setEnabled(False)
        self.bar.show()
        self.msg.setText("Abriendo…")

        if self._recovery:
            w = _UnlockWorker(self.vault_path, phrase=text)
        else:
            w = _UnlockWorker(self.vault_path, pin=text, need_face=self._need_face)
            if self._need_face:
                self.msg.setText("Mírate a la cámara y muévete un poco.")
        w.status.connect(self.msg.setText)
        w.preview.connect(self.video.set_frame)
        w.ok.connect(self._on_ok)
        w.fail.connect(self._on_fail)
        self._worker = w
        w.start()

    def _on_ok(self, session) -> None:
        self.bar.hide()
        self.msg.setText("Abierta ✓")
        self.unlocked.emit(session)

    def _on_fail(self, why: str) -> None:
        self.bar.hide()
        self.enter.setEnabled(True)
        self.field.setEnabled(True)
        self.field.selectAll()
        self.field.setFocus()
        self.msg.setText(why)
        self._tick_lock()

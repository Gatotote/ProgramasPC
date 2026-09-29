"""Diálogo de progreso indeterminado para operaciones que bloquean (descifrar,
importar, exportar, borrar). Ejecuta la función en un hilo y muestra un modal
mientras dura."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QProgressDialog


class _OpWorker(QThread):
    def __init__(self, fn) -> None:
        super().__init__()
        self._fn = fn
        self.result = None
        self.error: BaseException | None = None

    def run(self) -> None:
        try:
            self.result = self._fn()
        except BaseException as e:  # noqa: BLE001 - se relanza en el hilo principal
            self.error = e


def run_busy(parent, text: str, fn):
    """Ejecuta fn() en segundo plano mostrando «text». Devuelve su resultado o
    relanza su excepción."""
    worker = _OpWorker(fn)
    dlg = QProgressDialog(text, None, 0, 0, parent)
    dlg.setWindowTitle("Bóveda Inteligente")
    dlg.setCancelButton(None)
    dlg.setWindowModality(Qt.WindowModality.WindowModal)
    dlg.setMinimumDuration(0)
    dlg.setAutoClose(False)
    dlg.setAutoReset(False)
    worker.finished.connect(dlg.close)
    worker.start()
    dlg.exec()
    worker.wait()
    if worker.error is not None:
        raise worker.error
    return worker.result

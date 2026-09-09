"""Punto de entrada de la GUI:  bovedafacial-gui  [--vault RUTA]

Pieza 1: asistente de primer arranque + ventana de desbloqueo. Tras abrir la
bóveda se muestra una ventana provisional con el estado (la ventana principal
llega en la pieza 2).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from . import config, theme
from .widgets import hline


class _PlaceholderMain(QWidget):
    def __init__(self, session) -> None:
        super().__init__()
        self.session = session
        self.setWindowTitle("Bóveda Inteligente")
        self.resize(560, 380)
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(10)

        h = QLabel("Bóveda abierta ✓")
        h.setProperty("role", "h1")
        v.addWidget(h)
        v.addWidget(hline())

        s = session.activity_summary()
        st = session.storage_stats()
        disco = (f"En disco: {st['on_disk_bytes'] / 1e6:.1f} MB · "
                 f"{st['files']} archivos · {st['items']} elementos")
        lines = [
            f"Elementos añadidos hoy: {s['items_added_today']}",
            f"Archivos añadidos hoy: {s['files_added_today']}",
            f"Intentos bloqueados (24 h): {s['blocked_attempts_24h']}",
            disco,
        ]
        body = QLabel("\n".join(lines))
        body.setProperty("role", "mono")
        v.addWidget(body)
        v.addStretch(1)
        note = QLabel("La ventana principal (barra lateral, tarjetas, panel de "
                      "actividad) llega en la siguiente pieza.")
        note.setProperty("role", "dim")
        note.setWordWrap(True)
        v.addWidget(note)

    def closeEvent(self, ev):  # noqa: N802
        try:
            self.session.close()
        finally:
            super().closeEvent(ev)


def main() -> int:
    vault_override = None
    args = sys.argv[1:]
    if "--vault" in args:
        vault_override = Path(args[args.index("--vault") + 1])

    app = QApplication(sys.argv)
    app.setApplicationName("Bóveda Inteligente")
    app.setApplicationDisplayName("Bóveda Inteligente")
    theme.apply(app)

    vault_path = vault_override or config.vault_path()

    if not (vault_path / "header.json").exists():
        from PySide6.QtWidgets import QDialog

        from .setup_wizard import SetupWizard

        wiz = SetupWizard(vault_path)
        if wiz.exec() != QDialog.DialogCode.Accepted:
            return 0
        vault_path = wiz.vault_path
        config.set_vault_path(vault_path)

    from .unlock_view import UnlockWindow

    holder: dict = {}
    unlock = UnlockWindow(vault_path)

    def _on_unlocked(session):
        holder["main"] = _PlaceholderMain(session)
        holder["main"].show()
        unlock.close()

    unlock.unlocked.connect(_on_unlocked)
    unlock.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

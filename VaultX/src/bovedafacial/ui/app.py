"""Punto de entrada de la GUI:  bovedafacial-gui  [--vault RUTA]

Flujo: asistente si no hay bóveda → ventana de desbloqueo (PIN + rostro) →
ventana principal. Al bloquear (manual o por inactividad) se vuelve al
desbloqueo.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from . import config, theme


class _Controller:
    def __init__(self, vault_path: Path) -> None:
        self.vault_path = vault_path
        self.unlock = None
        self.main = None

    def show_unlock(self) -> None:
        from .unlock_view import UnlockWindow

        self.main = None
        self.unlock = UnlockWindow(self.vault_path)
        self.unlock.unlocked.connect(self._on_unlocked)
        self.unlock.show()

    def _on_unlocked(self, session) -> None:
        from .main_window import MainWindow

        self.main = MainWindow(session)
        self.main.locked.connect(self._on_locked)
        self.main.show()
        if self.unlock is not None:
            self.unlock.close()
            self.unlock = None

    def _on_locked(self) -> None:
        self.show_unlock()


def _initial_theme(app: QApplication) -> None:
    pref = config.get("theme", "system")
    theme.apply(app, dark=None if pref == "system" else pref == "dark")


def _demo() -> int:
    """--demo: bóveda temporal con datos de ejemplo y abre directo la ventana
    principal. Para ver la GUI sin configurar nada."""
    import tempfile

    from ..vault import create_vault, open_vault

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("VaultX (demo)")
    _initial_theme(app)
    d = Path(tempfile.mkdtemp(prefix="boveda-demo-"))
    kdf = {"type": "argon2id", "time_cost": 1, "memory_cost": 8192, "parallelism": 1}
    _, s = create_vault(d / "demo", "demo-demo-demo", kdf=kdf)
    s.close()
    s = open_vault(d / "demo.vault", pin="demo-demo-demo")
    s.add_item("/Contraseñas", "password", "Correo principal", {"usuario": "genaro@…", "password": "corta"})
    s.add_item("/Contraseñas", "password", "GitHub", {"usuario": "usuario.ejemplo", "password": "ContraseñaDeEjemplo#2026"})
    s.add_item("/Finanzas", "account", "BBVA · Cheques", {"institucion": "BBVA", "numero": "000004821", "saldo": "148 200"})
    s.add_item("/Finanzas", "card", "Visa Oro", {"numero": "4111111111111174", "vence": "07/27", "cvv": "123"})
    s.add_item("/Familiar", "contact", "Ana", {"parentesco": "esposa", "telefono": "55…"})
    doc = d / "Contrato de renta 2025.txt"
    doc.write_text("Contrato de arrendamiento (ejemplo).\n")
    s.import_path(doc, "/Documentos")
    from PySide6.QtGui import QColor, QImage
    for i, tint in enumerate((QColor("#8a5a2b"), QColor("#3b6ea5"), QColor("#5a7d4a"))):
        img = QImage(320, 240, QImage.Format.Format_RGB888)
        img.fill(tint)
        p = d / f"recuerdo_{i + 1}.png"
        img.save(str(p))
        s.import_path(p, "/Fotografias")
    from .main_window import MainWindow

    w = MainWindow(s)
    w.show()
    app._w = w
    return app.exec()


def main() -> int:
    args = sys.argv[1:]
    if "--demo" in args:
        return _demo()
    vault_override = Path(args[args.index("--vault") + 1]) if "--vault" in args else None

    app = QApplication(sys.argv)
    app.setApplicationName("VaultX")
    app.setApplicationDisplayName("VaultX")
    _initial_theme(app)

    vault_path = vault_override or config.vault_path()

    if not (vault_path / "header.json").exists():
        from PySide6.QtWidgets import QDialog

        from .setup_wizard import SetupWizard

        wiz = SetupWizard(vault_path)
        if wiz.exec() != QDialog.DialogCode.Accepted:
            return 0
        vault_path = wiz.vault_path
        config.set_vault_path(vault_path)

    ctrl = _Controller(vault_path)
    ctrl.show_unlock()
    app._ctrl = ctrl  # mantener viva la referencia
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

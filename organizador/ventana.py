"""Ventana principal del Organizador de Archivos (PySide6)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .motor import Accion, Opciones, Plan, construir_plan, ejecutar

ASSETS = Path(__file__).resolve().parent.parent / "assets"


class Trabajador(QObject):
    """Corre el escaneo/organización fuera del hilo de la interfaz."""

    linea = Signal(str)
    progreso = Signal(int, int)
    plan_listo = Signal(object)          # Plan
    terminado = Signal(int, list, list)  # hechos, errores, eliminadas
    fallo = Signal(str)

    def __init__(self, op: Opciones, solo_simular: bool) -> None:
        super().__init__()
        self.op = op
        self.solo_simular = solo_simular

    @Slot()
    def run(self) -> None:
        try:
            plan = construir_plan(self.op)
            self.plan_listo.emit(plan)
            if self.solo_simular:
                self.terminado.emit(0, [], [])
                return

            def cb(i: int, total: int, acc: Accion) -> None:
                self.progreso.emit(i, total)
                verbo = "Movido" if self.op.mover else "Copiado"
                self.linea.emit(f"  {verbo}: {acc.origen.name}  →  {acc.categoria}/")

            hechos, errores, eliminadas = ejecutar(plan, self.op, cb)
            self.terminado.emit(hechos, errores, eliminadas)
        except Exception as e:  # noqa: BLE001
            self.fallo.emit(str(e))


class VentanaPrincipal(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Organizador de Archivos")
        self.setAcceptDrops(True)
        self.resize(640, 560)
        self.setMinimumWidth(520)

        icono = ASSETS / "icono.png"
        if icono.exists():
            self.setWindowIcon(QIcon(str(icono)))

        self._hilo: QThread | None = None
        self._trabajador: Trabajador | None = None
        self._ultimo_plan: Plan | None = None

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(18, 18, 18, 18)
        raiz.setSpacing(12)

        titulo = QLabel("Organizador de Archivos")
        titulo.setStyleSheet("font-size: 18px; font-weight: 600;")
        subtitulo = QLabel(
            "Elige una carpeta (o arrastra una aquí) y separa su contenido "
            "en subcarpetas por tipo."
        )
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("color: palette(mid);")
        raiz.addWidget(titulo)
        raiz.addWidget(subtitulo)

        fila = QHBoxLayout()
        self.linea_carpeta = QLineEdit()
        self.linea_carpeta.setPlaceholderText("Ninguna carpeta seleccionada")
        self.linea_carpeta.setReadOnly(True)
        btn_elegir = QPushButton("Elegir…")
        btn_elegir.clicked.connect(self._elegir_carpeta)
        fila.addWidget(self.linea_carpeta, 1)
        fila.addWidget(btn_elegir)
        raiz.addLayout(fila)

        self.chk_subcarpetas = QCheckBox("Incluir subcarpetas (aplana su contenido)")
        self.chk_mover = QCheckBox("Mover los archivos (si lo desmarcas, los copia)")
        self.chk_mover.setChecked(True)
        self.chk_carpetas = QCheckBox('Meter también las carpetas sueltas en "Carpetas"')
        self.chk_ocultos = QCheckBox("Incluir archivos ocultos")
        for c in (self.chk_subcarpetas, self.chk_mover, self.chk_carpetas, self.chk_ocultos):
            raiz.addWidget(c)
        self.chk_subcarpetas.toggled.connect(self._sync_carpetas)

        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("color: palette(mid);")
        raiz.addWidget(linea)

        botones = QHBoxLayout()
        self.btn_simular = QPushButton("Simular")
        self.btn_simular.clicked.connect(lambda: self._arrancar(solo_simular=True))
        self.btn_organizar = QPushButton("Organizar")
        self.btn_organizar.setStyleSheet("font-weight: 600;")
        self.btn_organizar.clicked.connect(self._confirmar_y_organizar)
        botones.addWidget(self.btn_simular)
        botones.addWidget(self.btn_organizar)
        raiz.addLayout(botones)

        self.barra = QProgressBar()
        self.barra.setVisible(False)
        raiz.addWidget(self.barra)

        self.registro = QPlainTextEdit()
        self.registro.setReadOnly(True)
        self.registro.setPlaceholderText("Aquí aparece lo que se hará / se hizo.")
        raiz.addWidget(self.registro, 1)

    # ---- carpeta -----------------------------------------------------------

    def _carpeta_actual(self) -> Path | None:
        txt = self.linea_carpeta.text().strip()
        return Path(txt) if txt else None

    def _elegir_carpeta(self) -> None:
        inicio = str(self._carpeta_actual() or Path.home())
        elegida = QFileDialog.getExistingDirectory(self, "Elegir carpeta", inicio)
        if elegida:
            self.linea_carpeta.setText(elegida)

    def _sync_carpetas(self, recursivo: bool) -> None:
        # Con recursión, "carpetas sueltas" no aplica: se vacían y se limpian solas.
        self.chk_carpetas.setEnabled(not recursivo)
        if recursivo:
            self.chk_carpetas.setChecked(False)

    # ---- drag & drop -----------------------------------------------------

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:  # noqa: N802
        urls = e.mimeData().urls()
        if len(urls) == 1 and Path(urls[0].toLocalFile()).is_dir():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:  # noqa: N802
        ruta = Path(e.mimeData().urls()[0].toLocalFile())
        if ruta.is_dir():
            self.linea_carpeta.setText(str(ruta))

    # ---- ejecución -----------------------------------------------------

    def _opciones(self) -> Opciones | None:
        carpeta = self._carpeta_actual()
        if carpeta is None or not carpeta.is_dir():
            QMessageBox.warning(self, "Falta la carpeta", "Elige una carpeta válida primero.")
            return None
        return Opciones(
            carpeta=carpeta,
            incluir_subcarpetas=self.chk_subcarpetas.isChecked(),
            mover=self.chk_mover.isChecked(),
            incluir_carpetas=self.chk_carpetas.isChecked() and self.chk_carpetas.isEnabled(),
            incluir_ocultos=self.chk_ocultos.isChecked(),
        )

    def _confirmar_y_organizar(self) -> None:
        op = self._opciones()
        if op is None:
            return
        verbo = "mover" if op.mover else "copiar"
        msg = (
            f"Se van a {verbo} los archivos de:\n{op.carpeta}\n\n"
            "a subcarpetas por tipo dentro de esa misma carpeta.\n\n"
            "¿Continuar?"
        )
        if QMessageBox.question(self, "Confirmar", msg) == QMessageBox.StandardButton.Yes:
            self._arrancar(solo_simular=False)

    def _arrancar(self, solo_simular: bool) -> None:
        if self._hilo is not None:
            return
        op = self._opciones()
        if op is None:
            return

        self.registro.clear()
        self.registro.appendPlainText(
            ("SIMULACIÓN — no se toca nada.\n" if solo_simular else "Organizando…\n")
        )
        self._fijar_ocupado(True)

        self._hilo = QThread(self)
        self._trabajador = Trabajador(op, solo_simular)
        self._trabajador.moveToThread(self._hilo)
        self._hilo.started.connect(self._trabajador.run)
        self._trabajador.linea.connect(self.registro.appendPlainText)
        self._trabajador.progreso.connect(self._on_progreso)
        self._trabajador.plan_listo.connect(self._on_plan)
        self._trabajador.terminado.connect(self._on_terminado)
        self._trabajador.fallo.connect(self._on_fallo)
        self._hilo.start()

    # ---- señales del trabajador ----------------------------------------

    @Slot(int, int)
    def _on_progreso(self, i: int, total: int) -> None:
        self.barra.setMaximum(max(total, 1))
        self.barra.setValue(i)

    @Slot(object)
    def _on_plan(self, plan: Plan) -> None:
        self._ultimo_plan = plan
        conteo = plan.por_categoria()
        if not conteo:
            self.registro.appendPlainText("No hay nada que organizar en esta carpeta.")
        else:
            self.registro.appendPlainText("Resumen por tipo:")
            ancho = max(len(k) for k in conteo)
            for cat, n in conteo.items():
                self.registro.appendPlainText(f"  {cat.ljust(ancho)}  {n}")
            self.registro.appendPlainText(f"  {'TOTAL'.ljust(ancho)}  {sum(conteo.values())}")
        if plan.omitidos:
            self.registro.appendPlainText(f"\nOmitidos: {len(plan.omitidos)}")
            for ruta, motivo in plan.omitidos[:20]:
                self.registro.appendPlainText(f"  {ruta.name}  ({motivo})")
            if len(plan.omitidos) > 20:
                self.registro.appendPlainText(f"  … y {len(plan.omitidos) - 20} más")
        self.registro.appendPlainText("")

    @Slot(int, list, list)
    def _on_terminado(self, hechos: int, errores: list, eliminadas: list) -> None:
        simulacion = self._trabajador is not None and self._trabajador.solo_simular
        self._limpiar_hilo()
        self._fijar_ocupado(False)
        if simulacion:
            self.registro.appendPlainText(
                "Fin de la simulación. Pulsa «Organizar» para aplicarlo."
            )
            return
        self.registro.appendPlainText(f"\nListo. {hechos} archivo(s) procesado(s).")
        if eliminadas:
            self.registro.appendPlainText(f"Subcarpetas vacías eliminadas: {len(eliminadas)}")
        if errores:
            self.registro.appendPlainText(f"\nErrores ({len(errores)}):")
            for ruta, motivo in errores:
                self.registro.appendPlainText(f"  {ruta.name}: {motivo}")
        QMessageBox.information(
            self,
            "Terminado",
            f"{hechos} archivo(s) procesado(s)."
            + (f"\n{len(errores)} error(es) — mira el registro." if errores else ""),
        )

    @Slot(str)
    def _on_fallo(self, texto: str) -> None:
        self._limpiar_hilo()
        self._fijar_ocupado(False)
        QMessageBox.critical(self, "Error", texto)

    # ---- utilidades de estado ----------------------------------------

    def _fijar_ocupado(self, ocupado: bool) -> None:
        self.barra.setVisible(ocupado)
        if not ocupado:
            self.barra.reset()
        for w in (
            self.btn_simular,
            self.btn_organizar,
            self.chk_subcarpetas,
            self.chk_mover,
            self.chk_carpetas,
            self.chk_ocultos,
        ):
            w.setEnabled(not ocupado)
        if not ocupado:
            self._sync_carpetas(self.chk_subcarpetas.isChecked())

    def _limpiar_hilo(self) -> None:
        if self._hilo is not None:
            self._hilo.quit()
            self._hilo.wait()
            self._hilo.deleteLater()
        self._hilo = None
        self._trabajador = None

    def closeEvent(self, e) -> None:  # noqa: N802
        self._limpiar_hilo()
        super().closeEvent(e)


def main() -> int:
    import sys

    app = QApplication(sys.argv)
    app.setApplicationName("Organizador de Archivos")
    icono = ASSETS / "icono.png"
    if icono.exists():
        app.setWindowIcon(QIcon(str(icono)))
    v = VentanaPrincipal()
    v.show()
    return app.exec()

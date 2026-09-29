"""Ventana principal del Organizador de Archivos (PySide6).

Estilo visual: HUD / panel de control futurista (fondo azul profundo,
acentos cian, marcos con esquinas recortadas y corchetes de acento).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGraphicsDropShadowEffect,
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

# --- paleta HUD ---------------------------------------------------------
FONDO = "#081420"
PANEL = "#0b1f30"
BORDE = "#1f6f8c"
CIAN = "#2de2ff"
TEXTO = "#cfeffb"
TENUE = "#6f9fb5"
PELIGRO = "#ff5c7c"

QSS_HUD = f"""
* {{
    font-family: "Inter", "Segoe UI", "Cantarell", "Noto Sans", sans-serif;
}}
QWidget#Root {{
    background: {FONDO};
    color: {TEXTO};
}}
QLabel {{ color: {TEXTO}; background: transparent; }}
QLabel#Titulo {{
    color: #eafcff;
    font-size: 21px;
    font-weight: 700;
}}
QLabel#Subtitulo {{ color: {TENUE}; font-size: 12px; }}

QLineEdit {{
    background: #06121d;
    border: 1px solid #14435a;
    border-radius: 0;
    padding: 8px 10px;
    color: #dff6ff;
    selection-background-color: #0090b0;
}}
QLineEdit:focus {{ border: 1px solid {CIAN}; }}

QPushButton {{
    background: rgba(45, 226, 255, 0.08);
    border: 1px solid {BORDE};
    border-radius: 0;
    color: #bff0ff;
    padding: 8px 20px;
    font-weight: 600;
}}
QPushButton:hover {{
    border-color: {CIAN};
    background: rgba(45, 226, 255, 0.16);
    color: #eafdff;
}}
QPushButton:pressed {{ background: rgba(45, 226, 255, 0.28); }}
QPushButton:disabled {{
    color: #46707f;
    border-color: #123240;
    background: transparent;
}}
QPushButton#Primario {{
    background: rgba(45, 226, 255, 0.16);
    border: 1px solid {CIAN};
    color: #eafdff;
}}
QPushButton#Primario:hover {{ background: rgba(45, 226, 255, 0.30); }}
QPushButton#Primario:disabled {{
    color: #46707f;
    border-color: #123240;
    background: transparent;
}}

QCheckBox {{ color: #a9d9e8; spacing: 10px; padding: 3px 0; background: transparent; }}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border: 1px solid {BORDE};
    background: #06121d;
}}
QCheckBox::indicator:hover {{ border-color: {CIAN}; }}
QCheckBox::indicator:checked {{ background: {CIAN}; border-color: {CIAN}; }}
QCheckBox:disabled {{ color: #46707f; }}
QCheckBox::indicator:disabled {{ border-color: #123240; background: #0a1620; }}

QPlainTextEdit {{
    background: #050f18;
    border: 1px solid #14435a;
    border-radius: 0;
    color: #8fe6c4;
    font-family: "JetBrains Mono", "Noto Sans Mono", "DejaVu Sans Mono", monospace;
    font-size: 12px;
    padding: 8px;
    selection-background-color: #0090b0;
}}

QProgressBar {{
    background: #06121d;
    border: 1px solid #14435a;
    border-radius: 0;
    height: 14px;
    text-align: center;
    color: {TEXTO};
}}
QProgressBar::chunk {{ background: {CIAN}; }}

QScrollBar:vertical {{ background: #06121d; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDE}; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {CIAN}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: #06121d; height: 12px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {BORDE}; min-width: 24px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QMessageBox {{ background: {FONDO}; }}
QMessageBox QLabel {{ color: {TEXTO}; }}
"""


class MarcoHUD(QWidget):
    """Panel con marco estilo HUD: esquinas sup-izq / inf-der recortadas y
    corchetes de acento en las otras dos. Los widgets van en ``self.cuerpo``.
    """

    def __init__(self, titulo: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._titulo = titulo.upper()
        self._resaltado = False
        arriba = 34 if titulo else 16
        self.cuerpo = QVBoxLayout(self)
        self.cuerpo.setContentsMargins(18, arriba, 18, 16)
        self.cuerpo.setSpacing(10)

    def set_resaltado(self, valor: bool) -> None:
        if valor != self._resaltado:
            self._resaltado = valor
            self.update()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -2, -2)
        ch = 14  # tamaño del chaflán

        linea = QColor(CIAN) if self._resaltado else QColor(BORDE)
        acento = QColor(CIAN)

        cuerpo = QPainterPath()
        cuerpo.moveTo(r.left() + ch, r.top())
        cuerpo.lineTo(r.right(), r.top())
        cuerpo.lineTo(r.right(), r.bottom() - ch)
        cuerpo.lineTo(r.right() - ch, r.bottom())
        cuerpo.lineTo(r.left(), r.bottom())
        cuerpo.lineTo(r.left(), r.top() + ch)
        cuerpo.closeSubpath()

        p.fillPath(cuerpo, QColor(PANEL))
        p.setPen(QPen(linea, 1.2))
        p.drawPath(cuerpo)

        # corchetes de acento: esquina sup-der e inf-izq
        b = 18
        p.setPen(QPen(acento, 2))
        p.drawLine(r.right() - b, r.top(), r.right(), r.top())
        p.drawLine(r.right(), r.top(), r.right(), r.top() + b)
        p.drawLine(r.left(), r.bottom() - b, r.left(), r.bottom())
        p.drawLine(r.left(), r.bottom(), r.left() + b, r.bottom())
        # marca en el chaflán sup-izq
        p.drawLine(r.left(), r.top() + ch, r.left() + ch, r.top())

        if self._titulo:
            f = QFont(self.font())
            f.setPointSizeF(max(self.font().pointSizeF() - 1.5, 7.0))
            f.setBold(True)
            f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.0)
            p.setFont(f)
            p.setPen(acento)
            base_y = r.top() + 22
            p.drawText(r.left() + 16, base_y, self._titulo)
            ancho = p.fontMetrics().horizontalAdvance(self._titulo)
            p.setPen(QPen(QColor("#14435a"), 1))
            p.drawLine(r.left() + 26 + ancho, r.top() + 16, r.right() - 24, r.top() + 16)


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
        self.setObjectName("Root")
        self.setWindowTitle("Organizador de Archivos")
        self.setStyleSheet(QSS_HUD)
        self.setAcceptDrops(True)
        self.resize(660, 600)
        self.setMinimumWidth(540)

        icono = ASSETS / "icono.png"
        if icono.exists():
            self.setWindowIcon(QIcon(str(icono)))

        self._hilo: QThread | None = None
        self._trabajador: Trabajador | None = None
        self._ultimo_plan: Plan | None = None

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(16, 16, 16, 16)
        raiz.setSpacing(14)

        # ---- cabecera ----------------------------------------------------
        cabecera = MarcoHUD()
        titulo = QLabel("ORGANIZADOR DE ARCHIVOS")
        titulo.setObjectName("Titulo")
        glow = QGraphicsDropShadowEffect(self)
        glow.setColor(QColor(CIAN))
        glow.setBlurRadius(22)
        glow.setOffset(0, 0)
        titulo.setGraphicsEffect(glow)
        subtitulo = QLabel(
            "Elige una carpeta (o arrastra una aquí) y separa su contenido "
            "en subcarpetas por tipo."
        )
        subtitulo.setObjectName("Subtitulo")
        subtitulo.setWordWrap(True)
        cabecera.cuerpo.addWidget(titulo)
        cabecera.cuerpo.addWidget(subtitulo)
        raiz.addWidget(cabecera)

        # ---- carpeta ---------------------------------------------------
        self.panel_carpeta = MarcoHUD("Carpeta objetivo")
        fila = QHBoxLayout()
        self.linea_carpeta = QLineEdit()
        self.linea_carpeta.setPlaceholderText("Ninguna carpeta seleccionada")
        self.linea_carpeta.setReadOnly(True)
        btn_elegir = QPushButton("Elegir…")
        btn_elegir.clicked.connect(self._elegir_carpeta)
        fila.addWidget(self.linea_carpeta, 1)
        fila.addWidget(btn_elegir)
        self.panel_carpeta.cuerpo.addLayout(fila)
        raiz.addWidget(self.panel_carpeta)

        # ---- opciones ------------------------------------------------
        panel_opciones = MarcoHUD("Parámetros")
        self.chk_subcarpetas = QCheckBox("Incluir subcarpetas (aplana su contenido)")
        self.chk_mover = QCheckBox("Mover los archivos (si lo desmarcas, los copia)")
        self.chk_mover.setChecked(True)
        self.chk_carpetas = QCheckBox('Meter también las carpetas sueltas en "Carpetas"')
        self.chk_ocultos = QCheckBox("Incluir archivos ocultos")
        for c in (self.chk_subcarpetas, self.chk_mover, self.chk_carpetas, self.chk_ocultos):
            panel_opciones.cuerpo.addWidget(c)
        self.chk_subcarpetas.toggled.connect(self._sync_carpetas)
        raiz.addWidget(panel_opciones)

        # ---- acciones ----------------------------------------------
        botones = QHBoxLayout()
        botones.setSpacing(12)
        self.btn_simular = QPushButton("Simular")
        self.btn_simular.clicked.connect(lambda: self._arrancar(solo_simular=True))
        self.btn_organizar = QPushButton("Organizar")
        self.btn_organizar.setObjectName("Primario")
        self.btn_organizar.clicked.connect(self._confirmar_y_organizar)
        botones.addWidget(self.btn_simular)
        botones.addWidget(self.btn_organizar)
        raiz.addLayout(botones)

        self.barra = QProgressBar()
        self.barra.setVisible(False)
        raiz.addWidget(self.barra)

        # ---- registro --------------------------------------------
        panel_registro = MarcoHUD("Registro")
        self.registro = QPlainTextEdit()
        self.registro.setReadOnly(True)
        self.registro.setPlaceholderText("Aquí aparece lo que se hará / se hizo.")
        panel_registro.cuerpo.addWidget(self.registro)
        raiz.addWidget(panel_registro, 1)

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
        # Con recursion, "carpetas sueltas" no aplica: se vacian y se limpian solas.
        self.chk_carpetas.setEnabled(not recursivo)
        if recursivo:
            self.chk_carpetas.setChecked(False)

    # ---- drag & drop -----------------------------------------------------

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:  # noqa: N802
        urls = e.mimeData().urls()
        if len(urls) == 1 and Path(urls[0].toLocalFile()).is_dir():
            e.acceptProposedAction()
            self.panel_carpeta.set_resaltado(True)

    def dragLeaveEvent(self, _e) -> None:  # noqa: N802
        self.panel_carpeta.set_resaltado(False)

    def dropEvent(self, e: QDropEvent) -> None:  # noqa: N802
        self.panel_carpeta.set_resaltado(False)
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
    app.setStyleSheet(QSS_HUD)
    icono = ASSETS / "icono.png"
    if icono.exists():
        app.setWindowIcon(QIcon(str(icono)))
    v = VentanaPrincipal()
    v.show()
    return app.exec()

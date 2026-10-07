"""Pantallas: inicio, instrucciones, prueba en curso, resultados e historial."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPageSize, QPainter, QPdfWriter, QPen, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from .. import AUTOR, VERSION
from ..baterias import BATERIAS, SUBPRUEBAS
from ..datos import BaseDatos, edad
from ..personalidad.catalogo import CUESTIONARIOS
from ..salud import AVISO_REVISION, AVISO_SALUD, REVISADO
from ..salud.tamizajes import TAMIZAJES
from .estilo import ACENTO, BORDE, SUAVE, TEXTO

ICONO = Path(__file__).resolve().parent.parent / "icono.png"

AVISO = ("⚠ Esta es una estimación casera, NO un diagnóstico. Los tests reales (WAIS, WISC, "
         "Stanford-Binet, Cattell) los aplica un psicólogo con material y baremos oficiales. "
         "Las preguntas de este programa son propias y las normas por edad son aproximadas.")


def _etiqueta(texto: str, nombre: str = "", envolver: bool = True) -> QLabel:
    l = QLabel(texto)
    if nombre:
        l.setObjectName(nombre)
    l.setWordWrap(envolver)
    return l


def _tarjeta() -> tuple[QFrame, QVBoxLayout]:
    f = QFrame()
    f.setObjectName("tarjeta")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(18, 16, 18, 16)
    return f, lay


def pie_autor() -> QLabel:
    l = QLabel(f"GeniusIQ v{VERSION}  ·  {AUTOR}")
    l.setObjectName("suave")
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return l


# ------------------------------------------------------------------ persona nueva

class DialogoPersona(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva persona")
        lay = QFormLayout(self)
        self.nombre = QLineEdit()
        self.nacimiento = QDateEdit(QDate(2000, 1, 1))
        self.nacimiento.setCalendarPopup(True)
        self.nacimiento.setDisplayFormat("dd/MM/yyyy")
        self.nacimiento.setMaximumDate(QDate.currentDate())
        lay.addRow("Nombre:", self.nombre)
        lay.addRow("Fecha de nacimiento:", self.nacimiento)
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(self._aceptar)
        botones.rejected.connect(self.reject)
        lay.addRow(botones)

    def _aceptar(self):
        if self.nombre.text().strip():
            self.accept()

    def datos(self) -> tuple[str, str]:
        return self.nombre.text().strip(), self.nacimiento.date().toString("yyyy-MM-dd")


# ------------------------------------------------------------------ inicio

class PantallaInicio(QWidget):
    comenzar = Signal(object, object, list)   # persona (Row), batería, claves de subpruebas
    comenzar_personalidad = Signal(object, object)   # persona, cuestionario
    ver_historial = Signal()

    def __init__(self, db: BaseDatos):
        super().__init__()
        self.db = db
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 24, 30, 12)
        encabezado = QHBoxLayout()
        izquierda = QVBoxLayout()
        encabezado.addLayout(izquierda, 1)
        if ICONO.exists():
            logo = QLabel()
            logo.setPixmap(QPixmap(str(ICONO)).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation))
            encabezado.addWidget(logo, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        lay.addLayout(encabezado)
        izquierda.addWidget(_etiqueta("GeniusIQ", "titulo"))
        izquierda.addWidget(_etiqueta("Inteligencia (razonamiento, lenguaje, memoria y rapidez) y personalidad.",
                                      "suave"))

        fila = QHBoxLayout()
        fila.addWidget(QLabel("Persona:"))
        self.personas = QComboBox()
        self.personas.setMinimumWidth(280)
        self.personas.currentIndexChanged.connect(self._actualizar)
        nueva = QPushButton("＋ Nueva persona…")
        nueva.clicked.connect(self._nueva_persona)
        self.lbl_edad = _etiqueta("", "suave", False)
        fila.addWidget(self.personas)
        fila.addWidget(nueva)
        fila.addWidget(self.lbl_edad)
        fila.addStretch()
        izquierda.addSpacing(8)
        izquierda.addLayout(fila)
        izquierda.addStretch()

        cuerpo = QHBoxLayout()
        self.lista = QListWidget()
        self.lista.setMaximumWidth(300)
        for titulo, grupo, tipo in (("INTELIGENCIA", BATERIAS, "iq"), ("PERSONALIDAD", CUESTIONARIOS, "pers"),
                                    ("SALUD MENTAL (TAMIZAJE)", TAMIZAJES, "salud")):
            cab = QListWidgetItem(titulo)
            cab.setFlags(Qt.ItemFlag.NoItemFlags)
            cab.setForeground(QColor(ACENTO))
            f = cab.font()
            f.setBold(True)
            f.setPointSize(f.pointSize() - 1)
            cab.setFont(f)
            self.lista.addItem(cab)
            for x in grupo:
                it = QListWidgetItem("   " + x.nombre)
                it.setData(Qt.ItemDataRole.UserRole, (tipo, x))
                self.lista.addItem(it)
        self.seleccion = None
        self.lista.currentRowChanged.connect(self._elegir_bateria)
        cuerpo.addWidget(self.lista)

        tarjeta, self.det = _tarjeta()
        self.det_nombre = _etiqueta("", "subtitulo")
        self.det_desc = _etiqueta("")
        self.det_edad = _etiqueta("", "suave")
        self.det_subs = QVBoxLayout()
        self.det_tiempo = _etiqueta("", "suave")
        self.det_alerta = _etiqueta("", "aviso")
        self.det.addWidget(self.det_nombre)
        self.det.addWidget(self.det_desc)
        self.det.addWidget(self.det_edad)
        self.det.addSpacing(6)
        self.lbl_subs = _etiqueta("Subpruebas (puedes quitar las que no quieras):")
        self.det.addWidget(self.lbl_subs)
        self.det.addLayout(self.det_subs)
        self.det.addWidget(self.det_tiempo)
        self.det.addWidget(self.det_alerta)
        self.det.addStretch()
        cuerpo.addWidget(tarjeta, 1)
        lay.addLayout(cuerpo, 1)

        lay.addWidget(_etiqueta(AVISO, "aviso"))
        botones = QHBoxLayout()
        hist = QPushButton("📋 Historial")
        hist.clicked.connect(self.ver_historial.emit)
        self.btn_comenzar = QPushButton("Comenzar ▶")
        self.btn_comenzar.setObjectName("principal")
        self.btn_comenzar.clicked.connect(self._comenzar)
        botones.addWidget(hist)
        botones.addStretch()
        botones.addWidget(self.btn_comenzar)
        lay.addLayout(botones)
        lay.addWidget(pie_autor())

        self.checks: list[QCheckBox] = []
        self.recargar_personas()
        self.lista.setCurrentRow(1)

    def recargar_personas(self, seleccionar: int | None = None) -> None:
        self.personas.blockSignals(True)
        self.personas.clear()
        for p in self.db.personas():
            self.personas.addItem(p["nombre"], p)
            if seleccionar == p["id"]:
                self.personas.setCurrentIndex(self.personas.count() - 1)
        self.personas.blockSignals(False)
        self._actualizar()

    def _persona(self):
        return self.personas.currentData()

    def _nueva_persona(self) -> None:
        d = DialogoPersona(self)
        if d.exec():
            pid = self.db.agregar_persona(*d.datos())
            self.recargar_personas(pid)

    def _elegir_bateria(self, fila: int) -> None:
        dato = self.lista.item(fila).data(Qt.ItemDataRole.UserRole) if fila >= 0 else None
        if dato is None:
            return
        self.seleccion = dato
        while self.det_subs.count():
            w = self.det_subs.takeAt(0).widget()
            if w:
                w.hide()
                w.deleteLater()
        self.checks = []
        tipo, b = dato
        self.lbl_subs.setVisible(tipo == "iq")
        if tipo in ("pers", "salud"):
            self.det_nombre.setText(b.nombre)
            self.det_desc.setText(b.descripcion)
            self.det_edad.setText(f"De {b.edad_min} a {b.edad_max} años" if b.edad_max < 120
                                  else f"Desde {b.edad_min} años")
            self._actualizar()
            return
        self.det_nombre.setText(b.nombre)
        self.det_desc.setText(b.descripcion)
        self.det_edad.setText(f"Edades: {b.edad_min} a {b.edad_max if b.edad_max < 99 else '90+'} años")
        for clave in b.subpruebas:
            sp = SUBPRUEBAS[clave]
            indice = next((n for n, (_, cl) in b.indices.items() if clave in cl), "")
            c = QCheckBox(f"{sp.nombre}   ·   {indice}   ·   ~{sp.minutos:g} min")
            c.setChecked(True)
            c.setProperty("clave", clave)
            c.toggled.connect(self._actualizar)
            self.det_subs.addWidget(c)
            self.checks.append(c)
        self._actualizar()

    def _actualizar(self) -> None:
        persona = self._persona()
        if persona is not None:
            self.lbl_edad.setText(f"{int(edad(persona['nacimiento']))} años")
        else:
            self.lbl_edad.setText("← agrega a alguien para empezar")
        if self.seleccion is None:
            return
        tipo, b = self.seleccion
        if tipo in ("pers", "salud"):
            self.det_tiempo.setText(f"{len(b.preguntas)} preguntas  ·  unos {b.minutos} minutos")
            avisos = []
            if tipo == "salud":
                avisos.append(AVISO_SALUD)
                if not REVISADO:
                    avisos.append(AVISO_REVISION)
            if persona is not None and edad(persona["nacimiento"]) < b.edad_min:
                avisos.append(f"Este cuestionario es para personas de {b.edad_min} años o más.")
            elif persona is not None and int(edad(persona["nacimiento"])) > b.edad_max:
                avisos.append(f"Este cuestionario es para personas de {b.edad_min} a {b.edad_max} años.")
            alerta = "\n\n".join(avisos)
            self.det_alerta.setText(alerta)
            self.det_alerta.setVisible(bool(alerta))
            self.btn_comenzar.setEnabled(persona is not None)
            return
        elegidas = [c for c in self.checks if c.isChecked()]
        minutos = sum(SUBPRUEBAS[c.property("clave")].minutos for c in elegidas)
        self.det_tiempo.setText(f"Duración aproximada: {minutos:g} minutos")
        alerta = ""
        if persona is not None:
            e = edad(persona["nacimiento"])
            if e < b.edad_min or e > b.edad_max:
                tope = b.edad_max if b.edad_max < 99 else "90+"
                alerta = (f"Esta batería es para {b.edad_min} a {tope} años; con {int(e)} años "
                          "el resultado será menos confiable.")
            elif e < 6:
                alerta = "Para menores de 6 años las normas de este programa no sirven."
        self.det_alerta.setText(alerta)
        self.det_alerta.setVisible(bool(alerta))
        self.btn_comenzar.setEnabled(persona is not None and bool(elegidas))

    def _comenzar(self) -> None:
        tipo, b = self.seleccion
        if tipo == "salud" and not self._confirmar_tamizaje(b):
            return
        if tipo in ("pers", "salud"):
            self.comenzar_personalidad.emit(self._persona(), b)
        else:
            self.comenzar.emit(self._persona(), b, [c.property("clave") for c in self.checks if c.isChecked()])


    def _confirmar_tamizaje(self, b) -> bool:
        texto = [AVISO_SALUD]
        if not REVISADO:
            texto.append(AVISO_REVISION)
        e = edad(self._persona()["nacimiento"])
        nombre = self._persona()["nombre"]
        if b.informante:
            texto.append(f"Lo contesta un adulto (papá, mamá, tutor o maestro) pensando en {nombre}; el "
                         "resultado se guarda a nombre de " + nombre + ".")
        elif e < 18:
            texto.append("Es menor de edad: que lo conteste acompañado(a) de un adulto de confianza, y que ese "
                         "adulto vea el resultado.")
        if e < b.edad_min or int(e) > b.edad_max:
            rango = f"de {b.edad_min} a {b.edad_max} años" if b.edad_max < 120 else f"de {b.edad_min} años o más"
            texto.append(f"Ojo: este cuestionario está hecho para personas {rango}.")
        texto.append("Las respuestas quedan guardadas en el historial de esta computadora. ¿Continuar?")
        r = QMessageBox.question(self, b.nombre, "\n\n".join(texto))
        return r == QMessageBox.StandardButton.Yes


# ------------------------------------------------------------------ instrucciones

class PantallaInstrucciones(QWidget):
    empezar = Signal()
    salir = Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(60, 40, 60, 20)
        self.paso = _etiqueta("", "suave")
        self.nombre = _etiqueta("", "titulo")
        self.texto = _etiqueta("")
        self.texto.setStyleSheet("font-size: 19px;")
        lay.addWidget(self.paso)
        lay.addWidget(self.nombre)
        lay.addSpacing(10)
        lay.addWidget(self.texto)
        lay.addStretch()
        fila = QHBoxLayout()
        salir = QPushButton("Salir de la prueba")
        salir.setObjectName("peligro")
        salir.clicked.connect(self.salir.emit)
        ok = QPushButton("Empezar ▶")
        ok.setObjectName("principal")
        ok.clicked.connect(self.empezar.emit)
        fila.addWidget(salir)
        fila.addStretch()
        fila.addWidget(ok)
        lay.addLayout(fila)

    def mostrar(self, sp, i: int, n: int) -> None:
        self.paso.setText(f"Subprueba {i} de {n}")
        self.nombre.setText(sp.nombre)
        self.texto.setText(sp.instrucciones)


# ------------------------------------------------------------------ prueba en curso

class PantallaPrueba(QWidget):
    salir = Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 14, 24, 14)
        barra = QHBoxLayout()
        self.titulo = _etiqueta("", "subtitulo", False)
        self.progreso = _etiqueta("", "suave", False)
        self.reloj = _etiqueta("", "reloj", False)
        salir = QPushButton("Salir")
        salir.setObjectName("peligro")
        salir.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        salir.clicked.connect(self.salir.emit)
        barra.addWidget(self.titulo)
        barra.addSpacing(16)
        barra.addWidget(self.progreso)
        barra.addStretch()
        barra.addWidget(self.reloj)
        barra.addSpacing(16)
        barra.addWidget(salir)
        lay.addLayout(barra)
        self.contenido = QVBoxLayout()
        lay.addLayout(self.contenido, 1)
        self.actual: QWidget | None = None

    def poner(self, titulo: str, widget: QWidget) -> None:
        self.quitar()
        self.titulo.setText(titulo)
        self.progreso.setText("")
        self.reloj.setText("")
        widget.progreso.connect(self.progreso.setText)
        widget.reloj.connect(self.reloj.setText)
        self.actual = widget
        self.contenido.addWidget(widget)
        widget.setFocus()

    def quitar(self) -> None:
        if self.actual is not None:
            self.actual.detener()
            self.contenido.removeWidget(self.actual)
            self.actual.deleteLater()
            self.actual = None


# ------------------------------------------------------------------ resultados

class GraficaIndices(QWidget):
    """Barras horizontales de cada índice con su rango probable."""

    def __init__(self, filas: list[dict], sd: float):
        super().__init__()
        self.filas, self.sd = filas, sd
        self.setMinimumHeight(46 * len(filas) + 40)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        izq, der = 250, self.width() - 30
        lo, hi = 100 - 4 * self.sd, 100 + 4 * self.sd

        def x(v: float) -> float:
            return izq + (min(max(v, lo), hi) - lo) / (hi - lo) * (der - izq)

        alto = self.height() - 30
        p.fillRect(QRectF(QPointF(x(100 - 0.67 * self.sd), 0), QPointF(x(100 + 0.67 * self.sd), alto)),
                   QColor("#2a2018"))
        f = QFont()
        f.setPixelSize(12)
        p.setFont(f)
        for k in range(-4, 5):
            v = 100 + k * self.sd
            p.setPen(QPen(QColor(SUAVE if k == 0 else BORDE), 2 if k == 0 else 1, Qt.PenStyle.SolidLine if k == 0 else Qt.PenStyle.DotLine))
            p.drawLine(QPointF(x(v), 0), QPointF(x(v), alto))
            p.setPen(QColor(SUAVE))
            p.drawText(QRectF(x(v) - 20, alto + 4, 40, 20), Qt.AlignmentFlag.AlignCenter, f"{v:g}")
        for i, fila in enumerate(self.filas):
            y = 12 + i * 46
            f.setPixelSize(14)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor(TEXTO))
            p.drawText(QRectF(0, y, izq - 12, 26), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       fila["nombre"])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(ACENTO))
            p.drawRoundedRect(QRectF(QPointF(x(lo), y + 4), QPointF(x(fila["ci"]), y + 22)), 5, 5)
            r0, r1 = fila["rango"]
            p.setPen(QPen(QColor(TEXTO), 2))
            p.drawLine(QPointF(x(r0), y + 13), QPointF(x(r1), y + 13))
            p.drawLine(QPointF(x(r0), y + 7), QPointF(x(r0), y + 19))
            p.drawLine(QPointF(x(r1), y + 7), QPointF(x(r1), y + 19))
            p.drawText(QRectF(x(fila["ci"]) + 8, y - 12, 60, 20), Qt.AlignmentFlag.AlignLeft, str(fila["ci"]))


class PantallaResultados(QWidget):
    volver = Signal()

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 14, 20, 12)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        lay.addWidget(self.scroll, 1)
        fila = QHBoxLayout()
        pdf = QPushButton("Guardar como PDF…")
        pdf.clicked.connect(self._pdf)
        ok = QPushButton("Volver al inicio")
        ok.setObjectName("principal")
        ok.clicked.connect(self.volver.emit)
        fila.addWidget(pdf)
        fila.addStretch()
        fila.addWidget(ok)
        lay.addLayout(fila)
        self.nombre_archivo = "resultado"

    def mostrar(self, res: dict, persona: str, fecha: str) -> None:
        self.nombre_archivo = f"GeniusIQ {persona} {fecha[:10]}"
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setSpacing(12)
        fecha_txt = datetime.fromisoformat(fecha).strftime("%d/%m/%Y %H:%M")
        lay.addWidget(_etiqueta(f"Resultados de {persona}", "titulo"))
        lay.addWidget(_etiqueta(f"{res['nombre_bateria']}  ·  {fecha_txt}  ·  edad {int(res['edad'])} años", "suave"))

        total = res.get("total")
        if total:
            tarjeta, t = _tarjeta()
            fila = QHBoxLayout()
            ci = _etiqueta(str(total["ci"]), "ci", False)
            fila.addWidget(ci)
            der = QVBoxLayout()
            der.addWidget(_etiqueta("CI total estimado", "subtitulo"))
            der.addWidget(_etiqueta(f"Clasificación: <b>{total['clasificacion']}</b>   ·   "
                                    f"Percentil {total['percentil']:.0f} (supera al {total['percentil']:.0f}% "
                                    "de las personas de su edad)"))
            der.addWidget(_etiqueta(f"Rango probable (90%): {total['rango'][0]} – {total['rango'][1]}", "suave"))
            if res["sd"] != 15:
                der.addWidget(_etiqueta(f"Escala Cattell (desviación {res['sd']:g}). En escala Wechsler "
                                        f"(desviación 15) equivale a <b>{res['equivalente_15']}</b>.", "suave"))
            for e in res.get("extras", []):
                der.addWidget(_etiqueta(f"{e['nombre']}: <b>{e['ci']}</b> (rango {e['rango'][0]}–{e['rango'][1]})"))
            fila.addSpacing(20)
            fila.addLayout(der, 1)
            t.addLayout(fila)
            lay.addWidget(tarjeta)

        if res["indices"]:
            tarjeta, t = _tarjeta()
            t.addWidget(_etiqueta("Índices", "subtitulo"))
            t.addWidget(GraficaIndices(res["indices"] + res.get("extras", []), res["sd"]))
            t.addWidget(_etiqueta("La franja gris es el rango «Medio». La línea negra muestra el rango probable.",
                                  "suave"))
            lay.addWidget(tarjeta)

        tarjeta, t = _tarjeta()
        t.addWidget(_etiqueta("Subpruebas", "subtitulo"))
        tabla = QTableWidget(len(res["subpruebas"]), 3)
        tabla.setHorizontalHeaderLabels(["Subprueba", "Puntuación (1–19, media 10)", "Detalle"])
        tabla.verticalHeader().hide()
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i, s in enumerate(res["subpruebas"]):
            for j, v in enumerate([s["nombre"], str(s["escalar"]), s["detalle"]]):
                tabla.setItem(i, j, QTableWidgetItem(v))
        tabla.setMinimumHeight(36 * len(res["subpruebas"]) + 40)
        t.addWidget(tabla)
        lay.addWidget(tarjeta)
        lay.addWidget(_etiqueta(AVISO, "aviso"))
        lay.addWidget(pie_autor())
        lay.addStretch()
        self.scroll.setWidget(cont)

    def _pdf(self) -> None:
        carpeta = Path.home() / "Documentos" / "GeniusIQ"
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", str(carpeta / f"{self.nombre_archivo}.pdf"),
                                              "PDF (*.pdf)")
        if not ruta:
            return
        cont = self.scroll.widget()
        imagen = cont.grab()
        pdf = QPdfWriter(ruta)
        pdf.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        pdf.setResolution(150)
        p = QPainter(pdf)
        area = QRectF(p.viewport())
        escala = min(area.width() / imagen.width(), area.height() / imagen.height())
        p.drawPixmap(QRectF(0, 0, imagen.width() * escala, imagen.height() * escala), imagen,
                     QRectF(imagen.rect()))
        p.end()
        QMessageBox.information(self, "PDF", f"Guardado en:\n{ruta}")


# ------------------------------------------------------------------ historial

class PantallaHistorial(QWidget):
    volver = Signal()
    abrir = Signal(dict, str, str)

    def __init__(self, db: BaseDatos):
        super().__init__()
        self.db = db
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 24, 30, 14)
        lay.addWidget(_etiqueta("Historial", "titulo"))
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Persona", "Prueba", "Resultado"])
        self.tabla.verticalHeader().hide()
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.cellDoubleClicked.connect(lambda *_: self._ver())
        lay.addWidget(self.tabla, 1)
        fila = QHBoxLayout()
        volver = QPushButton("← Volver")
        volver.clicked.connect(self.volver.emit)
        borrar = QPushButton("Borrar")
        borrar.setObjectName("peligro")
        borrar.clicked.connect(self._borrar)
        ver = QPushButton("Ver resultado")
        ver.setObjectName("principal")
        ver.clicked.connect(self._ver)
        fila.addWidget(volver)
        fila.addStretch()
        fila.addWidget(borrar)
        fila.addWidget(ver)
        lay.addLayout(fila)
        self.filas: list = []

    def recargar(self) -> None:
        self.filas = self.db.sesiones()
        self.tabla.setRowCount(len(self.filas))
        for i, s in enumerate(self.filas):
            fecha = datetime.fromisoformat(s["fecha"]).strftime("%d/%m/%Y %H:%M")
            resultado = f"CI {s['ci']}" if s["ci"] is not None else json.loads(s["resultado"]).get("resumen", "")
            for j, v in enumerate([fecha, s["nombre"], s["bateria"], resultado]):
                self.tabla.setItem(i, j, QTableWidgetItem(v))

    def _sel(self):
        i = self.tabla.currentRow()
        return self.filas[i] if 0 <= i < len(self.filas) else None

    def _ver(self) -> None:
        s = self._sel()
        if s:
            self.abrir.emit(json.loads(s["resultado"]), s["nombre"], s["fecha"])

    def _borrar(self) -> None:
        s = self._sel()
        if s and QMessageBox.question(self, "Borrar", f"¿Borrar el resultado de {s['nombre']}?") \
                == QMessageBox.StandardButton.Yes:
            self.db.borrar_sesion(s["id"])
            self.recargar()

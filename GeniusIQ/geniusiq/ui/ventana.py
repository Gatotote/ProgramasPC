"""Ventana principal: lleva la sesión de una subprueba a la siguiente."""

from __future__ import annotations

import random
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from .. import VERSION
from ..baterias import SUBPRUEBAS, calcular, punto_inicio
from ..datos import BaseDatos, edad
from .estilo import QSS, paleta
from .pantallas import (PantallaHistorial, PantallaInicio, PantallaInstrucciones, PantallaPrueba,
                        PantallaResultados)
from .personalidad import PantallaCuestionario, PantallaPerfil
from .pruebas import PruebaBusqueda, PruebaClaves, PruebaCorsi, PruebaDigitos, PruebaItems

ICONO = Path(__file__).resolve().parent.parent / "icono.png"


class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"GeniusIQ {VERSION}")
        self.resize(1150, 820)
        self.db = BaseDatos()
        self.pila = QStackedWidget()
        self.setCentralWidget(self.pila)

        self.inicio = PantallaInicio(self.db)
        self.instr = PantallaInstrucciones()
        self.prueba = PantallaPrueba()
        self.resultados = PantallaResultados()
        self.historial = PantallaHistorial(self.db)
        self.cuestionario = PantallaCuestionario()
        self.perfil = PantallaPerfil()
        for w in (self.inicio, self.instr, self.prueba, self.resultados, self.historial, self.cuestionario,
                  self.perfil):
            self.pila.addWidget(w)

        self.inicio.comenzar.connect(self._comenzar)
        self.inicio.ver_historial.connect(self._ver_historial)
        self.instr.empezar.connect(self._empezar_subprueba)
        self.instr.salir.connect(self._salir)
        self.prueba.salir.connect(self._salir)
        self.resultados.volver.connect(lambda: self.pila.setCurrentWidget(self.inicio))
        self.historial.volver.connect(lambda: self.pila.setCurrentWidget(self.inicio))
        self.historial.abrir.connect(self._abrir_resultado)
        self.inicio.comenzar_personalidad.connect(self._comenzar_personalidad)
        self.cuestionario.terminado.connect(self._fin_cuestionario)
        self.cuestionario.salir.connect(self._salir)
        self.perfil.volver.connect(lambda: self.pila.setCurrentWidget(self.inicio))

    # ---------------------------------------------------------- sesión
    def _comenzar(self, persona, bateria, claves: list[str]) -> None:
        self.persona, self.bateria, self.claves = persona, bateria, claves
        self.edad = edad(persona["nacimiento"])
        self.rng = random.Random()
        self.paso = 0
        self.res: dict = {}
        self._instrucciones()

    def _instrucciones(self) -> None:
        if self.paso >= len(self.claves):
            self._terminar()
            return
        self.instr.mostrar(SUBPRUEBAS[self.claves[self.paso]], self.paso + 1, len(self.claves))
        self.pila.setCurrentWidget(self.instr)

    def _empezar_subprueba(self) -> None:
        sp = SUBPRUEBAS[self.claves[self.paso]]
        if sp.tipo == "items":
            items = sp.generar(self.rng)
            w = PruebaItems(sp, items, punto_inicio(items, self.edad, sp.norma))
        elif sp.tipo == "digitos":
            w = PruebaDigitos(self.edad, self.rng)
        elif sp.tipo == "corsi":
            w = PruebaCorsi(self.edad, self.rng)
        elif sp.tipo == "busqueda":
            w = PruebaBusqueda(self.rng)
        else:
            w = PruebaClaves(self.rng)
        w.terminado.connect(self._fin_subprueba)
        self.prueba.poner(sp.nombre, w)
        self.pila.setCurrentWidget(self.prueba)
        w.setFocus()

    def _fin_subprueba(self, resultado: dict) -> None:
        self.res[self.claves[self.paso]] = resultado
        self.prueba.quitar()
        self.paso += 1
        self._instrucciones()

    def _terminar(self) -> None:
        resultado = calcular(self.bateria, self.edad, self.res)
        self.db.guardar_sesion(self.persona["id"], resultado)
        self.resultados.mostrar(resultado, self.persona["nombre"], datetime.now().isoformat(timespec="minutes"))
        self.pila.setCurrentWidget(self.resultados)

    # ---------------------------------------------------------- personalidad
    def _comenzar_personalidad(self, persona, cuestionario) -> None:
        self.persona, self.c = persona, cuestionario
        self.cuestionario.iniciar(cuestionario)
        self.pila.setCurrentWidget(self.cuestionario)
        self.cuestionario.setFocus()

    def _fin_cuestionario(self, respuestas: list) -> None:
        e = edad(self.persona["nacimiento"])
        res = {**self.c.calificar(respuestas, e), "tipo": self.c.categoria, "prueba": self.c.clave,
               "nombre_bateria": self.c.nombre, "edad": e, "respuestas": respuestas}
        self.db.guardar_sesion(self.persona["id"], res)
        self.perfil.mostrar(res, self.persona["nombre"], datetime.now().isoformat(timespec="minutes"))
        self.pila.setCurrentWidget(self.perfil)

    def _salir(self) -> None:
        r = QMessageBox.question(self, "Salir", "¿Salir de la prueba? No se guardará nada.")
        if r == QMessageBox.StandardButton.Yes:
            self.prueba.quitar()
            self.pila.setCurrentWidget(self.inicio)

    # ---------------------------------------------------------- historial
    def _ver_historial(self) -> None:
        self.historial.recargar()
        self.pila.setCurrentWidget(self.historial)

    def _abrir_resultado(self, res: dict, nombre: str, fecha: str) -> None:
        if res.get("tipo") in ("personalidad", "salud"):
            self.perfil.mostrar(res, nombre, fecha)
            self.pila.setCurrentWidget(self.perfil)
        else:
            self.resultados.mostrar(res, nombre, fecha)
            self.pila.setCurrentWidget(self.resultados)

    def closeEvent(self, e):
        if self.pila.currentWidget() in (self.prueba, self.instr, self.cuestionario):
            r = QMessageBox.question(self, "Salir", "Hay una prueba en curso. ¿Cerrar de todos modos?")
            if r != QMessageBox.StandardButton.Yes:
                e.ignore()
                return
        self.prueba.quitar()
        e.accept()


def ejecutar() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GeniusIQ")
    app.setDesktopFileName("geniusiq")
    app.setStyle("Fusion")
    app.setPalette(paleta())
    app.setStyleSheet(QSS)
    if ICONO.exists():
        app.setWindowIcon(QIcon(str(ICONO)))
    v = Ventana()
    v.show()
    return app.exec()

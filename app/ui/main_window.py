from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.ui.configuracion_page import ConfiguracionPage
from app.ui.convertir_page import ConvertirPage
from app.ui.dashboard_page import DashboardPage
from app.ui.descargas_page import DescargasPage
from app.ui.historial_page import HistorialPage
from app.widgets.header import Header
from app.widgets.sidebar import Sidebar


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Descargador y Conversor")
        self.resize(1180, 780)
        self.setMinimumSize(940, 640)

        raiz = QWidget()
        horizontal = QHBoxLayout(raiz)
        horizontal.setContentsMargins(0, 0, 0, 0)
        horizontal.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.pagina_seleccionada.connect(self._cambiar_pagina)

        derecha = QWidget()
        vertical = QVBoxLayout(derecha)
        vertical.setContentsMargins(0, 0, 0, 0)
        vertical.setSpacing(0)
        self.header = Header()
        self.header.alternar_menu.connect(self._alternar_menu)
        vertical.addWidget(self.header)

        self.pagina_dashboard = DashboardPage()
        self.pagina_descargas = DescargasPage()
        self.pagina_convertir = ConvertirPage()
        self.pagina_historial = HistorialPage()
        self.pagina_config = ConfiguracionPage()

        self.paginas = QStackedWidget()
        for p in (
            self.pagina_dashboard,
            self.pagina_descargas,
            self.pagina_convertir,
            self.pagina_historial,
            self.pagina_config,
        ):
            self.paginas.addWidget(p)
        vertical.addWidget(self.paginas)

        horizontal.addWidget(self.sidebar)
        horizontal.addWidget(derecha, 1)
        self.setCentralWidget(raiz)

        if config.RUTA_TEMA.exists():
            self.setStyleSheet(config.RUTA_TEMA.read_text(encoding="utf-8"))

        # Enlaces entre páginas
        self.pagina_dashboard.ir_a.connect(self._cambiar_pagina)
        self.pagina_descargas.trabajo_terminado.connect(self._tras_trabajo)
        self.pagina_convertir.trabajo_terminado.connect(self._tras_trabajo)
        self.pagina_config.guardado.connect(self._tras_trabajo)

    def _alternar_menu(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _cambiar_pagina(self, indice):
        self.paginas.setCurrentIndex(indice)
        self.sidebar.seleccionar(indice)

    def _tras_trabajo(self):
        self.header.actualizar_estado()
        self.pagina_dashboard.refrescar()
        self.pagina_historial.refrescar()

    def closeEvent(self, evento):
        pendientes = self.pagina_descargas.hay_trabajo() or self.pagina_convertir.hay_trabajo()
        if pendientes:
            if QMessageBox.question(
                self, "Salir",
                "Hay un trabajo en curso. ¿Cancelarlo y salir?",
            ) != QMessageBox.Yes:
                evento.ignore()
                return
        self.pagina_descargas.detener()
        self.pagina_convertir.detener()
        super().closeEvent(evento)

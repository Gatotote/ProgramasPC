from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app import config
from app.widgets.iconos import icono

ITEMS = [
    ("Dashboard", "dashboard"),
    ("Descargar vídeos", "descargar"),
    ("Convertir archivos", "convertir"),
    ("Historial", "historial"),
    ("Configuración", "config"),
]


class Sidebar(QFrame):
    pagina_seleccionada = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(228)
        self.setStyleSheet("""
            QFrame#sidebar { background: #0b0f16; }
            QPushButton {
                text-align: left; padding: 11px 12px; border: none;
                color: #9aa6bc; background: transparent; font-size: 13px;
                border-radius: 8px;
            }
            QPushButton:hover { background: #151b27; color: #e8edf5; }
            QPushButton:checked {
                color: #ffffff; background: #1a2740;
                border-left: 3px solid #3b82f6;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 18, 12, 16)
        layout.setSpacing(3)

        marca = QWidget()
        fila_marca = QHBoxLayout(marca)
        fila_marca.setContentsMargins(4, 0, 4, 18)
        logo = QLabel()
        ruta_logo = config.RUTA_LOGO_CLARO if config.RUTA_LOGO_CLARO.exists() else config.RUTA_ICONO
        if ruta_logo.exists():
            pm = QPixmap(str(ruta_logo)).scaled(
                36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo.setPixmap(pm)
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("background:transparent;border:none;")
        titulo = QLabel("DESCARGA\nY CONVIERTE")
        titulo.setStyleSheet(
            "color:white;font-size:13px;font-weight:800;letter-spacing:0.8px;"
        )
        fila_marca.addWidget(logo)
        fila_marca.addWidget(titulo)
        fila_marca.addStretch()
        layout.addWidget(marca)

        self.botones = []
        for indice, (nombre, clave) in enumerate(ITEMS):
            boton = QPushButton(f"  {nombre}")
            boton.setIcon(icono(clave))
            boton.setCheckable(True)
            boton.setCursor(Qt.PointingHandCursor)
            boton.clicked.connect(lambda _, i=indice: self.pagina_seleccionada.emit(i))
            layout.addWidget(boton)
            self.botones.append(boton)

        self.botones[0].setChecked(True)
        layout.addStretch()

        pie = QLabel(f"v{config.VERSION}  ·  Hecho con IA y Genaro Velasco")
        pie.setAlignment(Qt.AlignCenter)
        pie.setStyleSheet("color:#5b6b82;font-size:9px;letter-spacing:0.3px;")
        layout.addWidget(pie)

    def seleccionar(self, indice):
        for i, boton in enumerate(self.botones):
            boton.setChecked(i == indice)

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from app import config
from app.services import descargas, ffmpeg
from app.widgets.iconos import icono


class Header(QFrame):
    alternar_menu = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(58)
        self.setStyleSheet("""
            QFrame { background: #121821; border-bottom: 1px solid #2a3142; }
            QLabel#titulo { font-size: 16px; font-weight: 800; letter-spacing: 1.4px; }
            QLabel#sub { color: #7b879c; font-size: 11px; }
            QPushButton { background: transparent; border: none; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 18, 8)

        hamburguesa = QPushButton()
        hamburguesa.setIcon(icono("menu", 20))
        hamburguesa.setIconSize(QSize(20, 20))
        hamburguesa.setCursor(Qt.PointingHandCursor)
        hamburguesa.setToolTip("Mostrar u ocultar el menú lateral")
        hamburguesa.clicked.connect(self.alternar_menu.emit)

        marca = QLabel()
        if config.RUTA_ICONO.exists():
            marca.setPixmap(QPixmap(str(config.RUTA_ICONO)).scaled(
                28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        marca.setFixedSize(32, 32)
        marca.setAlignment(Qt.AlignCenter)
        marca.setStyleSheet("background:transparent;border:none;")

        titulo = QLabel("DESCARGADOR Y CONVERSOR")
        titulo.setObjectName("titulo")

        self.lbl_estado = QLabel()
        self.lbl_estado.setObjectName("sub")
        self.lbl_estado.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(hamburguesa)
        layout.addSpacing(8)
        layout.addWidget(marca)
        layout.addSpacing(6)
        layout.addWidget(titulo)
        layout.addStretch()
        layout.addWidget(self.lbl_estado)
        self.actualizar_estado()

    def actualizar_estado(self):
        partes = []
        partes.append("FFmpeg ✓" if ffmpeg.disponible() else "FFmpeg ✗")
        js = descargas.runtime_js()
        partes.append(f"JS ✓ ({js})" if js else "JS ✗")
        v = descargas.version_yt_dlp()
        partes.append(f"yt-dlp {v}" if v else "yt-dlp ✗")
        self.lbl_estado.setText("   ·   ".join(partes))

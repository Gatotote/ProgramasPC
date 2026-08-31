from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class TarjetaKPI(QFrame):
    """Recuadro de color con un número grande y una etiqueta debajo."""

    def __init__(self, titulo, valor, color):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{ background: {color}; border-radius: 10px; }}
            QLabel#valor {{ font-size: 28px; font-weight: 800; color: white; }}
            QLabel#titulo {{ font-size: 12px; color: rgba(255,255,255,0.88); letter-spacing: 0.6px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        self.valor_lbl = QLabel(str(valor))
        self.valor_lbl.setObjectName("valor")
        titulo_lbl = QLabel(titulo.upper())
        titulo_lbl.setObjectName("titulo")
        layout.addWidget(self.valor_lbl)
        layout.addWidget(titulo_lbl)

    def actualizar_valor(self, valor):
        self.valor_lbl.setText(str(valor))


class Panel(QFrame):
    """Contenedor con borde de color y título en mayúsculas."""

    def __init__(self, titulo, borde="#2a3142", acento=None):
        super().__init__()
        color_titulo = acento or "#9aa6bc"
        self.setObjectName("panel")
        self.setStyleSheet(f"""
            QFrame#panel {{
                background: #171b24;
                border: 2px solid {borde};
                border-radius: 10px;
            }}
            QLabel#panelTitulo {{
                color: {color_titulo};
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.8px;
                border: none;
                background: transparent;
            }}
        """)
        self.layout_panel = QVBoxLayout(self)
        self.layout_panel.setContentsMargins(14, 12, 14, 12)
        self.layout_panel.setSpacing(10)
        etiqueta = QLabel(titulo.upper())
        etiqueta.setObjectName("panelTitulo")
        etiqueta.setAlignment(Qt.AlignLeft)
        self.layout_panel.addWidget(etiqueta)

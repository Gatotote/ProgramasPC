from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget


class SelectorCarpeta(QWidget):
    """Campo de texto con botón «…» para elegir una carpeta."""

    def __init__(self, valor="", titulo="Elegir carpeta"):
        super().__init__()
        self.titulo = titulo
        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(6)
        self.linea = QLineEdit(valor)
        self.boton = QPushButton("…")
        self.boton.setObjectName("ghost")
        self.boton.setFixedWidth(40)
        self.boton.clicked.connect(self._elegir)
        fila.addWidget(self.linea, 1)
        fila.addWidget(self.boton, 0)

    def _elegir(self):
        carpeta = QFileDialog.getExistingDirectory(self, self.titulo, self.linea.text())
        if carpeta:
            self.linea.setText(carpeta)

    def valor(self):
        return self.linea.text().strip()

    def set_valor(self, texto):
        self.linea.setText(texto)

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.services import descargas, ffmpeg
from app.widgets.campos import SelectorCarpeta
from app.widgets.tarjeta import Panel


class ConfiguracionPage(QWidget):
    guardado = Signal()

    def __init__(self):
        super().__init__()
        s = config.cargar_settings()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        cabecera = QLabel("Configuración")
        cabecera.setStyleSheet("font-size:20px;font-weight:800;")
        layout.addWidget(cabecera)

        # --- Carpetas y opciones ---
        gen = Panel("Carpetas y opciones por defecto", borde="#3b82f6", acento="#93c5fd")
        gen.layout_panel.addWidget(QLabel("Carpeta de descargas:"))
        self.sel_desc = SelectorCarpeta(s["carpeta_descargas"])
        gen.layout_panel.addWidget(self.sel_desc)
        gen.layout_panel.addWidget(QLabel("Carpeta de conversiones:"))
        self.sel_conv = SelectorCarpeta(s["carpeta_conversiones"])
        gen.layout_panel.addWidget(self.sel_conv)

        fila_cal = QHBoxLayout()
        fila_cal.addWidget(QLabel("Calidad por defecto:"))
        self.combo_calidad = QComboBox()
        self.combo_calidad.addItems(descargas.CALIDADES)
        if s["calidad"] in descargas.CALIDADES:
            self.combo_calidad.setCurrentText(s["calidad"])
        self.combo_calidad.setFixedWidth(240)
        fila_cal.addWidget(self.combo_calidad)
        fila_cal.addStretch()
        gen.layout_panel.addLayout(fila_cal)

        self.chk_audio = QCheckBox("Descargar solo audio (MP3) por defecto")
        self.chk_audio.setChecked(bool(s["solo_audio"]))
        gen.layout_panel.addWidget(self.chk_audio)

        fila_ck = QHBoxLayout()
        fila_ck.addWidget(QLabel("Cookies del navegador:"))
        self.combo_cookies = QComboBox()
        self.combo_cookies.addItems(list(descargas.NAVEGADORES_COOKIES.keys()))
        for etiqueta, valor in descargas.NAVEGADORES_COOKIES.items():
            if valor == s.get("navegador_cookies", ""):
                self.combo_cookies.setCurrentText(etiqueta)
                break
        self.combo_cookies.setFixedWidth(200)
        fila_ck.addWidget(self.combo_cookies)
        fila_ck.addStretch()
        gen.layout_panel.addLayout(fila_ck)
        nota_ck = QLabel(
            "Para el aviso de YouTube «confirma que no eres un bot»: yt-dlp usará las "
            "cookies de ese navegador (debes tener la sesión iniciada allí)."
        )
        nota_ck.setWordWrap(True)
        nota_ck.setStyleSheet("color:#8b97ad;font-size:11px;")
        gen.layout_panel.addWidget(nota_ck)
        layout.addWidget(gen)

        # --- FFmpeg ---
        ffm = Panel("FFmpeg", borde="#f59e0b", acento="#fbbf24")
        self.lbl_ffmpeg = QLabel()
        self.lbl_ffmpeg.setWordWrap(True)
        ffm.layout_panel.addWidget(self.lbl_ffmpeg)
        fila_ff = QHBoxLayout()
        self.linea_ffmpeg = QLineEdit(s["ffmpeg_manual"])
        self.linea_ffmpeg.setPlaceholderText("Ruta a ffmpeg.exe (opcional, si no está en el PATH)")
        b_ff = QPushButton("…")
        b_ff.setObjectName("ghost")
        b_ff.setFixedWidth(40)
        b_ff.clicked.connect(self._elegir_ffmpeg)
        fila_ff.addWidget(self.linea_ffmpeg, 1)
        fila_ff.addWidget(b_ff, 0)
        ffm.layout_panel.addLayout(fila_ff)
        ayuda = QLabel(
            "En Windows puedes instalarlo con  winget install ffmpeg  y reiniciar el programa. "
            "yt-dlp se actualiza con  pip install -U yt-dlp."
        )
        ayuda.setWordWrap(True)
        ayuda.setStyleSheet("color:#8b97ad;font-size:11px;")
        ffm.layout_panel.addWidget(ayuda)
        layout.addWidget(ffm)

        fila_guardar = QHBoxLayout()
        b_guardar = QPushButton("Guardar cambios")
        b_guardar.setCursor(Qt.PointingHandCursor)
        b_guardar.clicked.connect(self._guardar)
        fila_guardar.addWidget(b_guardar)
        fila_guardar.addStretch()
        layout.addLayout(fila_guardar)
        layout.addStretch()

        self._pintar_estado_ffmpeg()

    def _elegir_ffmpeg(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Elegir ffmpeg", "", "ffmpeg (ffmpeg.exe ffmpeg);;Todos (*.*)")
        if ruta:
            self.linea_ffmpeg.setText(ruta)

    def _pintar_estado_ffmpeg(self):
        v = ffmpeg.version()
        if v:
            self.lbl_ffmpeg.setText(f"✓ FFmpeg detectado: {v}")
            self.lbl_ffmpeg.setStyleSheet("color:#86efac;")
        else:
            self.lbl_ffmpeg.setText("✗ FFmpeg no encontrado. Sin él no se puede convertir ni bajar MP3.")
            self.lbl_ffmpeg.setStyleSheet("color:#fbbf24;")

    def _guardar(self):
        config.guardar_settings({
            "carpeta_descargas": self.sel_desc.valor(),
            "carpeta_conversiones": self.sel_conv.valor(),
            "calidad": self.combo_calidad.currentText(),
            "solo_audio": self.chk_audio.isChecked(),
            "ffmpeg_manual": self.linea_ffmpeg.text().strip(),
            "navegador_cookies": descargas.NAVEGADORES_COOKIES.get(
                self.combo_cookies.currentText(), ""
            ),
        })
        self._pintar_estado_ffmpeg()
        self.guardado.emit()
        QMessageBox.information(self, "Configuración", "Cambios guardados.")

    def showEvent(self, evento):
        self._pintar_estado_ffmpeg()
        super().showEvent(evento)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.services import descargas, ffmpeg
from app.widgets.campos import SelectorCarpeta
from app.widgets.tarjeta import Panel

ANCHO_MINIATURA = 200
ALTO_MINIATURA = 112


class DescargasPage(QWidget):
    trabajo_terminado = Signal()

    def __init__(self):
        super().__init__()
        self.worker = None
        s = config.cargar_settings()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        cabecera = QLabel("Descargar vídeos")
        cabecera.setStyleSheet("font-size:20px;font-weight:800;")
        layout.addWidget(cabecera)
        sub = QLabel("Pega uno o varios enlaces (uno por línea). Compatible con cientos de sitios vía yt-dlp.")
        sub.setStyleSheet("color:#8b97ad;font-size:11px;")
        layout.addWidget(sub)

        # --- Origen ---
        origen = Panel("Origen", borde="#3b82f6", acento="#93c5fd")
        self.txt_urls = QPlainTextEdit()
        self.txt_urls.setPlaceholderText("https://…\nhttps://…")
        self.txt_urls.setFixedHeight(96)
        origen.layout_panel.addWidget(self.txt_urls)
        layout.addWidget(origen)

        # --- Opciones ---
        opciones = Panel("Opciones", borde="#f59e0b", acento="#fbbf24")
        fila_cal = QHBoxLayout()
        fila_cal.setSpacing(10)
        fila_cal.addWidget(QLabel("Calidad:"))
        self.combo_calidad = QComboBox()
        self.combo_calidad.addItems(descargas.CALIDADES)
        if s["calidad"] in descargas.CALIDADES:
            self.combo_calidad.setCurrentText(s["calidad"])
        self.combo_calidad.setFixedWidth(240)
        fila_cal.addWidget(self.combo_calidad)
        fila_cal.addStretch()
        opciones.layout_panel.addLayout(fila_cal)

        self.chk_audio = QCheckBox("Descargar solo audio (MP3)")
        self.chk_audio.setChecked(bool(s["solo_audio"]))
        opciones.layout_panel.addWidget(self.chk_audio)

        fila_ck = QHBoxLayout()
        fila_ck.setSpacing(10)
        fila_ck.addWidget(QLabel("Cookies de:"))
        self.combo_cookies = QComboBox()
        self.combo_cookies.addItems(list(descargas.NAVEGADORES_COOKIES.keys()))
        for etiqueta, valor in descargas.NAVEGADORES_COOKIES.items():
            if valor == s.get("navegador_cookies", ""):
                self.combo_cookies.setCurrentText(etiqueta)
                break
        self.combo_cookies.setFixedWidth(160)
        self.combo_cookies.setToolTip(
            "Si YouTube pide «confirma que no eres un bot», elige el navegador\n"
            "donde tienes la sesión iniciada para que yt-dlp use sus cookies."
        )
        fila_ck.addWidget(self.combo_cookies)
        fila_ck.addWidget(QLabel("(para el aviso de YouTube «no soy un bot»)"))
        fila_ck.addStretch()
        opciones.layout_panel.addLayout(fila_ck)

        self.aviso_ffmpeg = QLabel(
            "⚠ FFmpeg no encontrado: se usará una sola calidad combinada para no "
            "dejar vídeo y audio en archivos separados. El MP3 tampoco estará disponible."
        )
        self.aviso_ffmpeg.setWordWrap(True)
        self.aviso_ffmpeg.setStyleSheet("color:#fbbf24;font-size:11px;")
        self.aviso_ffmpeg.setVisible(not ffmpeg.disponible())
        opciones.layout_panel.addWidget(self.aviso_ffmpeg)

        opciones.layout_panel.addWidget(QLabel("Carpeta de destino:"))
        self.sel_carpeta = SelectorCarpeta(s["carpeta_descargas"], "Carpeta de descargas")
        opciones.layout_panel.addWidget(self.sel_carpeta)
        layout.addWidget(opciones)

        # --- Acciones ---
        acciones = QHBoxLayout()
        self.btn_descargar = QPushButton("Descargar")
        self.btn_descargar.setCursor(Qt.PointingHandCursor)
        self.btn_descargar.clicked.connect(self._iniciar)
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("ghost")
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.clicked.connect(self._cancelar)
        acciones.addWidget(self.btn_descargar)
        acciones.addWidget(self.btn_cancelar)
        acciones.addStretch()
        layout.addLayout(acciones)

        # --- Progreso ---
        progreso = Panel("Progreso", borde="#22c55e", acento="#86efac")
        fila_p = QHBoxLayout()
        fila_p.setSpacing(12)
        self.lbl_miniatura = QLabel("🎬")
        self.lbl_miniatura.setFixedSize(ANCHO_MINIATURA, ALTO_MINIATURA)
        self.lbl_miniatura.setAlignment(Qt.AlignCenter)
        self.lbl_miniatura.setStyleSheet(
            "background:#0f141d;border:1px solid #2a3142;border-radius:8px;font-size:26px;"
        )
        col_p = QVBoxLayout()
        col_p.setSpacing(6)
        self.lbl_titulo = QLabel("Ningún vídeo en curso.")
        self.lbl_titulo.setWordWrap(True)
        self.lbl_titulo.setStyleSheet("font-weight:700;")
        self.barra = QProgressBar()
        self.barra.setValue(0)
        self.lbl_sub = QLabel("Listo para descargar.")
        self.lbl_sub.setStyleSheet("color:#8b97ad;font-size:11px;")
        col_p.addWidget(self.lbl_titulo)
        col_p.addWidget(self.barra)
        col_p.addWidget(self.lbl_sub)
        col_p.addStretch()
        fila_p.addWidget(self.lbl_miniatura, 0)
        fila_p.addLayout(col_p, 1)
        progreso.layout_panel.addLayout(fila_p)
        layout.addWidget(progreso)
        layout.addStretch()

        scroll.setWidget(cont)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.addWidget(scroll)

    # -- lógica -------------------------------------------------------------

    def _iniciar(self):
        if not descargas.yt_dlp_disponible():
            QMessageBox.critical(
                self, "Falta yt-dlp",
                "No se encontró la librería yt-dlp.\n\nInstálala con:\npip install yt-dlp",
            )
            return
        texto = self.txt_urls.toPlainText()
        urls = [l.strip() for l in texto.splitlines() if l.strip()]
        if not urls:
            QMessageBox.warning(self, "Faltan enlaces", "Pega al menos una URL (una por línea).")
            return
        if self.chk_audio.isChecked() and not ffmpeg.disponible():
            QMessageBox.warning(
                self, "Falta FFmpeg",
                "Convertir a MP3 requiere FFmpeg. Instálalo o desmarca «solo audio».",
            )
            return

        carpeta = self.sel_carpeta.valor()
        navegador = descargas.NAVEGADORES_COOKIES.get(self.combo_cookies.currentText(), "")
        config.guardar_settings({
            "carpeta_descargas": carpeta,
            "calidad": self.combo_calidad.currentText(),
            "solo_audio": self.chk_audio.isChecked(),
            "navegador_cookies": navegador,
        })

        self._poner_en_marcha(True)
        self.barra.setValue(0)
        self.lbl_titulo.setText("Buscando información…")
        self.lbl_sub.setText(f"Preparando {len(urls)} vídeo(s)…")
        self._restablecer_miniatura()

        self.worker = descargas.DescargaWorker(
            urls, carpeta, self.combo_calidad.currentText(), self.chk_audio.isChecked(),
            navegador_cookies=navegador,
        )
        self.worker.empieza_uno.connect(self._al_empezar_uno)
        self.worker.info_lista.connect(self._al_recibir_info)
        self.worker.progreso.connect(self._al_progreso)
        self.worker.uno_terminado.connect(self._al_terminar_uno)
        self.worker.todo_terminado.connect(self._al_terminar_todo)
        self.worker.start()

    def _cancelar(self):
        if self.worker:
            self.worker.cancelar()
            self.btn_cancelar.setEnabled(False)
            self.lbl_sub.setText("Cancelando…")

    def _poner_en_marcha(self, activo):
        self.btn_descargar.setEnabled(not activo)
        self.btn_cancelar.setEnabled(activo)

    def _restablecer_miniatura(self):
        self.lbl_miniatura.setPixmap(QPixmap())
        self.lbl_miniatura.setText("🎬")

    def _al_empezar_uno(self, idx, total, url):
        self.barra.setValue(0)
        self.lbl_sub.setText(f"Vídeo {idx} de {total}…")

    def _al_recibir_info(self, titulo, miniatura):
        self.lbl_titulo.setText(titulo)
        if miniatura:
            pm = QPixmap()
            if pm.loadFromData(bytes(miniatura)):
                self.lbl_miniatura.setPixmap(pm.scaled(
                    ANCHO_MINIATURA, ALTO_MINIATURA,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation,
                ))
                self.lbl_miniatura.setText("")
                return
        self._restablecer_miniatura()

    def _al_progreso(self, pct, texto):
        self.barra.setValue(pct)
        self.lbl_sub.setText(f"Descargando… {texto}".strip())

    def _al_terminar_uno(self, titulo, ok):
        estado = "ok" if ok else "error"
        config.agregar_historial(
            "descarga", titulo if ok else "Descarga fallida",
            detalle=self.combo_calidad.currentText() if not self.chk_audio.isChecked() else "MP3",
            origen=titulo, carpeta=self.sel_carpeta.valor(), estado=estado,
        )

    def _al_terminar_todo(self, ok, total, errores):
        self._poner_en_marcha(False)
        self.worker = None
        self.barra.setValue(100 if ok else 0)
        self.lbl_sub.setText(f"Completado: {ok} de {total}.")
        self.lbl_titulo.setText("Ningún vídeo en curso.")
        self._restablecer_miniatura()
        self.trabajo_terminado.emit()
        if errores and errores[0][0] == "" and "yt-dlp" in errores[0][1]:
            QMessageBox.critical(self, "Error", errores[0][1])
            return
        if errores:
            det = "\n".join(f"• {u[:60]}: {m}" for u, m in errores[:5])
            extra = ""
            if any(descargas.es_error_de_cookies(m) for _, m in errores):
                if self.combo_cookies.currentText() == "Ninguno":
                    extra = (
                        "\n\nYouTube pide iniciar sesión. En «Cookies de:» elige el "
                        "navegador donde tengas tu cuenta abierta y vuelve a intentarlo."
                    )
                else:
                    extra = (
                        "\n\nNo se pudieron leer las cookies de "
                        f"{self.combo_cookies.currentText()}. Cierra ese navegador por "
                        "completo (o prueba con otro) y reintenta."
                    )
            QMessageBox.warning(
                self, "Terminó con errores", f"{ok} de {total} correctos.\n\n{det}{extra}"
            )
        else:
            QMessageBox.information(self, "Listo", f"Se descargaron {ok} de {total} vídeo(s).")

    def hay_trabajo(self):
        return self.worker is not None and self.worker.isRunning()

    def detener(self):
        if self.worker:
            self.worker.cancelar()
            self.worker.wait(3000)

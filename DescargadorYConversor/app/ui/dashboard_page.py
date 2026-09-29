from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.services import descargas, ffmpeg, imagenes
from app.widgets.chip import Chip
from app.widgets.tarjeta import IndicadorCircular, Panel


class DashboardPage(QWidget):
    ir_a = Signal(int)   # índice de página en el QStackedWidget

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cont = QWidget()
        layout = QVBoxLayout(cont)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        cabecera = QLabel("Panel principal")
        cabecera.setStyleSheet("font-size:20px;font-weight:800;")
        layout.addWidget(cabecera)

        # --- Cuerpo: círculos a la izquierda, paneles en lista a la derecha ---
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(14)

        col_ind = QVBoxLayout()
        col_ind.setSpacing(10)
        self.kpi_descargas = IndicadorCircular("Descargas", 0, "#3b82f6")
        self.kpi_conversiones = IndicadorCircular("Conversiones", 0, "#f59e0b")
        self.kpi_audio = IndicadorCircular("Solo audio", 0, "#22c55e")
        self.kpi_errores = IndicadorCircular("Con error", 0, "#ef4444")
        for ind in (self.kpi_descargas, self.kpi_conversiones, self.kpi_audio, self.kpi_errores):
            col_ind.addWidget(ind)
        col_ind.addStretch()
        panel_ind = QWidget()
        panel_ind.setLayout(col_ind)
        panel_ind.setFixedWidth(140)
        cuerpo.addWidget(panel_ind, 0, Qt.AlignTop)

        col_pan = QVBoxLayout()
        col_pan.setSpacing(12)

        acciones = Panel("Acciones rápidas", borde="#3b82f6", acento="#93c5fd")
        b_desc = QPushButton("  Descargar un vídeo")
        b_desc.setObjectName("ghost")
        b_desc.setMinimumHeight(44)
        b_desc.setCursor(Qt.PointingHandCursor)
        b_desc.clicked.connect(lambda: self.ir_a.emit(1))
        b_conv = QPushButton("  Convertir un archivo")
        b_conv.setObjectName("ghost")
        b_conv.setMinimumHeight(44)
        b_conv.setCursor(Qt.PointingHandCursor)
        b_conv.clicked.connect(lambda: self.ir_a.emit(2))
        b_hist = QPushButton("  Ver historial")
        b_hist.setObjectName("ghost")
        b_hist.setMinimumHeight(44)
        b_hist.setCursor(Qt.PointingHandCursor)
        b_hist.clicked.connect(lambda: self.ir_a.emit(3))
        for b in (b_desc, b_conv, b_hist):
            acciones.layout_panel.addWidget(b)
        col_pan.addWidget(acciones)

        estado = Panel("Estado del sistema", borde="#f59e0b", acento="#fbbf24")
        self.fila_ffmpeg = QHBoxLayout()
        self.fila_ffmpeg.addWidget(QLabel("FFmpeg:"))
        self.chip_ffmpeg = Chip("—", "gris")
        self.fila_ffmpeg.addWidget(self.chip_ffmpeg)
        self.fila_ffmpeg.addStretch()
        estado.layout_panel.addLayout(self.fila_ffmpeg)
        self.lbl_ytdlp = QLabel()
        self.lbl_js = QLabel()
        self.lbl_js.setWordWrap(True)
        self.lbl_raw = QLabel()
        self.lbl_raw.setWordWrap(True)
        self.lbl_carpetas = QLabel()
        self.lbl_carpetas.setWordWrap(True)
        for w in (self.lbl_ytdlp, self.lbl_js, self.lbl_raw, self.lbl_carpetas):
            w.setStyleSheet("color:#9aa6bc;font-size:11px;")
            estado.layout_panel.addWidget(w)
        col_pan.addWidget(estado)

        reciente = Panel("Actividad reciente", borde="#a78bfa", acento="#c4b5fd")
        scroll_r = QScrollArea()
        scroll_r.setWidgetResizable(True)
        scroll_r.setFrameShape(QScrollArea.NoFrame)
        scroll_r.setMinimumHeight(160)
        cont_r = QWidget()
        self.layout_reciente = QVBoxLayout(cont_r)
        self.layout_reciente.setContentsMargins(0, 0, 4, 0)
        self.layout_reciente.setSpacing(6)
        scroll_r.setWidget(cont_r)
        reciente.layout_panel.addWidget(scroll_r)
        col_pan.addWidget(reciente, 1)

        cuerpo.addLayout(col_pan, 1)
        layout.addLayout(cuerpo, 1)

        scroll.setWidget(cont)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.addWidget(scroll)
        self.refrescar()

    def refrescar(self):
        historial = config.cargar_historial()
        descargas_n = sum(1 for h in historial if h.get("tipo") == "descarga" and h.get("estado") == "ok")
        conv_n = sum(1 for h in historial if h.get("tipo") == "conversion" and h.get("estado") == "ok")
        audio_n = sum(
            1 for h in historial
            if h.get("tipo") == "descarga" and h.get("estado") == "ok"
            and "mp3" in (h.get("detalle") or "").lower()
        )
        err_n = sum(1 for h in historial if h.get("estado") == "error")
        self.kpi_descargas.actualizar_valor(descargas_n)
        self.kpi_conversiones.actualizar_valor(conv_n)
        self.kpi_audio.actualizar_valor(audio_n)
        self.kpi_errores.actualizar_valor(err_n)

        if ffmpeg.disponible():
            self.chip_ffmpeg.setText("Detectado")
            self.chip_ffmpeg.setStyleSheet(
                "background:#052e16;color:#4ade80;border-radius:9px;padding:3px 10px;"
                "font-size:11px;font-weight:700;"
            )
        else:
            self.chip_ffmpeg.setText("No encontrado")
            self.chip_ffmpeg.setStyleSheet(
                "background:#3f0d0d;color:#f87171;border-radius:9px;padding:3px 10px;"
                "font-size:11px;font-weight:700;"
            )
        v = descargas.version_yt_dlp()
        self.lbl_ytdlp.setText(f"yt-dlp: {v}" if v else "yt-dlp: no instalado")
        js = descargas.runtime_js()
        if js:
            self.lbl_js.setText(f"Motor JS: {js} (necesario para YouTube)")
            self.lbl_js.setStyleSheet("color:#86efac;font-size:11px;")
        else:
            self.lbl_js.setText("Motor JS: falta — YouTube no funcionará. Instala Deno (winget install DenoLand.Deno)")
            self.lbl_js.setStyleSheet("color:#fbbf24;font-size:11px;")
        if imagenes.raw_disponible():
            self.lbl_raw.setText("RAW de cámara: rawpy OK (CR2/CR3, NEF, ARW, RAF, RW2, ORF…)")
            self.lbl_raw.setStyleSheet("color:#86efac;font-size:11px;")
        else:
            self.lbl_raw.setText("RAW de cámara: falta rawpy (pip install rawpy)")
            self.lbl_raw.setStyleSheet("color:#fbbf24;font-size:11px;")
        s = config.cargar_settings()
        self.lbl_carpetas.setText(
            f"Descargas → {s['carpeta_descargas']}\nConversiones → {s['carpeta_conversiones']}"
        )

        while self.layout_reciente.count():
            item = self.layout_reciente.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        ultimos = list(reversed(historial))[:9]
        if not ultimos:
            vacio = QLabel("Aún no hay actividad.")
            vacio.setStyleSheet("color:#8b97ad;")
            self.layout_reciente.addWidget(vacio)
        for h in ultimos:
            icono = "⬇" if h.get("tipo") == "descarga" else "⇄"
            color = "#86efac" if h.get("estado") == "ok" else "#f87171"
            fila = QLabel(f"{icono}  {(h.get('titulo') or '')[:42]}")
            fila.setToolTip(f"{h.get('fecha','')} · {h.get('detalle','')}")
            fila.setStyleSheet(f"color:{color};font-size:11px;")
            self.layout_reciente.addWidget(fila)
        self.layout_reciente.addStretch()

    def showEvent(self, evento):
        self.refrescar()
        super().showEvent(evento)

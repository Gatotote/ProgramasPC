"""
Descargador de Videos - Interfaz gráfica para Windows
Usa la librería yt-dlp para descargar videos de una gran variedad de sitios web.
Incluye historial de descargas, miniatura y nombre del archivo en progreso,
ventana redimensionable con apariencia moderna, y fusión automática de
video+audio en un solo archivo cuando FFmpeg está disponible.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import json
import shutil
import subprocess
import urllib.request
from io import BytesIO
from datetime import datetime

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

CARPETA_CONFIG = os.path.join(os.path.expanduser("~"), ".descargador_videos")
ARCHIVO_SETTINGS = os.path.join(CARPETA_CONFIG, "settings.json")
ARCHIVO_HISTORIAL = os.path.join(CARPETA_CONFIG, "historial.json")

ANCHO_MINIATURA = 192
ALTO_MINIATURA = 108


def cargar_json(ruta, valor_por_defecto):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return valor_por_defecto


def guardar_json(ruta, datos):
    os.makedirs(CARPETA_CONFIG, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def ffmpeg_disponible():
    return shutil.which("ffmpeg") is not None


class DescargadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Descargador de Videos")
        self.root.minsize(620, 560)
        self.root.geometry("680x600")
        self.root.resizable(True, True)

        self._configurar_estilo()

        settings = cargar_json(ARCHIVO_SETTINGS, {})
        carpeta_guardada = settings.get(
            "ultima_carpeta", os.path.join(os.path.expanduser("~"), "Downloads")
        )

        self.historial = cargar_json(ARCHIVO_HISTORIAL, [])

        self.carpeta_destino = tk.StringVar(value=carpeta_guardada)
        self.calidad_var = tk.StringVar(value="Mejor calidad disponible")
        self.solo_audio_var = tk.BooleanVar(value=False)
        self.cancelar_evento = threading.Event()
        self.imagen_miniatura_actual = None
        self.ffmpeg_ok = ffmpeg_disponible()

        self._construir_interfaz()

    def _configurar_estilo(self):
        style = ttk.Style(self.root)
        temas = style.theme_names()
        # "vista" es el tema con apariencia nativa más moderna disponible en Tk para Windows.
        for preferido in ("vista", "winnative", "clam"):
            if preferido in temas:
                style.theme_use(preferido)
                break

        color_fondo = "#f3f3f3"
        self.root.configure(bg=color_fondo)
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TLabelframe", padding=10)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Titulo.TLabel", font=("Segoe UI Semibold", 17, "bold"))
        style.configure("Subtitulo.TLabel", font=("Segoe UI", 10), foreground="#555555")
        style.configure("Accion.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("TButton", padding=6)
        style.configure("TNotebook", tabmargins=[6, 6, 6, 0])
        style.configure("TNotebook.Tab", padding=[14, 6], font=("Segoe UI", 10))

    def _construir_interfaz(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_descarga = ttk.Frame(notebook)
        self.tab_historial = ttk.Frame(notebook)
        notebook.add(self.tab_descarga, text="Descargar")
        notebook.add(self.tab_historial, text="Historial")

        self._construir_tab_descarga(self.tab_descarga)
        self._construir_tab_historial(self.tab_historial)

    def _construir_tab_descarga(self, contenedor):
        contenedor.columnconfigure(0, weight=1)

        encabezado = ttk.Frame(contenedor)
        encabezado.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ttk.Label(encabezado, text="Descargador de Videos", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            encabezado,
            text="Pega el enlace, elige tus opciones y descarga.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w")

        grupo_origen = ttk.LabelFrame(contenedor, text="Origen")
        grupo_origen.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        grupo_origen.columnconfigure(0, weight=1)
        ttk.Label(
            grupo_origen, text="URLs del video (una por línea; puedes pegar varias):"
        ).grid(row=0, column=0, sticky="w")
        self.url_text = tk.Text(
            grupo_origen, height=4, font=("Segoe UI", 10), wrap="word",
            relief="solid", borderwidth=1
        )
        self.url_text.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        grupo_opciones = ttk.LabelFrame(contenedor, text="Opciones")
        grupo_opciones.grid(row=2, column=0, sticky="ew", padx=16, pady=8)
        grupo_opciones.columnconfigure(1, weight=1)

        ttk.Label(grupo_opciones, text="Calidad:").grid(row=0, column=0, sticky="w")
        combo_calidad = ttk.Combobox(
            grupo_opciones,
            textvariable=self.calidad_var,
            values=["Mejor calidad disponible", "1080p", "720p", "480p", "360p"],
            state="readonly",
            width=25,
        )
        combo_calidad.grid(row=0, column=1, sticky="w", padx=10)

        check_audio = ttk.Checkbutton(
            grupo_opciones, text="Descargar solo audio (MP3)", variable=self.solo_audio_var
        )
        check_audio.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 4))

        if not self.ffmpeg_ok:
            ttk.Label(
                grupo_opciones,
                text="⚠ FFmpeg no encontrado: se usará una sola calidad combinada\n"
                     "para evitar archivos separados de video y audio.",
                foreground="#a15c00",
                justify="left",
            ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))

        ttk.Label(grupo_opciones, text="Carpeta de destino:").grid(row=3, column=0, sticky="w", pady=(10, 0))
        subframe = ttk.Frame(grupo_opciones)
        subframe.grid(row=4, column=0, columnspan=2, sticky="ew", pady=4)
        subframe.columnconfigure(0, weight=1)
        entry_carpeta = ttk.Entry(subframe, textvariable=self.carpeta_destino)
        entry_carpeta.grid(row=0, column=0, sticky="ew")
        boton_carpeta = ttk.Button(subframe, text="📁", width=3, command=self._elegir_carpeta)
        boton_carpeta.grid(row=0, column=1, padx=(6, 0))

        frame_acciones = ttk.Frame(contenedor)
        frame_acciones.grid(row=3, column=0, pady=(4, 8))
        self.boton_descargar = ttk.Button(
            frame_acciones, text="Descargar", style="Accion.TButton", command=self._iniciar_descarga
        )
        self.boton_descargar.pack(side="left", padx=6)
        self.boton_cancelar = ttk.Button(
            frame_acciones, text="Cancelar", command=self._cancelar_descarga, state="disabled"
        )
        self.boton_cancelar.pack(side="left", padx=6)

        grupo_progreso = ttk.LabelFrame(contenedor, text="Progreso")
        grupo_progreso.grid(row=4, column=0, sticky="ew", padx=16, pady=(8, 16))
        grupo_progreso.columnconfigure(1, weight=1)

        self.label_miniatura = ttk.Label(
            grupo_progreso, text="🎬", anchor="center", relief="solid", borderwidth=1,
            font=("Segoe UI", 28)
        )
        self.label_miniatura.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 12), ipadx=30, ipady=30)

        self.label_titulo_descarga = ttk.Label(
            grupo_progreso, text="Ningún video en curso.", font=("Segoe UI", 10, "bold"), wraplength=380
        )
        self.label_titulo_descarga.grid(row=0, column=1, sticky="w")

        self.barra_progreso = ttk.Progressbar(grupo_progreso, orient="horizontal", mode="determinate")
        self.barra_progreso.grid(row=1, column=1, sticky="ew", pady=(6, 4))

        self.label_estado = ttk.Label(grupo_progreso, text="Listo para descargar.", style="Subtitulo.TLabel")
        self.label_estado.grid(row=2, column=0, columnspan=2, sticky="w")

    def _construir_tab_historial(self, contenedor):
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(1, weight=1)
        padding = {"padx": 16, "pady": 6}

        ttk.Label(contenedor, text="Historial de descargas", style="Titulo.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 8)
        )

        columnas = ("titulo", "fecha", "carpeta")
        self.tabla_historial = ttk.Treeview(contenedor, columns=columnas, show="headings")
        self.tabla_historial.heading("titulo", text="Título")
        self.tabla_historial.heading("fecha", text="Fecha")
        self.tabla_historial.heading("carpeta", text="Carpeta")
        self.tabla_historial.column("titulo", width=260)
        self.tabla_historial.column("fecha", width=130)
        self.tabla_historial.column("carpeta", width=200)
        self.tabla_historial.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        self.tabla_historial.bind("<Double-1>", self._abrir_carpeta_seleccionada)

        frame_botones = ttk.Frame(contenedor)
        frame_botones.grid(row=2, column=0, sticky="w", **padding)
        ttk.Button(frame_botones, text="Abrir carpeta", command=self._abrir_carpeta_seleccionada).pack(
            side="left", padx=4
        )
        ttk.Button(frame_botones, text="Borrar historial", command=self._borrar_historial).pack(
            side="left", padx=4
        )

        self._refrescar_historial()

    def _refrescar_historial(self):
        for fila in self.tabla_historial.get_children():
            self.tabla_historial.delete(fila)
        for entrada in reversed(self.historial):
            self.tabla_historial.insert(
                "", "end",
                values=(entrada.get("titulo", ""), entrada.get("fecha", ""), entrada.get("carpeta", "")),
            )

    def _abrir_carpeta_seleccionada(self, event=None):
        seleccion = self.tabla_historial.selection()
        if not seleccion:
            messagebox.showinfo("Historial", "Selecciona primero un elemento del historial.")
            return
        valores = self.tabla_historial.item(seleccion[0], "values")
        carpeta = valores[2] if len(valores) > 2 else None
        if carpeta and os.path.isdir(carpeta):
            if sys.platform == "win32":
                os.startfile(carpeta)
            else:
                subprocess.Popen(["xdg-open", carpeta])
        else:
            messagebox.showwarning("Carpeta no encontrada", "La carpeta ya no existe en esta ubicación.")

    def _borrar_historial(self):
        if not self.historial:
            return
        confirmar = messagebox.askyesno("Borrar historial", "¿Seguro que quieres borrar todo el historial?")
        if confirmar:
            self.historial = []
            guardar_json(ARCHIVO_HISTORIAL, self.historial)
            self._refrescar_historial()

    def _agregar_al_historial(self, titulo, url, carpeta):
        entrada = {
            "titulo": titulo,
            "url": url,
            "carpeta": carpeta,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self.historial.append(entrada)
        guardar_json(ARCHIVO_HISTORIAL, self.historial)
        self._refrescar_historial()

    def _elegir_carpeta(self):
        carpeta = filedialog.askdirectory(initialdir=self.carpeta_destino.get())
        if carpeta:
            self.carpeta_destino.set(carpeta)
            guardar_json(ARCHIVO_SETTINGS, {"ultima_carpeta": carpeta})

    def _iniciar_descarga(self):
        if yt_dlp is None:
            messagebox.showerror(
                "Falta una dependencia",
                "No se encontró la librería 'yt-dlp'.\n\nInstálala con:\npip install yt-dlp",
            )
            return

        texto = self.url_text.get("1.0", "end")
        urls = [linea.strip() for linea in texto.splitlines() if linea.strip()]
        if not urls:
            messagebox.showwarning(
                "Faltan URLs", "Pega al menos una URL del video que quieres descargar (una por línea)."
            )
            return

        if self.solo_audio_var.get() and not self.ffmpeg_ok:
            messagebox.showwarning(
                "Falta FFmpeg",
                "Convertir a MP3 requiere FFmpeg instalado.\nInstálalo y vuelve a intentarlo.",
            )
            return

        guardar_json(ARCHIVO_SETTINGS, {"ultima_carpeta": self.carpeta_destino.get()})

        self.cancelar_evento.clear()
        self.boton_descargar.config(state="disabled")
        self.boton_cancelar.config(state="normal")
        self.label_estado.config(text=f"Preparando {len(urls)} video(s)...")
        self.label_titulo_descarga.config(text="Buscando información...")
        self._restablecer_miniatura()
        self.barra_progreso["value"] = 0

        hilo = threading.Thread(target=self._descargar_multiples, args=(urls,), daemon=True)
        hilo.start()

    def _cancelar_descarga(self):
        self.cancelar_evento.set()
        self.boton_cancelar.config(state="disabled")
        self.label_estado.config(text="Cancelando descarga...")

    def _restablecer_miniatura(self):
        self.imagen_miniatura_actual = None
        self.label_miniatura.configure(image="", text="🎬")

    def _mapear_calidad(self):
        calidad = self.calidad_var.get()
        if self.ffmpeg_ok:
            mapa = {
                "Mejor calidad disponible": "bestvideo+bestaudio/best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            }
        else:
            # Sin FFmpeg no se puede fusionar video+audio: se elige un solo
            # stream combinado para evitar que queden dos archivos sueltos.
            mapa = {
                "Mejor calidad disponible": "best",
                "1080p": "best[height<=1080]",
                "720p": "best[height<=720]",
                "480p": "best[height<=480]",
                "360p": "best[height<=360]",
            }
        return mapa.get(calidad, "best")

    def _obtener_info_previa(self, url):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            titulo = info.get("title", "Video")
            thumb_url = info.get("thumbnail")
            imagen_pil = None
            if thumb_url and Image is not None and ImageTk is not None:
                try:
                    peticion = urllib.request.Request(
                        thumb_url, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(peticion, timeout=10) as resp:
                        datos = resp.read()
                    imagen_pil = Image.open(BytesIO(datos)).convert("RGB")
                    imagen_pil = imagen_pil.resize((ANCHO_MINIATURA, ALTO_MINIATURA))
                except Exception:
                    imagen_pil = None
            return titulo, imagen_pil
        except Exception:
            return None, None

    def _mostrar_info_previa(self, titulo, imagen_pil):
        if titulo:
            self.label_titulo_descarga.config(text=titulo)
        if imagen_pil is not None:
            # El objeto PhotoImage de Tk debe crearse en el hilo principal.
            imagen_tk = ImageTk.PhotoImage(imagen_pil)
            self.imagen_miniatura_actual = imagen_tk
            self.label_miniatura.configure(image=imagen_tk, text="")
        else:
            self._restablecer_miniatura_widget_only()
        self.label_estado.config(text="Descargando...")

    def _restablecer_miniatura_widget_only(self):
        self.imagen_miniatura_actual = None
        self.label_miniatura.configure(image="", text="🎬")

    def _hook_progreso(self, d):
        if self.cancelar_evento.is_set():
            raise Exception("CANCELADO_POR_USUARIO")
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            descargado = d.get("downloaded_bytes", 0)
            if total:
                porcentaje = descargado / total * 100
                self.root.after(0, self._actualizar_progreso, porcentaje, d.get("_percent_str", ""))
        elif d.get("status") == "finished":
            self.root.after(0, self._actualizar_progreso, 100, "Procesando archivo final...")

    def _actualizar_progreso(self, porcentaje, texto):
        self.barra_progreso["value"] = porcentaje
        self.label_estado.config(text=f"Descargando... {texto}".strip())

    def _actualizar_estado_cola(self, idx, total):
        self.label_estado.config(text=f"Preparando video {idx} de {total}...")
        self.barra_progreso["value"] = 0

    def _descargar_multiples(self, urls):
        total = len(urls)
        exitosos = 0
        fallidos = []

        for idx, url in enumerate(urls, start=1):
            if self.cancelar_evento.is_set():
                break

            self.root.after(0, self._actualizar_estado_cola, idx, total)
            titulo_previo, imagen_previa = self._obtener_info_previa(url)
            prefijo = f"[{idx}/{total}] "
            self.root.after(
                0, self._mostrar_info_previa, prefijo + (titulo_previo or "Video"), imagen_previa
            )

            if self.cancelar_evento.is_set():
                break

            carpeta = self.carpeta_destino.get()
            os.makedirs(carpeta, exist_ok=True)

            opciones = {
                "outtmpl": os.path.join(carpeta, "%(title)s.%(ext)s"),
                "progress_hooks": [self._hook_progreso],
                "noplaylist": True,
            }

            if self.solo_audio_var.get():
                opciones.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                })
            else:
                opciones["format"] = self._mapear_calidad()
                if self.ffmpeg_ok:
                    opciones["merge_output_format"] = "mp4"

            try:
                with yt_dlp.YoutubeDL(opciones) as ydl:
                    info = ydl.extract_info(url, download=True)
                    titulo = info.get("title", titulo_previo or "Video descargado")
                self.root.after(0, self._agregar_al_historial, titulo, url, carpeta)
                exitosos += 1
            except Exception as e:
                if str(e) == "CANCELADO_POR_USUARIO" or self.cancelar_evento.is_set():
                    break
                fallidos.append((url, str(e)))

        self.root.after(
            0, self._descarga_cola_terminada, exitosos, total, fallidos, self.cancelar_evento.is_set()
        )

    def _descarga_cola_terminada(self, exitosos, total, fallidos, cancelado):
        self.boton_descargar.config(state="normal")
        self.boton_cancelar.config(state="disabled")

        if cancelado:
            self.label_estado.config(text=f"Cancelado. {exitosos} de {total} completados.")
        else:
            self.label_estado.config(text=f"Completado: {exitosos} de {total} video(s).")

        mensaje = f"Se descargaron {exitosos} de {total} video(s) correctamente."
        if fallidos:
            detalles = "\n".join(f"- {u}: {err}" for u, err in fallidos[:5])
            mensaje += f"\n\nAlgunos fallaron:\n{detalles}"

        if cancelado:
            messagebox.showinfo("Descarga cancelada", mensaje)
        elif fallidos:
            messagebox.showwarning("Descarga completada con errores", mensaje)
        else:
            messagebox.showinfo("Listo", mensaje)
        self.boton_descargar.config(state="normal")
        self.boton_cancelar.config(state="disabled")


def main():
    root = tk.Tk()
    ruta_icono = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cat_icon.ico")
    try:
        if os.path.exists(ruta_icono):
            root.iconbitmap(ruta_icono)
    except Exception:
        pass
    app = DescargadorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

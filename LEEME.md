# Descargador y Conversor

Aplicación de escritorio para **descargar vídeos** (cientos de sitios vía
`yt-dlp`) y **convertir archivos de vídeo y audio** entre formatos (vía FFmpeg).

La interfaz está hecha en **PySide6 (Qt)** con el mismo estilo que el Centro de
Control: barra lateral oscura, cabecera superior, páginas por módulo y tarjetas
con borde de color.

## Requisitos

- Windows 10/11 y Python 3.9 o superior.
- Dependencias de Python:
  ```
  pip install -r requirements.txt
  ```
- **FFmpeg** para el conversor y para bajar MP3 / fusionar vídeo+audio en
  calidades altas:
  ```
  winget install ffmpeg
  ```
  Si no está en el PATH, puedes indicar la ruta a `ffmpeg.exe` en la página
  **Configuración**.

## Ejecutar

```
python main.py
```

## Módulos

| Página | Qué hace |
|---|---|
| **Dashboard** | Contadores (descargas, conversiones, solo audio, errores), acciones rápidas, estado de FFmpeg/yt-dlp y actividad reciente. |
| **Descargar vídeos** | Pega una o varias URLs (una por línea), elige calidad o «solo audio (MP3)», carpeta destino, y descarga con miniatura y barra de progreso. |
| **Convertir archivos** | Añade uno o varios archivos, elige tipo (Vídeo/Audio) y formato de salida (MP4, MKV, WebM, AVI, MOV, GIF / MP3, M4A, WAV, FLAC, OGG) y carpeta destino. |
| **Historial** | Tabla con todas las descargas y conversiones; doble clic abre la carpeta. |
| **Configuración** | Carpetas por defecto, calidad por defecto, ruta manual de FFmpeg. |

La configuración y el historial se guardan en `%USERPROFILE%\.descargador_videos\`
(`settings.json`, `historial.json`), compatibles con la versión anterior.

## Estructura

```
main.py                     Punto de entrada (PySide6)
app/
  config.py                 Ajustes e historial persistentes
  resources/theme.qss       Tema oscuro (idéntico al de Centro de Control)
  services/
    ffmpeg.py               Localiza FFmpeg/FFprobe y lo lanza sin consola
    descargas.py            Envoltorio de yt-dlp + hilo de descarga
    conversion.py           Presets de formato + hilo de conversión FFmpeg
  widgets/                   sidebar, header, tarjeta/panel, chip, tabla, campos, iconos
  ui/                        dashboard / descargas / convertir / historial / configuración / ventana
generar_icono.py            Genera cat_icon.ico (Pillow)
descargador_videos.py       Interfaz antigua en Tkinter (se conserva de momento)
```

## Empaquetar como .exe (opcional)

```
pyinstaller --onefile --windowed --icon=cat_icon.ico --name "DescargadorYConversor" ^
  --add-data "app/resources/theme.qss;app/resources" --add-data "cat_icon.ico;." main.py
```

## Nota sobre derechos de autor

Herramienta de uso general. Descarga solo contenido sobre el que tengas
derechos (propio, de dominio público, con licencia que lo permita o con permiso
explícito del sitio). Descargar material protegido sin permiso puede infringir
los términos del sitio y la ley aplicable.

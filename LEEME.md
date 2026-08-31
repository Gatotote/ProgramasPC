# Descargador de Videos para Windows

Programa con interfaz gráfica para descargar videos de sitios web (compatible con
cientos de sitios gracias a `yt-dlp`, incluyendo YouTube, Vimeo, y muchos más).

## Requisitos

- Windows 10 u 11
- Python 3.9 o superior instalado ([python.org](https://www.python.org/downloads/))
- FFmpeg (solo necesario si vas a convertir a MP3 o unir video+audio en calidades
  altas). Puedes instalarlo con `winget install ffmpeg` desde la terminal de Windows.

## Instalación de dependencias

Abre una terminal (CMD o PowerShell) en esta carpeta y ejecuta:

```
pip install -r requirements.txt
```

## Cómo usar el programa

1. Ejecuta el programa con:
   ```
   python descargador_videos.py
   ```
2. Pega la URL del video que quieres descargar. Puedes pegar **varias URLs,
   una por línea**, y el programa las descargará una por una en orden.
3. Elige la calidad deseada, o marca "Descargar solo audio (MP3)" si solo
   quieres el audio (aplica a todas las URLs de la lista).
4. Presiona el ícono de carpeta (📁) para elegir dónde se guardará el video.
   El programa recuerda la última carpeta que usaste, así no tienes que
   elegirla cada vez.
5. Presiona "Descargar". Verás el título del video y una miniatura en la
   sección "Progreso" mientras se descarga. Si algo va mal o cambias de
   opinión, presiona "Cancelar" para detener la descarga.
6. La ventana ahora se puede redimensionar arrastrando las esquinas o
   bordes, por si quieres verla más grande.

## Evitar archivos separados de video y audio

Algunos videos se descargan como dos archivos (uno de video y otro de
audio) cuando **FFmpeg no está instalado**, porque el programa no puede
fusionarlos en uno solo. El programa ahora detecta automáticamente si
tienes FFmpeg:

- **Con FFmpeg instalado:** descarga la mejor calidad de video y audio por
  separado y los fusiona en un único archivo `.mp4`.
- **Sin FFmpeg:** verás una advertencia en la pestaña "Descargar" y el
  programa elegirá automáticamente una sola calidad combinada (puede ser
  algo menor a 1080p en algunos sitios), así siempre queda un solo archivo.

Para tener siempre la mejor calidad fusionada, instala FFmpeg con:
```
winget install ffmpeg
```
y reinicia el programa.

## Historial de descargas

El programa tiene una segunda pestaña llamada "Historial" donde se guarda
cada video que descargas, con su título, fecha y la carpeta donde quedó
guardado. Puedes:

- Hacer doble clic en un elemento (o seleccionarlo y presionar "Abrir
  carpeta") para abrir la carpeta donde se guardó ese video.
- Presionar "Borrar historial" para limpiar la lista completa.

El historial y la carpeta recordada se guardan en archivos de configuración
dentro de `%USERPROFILE%\.descargador_videos\` (historial.json y
settings.json), así que se mantienen aunque cierres y vuelvas a abrir el
programa.

## Convertirlo en un .exe (opcional)

Si quieres un archivo ejecutable independiente que no requiera tener Python
instalado, usa PyInstaller (ya incluido en requirements.txt):

```
pyinstaller --onefile --windowed --name "DescargadorDeVideos" descargador_videos.py
```

El ejecutable quedará en la carpeta `dist/DescargadorDeVideos.exe`. Puedes
copiarlo a cualquier parte de tu computadora y usarlo directamente.

## Ícono personalizado (gato)

El programa incluye `cat_icon.ico`, un ícono con un gato minimalista dibujado
para esta app. Ya está conectado: la ventana lo mostrará automáticamente al
abrir el programa (siempre que `cat_icon.ico` esté en la misma carpeta que
`descargador_videos.py`).

Si generas el `.exe` con PyInstaller, agrégalo también como ícono del
ejecutable con:

```
pyinstaller --onefile --windowed --icon=cat_icon.ico --name "DescargadorDeVideos" descargador_videos.py
```

Si quieres regenerar o modificar el ícono, usa `generar_icono.py` (dibuja el
gato con Pillow, sin depender de ninguna imagen externa).

## Nota importante sobre derechos de autor

Este programa es una herramienta general para descargar contenido. Úsalo solo
para descargar videos de los que tengas derecho a descargar (contenido propio,
de dominio público, con licencia que lo permita, o cuando el sitio lo autorice
explícitamente). Descargar contenido protegido por derechos de autor sin
permiso puede ir en contra de los términos de servicio del sitio y de la ley
aplicable en tu país.

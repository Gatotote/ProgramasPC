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
- **Deno** (motor de JavaScript) para descargar de **YouTube**: desde 2025
  YouTube exige resolver un reto en JS y `yt-dlp` lo hace con Deno.
  ```
  winget install DenoLand.Deno
  ```
  La app descarga sola el script resolvedor (`remote_components: ejs:github`).
  La cabecera muestra `JS ✓` cuando Deno (o Node) está disponible.

## Ejecutar

```
python main.py
```

En Windows también puedes hacer doble clic en **`abrir.bat`**. Para tener un
acceso directo en el Escritorio, ejecuta una vez (clic derecho → *Ejecutar con
PowerShell*):

```
crear-acceso-escritorio.ps1
```

Si mueves la carpeta del proyecto, vuelve a ejecutar ese script.

## Módulos

| Página | Qué hace |
|---|---|
| **Dashboard** | Contadores (descargas, conversiones, solo audio, errores), acciones rápidas, estado de FFmpeg/yt-dlp y actividad reciente. |
| **Descargar vídeos** | Pega una o varias URLs (una por línea), elige calidad o «solo audio (MP3)», carpeta destino, y descarga con miniatura y barra de progreso. |
| **Convertir archivos** | Añade uno o varios archivos y elige tipo: **Vídeo** (MP4, MKV, WebM, AVI, MOV, GIF), **Audio** (MP3, M4A, WAV, FLAC, OGG) o **Imagen** (JPEG, PNG, WebP, TIFF, BMP), con opción de redimensionar. Las imágenes admiten **RAW de cámara**: CR2/CR3 (Canon), NEF (Nikon), ARW (Sony), RAF (Fujifilm), RW2 (Panasonic), ORF (Olympus/OM System) y más, vía `rawpy`/LibRaw. |
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
    conversion.py           Presets de formato + hilo de conversión FFmpeg (vídeo/audio)
    imagenes.py             Conversión de imágenes y RAW de cámara (rawpy + Pillow)
  widgets/                   sidebar, header, tarjeta/panel, chip, tabla, campos, iconos
  ui/                        dashboard / descargas / convertir / historial / configuración / ventana
generar_recursos.py         Genera assets/ (emblema, logos, banner) con Pillow
assets/                     icono.ico, logo_azul|claro|oscuro.png, banner.png
DescargadorYConversor.spec  Config de PyInstaller
installer/instalador.iss    Script de Inno Setup (Windows)
installer/instalar-linux.sh Instala el .tar.gz ya compilado en el equipo del usuario (Linux)
construir_instalador.ps1    Build Windows: PyInstaller + Inno Setup → Output/…-Setup.exe
empaquetar-linux.sh         Build Linux: PyInstaller + tar.gz → Output/…-Linux.tar.gz
VERSION                     Versión de la app
generar_icono.py            (1ª versión) genera cat_icon.ico
abrir.sh / abrir.bat        Lanzadores directos (Linux / Windows), sin pasar por el instalador
```

## Recursos gráficos

El emblema (aro fino con flechas de descarga/conversión, en azul) es de la
misma familia que el de Centro de Control pero distinto. Se regenera con:

```
python generar_recursos.py
```

Produce `assets/icono.ico`, `assets/logo_azul|claro|oscuro.png` y
`assets/banner.png`. (`cat_icon.ico` y `generar_icono.py` son la marca de la
primera versión; se conservan pero ya no se usan.)

## Crear el instalador de Windows

Necesitas una vez: `pip install pyinstaller` y `winget install JRSoftware.InnoSetup`.

```
powershell -ExecutionPolicy Bypass -File construir_instalador.ps1
```

Hace dos pasos:

1. **PyInstaller** (`DescargadorYConversor.spec`) → `dist/DescargadorYConversor/`
   (la app y todo lo que necesita, sin Python).
2. **Inno Setup** (`installer/instalador.iss`) → `Output/DescargadorYConversor-<versión>-Setup.exe`
   (~58 MB).

El `Setup.exe` instala en *Archivos de programa*, crea accesos en Inicio y
(opcional) Escritorio, añade desinstalador, y ofrece casillas para instalar
**FFmpeg** y **Deno** con winget durante la instalación. La versión sale de
`VERSION` (ajústala también en `installer/instalador.iss`).

## Nota sobre derechos de autor

Herramienta de uso general. Descarga solo contenido sobre el que tengas
derechos (propio, de dominio público, con licencia que lo permita o con permiso
explícito del sitio). Descargar material protegido sin permiso puede infringir
los términos del sitio y la ley aplicable.

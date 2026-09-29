# PyInstaller — build de una carpeta (más fiable con Qt que --onefile).
#   pyinstaller DescargadorYConversor.spec --noconfirm
# Salida: dist/DescargadorYConversor/

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs

datas = [
    ("app/resources/theme.qss", "app/resources"),
    ("assets", "assets"),
    ("cat_icon.ico", "."),
    ("VERSION", "."),
]
binaries = []
hiddenimports = []

# yt-dlp carga sus extractores de forma perezosa: hay que incluirlos todos.
d, b, h = collect_all("yt_dlp")
datas += d
binaries += b
hiddenimports += h

# rawpy trae la DLL de LibRaw.
binaries += collect_dynamic_libs("rawpy")

# Módulos Qt pesados que la app no usa.
excludes = [
    "tkinter",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQml", "PySide6.QtQmlModels",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DAnimation",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets", "PySide6.QtDesigner", "PySide6.QtPdf",
    "PySide6.QtPdfWidgets", "PySide6.QtSensors", "PySide6.QtPositioning",
    "PySide6.QtBluetooth", "PySide6.QtSql", "PySide6.QtTest",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DescargadorYConversor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon="assets/icono.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DescargadorYConversor",
)

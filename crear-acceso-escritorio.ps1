# Crea un acceso directo en el Escritorio para abrir el Descargador y Conversor.
$ErrorActionPreference = "Stop"
$desktop = [Environment]::GetFolderPath("Desktop")
$carpeta = $PSScriptRoot
$destino = Join-Path $carpeta "abrir.bat"
$icono   = Join-Path $carpeta "cat_icon.ico"

$shell = New-Object -ComObject WScript.Shell
$lnk = $shell.CreateShortcut((Join-Path $desktop "Descargador y Conversor.lnk"))
$lnk.TargetPath = $destino
$lnk.WorkingDirectory = $carpeta
$lnk.WindowStyle = 7          # minimizado (la ventana real la abre Python)
$lnk.Description = "Descargar videos y convertir archivos"
if (Test-Path $icono) { $lnk.IconLocation = $icono }
$lnk.Save()

Write-Host "Acceso creado en el Escritorio: 'Descargador y Conversor'"

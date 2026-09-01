# Construye el ejecutable con PyInstaller y luego el instalador con Inno Setup.
#   powershell -ExecutionPolicy Bypass -File construir_instalador.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== 1/2  PyInstaller ==" -ForegroundColor Cyan
& py -m PyInstaller DescargadorYConversor.spec --noconfirm --clean
if (-not (Test-Path "dist\DescargadorYConversor\DescargadorYConversor.exe")) {
    throw "PyInstaller no generó el ejecutable."
}

Write-Host "== 2/2  Inno Setup ==" -ForegroundColor Cyan
$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "No se encontró ISCC.exe (Inno Setup 6)." }

& $iscc "installer\instalador.iss"

$setup = Get-ChildItem "Output\*Setup.exe" | Select-Object -Last 1
Write-Host "`nListo:" $setup.FullName -ForegroundColor Green
Write-Host ("Tamaño: {0:N1} MB" -f ($setup.Length / 1MB))

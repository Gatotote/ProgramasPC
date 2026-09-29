@echo off
setlocal
cd /d "%~dp0"
title Descargador y Conversor

where pyw >nul 2>&1
if %errorlevel%==0 (
  start "Descargador y Conversor" /d "%~dp0" pyw main.py
  exit /b 0
)
where pythonw >nul 2>&1
if %errorlevel%==0 (
  start "Descargador y Conversor" /d "%~dp0" pythonw main.py
  exit /b 0
)
where py >nul 2>&1
if %errorlevel%==0 (
  start "Descargador y Conversor" /d "%~dp0" py main.py
  exit /b 0
)
echo No se encontro Python. Instala Python y marca "py launcher".
pause

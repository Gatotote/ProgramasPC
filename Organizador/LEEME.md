# Organizador de Archivos

App de escritorio (PySide6) para separar el contenido de una carpeta en
subcarpetas por tipo: `Imágenes/`, `Vídeos/`, `Audio/`, `Documentos/`,
`Hojas de cálculo/`, `Presentaciones/`, `Comprimidos/`, `Instaladores/`,
`Código/`, `Fuentes/` y `Otros/`.

## Uso

- Abrir con el acceso del Escritorio / menú de KDE, o `./abrir.sh`.
- Elegir una carpeta (o **arrastrarla** a la ventana).
- **Simular** muestra qué haría sin tocar nada.
- **Organizar** lo aplica (pide confirmación).

## Opciones

- **Incluir subcarpetas**: recorre también lo que hay dentro de subcarpetas y
  lo saca a las carpetas de tipo en la raíz; las subcarpetas que quedan vacías
  se borran.
- **Mover / copiar**: por defecto mueve; desmárcalo para copiar.
- **Carpetas sueltas → "Carpetas"**: agrupa las subcarpetas de primer nivel.
- **Incluir archivos ocultos**: por defecto se ignoran los que empiezan por `.`.

## Notas

- Es repetible: al volver a ejecutarlo no vuelve a mover lo que ya está
  clasificado (ignora sus propias carpetas de tipo).
- Si en el destino ya hay un archivo con el mismo nombre, el nuevo se guarda
  como `nombre (2).ext`.
- Las categorías se editan en `organizador/categorias.py`.

## Desarrollo

```
uv venv --python 3.13 .venv
uv pip install --python .venv -r requirements.txt
.venv/bin/python main.py
```

El icono se edita en `assets/icono.svg` (Inkscape). `generar_icono.py` lo
rasteriza a `assets/icono.png` 256x256 (requiere `rsvg-convert` o `inkscape`,
no son dependencia de la app).

## Licencia

[MIT](LICENSE) — se puede usar, copiar, modificar y compartir libremente, siempre que se conserve la mención del autor. Este programa fue realizado por **Genaro Velasco**.

Dependencias: PySide6 (LGPL-3.0).

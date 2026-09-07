"""Genera assets/icono.png — una carpeta con tres pestañas de colores."""

from pathlib import Path

from PIL import Image, ImageDraw

TAM = 256
ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(exist_ok=True)

img = Image.new("RGBA", (TAM, TAM), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Carpeta.
cuerpo = (28, 78, 228, 208)
pestana = (28, 58, 120, 88)
d.rounded_rectangle(pestana, radius=10, fill=(70, 130, 210, 255))
d.rounded_rectangle(cuerpo, radius=16, fill=(96, 160, 235, 255))

# Tres "documentos" clasificados asomando.
colores = [(240, 196, 82, 255), (231, 111, 81, 255), (138, 201, 123, 255)]
x = 58
for c in colores:
    d.rounded_rectangle((x, 96, x + 40, 176), radius=6, fill=c)
    x += 52

img.save(ASSETS / "icono.png")
print("escrito:", ASSETS / "icono.png")

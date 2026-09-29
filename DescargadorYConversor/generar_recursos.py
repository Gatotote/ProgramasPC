"""Genera los recursos gráficos de la app con Pillow (sin imágenes externas).

Misma familia visual que Centro de Control (emblema de línea dentro de un aro
fino, fondo transparente, variantes de color) pero distinto: en vez del cristal
morado, dos flechas —descargar / convertir— sobre una bandeja, en azul.

    assets/icono.ico        icono de la ventana y del .exe (16…256 px)
    assets/logo_azul.png    emblema azul  (marca principal)
    assets/logo_claro.png   emblema gris azulado (para fondos oscuros: sidebar)
    assets/logo_oscuro.png  emblema azul muy oscuro (para fondos claros)
    assets/banner.png       1280×640 para el README / GitHub
"""

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(RAIZ, "assets")
os.makedirs(ASSETS, exist_ok=True)

S = 1024                     # lienzo de trabajo (se reduce al exportar)
GROSOR = S * 0.036           # grosor de trazo, como el aro de Centro de Control

AZUL = (47, 107, 223)
CLARO = (174, 185, 200)      # igual tono que el logo_claro de Centro de Control
OSCURO = (30, 39, 64)
FONDO_ARRIBA = (23, 30, 42)
FONDO_ABAJO = (12, 15, 22)
TEXTO = (232, 237, 245)
TEXTO_TENUE = (139, 151, 173)


def _fuente(tam, negrita=True):
    for ruta in (
        r"C:\Windows\Fonts\segoeuib.ttf" if negrita else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            continue
    return ImageFont.load_default()


def _fuente_que_quepa(texto, ancho_max, tam_inicial, negrita=True):
    tam = tam_inicial
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    while tam > 8:
        f = _fuente(tam, negrita)
        if tmp.textlength(texto, font=f) <= ancho_max:
            return f
        tam -= 2
    return _fuente(8, negrita)


def _gradiente_vertical(w, h, arriba, abajo):
    grad = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=(
            int(arriba[0] * (1 - t) + abajo[0] * t),
            int(arriba[1] * (1 - t) + abajo[1] * t),
            int(arriba[2] * (1 - t) + abajo[2] * t),
        ))
    return grad


def _flecha_trazo(d, cx, y_ini, y_fin, ancho_cabeza, color, grosor, hacia):
    """Flecha dibujada a trazo (línea + galón), no rellena. Punta en y_fin."""
    d.line([(cx, y_ini), (cx, y_fin)], fill=color, width=grosor)
    for extremo in (-1, 1):
        if hacia == "abajo":
            d.line(
                [(cx + extremo * ancho_cabeza, y_fin - ancho_cabeza), (cx, y_fin)],
                fill=color, width=grosor,
            )
        else:
            d.line(
                [(cx + extremo * ancho_cabeza, y_ini + ancho_cabeza), (cx, y_ini)],
                fill=color, width=grosor,
            )
    # remata las esquinas para simular caps redondeados
    r = grosor / 2
    for px, py in ((cx, y_ini), (cx, y_fin)):
        d.ellipse([px - r, py - r, px + r, py + r], fill=color)


def emblema(color, grosor=GROSOR):
    """Aro fino + flecha abajo + flecha arriba + bandeja, a trazo. RGBA S×S."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    g = int(round(grosor))

    # Aro exterior (como el de Centro de Control)
    m = S * 0.055
    d.ellipse([m, m, S - m, S - m], outline=color, width=g)

    # Flechas
    ancho_cab = S * 0.115
    cx_izq, cx_der = S * 0.385, S * 0.615
    y_top, y_bot = S * 0.30, S * 0.66
    _flecha_trazo(d, cx_izq, y_top, y_bot, ancho_cab, color, g, "abajo")
    _flecha_trazo(d, cx_der, y_top, y_bot, ancho_cab, color, g, "arriba")

    # Bandeja
    by = S * 0.735
    d.line([(S * 0.34, by), (S * 0.66, by)], fill=color, width=g)
    r = g / 2
    for px in (S * 0.34, S * 0.66):
        d.ellipse([px - r, by - r, px + r, by + r], fill=color)

    return img


def _exportar(img, nombre, tam):
    out = img.resize((tam, tam), Image.LANCZOS)
    out.save(os.path.join(ASSETS, nombre))
    return out


def generar_iconos():
    azul = emblema(AZUL)
    _exportar(azul, "logo_azul.png", 512)
    _exportar(emblema(CLARO), "logo_claro.png", 512)
    _exportar(emblema(OSCURO), "logo_oscuro.png", 512)
    azul.resize((512, 512), Image.LANCZOS).save(
        os.path.join(ASSETS, "icono.ico"),
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print("assets/icono.ico  +  logo_azul/claro/oscuro.png")


def generar_banner():
    w, h = 1280, 640
    banner = _gradiente_vertical(w, h, FONDO_ARRIBA, FONDO_ABAJO).convert("RGBA")

    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([120, 110, 560, 530], fill=(47, 107, 223, 70))
    banner = Image.alpha_composite(banner, glow.filter(ImageFilter.GaussianBlur(90)))

    marca = emblema(AZUL).resize((340, 340), Image.LANCZOS)
    banner.alpha_composite(marca, (150, (h - 340) // 2))

    d = ImageDraw.Draw(banner)
    x = 560
    titulo = "Descargador y Conversor"
    sub = "Descarga vídeos · convierte vídeo, audio e imágenes (RAW incluido)"
    d.text((x, h / 2 - 26), titulo,
           font=_fuente_que_quepa(titulo, w - x - 60, 74), fill=TEXTO, anchor="lm")
    d.text((x, h / 2 + 40), sub,
           font=_fuente_que_quepa(sub, w - x - 60, 30, negrita=False), fill=TEXTO_TENUE, anchor="lm")

    banner.convert("RGB").save(os.path.join(ASSETS, "banner.png"))
    print("assets/banner.png")


if __name__ == "__main__":
    generar_iconos()
    generar_banner()
    print("Listo. Recursos en:", ASSETS)

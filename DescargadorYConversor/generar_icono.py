"""
Genera un ícono .ico con un gato minimalista dibujado con PIL,
para usar como ícono de la ventana y del ejecutable del programa.
"""

from PIL import Image, ImageDraw

ESCALA = 4  # se dibuja más grande y se reduce al final (antialiasing)
TAMANO_BASE = 256
TAMANO = TAMANO_BASE * ESCALA

COLOR_PELAJE = (240, 152, 70, 255)      # naranja gato
COLOR_PELAJE_OSCURO = (214, 122, 44, 255)
COLOR_CONTORNO = (60, 35, 20, 255)
COLOR_ROSA = (255, 180, 190, 255)
FONDO_CIRCULO = (30, 33, 41, 255)       # fondo oscuro tipo "app icon"


def dibujar_gato():
    img = Image.new("RGBA", (TAMANO, TAMANO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    centro = TAMANO // 2
    radio_fondo = int(TAMANO * 0.47)
    draw.ellipse(
        [centro - radio_fondo, centro - radio_fondo, centro + radio_fondo, centro + radio_fondo],
        fill=FONDO_CIRCULO,
    )

    # Orejas (triángulos)
    ancho_oreja = TAMANO * 0.30
    alto_oreja = TAMANO * 0.28
    y_base_oreja = TAMANO * 0.34

    oreja_izq = [
        (centro - TAMANO * 0.30, y_base_oreja),
        (centro - TAMANO * 0.10, y_base_oreja - alto_oreja * 0.15),
        (centro - TAMANO * 0.06, y_base_oreja + TAMANO * 0.05),
    ]
    oreja_der = [
        (centro + TAMANO * 0.30, y_base_oreja),
        (centro + TAMANO * 0.10, y_base_oreja - alto_oreja * 0.15),
        (centro + TAMANO * 0.06, y_base_oreja + TAMANO * 0.05),
    ]
    draw.polygon(oreja_izq, fill=COLOR_PELAJE, outline=COLOR_CONTORNO)
    draw.polygon(oreja_der, fill=COLOR_PELAJE, outline=COLOR_CONTORNO)

    # Interior de orejas (rosa)
    interior_izq = [
        (centro - TAMANO * 0.245, y_base_oreja - TAMANO * 0.01),
        (centro - TAMANO * 0.135, y_base_oreja - alto_oreja * 0.10),
        (centro - TAMANO * 0.10, y_base_oreja + TAMANO * 0.035),
    ]
    interior_der = [
        (centro + TAMANO * 0.245, y_base_oreja - TAMANO * 0.01),
        (centro + TAMANO * 0.135, y_base_oreja - alto_oreja * 0.10),
        (centro + TAMANO * 0.10, y_base_oreja + TAMANO * 0.035),
    ]
    draw.polygon(interior_izq, fill=COLOR_ROSA)
    draw.polygon(interior_der, fill=COLOR_ROSA)

    # Cabeza (círculo principal)
    radio_cabeza = TAMANO * 0.28
    y_cabeza = TAMANO * 0.56
    bbox_cabeza = [
        centro - radio_cabeza, y_cabeza - radio_cabeza,
        centro + radio_cabeza, y_cabeza + radio_cabeza,
    ]
    draw.ellipse(bbox_cabeza, fill=COLOR_PELAJE, outline=COLOR_CONTORNO, width=int(TAMANO * 0.012))

    # Rayas suaves en la frente
    for dx in (-0.10, 0.0, 0.10):
        x = centro + TAMANO * dx
        draw.line(
            [(x, y_cabeza - radio_cabeza * 0.85), (x, y_cabeza - radio_cabeza * 0.35)],
            fill=COLOR_PELAJE_OSCURO, width=int(TAMANO * 0.012),
        )

    # Ojos
    radio_ojo = TAMANO * 0.028
    y_ojos = y_cabeza - TAMANO * 0.02
    for dx in (-0.115, 0.115):
        x = centro + TAMANO * dx
        draw.ellipse(
            [x - radio_ojo, y_ojos - radio_ojo * 1.3, x + radio_ojo, y_ojos + radio_ojo * 1.3],
            fill=COLOR_CONTORNO,
        )

    # Nariz (pequeño triángulo/corazón simplificado)
    y_nariz = y_cabeza + TAMANO * 0.045
    nariz = [
        (centro - TAMANO * 0.018, y_nariz),
        (centro + TAMANO * 0.018, y_nariz),
        (centro, y_nariz + TAMANO * 0.02),
    ]
    draw.polygon(nariz, fill=(200, 110, 120, 255))

    # Boca (una "w" simple)
    y_boca = y_nariz + TAMANO * 0.02
    draw.line(
        [(centro, y_boca), (centro - TAMANO * 0.035, y_boca + TAMANO * 0.03)],
        fill=COLOR_CONTORNO, width=int(TAMANO * 0.01),
    )
    draw.line(
        [(centro, y_boca), (centro + TAMANO * 0.035, y_boca + TAMANO * 0.03)],
        fill=COLOR_CONTORNO, width=int(TAMANO * 0.01),
    )

    # Bigotes
    y_bigotes = y_cabeza + TAMANO * 0.01
    for lado in (-1, 1):
        x_inicio = centro + lado * radio_cabeza * 0.55
        for offset in (-0.04, 0.0, 0.04):
            y = y_bigotes + TAMANO * offset
            x_fin = centro + lado * radio_cabeza * 1.05
            draw.line([(x_inicio, y), (x_fin, y + TAMANO * offset * 0.3)],
                      fill=COLOR_CONTORNO, width=int(TAMANO * 0.008))

    return img.resize((TAMANO_BASE, TAMANO_BASE), Image.LANCZOS)


if __name__ == "__main__":
    icono = dibujar_gato()
    icono.save("cat_icon.ico", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    icono.save("cat_icon_preview.png")
    print("Ícono generado: cat_icon.ico")

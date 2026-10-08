"""Pantalla completa del Teclado Mágico."""

import math
import random
import signal
import sys
import time
from pathlib import Path

import pygame

from . import AUTOR, PALABRA_SALIR, VERSION
from .sonido import Sonidos

REGISTRO = Path.home() / ".cache" / "tecladomagico" / "ultima-sesion.log"  # se reescribe cada vez
FUENTE_EMOJI = "/usr/share/fonts/noto/NotoColorEmoji.ttf"
TAM_EMOJI = 109  # Noto Color Emoji es de mapa de bits: solo se carga a este tamaño y luego se escala
MAX_COSAS = 14
VIDA = 4.5      # segundos que dura cada figura en pantalla
POP = 0.45      # duración del «brinco» al aparecer
CICLO_VOZ = 6   # misma letra/número seguido: la nota musical 5 veces y a la 6ª la voz

COLORES = [
    (255, 89, 94), (255, 146, 76), (255, 202, 58), (138, 201, 38), (82, 166, 117),
    (25, 130, 196), (106, 76, 147), (255, 112, 166), (0, 187, 212), (255, 255, 255),
]

LETRAS = {
    "a": ("✈️", "avión"), "b": ("🐳", "ballena"), "c": ("🐴", "caballo"), "d": ("🐬", "delfín"),
    "e": ("🐘", "elefante"), "f": ("🦭", "foca"), "g": ("🐱", "gato"), "h": ("🐜", "hormiga"),
    "i": ("🦎", "iguana"), "j": ("🦒", "jirafa"), "k": ("🐨", "koala"), "l": ("🦁", "león"),
    "m": ("🐵", "mono"), "n": ("☁️", "nube"), "ñ": ("🦬", "ñu"), "o": ("🐻", "oso"),
    "p": ("🦆", "pato"), "q": ("🧀", "queso"), "r": ("🐭", "ratón"), "s": ("🐸", "sapo"),
    "t": ("🐢", "tortuga"), "u": ("🦄", "unicornio"), "v": ("🐮", "vaca"), "w": ("🧇", "wafle"),
    "x": ("🎹", "xilófono"), "y": ("🪀", "yoyo"), "z": ("🦊", "zorro"),
}
ORDEN_LETRAS = "abcdefghijklmnñopqrstuvwxyz"
ANIMALITOS = ["🐶", "🐱", "🐰", "🐻", "🐼", "🐷", "🐸", "🐥", "🐙", "🦋", "🐞", "🐠", "🦕", "🐳", "🦉", "🐝"]
COSITAS = ["⭐", "🌈", "🎈", "🌸", "🍎", "🍌", "🚗", "🚂", "🚀", "⚽", "🌙", "☀️", "🍓", "🎁"]
FORMAS = ["circulo", "estrella", "corazon", "cuadro", "triangulo", "flor"]


def _elastico(p):
    if p >= 1:
        return 1.0
    return 1 - math.cos(p * math.pi * 2.5) * math.exp(-p * 6)


def _con_contorno(fuente, texto, color, grosor):
    base = fuente.render(texto, True, color)
    borde = fuente.render(texto, True, (255, 255, 255))
    sup = pygame.Surface((base.get_width() + grosor * 2, base.get_height() + grosor * 2), pygame.SRCALPHA)
    for ang in range(0, 360, 30):
        dx = round(math.cos(math.radians(ang)) * grosor)
        dy = round(math.sin(math.radians(ang)) * grosor)
        sup.blit(borde, (grosor + dx, grosor + dy))
    sup.blit(base, (grosor, grosor))
    return sup.subsurface(sup.get_bounding_rect()).copy()  # sin el aire de la fuente


def _carita(sup, cx, cy, r):
    ojo = max(3, r // 9)
    for lado in (-1, 1):
        pygame.draw.circle(sup, (30, 30, 40), (cx + lado * r // 3, cy - r // 6), ojo)
        pygame.draw.circle(sup, (255, 255, 255), (cx + lado * r // 3 + ojo // 3, cy - r // 6 - ojo // 3), max(1, ojo // 3))
    caja = pygame.Rect(0, 0, r, r * 2 // 3)
    caja.center = (cx, cy + r // 8)
    pygame.draw.arc(sup, (30, 30, 40), caja, math.pi * 1.15, math.pi * 1.85, max(3, r // 14))


def _poligono_estrella(cx, cy, r_ext, r_int, puntas=5):
    pts = []
    for i in range(puntas * 2):
        r = r_ext if i % 2 == 0 else r_int
        a = -math.pi / 2 + i * math.pi / puntas
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def forma(tipo, color, tam):
    """Dibuja una figura con carita al doble de tamaño y la suaviza al reducirla."""
    g = tam * 2
    s = pygame.Surface((g, g), pygame.SRCALPHA)
    c = g // 2
    r = int(g * 0.44)
    blanco = (255, 255, 255)
    if tipo == "circulo":
        pygame.draw.circle(s, blanco, (c, c), r)
        pygame.draw.circle(s, color, (c, c), r - 12)
        cara_y, cara_r = c, r
    elif tipo == "estrella":
        pygame.draw.polygon(s, blanco, _poligono_estrella(c, c + 10, r + 6, r * 0.5 + 6))
        pygame.draw.polygon(s, color, _poligono_estrella(c, c + 10, r - 8, r * 0.5 - 4))
        cara_y, cara_r = c + 18, int(r * 0.5)
    elif tipo == "corazon":
        for borde, col in ((0, blanco), (12, color)):
            rr = int(r * 0.52) - borde
            pygame.draw.circle(s, col, (c - int(r * 0.45), c - int(r * 0.2)), rr)
            pygame.draw.circle(s, col, (c + int(r * 0.45), c - int(r * 0.2)), rr)
            pygame.draw.polygon(s, col, [
                (c - r + borde * 0.6, c - int(r * 0.05)), (c + r - borde * 0.6, c - int(r * 0.05)),
                (c, c + r - borde * 1.4)])
        cara_y, cara_r = c, int(r * 0.6)
    elif tipo == "cuadro":
        caja = pygame.Rect(0, 0, r * 2 - 30, r * 2 - 30)
        caja.center = (c, c)
        pygame.draw.rect(s, blanco, caja, border_radius=r // 3)
        pygame.draw.rect(s, color, caja.inflate(-24, -24), border_radius=r // 3 - 8)
        cara_y, cara_r = c, int(r * 0.8)
    elif tipo == "triangulo":
        pts = [(c, c - r), (c + r * 0.95, c + r * 0.75), (c - r * 0.95, c + r * 0.75)]
        pygame.draw.polygon(s, blanco, pts)
        pts2 = [(c, c - r + 24), (c + r * 0.95 - 22, c + r * 0.75 - 12), (c - r * 0.95 + 22, c + r * 0.75 - 12)]
        pygame.draw.polygon(s, color, pts2)
        cara_y, cara_r = c + r // 4, int(r * 0.55)
    else:  # flor
        petalo = int(r * 0.38)
        for i in range(6):
            a = i * math.pi / 3
            px, py = c + int(math.cos(a) * r * 0.6), c + int(math.sin(a) * r * 0.6)
            pygame.draw.circle(s, blanco, (px, py), petalo)
            pygame.draw.circle(s, color, (px, py), petalo - 10)
        pygame.draw.circle(s, blanco, (c, c), int(r * 0.45))
        pygame.draw.circle(s, (255, 214, 10), (c, c), int(r * 0.45) - 10)
        cara_y, cara_r = c, int(r * 0.45)
    _carita(s, c, cara_y, cara_r)
    return pygame.transform.smoothscale(s, (tam, tam))


class Cosa:
    """Algo que aparece en pantalla: brinca al nacer, flota y se desvanece."""

    def __init__(self, sup, x, y, ahora):
        self.sup = sup
        self.x, self.y = x, y
        self.nace = ahora
        self.fase = random.uniform(0, math.tau)
        self.giro = random.uniform(-8, 8)

    def viva(self, ahora):
        return ahora - self.nace < VIDA

    def dibujar(self, pantalla, ahora):
        edad = ahora - self.nace
        escala = _elastico(min(1.0, edad / POP))
        alfa = 255
        if edad > VIDA - 1.2:
            alfa = int(255 * max(0.0, (VIDA - edad) / 1.2))
        y = self.y + math.sin(edad * 2 + self.fase) * 8 - max(0.0, edad - (VIDA - 1.2)) * 60
        if escala < 0.999 or self.giro:
            ang = math.sin(edad * 1.5 + self.fase) * self.giro
            img = pygame.transform.rotozoom(self.sup, ang, max(0.01, escala))
        else:
            img = self.sup
        img.set_alpha(alfa)
        pantalla.blit(img, img.get_rect(center=(self.x, y)))


class Juego:
    def __init__(self, ventana=False):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.ventana = ventana
        if ventana:
            self.pantalla = pygame.display.set_mode((1280, 760))
        else:
            self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.Window.from_display_module().grab_keyboard = True
            pygame.mouse.set_visible(False)
        pygame.display.set_caption(f"Teclado Mágico {VERSION}")
        pygame.key.set_repeat()  # mantener una tecla apretada no repite
        self.ancho, self.alto = self.pantalla.get_size()
        self.reloj = pygame.time.Clock()
        self.sonidos = Sonidos()

        alto_letra = int(self.alto * 0.34)
        self.f_letra = pygame.font.SysFont("comicsansms,cantarell,dejavusans", alto_letra, bold=True)
        self.f_palabra = pygame.font.SysFont("comicsansms,cantarell,dejavusans", int(self.alto * 0.07), bold=True)
        self.f_pie = pygame.font.SysFont("cantarell,dejavusans", max(14, self.alto // 60))
        try:
            self.f_emoji = pygame.font.Font(FUENTE_EMOJI, TAM_EMOJI)
        except (OSError, FileNotFoundError):
            self.f_emoji = None
        self._cache_emoji = {}

        self.cosas = []
        self.particulas = []
        self.estela = []
        self.tecleado = ""
        self.ultima_tecla, self.repeticiones = None, 0
        self.tono = random.random()
        self.pie = self._hacer_pie()

    # ---------- construcción de imágenes ----------

    def _hacer_pie(self):
        texto = f"Teclado Mágico v{VERSION}  ·  {AUTOR}  ·  para cerrar escribe «{PALABRA_SALIR}»"
        sup = self.f_pie.render(texto, True, (255, 255, 255))
        sup.set_alpha(90)
        return sup

    def emoji(self, ch, tam):
        clave = (ch, tam)
        if clave not in self._cache_emoji:
            if self.f_emoji is None:
                return forma(random.choice(FORMAS), random.choice(COLORES), tam)
            base = self.f_emoji.render(ch, True, (0, 0, 0))
            proporcion = tam / base.get_height()
            self._cache_emoji[clave] = pygame.transform.smoothscale(
                base, (int(base.get_width() * proporcion), tam))
        return self._cache_emoji[clave]

    def tarjeta_letra(self, letra):
        dibujo, palabra = LETRAS[letra]
        color = random.choice(COLORES[:-1])
        grande = _con_contorno(self.f_letra, letra.upper(), color, max(4, self.alto // 120))
        animal = self.emoji(dibujo, int(grande.get_height() * 0.8))
        texto = _con_contorno(self.f_palabra, palabra, color, 3)
        ancho = grande.get_width() + animal.get_width() + 30
        alto = max(grande.get_height(), animal.get_height()) + texto.get_height() + 12
        sup = pygame.Surface((max(ancho, texto.get_width()), alto), pygame.SRCALPHA)
        arriba = max(grande.get_height(), animal.get_height())
        x0 = (sup.get_width() - ancho) // 2
        sup.blit(grande, (x0, (arriba - grande.get_height()) // 2))
        sup.blit(animal, (x0 + grande.get_width() + 30, (arriba - animal.get_height()) // 2))
        sup.blit(texto, ((sup.get_width() - texto.get_width()) // 2, arriba + 12))
        return sup

    def tarjeta_numero(self, n):
        color = random.choice(COLORES[:-1])
        grande = _con_contorno(self.f_letra, str(n), color, max(4, self.alto // 120))
        animal = random.choice(ANIMALITOS)
        tam = int(self.alto * 0.075)
        por_fila = 5
        filas = math.ceil(n / por_fila)
        ancho_ani = min(n, por_fila) * (tam + 8)
        sup = pygame.Surface((max(grande.get_width(), ancho_ani), grande.get_height() + 16 + filas * (tam + 8)), pygame.SRCALPHA)
        sup.blit(grande, ((sup.get_width() - grande.get_width()) // 2, 0))
        img = self.emoji(animal, tam)
        for i in range(n):
            fila, col = divmod(i, por_fila)
            en_fila = min(por_fila, n - fila * por_fila)
            x0 = (sup.get_width() - en_fila * (tam + 8)) // 2
            sup.blit(img, (x0 + col * (tam + 8), grande.get_height() + 16 + fila * (tam + 8)))
        return sup

    def tarjeta_sorpresa(self):
        tam = int(self.alto * random.uniform(0.18, 0.3))
        if random.random() < 0.5:
            return forma(random.choice(FORMAS), random.choice(COLORES[:-1]), tam)
        return self.emoji(random.choice(ANIMALITOS + COSITAS), tam)

    # ---------- aparición de cosas ----------

    def _lugar(self, sup):
        margen_x = sup.get_width() // 2 + 20
        margen_y = sup.get_height() // 2 + 20
        x_min, x_max = margen_x, max(margen_x, self.ancho - margen_x)
        y_min, y_max = margen_y, max(margen_y, self.alto - margen_y - 30)
        mejor, mejor_d = None, -1
        recientes = self.cosas[-5:]
        for _ in range(10):  # entre varios lugares al azar, el más alejado de lo reciente
            x, y = random.randint(x_min, x_max), random.randint(y_min, y_max)
            d = min((math.hypot(x - c.x, y - c.y) for c in recientes), default=1e9)
            if d > mejor_d:
                mejor, mejor_d = (x, y), d
        return mejor

    def agregar(self, sup, ahora, lugar=None):
        x, y = lugar or self._lugar(sup)
        self.cosas.append(Cosa(sup, x, y, ahora))
        if len(self.cosas) > MAX_COSAS:
            self.cosas.pop(0)

    def confeti(self, x, y, ahora, cantidad=45):
        for _ in range(cantidad):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(150, 650)
            self.particulas.append([x, y, math.cos(ang) * vel, math.sin(ang) * vel - 250,
                                    random.choice(COLORES), random.randint(5, 13), ahora])
        if len(self.particulas) > 600:
            del self.particulas[:len(self.particulas) - 600]

    # ---------- eventos ----------

    def voz_o_nota(self, tecla, voz, nota, ahora):
        """Ciclo de 6 con la misma tecla seguida: 5 veces la nota musical, la 6ª la voz, y otra vez."""
        self.repeticiones = self.repeticiones + 1 if tecla == self.ultima_tecla else 1
        self.ultima_tecla = tecla
        if self.repeticiones % CICLO_VOZ != 0 or not self.sonidos.decir(voz):
            self.sonidos.tocar_nota(nota, ahora)

    def tecla(self, evento, ahora):
        ch = (evento.unicode or "").lower()
        if ch:
            self.tecleado = (self.tecleado + ch)[-len(PALABRA_SALIR):]
            if self.tecleado == PALABRA_SALIR:
                return False

        if ch in LETRAS:
            self.agregar(self.tarjeta_letra(ch), ahora)
            self.voz_o_nota(ch, ch, ORDEN_LETRAS.index(ch), ahora)
        elif ch.isdigit():
            n = int(ch) or 10
            self.agregar(self.tarjeta_numero(n), ahora)
            self.voz_o_nota(ch, str(n), n - 1, ahora)
        elif evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.confeti(random.randint(self.ancho // 4, self.ancho * 3 // 4),
                         random.randint(self.alto // 4, self.alto * 2 // 3), ahora, 90)
            if self.sonidos.ok:
                self.sonidos.tocar(self.sonidos.arpegio, ahora)
        else:
            sup = self.tarjeta_sorpresa()
            self.agregar(sup, ahora)
            if self.sonidos.ok:
                if random.random() < 0.5:
                    self.sonidos.tocar(self.sonidos.boing, ahora)
                else:
                    self.sonidos.tocar_nota(random.randrange(15), ahora)
        return True

    def _anotar(self, texto):
        """Registro de la última sesión: teclas especiales, foco de la ventana y por qué se cerró."""
        try:
            with REGISTRO.open("a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%H:%M:%S')} {texto}\n")
        except OSError:
            pass

    def correr(self):
        try:
            REGISTRO.parent.mkdir(parents=True, exist_ok=True)
            REGISTRO.write_text("")
        except OSError:
            pass
        ventana = pygame.Window.from_display_module()
        self._anotar(f"inicio v{VERSION} driver={pygame.display.get_driver()} "
                     f"teclado_apartado={ventana.keyboard_grabbed} tamaño={self.ancho}x{self.alto}")

        def senal(num, _marco):
            self._anotar(f"cerrado por señal {signal.Signals(num).name}")
            sys.exit(0)
        for num in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            signal.signal(num, senal)
        try:
            self._ciclo()
        except Exception as e:
            self._anotar(f"error: {e!r}")
            raise
        finally:
            pygame.quit()

    def _ciclo(self):
        while True:
            ahora = time.monotonic()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    # Alt+F4 y la «X» no cierran en pantalla completa: solo escribir «salir».
                    self._anotar("pidieron cerrar la ventana (QUIT)" + (", cerrando" if self.ventana else ", ignorado"))
                    if self.ventana:
                        return
                elif ev.type == pygame.KEYDOWN:
                    self._anotar(f"tecla {pygame.key.name(ev.key)!r} {ev.unicode!r} scancode={ev.scancode} mod={ev.mod:#x}")
                    if not self.tecla(ev, ahora):
                        self._anotar("cerrado: escribieron «salir»")
                        return
                elif ev.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWFOCUSGAINED, pygame.WINDOWMINIMIZED,
                                 pygame.WINDOWRESTORED, pygame.WINDOWHIDDEN, pygame.WINDOWSHOWN):
                    self._anotar(f"ventana: {pygame.event.event_name(ev.type)}")
                    if ev.type == pygame.WINDOWFOCUSGAINED and not self.ventana:
                        # El bloqueo solo se activa con la ventana enfocada: pedirlo cada vez que regresa el foco.
                        win = pygame.Window.from_display_module()
                        win.grab_keyboard = True
                        self._anotar(f"teclado apartado: {win.keyboard_grabbed}")
                elif ev.type == pygame.MOUSEMOTION:
                    color = pygame.Color(0)
                    color.hsva = ((ahora * 120) % 360, 70, 100, 100)
                    self.estela.append((ev.pos[0], ev.pos[1], ahora, color))
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 2, 3):
                    self.confeti(ev.pos[0], ev.pos[1], ahora, 35)
                    self.sonidos.tocar_nota(random.randrange(15), ahora)
            self._dibujar(ahora)
            self.reloj.tick(60)

    # ---------- dibujo ----------

    def _dibujar(self, ahora):
        self.tono = (self.tono + 0.0004) % 1
        fondo = pygame.Color(0)
        fondo.hsva = (self.tono * 360, 55, 22, 100)
        self.pantalla.fill(fondo)

        self.estela = [p for p in self.estela if ahora - p[2] < 0.8]
        for x, y, t, col in self.estela:
            vida = 1 - (ahora - t) / 0.8
            pygame.draw.circle(self.pantalla, col, (x, y), max(1, int(26 * vida)))

        self.cosas = [c for c in self.cosas if c.viva(ahora)]
        for c in self.cosas:
            c.dibujar(self.pantalla, ahora)

        dt = min(0.05, self.reloj.get_time() / 1000)
        vivas = []
        for p in self.particulas:
            edad = ahora - p[6]
            if edad > 2.2 or p[1] > self.alto + 20:
                continue
            p[2] *= 0.985
            p[3] += 700 * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            r = max(1, int(p[5] * (1 - edad / 2.2)))
            pygame.draw.circle(self.pantalla, p[4], (int(p[0]), int(p[1])), r)
            vivas.append(p)
        self.particulas = vivas

        self.pantalla.blit(self.pie, (14, self.alto - self.pie.get_height() - 8))
        pygame.display.flip()

"""Proceso aparte que estresa la parte GRÁFICA de la GPU (renderizado 3D con OpenGL).

Dibuja sin ventana (EGL, directo sobre la tarjeta elegida) una escena que carga a la vez:
  - sombreado: trazado por pasos (raymarching) de una escena con sombras suaves;
  - geometría/rasterización: 100 000 cubos animados con iluminación;
  - memoria de video: un arreglo de texturas grande muestreado en toda la escena.

Verificación: cada `--verificar` segundos dibuja una IMAGEN DE CONTROL (mismos datos, mismo
instante) y la compara píxel por píxel con la primera. Una GPU sana la dibuja idéntica; un
píxel distinto es un artefacto (error de cálculo o de VRAM).

Salida: una línea JSON por evento en stdout (igual que los otros trabajadores).
"""

import argparse
import json
import os
import signal
import sys
import time

os.environ.setdefault("EGL_LOG_LEVEL", "fatal")  # silencia avisos de Mesa de otras GPUs

import numpy as np

VERT_PANTALLA = """
#version 330
in vec2 pos;
out vec2 uv;
void main() { uv = pos * 0.5 + 0.5; gl_Position = vec4(pos, 0.0, 1.0); }
"""

FRAG_ESCENA = """
#version 330
uniform float t;
uniform vec2 res;
uniform sampler2DArray tex;
uniform int capas;
in vec2 uv;
out vec4 color;

mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float caja(vec3 p, vec3 b) { vec3 q = abs(p) - b; return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0); }

float escena(vec3 p) {
    vec3 q = p;
    q.xz *= rot(0.15 * t);
    vec3 c = mod(q + 2.0, 4.0) - 2.0;              // repetición infinita
    c.xy *= rot(q.z * 0.3 + t * 0.2);              // torsión
    float d = caja(c, vec3(0.7, 0.35, 0.7)) - 0.08;
    d = max(d, -(length(c) - 0.85));               // hueco esférico
    d = min(d, length(c - vec3(0.0, 0.9 + 0.3 * sin(t + q.x), 0.0)) - 0.35);
    return min(d, p.y + 1.8);                      // piso
}
vec3 normal(vec3 p) {
    vec2 e = vec2(0.0015, 0.0);
    return normalize(vec3(escena(p + e.xyy) - escena(p - e.xyy),
                          escena(p + e.yxy) - escena(p - e.yxy),
                          escena(p + e.yyx) - escena(p - e.yyx)));
}
float sombra(vec3 ro, vec3 rd) {
    float r = 1.0, h, s = 0.03;
    for (int i = 0; i < 40; i++) {
        h = escena(ro + rd * s);
        r = min(r, 10.0 * h / s);
        s += clamp(h, 0.02, 0.4);
        if (h < 0.001 || s > 12.0) break;
    }
    return clamp(r, 0.0, 1.0);
}
vec3 textura(vec3 p, vec3 n) {                      // triplanar sobre el arreglo de texturas
    int capa = int(mod(floor(p.x * 0.25) + floor(p.z * 0.25) * 7.0, float(capas)));
    vec3 w = abs(n) / (abs(n.x) + abs(n.y) + abs(n.z));
    return texture(tex, vec3(p.yz * 0.37, capa)).rgb * w.x +
           texture(tex, vec3(p.xz * 0.37, capa)).rgb * w.y +
           texture(tex, vec3(p.xy * 0.37, capa)).rgb * w.z;
}
void main() {
    vec2 p = (uv * res - 0.5 * res) / res.y;
    vec3 ro = vec3(3.0 * sin(0.1 * t), 1.2, t * 1.5);
    vec3 rd = normalize(vec3(p, 1.4));
    rd.yz *= rot(0.25);
    float s = 0.0, h;
    int i;
    for (i = 0; i < 128; i++) {
        h = escena(ro + rd * s);
        if (h < 0.0008 || s > 40.0) break;
        s += h;
    }
    vec3 col = vec3(0.04, 0.06, 0.12);
    if (s < 40.0) {
        vec3 pos = ro + rd * s, n = normal(pos);
        vec3 luz = normalize(vec3(0.6, 0.8, -0.4));
        float dif = max(dot(n, luz), 0.0) * sombra(pos + n * 0.01, luz);
        float ao = 0.0;
        for (int k = 1; k <= 5; k++) ao += (0.12 * float(k) - escena(pos + n * 0.12 * float(k)));
        col = textura(pos, n) * (0.15 + 0.85 * dif) * (1.0 - clamp(ao * 1.5, 0.0, 0.8));
        col += vec3(0.0, 0.5, 1.0) * pow(max(dot(reflect(rd, n), luz), 0.0), 32.0);
        col = mix(col, vec3(0.04, 0.06, 0.12), 1.0 - exp(-0.004 * s * s));
    }
    color = vec4(pow(col, vec3(0.4545)), 1.0);
}
"""

VERT_CUBOS = """
#version 330
uniform float t;
uniform mat4 proy;
in vec3 v; in vec3 nv;
out vec3 n; out vec3 base; flat out int capa;
void main() {
    int id = gl_InstanceID;
    float x = float(id % 400) - 200.0, z = float(id / 400) - 125.0;
    float y = 0.6 * sin(0.15 * x + t) * cos(0.13 * z - 0.7 * t);
    float a = 0.5 * t + float(id) * 0.01;
    mat3 r = mat3(cos(a), 0.0, sin(a), 0.0, 1.0, 0.0, -sin(a), 0.0, cos(a));
    vec3 p = r * (v * 0.3) + vec3(x * 0.8, y - 2.5, z * 0.8 + 90.0);
    n = r * nv;
    base = vec3(0.5 + 0.5 * sin(x * 0.1), 0.5 + 0.5 * sin(z * 0.1 + 2.0), 0.9);
    capa = id % 16;
    gl_Position = proy * vec4(p, 1.0);
}
"""
FRAG_CUBOS = """
#version 330
uniform sampler2DArray tex;
uniform int capas;
in vec3 n; in vec3 base; flat in int capa;
out vec4 color;
void main() {
    vec3 luz = normalize(vec3(0.3, 1.0, -0.5));
    vec3 tx = texture(tex, vec3(gl_FragCoord.xy / 512.0, capa % capas)).rgb;
    color = vec4(base * tx * (0.25 + 0.75 * max(dot(normalize(n), luz), 0.0)), 1.0);
}
"""


def emitir(**datos):
    print(json.dumps(datos), flush=True)


def perspectiva(fov, aspecto, cerca, lejos):
    f = 1.0 / np.tan(np.radians(fov) / 2)
    m = np.zeros((4, 4), dtype="f4")
    m[0, 0], m[1, 1] = f / aspecto, f
    m[2, 2], m[2, 3] = (lejos + cerca) / (cerca - lejos), 2 * lejos * cerca / (cerca - lejos)
    m[3, 2] = -1.0
    return m.T  # OpenGL espera columnas


def cubo():
    caras = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, 1, 0), (0, 0, -1)),
             ((0, 1, 0), (0, 0, 1), (1, 0, 0)), ((0, -1, 0), (0, 0, -1), (1, 0, 0)),
             ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (-1, 0, 0), (0, 1, 0))]
    datos = []
    for n, u, w in caras:
        n, u, w = map(np.array, (n, u, w))
        esq = [n - u - w, n + u - w, n + u + w, n - u - w, n + u + w, n - u + w]
        for e in esq:
            datos += list(e) + list(n)
    return np.array(datos, dtype="f4")


def elegir(nombre):
    import moderngl
    for i in range(8):
        try:
            ctx = moderngl.create_context(standalone=True, backend="egl", device_index=i, require=330)
        except Exception:
            continue
        r = ctx.info["GL_RENDERER"]
        if (nombre and nombre.lower() in r.lower()) or (not nombre and "llvmpipe" not in r):
            return ctx
        ctx.release()
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dispositivo", default="NVIDIA", help="parte del nombre de la GPU")
    ap.add_argument("--ancho", type=int, default=3840)
    ap.add_argument("--alto", type=int, default=2160)
    ap.add_argument("--vram-mb", type=int, default=1024, help="memoria para texturas")
    ap.add_argument("--verificar", type=float, default=4.0, help="segundos entre imágenes de control")
    ap.add_argument("--guardar", default="", help="guardar la imagen de control en este PNG")
    ap.add_argument("--escena", default="", help="dibujar esta escena .glb en vez de la procedural")
    ap.add_argument("--hdri", default="", help="HDRI .npy (float16) para fondo y luz de la escena")
    ap.add_argument("--max-textura", type=int, default=1024)
    ap.add_argument("--muestras", type=int, default=4, help="antialiasing MSAA de la escena")
    ap.add_argument("--camara", choices=["dentro", "fuera"], default="dentro",
                    help="dentro: recorrer un escenario; fuera: girar alrededor de un objeto")
    ap.add_argument("--exposicion", type=float, default=1.0)
    ap.add_argument("--ruta", default="", help="puntos de la cámara «x,y,z;x,y,z;…» en metros")
    args = ap.parse_args()

    parar = False

    def al_senal(*_):
        nonlocal parar
        parar = True

    signal.signal(signal.SIGINT, al_senal)
    signal.signal(signal.SIGTERM, al_senal)

    ctx = elegir(args.dispositivo)
    if ctx is None:
        emitir(tipo="error", mensaje=f"No se encontró una GPU «{args.dispositivo}» con OpenGL (EGL)")
        return 1
    W, H = args.ancho, args.alto
    if args.escena:
        return con_escena(ctx, args, W, H, lambda: parar)
    try:
        # Texturas deterministas (misma semilla siempre): 1024×1024 RGBA8 = 4 MB por capa.
        capas = max(4, min(args.vram_mb // 4, 1024))
        # Una capa aleatoria (semilla fija) y las demás derivadas de ella con desplazamientos:
        # igual de determinista, pero arranca en décimas de segundo en vez de segundos.
        base = np.random.default_rng(12345).integers(40, 255, (1024, 1024, 4), dtype=np.uint8)
        tex = ctx.texture_array((1024, 1024, capas), 4)
        for c in range(capas):
            capa = np.roll(base, (c * 37, c * 91), axis=(0, 1))
            tex.write(capa.tobytes(), viewport=(0, 0, c, 1024, 1024, 1))
        tex.build_mipmaps()
        tex.use(0)

        fbo = ctx.framebuffer(ctx.renderbuffer((W, H), 4), ctx.depth_renderbuffer((W, H)))
        fbo.use()
        pantalla = ctx.program(vertex_shader=VERT_PANTALLA, fragment_shader=FRAG_ESCENA)
        pantalla["res"].value = (W, H)
        pantalla["tex"].value = 0
        pantalla["capas"].value = capas
        vao_pantalla = ctx.vertex_array(pantalla, ctx.buffer(
            np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")), "pos")
        cubos = ctx.program(vertex_shader=VERT_CUBOS, fragment_shader=FRAG_CUBOS)
        cubos["proy"].write(perspectiva(60, W / H, 0.1, 300).tobytes())
        cubos["tex"].value = 0
        cubos["capas"].value = capas
        vao_cubos = ctx.vertex_array(cubos, [(ctx.buffer(cubo()), "3f 3f", "v", "nv")])
    except Exception as e:
        emitir(tipo="error", mensaje=f"No se pudo preparar la escena: {e}")
        return 1

    def dibujar(t):
        fbo.use()
        fbo.clear(0.0, 0.0, 0.0, 1.0, depth=1.0)
        # 1) Escena por trazado de pasos (pinta todos los píxeles; sin prueba de profundidad).
        ctx.disable(ctx.DEPTH_TEST)
        pantalla["t"].value = t
        vao_pantalla.render(mode=ctx.TRIANGLE_STRIP)
        # 2) 100 000 cubos encima, con prueba de profundidad.
        ctx.enable(ctx.DEPTH_TEST)
        cubos["t"].value = t
        vao_cubos.render(instances=100_000)

    def imagen_control():
        dibujar(7.25)  # instante fijo: la imagen debe salir idéntica siempre
        return np.frombuffer(fbo.read(components=4), dtype=np.uint8)

    referencia = imagen_control()
    if args.guardar:
        from PySide6.QtGui import QImage
        QImage(referencia.tobytes(), W, H, QImage.Format_RGBA8888).mirrored().save(args.guardar)
    emitir(tipo="inicio", dispositivo=ctx.info["GL_RENDERER"], resolucion=f"{W}x{H}",
           vram_texturas_mb=capas * 4, capas=capas)

    errores = 0
    cuadros, t0 = 0, time.monotonic()
    t_reporte = t_control = t0
    while not parar:
        dibujar(time.monotonic() - t0)
        ctx.finish()
        cuadros += 1
        ahora = time.monotonic()
        if ahora - t_control >= args.verificar:
            img = imagen_control()
            distintos = int(np.count_nonzero((img != referencia).reshape(-1, 4).any(axis=1)))
            if distintos:
                errores += 1
                emitir(tipo="aviso", mensaje=f"Imagen de control con {distintos} píxel(es) distintos")
            t_control = time.monotonic()
        if ahora - t_reporte >= 1.0:
            emitir(tipo="progreso", fps=round(cuadros / (ahora - t_reporte), 1), errores=errores)
            cuadros, t_reporte = 0, ahora

    emitir(tipo="fin", errores=errores)
    return 0


def con_escena(ctx, args, W, H, hay_que_parar):
    from .escena3d import Escena, RenderEscena
    t_carga = time.monotonic()
    try:
        escena = Escena(args.escena, args.max_textura)
        if args.hdri:
            hdri = np.load(args.hdri)
        else:  # sin HDRI: cielo gris azulado uniforme
            hdri = np.full((64, 128, 3), 0.6, dtype=np.float16) * np.array([0.7, 0.8, 1.0], dtype=np.float16)
        r = RenderEscena(ctx, escena, hdri, W, H, muestras=args.muestras, camara=args.camara,
                         exposicion=args.exposicion,
                         ruta=[tuple(map(float, p.split(","))) for p in args.ruta.split(";") if p.strip()])
    except Exception as e:
        emitir(tipo="error", mensaje=f"No se pudo cargar la escena: {e}")
        return 1

    def imagen_control():
        r.dibujar(7.25)
        return r.leer()

    referencia = imagen_control()
    if args.guardar:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QImage
        QImage(referencia.tobytes(), W, H, QImage.Format_RGBA8888).flipped(Qt.Vertical).save(args.guardar)
    emitir(tipo="inicio", dispositivo=ctx.info["GL_RENDERER"], resolucion=f"{W}x{H}",
           escena=os.path.basename(args.escena), triangulos=escena.triangulos,
           materiales=len(r.vaos), vram_texturas_mb=r.vram_texturas >> 20,
           carga_s=round(time.monotonic() - t_carga, 1))
    errores, cuadros, t0 = 0, 0, time.monotonic()
    t_reporte = t_control = t0
    while not hay_que_parar():
        r.dibujar(time.monotonic() - t0)
        cuadros += 1
        # Como los juegos: se dejan hasta 3 cuadros en cola para que la GPU nunca espere a Python
        # (esperar cada cuadro dejaba la GPU al 8 % con Bistro).
        if cuadros % 3 == 0:
            ctx.finish()
        ahora = time.monotonic()
        if ahora - t_control >= args.verificar:
            img = imagen_control()
            distintos = int(np.count_nonzero((img != referencia).reshape(-1, 4).any(axis=1)))
            if distintos:
                errores += 1
                emitir(tipo="aviso", mensaje=f"Imagen de control con {distintos} píxel(es) distintos")
            t_control = time.monotonic()
        if ahora - t_reporte >= 1.0:
            emitir(tipo="progreso", fps=round(cuadros / (ahora - t_reporte), 1), errores=errores)
            cuadros, t_reporte = 0, ahora
    emitir(tipo="fin", errores=errores)
    return 0


if __name__ == "__main__":
    sys.exit(main())

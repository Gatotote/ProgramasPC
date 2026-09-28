"""Render de escenas glTF (.glb) para la prueba de render 3D: carga la escena, la agrupa por
material y la dibuja como un juego moderno, en dos pasadas por cuadro:

  1. sombras: toda la escena vista desde el sol, en un mapa de profundidad de 4096×4096;
  2. cámara: 4K con antialiasing 4× (MSAA), texturas con transparencia recortada, sombras
     suavizadas, luz del sol y luz ambiental/reflejos tomados de un HDRI (que también es el fondo).

La cámara recorre la escena en círculo. `imagen_control()` dibuja siempre la misma toma
(instante fijo) para compararla píxel por píxel.
"""

import json
import math
import struct

import numpy as np

TIPOS = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
COMPONENTES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


# ------------------------------------------------------------------ matemáticas
def _trs(nodo):
    if "matrix" in nodo:
        return np.array(nodo["matrix"], dtype=np.float64).reshape(4, 4).T
    t = nodo.get("translation", [0, 0, 0])
    x, y, z, w = nodo.get("rotation", [0, 0, 0, 1])
    s = nodo.get("scale", [1, 1, 1])
    r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    m = np.eye(4)
    m[:3, :3] = r * np.array(s)
    m[:3, 3] = t
    return m


def perspectiva(fov, aspecto, cerca, lejos):
    f = 1 / math.tan(math.radians(fov) / 2)
    return np.array([[f / aspecto, 0, 0, 0], [0, f, 0, 0],
                     [0, 0, (lejos + cerca) / (cerca - lejos), 2 * lejos * cerca / (cerca - lejos)],
                     [0, 0, -1, 0]], dtype=np.float64)


def ortografica(l, r, b, t, n, f):
    return np.array([[2 / (r - l), 0, 0, -(r + l) / (r - l)], [0, 2 / (t - b), 0, -(t + b) / (t - b)],
                     [0, 0, -2 / (f - n), -(f + n) / (f - n)], [0, 0, 0, 1]], dtype=np.float64)


def mirar(ojo, objetivo, arriba=(0, 1, 0)):
    ojo, objetivo, arriba = map(lambda v: np.array(v, dtype=np.float64), (ojo, objetivo, arriba))
    f = objetivo - ojo
    f /= np.linalg.norm(f)
    s = np.cross(f, arriba)
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[:3, 3] = -m[:3, :3] @ ojo
    return m


def gl(m):
    """Matriz numpy (filas) → bytes para un uniform mat4 de OpenGL (columnas)."""
    return np.ascontiguousarray(m.T, dtype="f4").tobytes()


# ------------------------------------------------------------------ carga del .glb
class Escena:
    """Geometría ya transformada al mundo y agrupada por material."""

    def __init__(self, ruta, max_textura=1024):
        with open(ruta, "rb") as f:
            magia, _ver, _total = struct.unpack("<4sII", f.read(12))
            if magia != b"glTF":
                raise ValueError("no es un archivo .glb")
            lon, _ = struct.unpack("<II", f.read(8))
            self.js = json.loads(f.read(lon))
            lon, _ = struct.unpack("<II", f.read(8))
            self.bin = f.read(lon)
        self.max_textura = max_textura
        grupos = {}  # material → [pos, nor, uv, índices]
        escena = self.js.get("scenes", [{}])[self.js.get("scene", 0)]
        pila = [(n, np.eye(4)) for n in escena.get("nodes", range(len(self.js.get("nodes", []))))]
        while pila:
            i, padre = pila.pop()
            nodo = self.js["nodes"][i]
            m = padre @ _trs(nodo)
            if "mesh" in nodo:
                self._agregar_malla(self.js["meshes"][nodo["mesh"]], m, grupos)
            pila += [(h, m) for h in nodo.get("children", [])]
        self.grupos = []
        minimo, maximo = np.full(3, np.inf), np.full(3, -np.inf)
        for mat, (pos, nor, uv, idx) in grupos.items():
            p = np.concatenate(pos)
            minimo, maximo = np.minimum(minimo, p.min(0)), np.maximum(maximo, p.max(0))
            vert = np.hstack([p, np.concatenate(nor), np.concatenate(uv)]).astype("f4")
            self.grupos.append((mat, vert, np.concatenate(idx).astype("u4")))
        self.minimo, self.maximo = minimo, maximo
        self.triangulos = sum(len(i) // 3 for _m, _v, i in self.grupos)

    def _datos(self, n):
        a = self.js["accessors"][n]
        vista = self.js["bufferViews"][a["bufferView"]]
        tipo, comp = TIPOS[a["componentType"]], COMPONENTES[a["type"]]
        inicio = vista.get("byteOffset", 0) + a.get("byteOffset", 0)
        paso = vista.get("byteStride", 0)
        tam = np.dtype(tipo).itemsize * comp
        if paso and paso != tam:
            crudo = np.frombuffer(self.bin, np.uint8, count=paso * (a["count"] - 1) + tam, offset=inicio)
            filas = np.lib.stride_tricks.as_strided(crudo, (a["count"], tam), (paso, 1))
            datos = np.ascontiguousarray(filas).view(tipo).reshape(a["count"], comp)
        else:
            datos = np.frombuffer(self.bin, tipo, count=a["count"] * comp, offset=inicio).reshape(a["count"], comp)
        if a.get("normalized") and tipo != np.float32:
            datos = datos.astype(np.float32) / np.iinfo(tipo).max
        return datos.astype(np.float32) if tipo == np.float32 or comp > 1 else datos

    def _agregar_malla(self, malla, m, grupos):
        normal_m = np.linalg.inv(m[:3, :3]).T
        for prim in malla["primitives"]:
            if prim.get("mode", 4) != 4 or "POSITION" not in prim["attributes"]:
                continue  # solo triángulos
            at = prim["attributes"]
            p = self._datos(at["POSITION"]).astype(np.float64)
            p = p @ m[:3, :3].T + m[:3, 3]
            n = self._datos(at["NORMAL"]).astype(np.float64) @ normal_m.T if "NORMAL" in at else np.tile([0, 1, 0], (len(p), 1))
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-8)
            uv = self._datos(at["TEXCOORD_0"]) if "TEXCOORD_0" in at else np.zeros((len(p), 2), np.float32)
            idx = self._datos(prim["indices"]).reshape(-1).astype(np.int64) if "indices" in prim else np.arange(len(p))
            g = grupos.setdefault(prim.get("material", -1), [[], [], [], []])
            base = sum(len(x) for x in g[0])
            g[0].append(p.astype("f4"))
            g[1].append(n.astype("f4"))
            g[2].append(uv.astype("f4"))
            g[3].append(idx + base)

    def imagen(self, n):
        """RGBA8 de la imagen n del glb (decodificada con Qt), reducida a max_textura."""
        from PySide6.QtCore import QByteArray, Qt
        from PySide6.QtGui import QImage
        im = self.js["images"][n]
        vista = self.js["bufferViews"][im["bufferView"]]
        ini = vista.get("byteOffset", 0)
        q = QImage.fromData(QByteArray(self.bin[ini:ini + vista["byteLength"]]))
        if q.isNull():
            return None
        if max(q.width(), q.height()) > self.max_textura:
            q = q.scaled(self.max_textura, self.max_textura, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        q = q.convertToFormat(QImage.Format_RGBA8888)
        return q.width(), q.height(), bytes(q.constBits())[:q.width() * q.height() * 4]


# ------------------------------------------------------------------ shaders
VERT = """
#version 330
uniform mat4 vp; uniform mat4 luz_vp;
in vec3 pos; in vec3 nor; in vec2 uv;
out vec3 v_pos; out vec3 v_nor; out vec2 v_uv; out vec4 v_luz;
void main() {
    v_pos = pos; v_nor = nor; v_uv = uv;
    v_luz = luz_vp * vec4(pos, 1.0);
    gl_Position = vp * vec4(pos, 1.0);
}
"""
FRAG = """
#version 330
uniform sampler2D color_tex; uniform int con_textura; uniform vec4 factor;
uniform sampler2DShadow sombra; uniform sampler2D cielo;
uniform vec3 sol; uniform vec3 camara; uniform float exposicion;
in vec3 v_pos; in vec3 v_nor; in vec2 v_uv; in vec4 v_luz;
out vec4 salida;
const float PI = 3.14159265;
vec2 equirect(vec3 d) { return vec2(0.5 + atan(d.z, d.x) / (2.0 * PI), 0.5 + asin(clamp(d.y, -1.0, 1.0)) / PI); }
void main() {
    vec4 base = factor * (con_textura == 1 ? texture(color_tex, v_uv) : vec4(1.0));
    if (base.a < 0.5) discard;                      // hojas, rejas, letreros recortados
    vec3 n = normalize(v_nor);
    if (!gl_FrontFacing) n = -n;
    vec3 v = normalize(camara - v_pos);
    vec3 l = normalize(sol);
    // sombra suavizada (PCF 5×5 sobre el mapa de 4096)
    vec3 p = v_luz.xyz / v_luz.w * 0.5 + 0.5;
    float s = 0.0;
    for (int x = -2; x <= 2; x++) for (int y = -2; y <= 2; y++)
        s += texture(sombra, vec3(p.xy + vec2(x, y) / 4096.0, p.z - 0.0015));
    s /= 25.0;
    float dif = max(dot(n, l), 0.0) * s;
    vec3 amb = textureLod(cielo, equirect(n), 7.0).rgb;             // luz ambiental del HDRI
    vec3 r = reflect(-v, n);
    vec3 refl = textureLod(cielo, equirect(r), 3.0).rgb;            // reflejo borroso del HDRI
    float fres = 0.04 + 0.96 * pow(1.0 - max(dot(n, v), 0.0), 5.0);
    vec3 c = base.rgb * (amb + dif * vec3(3.0, 2.85, 2.6)) + refl * fres * 0.5;
    c *= exposicion;
    c = (c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14);   // tono tipo cine (ACES)
    salida = vec4(pow(clamp(c, 0.0, 1.0), vec3(1.0 / 2.2)), 1.0);
}
"""
VERT_SOMBRA = """
#version 330
uniform mat4 luz_vp;
in vec3 pos; in vec2 uv;
out vec2 v_uv;
void main() { v_uv = uv; gl_Position = luz_vp * vec4(pos, 1.0); }
"""
FRAG_SOMBRA = """
#version 330
uniform sampler2D color_tex; uniform int con_textura;
in vec2 v_uv;
void main() { if (con_textura == 1 && texture(color_tex, v_uv).a < 0.5) discard; }
"""
VERT_CIELO = """
#version 330
in vec2 pos; out vec2 v;
void main() { v = pos; gl_Position = vec4(pos, 0.9999, 1.0); }
"""
FRAG_CIELO = """
#version 330
uniform mat4 inv_vp; uniform vec3 camara; uniform sampler2D cielo; uniform float exposicion;
in vec2 v; out vec4 salida;
const float PI = 3.14159265;
void main() {
    vec4 w = inv_vp * vec4(v, 1.0, 1.0);
    vec3 d = normalize(w.xyz / w.w - camara);
    // textureLod 0: con mipmaps automáticos se ve una línea en la costura (u = 0/1) del panorama
    vec3 c = textureLod(cielo, vec2(0.5 + atan(d.z, d.x) / (2.0 * PI), 0.5 + asin(clamp(d.y, -1.0, 1.0)) / PI), 0.0).rgb;
    c *= exposicion;
    c = (c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14);
    salida = vec4(pow(clamp(c, 0.0, 1.0), vec3(1.0 / 2.2)), 1.0);
}
"""


class RenderEscena:
    def __init__(self, ctx, escena, hdri, ancho, alto, muestras=4, sombra_px=4096, camara="dentro",
                 exposicion=1.0, ruta=None):
        self.ctx, self.e, self.W, self.H = ctx, escena, ancho, alto
        self.modo_camara, self.exposicion = camara, exposicion
        # ruta: puntos (x, y, z) en metros; la cámara camina por ellos (ida y vuelta) mirando adelante.
        self.ruta = [np.array(p, dtype=np.float64) for p in (ruta or [])]
        self.prog = ctx.program(vertex_shader=VERT, fragment_shader=FRAG)
        self.prog_sombra = ctx.program(vertex_shader=VERT_SOMBRA, fragment_shader=FRAG_SOMBRA)
        self.prog_cielo = ctx.program(vertex_shader=VERT_CIELO, fragment_shader=FRAG_CIELO)

        # Texturas de color por material (con mipmaps y filtrado anisotrópico).
        self.materiales = {}
        vistas = {}
        for m_idx, js in enumerate(escena.js.get("materials", [])):
            pbr = js.get("pbrMetallicRoughness", {})
            tex = None
            if "baseColorTexture" in pbr:
                img = escena.js["textures"][pbr["baseColorTexture"]["index"]].get("source")
                if img is not None and img not in vistas:
                    d = escena.imagen(img)
                    vistas[img] = None
                    if d:
                        t = ctx.texture((d[0], d[1]), 4, d[2])
                        t.build_mipmaps()
                        t.anisotropy = 8.0
                        vistas[img] = t
                tex = vistas.get(img)
            self.materiales[m_idx] = (tex, tuple(pbr.get("baseColorFactor", [1, 1, 1, 1])))
        self.vram_texturas = sum(t.width * t.height * 4 * 4 // 3 for t in vistas.values() if t)

        self.vaos = []
        for mat, vert, idx in escena.grupos:
            vbo, ibo = ctx.buffer(vert.tobytes()), ctx.buffer(idx.tobytes())
            vao = ctx.vertex_array(self.prog, [(vbo, "3f 3f 2f", "pos", "nor", "uv")], ibo)
            vao_s = ctx.vertex_array(self.prog_sombra, [(vbo, "3f 12x 2f", "pos", "uv")], ibo)
            self.vaos.append((mat, vao, vao_s))

        # HDRI: fondo y luz ambiental.
        h, w = hdri.shape[:2]
        self.cielo = ctx.texture((w, h), 3, np.ascontiguousarray(hdri, dtype="f2").tobytes(), dtype="f2")
        self.cielo.build_mipmaps()
        self.cielo.repeat_y = False
        self.vao_cielo = ctx.vertex_array(self.prog_cielo, ctx.buffer(
            np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4")), "pos")

        # Mapa de sombras y búferes de dibujo.
        self.sombra = ctx.depth_texture((sombra_px, sombra_px))
        self.sombra.compare_func = "<="
        self.sombra.repeat_x = self.sombra.repeat_y = False
        self.fbo_sombra = ctx.framebuffer(depth_attachment=self.sombra)
        self.fbo = ctx.framebuffer(ctx.renderbuffer((ancho, alto), 4, samples=muestras),
                                   ctx.depth_renderbuffer((ancho, alto), samples=muestras))
        self.fbo_final = ctx.framebuffer(ctx.renderbuffer((ancho, alto), 4))

        # Encuadre: centro y tamaño de la escena; el sol fijo en diagonal.
        self.centro = (escena.minimo + escena.maximo) / 2
        self.tam = float(np.linalg.norm(escena.maximo - escena.minimo))
        self.sol = np.array([0.45, 0.8, 0.35])
        self.sol /= np.linalg.norm(self.sol)
        extension = self.tam / 2
        luz_vista = mirar(self.centro + self.sol * self.tam, self.centro)
        self.luz_vp = ortografica(-extension, extension, -extension, extension, 0.1, self.tam * 2) @ luz_vista

    def _camara(self, t):
        if len(self.ruta) >= 2:
            puntos = self.ruta + self.ruta[-2:0:-1]          # ida y vuelta
            tramos = [(puntos[i], puntos[(i + 1) % len(puntos)]) for i in range(len(puntos))]
            largos = [np.linalg.norm(b - a) for a, b in tramos]
            d = (1.4 * t) % sum(largos)                         # 1.4 m/s: paso de caminata
            for (a, b), largo in zip(tramos, largos):
                if d <= largo:
                    ojo = a + (b - a) * (d / largo)
                    adelante = (b - a) / largo
                    return ojo, ojo + adelante * 5.0 + np.array([0.0, -0.4, 0.0])
                d -= largo
        a = 0.08 * t
        mn, mx = self.e.minimo, self.e.maximo
        if self.modo_camara == "fuera":   # objeto suelto: girar alrededor, un poco desde arriba
            radio = 0.75 * self.tam
            ojo = np.array([self.centro[0] + radio * math.cos(a), self.centro[1] + 0.3 * self.tam,
                            self.centro[2] + radio * math.sin(a)])
            return ojo, self.centro
        radio = 0.28 * max(mx[0] - mn[0], mx[2] - mn[2])
        altura = mn[1] + 0.12 * (mx[1] - mn[1]) + 0.02 * self.tam
        ojo = np.array([self.centro[0] + radio * math.cos(a), altura, self.centro[2] + radio * math.sin(a)])
        objetivo = np.array([self.centro[0], altura - 0.01 * self.tam, self.centro[2]])
        return ojo, objetivo

    def dibujar(self, t):
        ctx = self.ctx
        ctx.enable(ctx.DEPTH_TEST)
        ctx.disable(ctx.CULL_FACE)
        # 1) sombras
        self.fbo_sombra.use()
        self.fbo_sombra.clear(depth=1.0)
        self.prog_sombra["luz_vp"].write(gl(self.luz_vp))
        for mat, _vao, vao_s in self.vaos:
            tex, _f = self.materiales.get(mat, (None, None))
            self.prog_sombra["con_textura"].value = 1 if tex else 0
            if tex:
                tex.use(0)
                self.prog_sombra["color_tex"].value = 0
            vao_s.render()
        # 2) cámara
        ojo, objetivo = self._camara(t)
        vp = perspectiva(60, self.W / self.H, self.tam * 0.0005, self.tam * 1.5) @ mirar(ojo, objetivo)
        self.fbo.use()
        self.fbo.clear(0, 0, 0, 1, depth=1.0)
        exp = self.exposicion
        ctx.disable(ctx.DEPTH_TEST)
        self.cielo.use(2)
        self.prog_cielo["cielo"].value = 2
        self.prog_cielo["inv_vp"].write(gl(np.linalg.inv(vp)))
        self.prog_cielo["camara"].value = tuple(ojo)
        self.prog_cielo["exposicion"].value = exp
        self.vao_cielo.render(mode=ctx.TRIANGLE_STRIP)
        ctx.enable(ctx.DEPTH_TEST)
        p = self.prog
        p["vp"].write(gl(vp))
        p["luz_vp"].write(gl(self.luz_vp))
        self.sombra.use(1)
        p["sombra"].value = 1
        p["cielo"].value = 2
        p["sol"].value = tuple(self.sol)
        p["camara"].value = tuple(ojo)
        p["exposicion"].value = exp
        for mat, vao, _vs in self.vaos:
            tex, factor = self.materiales.get(mat, (None, (0.8, 0.8, 0.8, 1)))
            p["con_textura"].value = 1 if tex else 0
            p["factor"].value = factor
            if tex:
                tex.use(0)
                p["color_tex"].value = 0
            vao.render()
        ctx.copy_framebuffer(self.fbo_final, self.fbo)   # resuelve el antialiasing

    def leer(self):
        return np.frombuffer(self.fbo_final.read(components=4), dtype=np.uint8)

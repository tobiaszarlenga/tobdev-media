# Reel "El que inventó las reglas de las contraseñas dice que se equivocó". Uso: python3 contrasenas.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = "alarma"; INK = PAL[PA]["ink"]; SOFT = PAL[PA]["soft"]; ACC = "#FF4D5E"; OK = "#4ADE80"; DK = "#1A0A0E"


def field(x, y, w, txt, fid, color="#1A0A0E", size=54, bg="#FFF1F2", op=None):
    return G(fid, R(x, y, w, 130, 28, bg, filter="url(#{id}-sh)") + T(x + 40, y + 84, txt, size, color, "start", mono=True, weight=700, ls="0"), op=op)


def row(y, txt, rid, w=760):
    return G(rid, R(160, y, w, 110, 24, "#2A0D13", stroke="#6E1F2A", stroke_width=4) + R(190, y + 25, 60, 60, 14, "none", stroke=SOFT, stroke_width=5)
             + T(280, y + 70, txt, 40, INK, "start", weight=700))


def bank(cx, by, s, bid):
    return G(bid, P(f"M{cx - s * .6} {by - s * .9} L{cx} {by - s * 1.25} L{cx + s * .6} {by - s * .9} Z", "#FFD0D5") + "".join(R(cx - s * .5 + k * s * .27, by - s * .85, s * .12, s * .75, 4, "#FFD0D5") for k in range(4))
             + R(cx - s * .62, by - s * .12, s * 1.24, s * .12, 4, "#FFD0D5"))


def tower_b(cx, by, s, tid):
    win = "".join(R(cx - s * .3 + (k % 3) * s * .22, by - s * 1.3 + (k // 3) * s * .25, s * .14, s * .16, 3, "#2A0D13") for k in range(12))
    return G(tid, R(cx - s * .4, by - s * 1.45, s * .8, s * 1.45, 10, "#FF9AA5") + win)


def uni(cx, by, s, uid):
    return G(uid, R(cx - s * .6, by - s * .7, s * 1.2, s * .7, 8, "#FFD0D5") + P(f"M{cx - s * .3} {by - s * .7} A{s * .3} {s * .3} 0 0 1 {cx + s * .3} {by - s * .7} Z", "#FF9AA5")
             + "".join(R(cx - s * .45 + k * s * .3, by - s * .55, s * .14, s * .4, 4, "#2A0D13") for k in range(4)))


B = []
# 1
B.append(beat("El tipo que inventó las reglas de las contraseñas dice que se *equivocó*.",
              svg(PA, lock(540, 760, 220, "lk", "#FF9AA5", INK, "#2A0D13") + field(150, 940, 780, "P@ssw0rd!", "f") + stamp(540, 1260, 420, 130, "ERROR", ACC, "st", -6, 72), gy=950),
              """IL.pop(id+"-lk", c.t0, .4); IL.in(id+"-f", c.t0+.15, 0, 60);
F(id+"-lks", {y:0}, {y:-30, duration:.3, yoyo:true, repeat:3}, c.t0+.6);
F(id+"-st", {opacity:0, scale:1.8, rotation:-14, transformOrigin:"50% 50%"}, {opacity:1, scale:1, rotation:0, duration:.22, ease:"power4.in"}, cue(0)-.05);
IL.shake(id+"-f", cue(0)+.15, 5, 14); IL.zoom(id+"-glow", c.t0, c.t1-c.t0, 1.2);""", ["equivocó"]))
# 2
docs = "".join(doc(260 + k * 30, 640 + k * 40, 520, 680, f"d{k}", 7, "#FFF1F2", "#B85A66", "NIST · 2003" if k == 2 else "") for k in range(3))
B.append(beat("En 2003, Bill Burr escribió una guía para el gobierno de Estados Unidos.",
              svg(PA, docs + G("y", R(640, 1260, 300, 110, 55, ACC) + T(790, 1335, "2003", 62, "#fff", mono=True), op=0), gy=1000),
              """for (let k=0;k<3;k++) IL.in(id+"-d"+k, c.t0+k*.12, 0, 120, .45); IL.pop(id+"-y", c.t0+.6);
IL.float(id+"-d2", c.t0+.8, c.t1-c.t0, 8);""", []))
# 3
rows = ["MAYÚSCULAS", "NÚMEROS", "SÍMBOLOS  # $ %", "CAMBIARLA CADA 90 DÍAS"]
B.append(beat("Pedía mayúsculas, números, símbolos raros y cambiarla cada noventa días.",
              svg(PA, "".join(row(640 + k * 150, t, f"r{k}") for k, t in enumerate(rows)) + "".join(check(220, 695 + k * 150, 34, f"c{k}", OK) for k in range(4)), gy=1000),
              """const w = ["mayúsculas","números","símbolos","noventa"];
for (let k=0;k<4;k++){ const t = (p.wt && p.wt.length) ? c.t0 + (c.t1-c.t0-.6)*k/4 : c.t0+k*.5; IL.in(id+"-r"+k, c.t0+k*.08, -200, 0, .35); IL.pop(id+"-c"+k, cue(k)); }""",
              ["mayúsculas", "números", "símbolos", "noventa"]))
# 4
B.append(beat("Bancos, empresas y universidades la copiaron.",
              svg(PA, bank(270, 1260, 230, "b1") + tower_b(540, 1260, 280, "b2") + uni(810, 1260, 230, "b3") + R(80, 1258, 920, 10, 5, "#6E1F2A")
                  + "".join(G(f"p{k}", R(220 + k * 290, 620, 80, 100, 8, "#FFF1F2") + R(235 + k * 290, 645, 50, 8, 4, "#B85A66") + R(235 + k * 290, 665, 40, 8, 4, "#B85A66")) for k in range(3)), gy=1050),
              """IL.in(id+"-b1", c.t0, 0, 200); IL.in(id+"-b2", c.t0+.12, 0, 200); IL.in(id+"-b3", c.t0+.24, 0, 200);
for (let k=0;k<3;k++){ const t = cue(k); F(id+"-p"+k, {y:-300, opacity:0}, {y:0, opacity:1, duration:.3, ease:"power2.in"}, t-.2); F(id+"-p"+k, {y:0}, {y:330, scale:.4, opacity:0, duration:.4, ease:"power2.in"}, t+.3); }""",
              ["Bancos", "empresas", "universidades"]))
# 5
B.append(beat("Y la gente hizo lo obvio: la misma clave con un *uno* al final. Después, un dos.",
              svg(PA, field(150, 820, 780, "Juan1987!", "f0") + field(150, 820, 780, "Juan1987!1", "f1", op=0) + field(150, 820, 780, "Juan1987!2", "f2", op=0)
                  + G("cal", R(380, 1060, 320, 300, 26, "#FFF1F2") + R(380, 1060, 320, 80, 26, ACC) + R(380, 1110, 320, 30, 0, ACC) + T(540, 1270, "90", 120, DK, mono=True) + T(540, 1330, "DÍAS", 30, "#B85A66", mono=True), op=0), gy=1000),
              """IL.in(id+"-f0", c.t0, 0, 60); IL.pop(id+"-cal", c.t0+.3);
const t1 = cue(0); IL.out(id+"-f0", t1, .05); IL.fade(id+"-f1", t1, .05); IL.pulse(id+"-f1", t1, 1, 1.04); IL.spin(id+"-cal", t1, .5, 360);
const t2 = Math.max(t1+.8, c.t1-1.0); IL.out(id+"-f1", t2, .05); IL.fade(id+"-f2", t2, .05); IL.pulse(id+"-f2", t2, 1, 1.04); IL.spin(id+"-cal", t2, .5, 360);""", ["uno"]))
# 6 — cita (escena del motor)
B.append({"texto": "En 2017, Burr le dijo al {Wall Street Journal|uól strit yórnal}: «Mucho de lo que hice, hoy lo lamento».",
          "escena": {"tipo": "cita", "texto": "Mucho de lo que hice, hoy lo lamento.", "autor": "Bill Burr", "cargo": "The Wall Street Journal · 2017", "en": "Mucho"}})
# 7
B.append(beat("Hoy la guía oficial dice otra cosa: lo que importa es el *largo*.",
              svg(PA, field(150, 760, 380, "Tr0b@!", "s", size=48) + field(150, 960, 780, "caballo-faro-lluvia-tostada", "l", size=36)
                  + G("ru", L(150, 1180, 930, 1180, SOFT, 6) + "".join(L(150 + k * 39, 1160 if k % 5 else 1145, 150 + k * 39, 1180, SOFT, 4) for k in range(21)))
                  + R(150, 1210, 0, 26, 13, ACC, id="{id}-bs") + R(150, 1250, 0, 26, 13, OK, id="{id}-bl"), gy=1000),
              """IL.in(id+"-s", c.t0, -200, 0); IL.in(id+"-l", c.t0+.15, -200, 0); IL.fade(id+"-ru", c.t0+.3);
F(id+"-bs", {attr:{width:0}}, {attr:{width:380}, duration:.5}, cue(0)-.2); F(id+"-bl", {attr:{width:0}}, {attr:{width:780}, duration:.8, ease:"power2.out"}, cue(0)-.1);
IL.pulse(id+"-l", cue(0)+.4, 1, 1.03);""", ["largo"]))
# 8 — número (escena del motor)
B.append({"texto": "Si la clave es tu única protección, mínimo *quince* caracteres.",
          "escena": {"tipo": "numero", "valor": 15, "etiqueta": "caracteres como *mínimo*", "en": "quince", "desde": 0}})
# 9
rows2 = ["SÍMBOLOS OBLIGATORIOS", "CAMBIARLA CADA 90 DÍAS", "QUE SEA LARGA"]
B.append(beat("Nada de obligarte a usar símbolos, ni de cambiarla cada tres meses.",
              svg(PA, "".join(row(700 + k * 170, t, f"r{k}") for k, t in enumerate(rows2)) + cross(220, 755, 34, "x0") + cross(220, 925, 34, "x1") + check(220, 1095, 34, "c2", OK)
                  + R(270, 752, 0, 8, 4, ACC, id="{id}-s0") + R(270, 922, 0, 8, 4, ACC, id="{id}-s1"), gy=1000),
              """for (let k=0;k<3;k++) IL.in(id+"-r"+k, c.t0+k*.08, 200, 0, .35);
IL.pop(id+"-x0", cue(0)); F(id+"-s0", {attr:{width:0}}, {attr:{width:600}, duration:.3}, cue(0));
IL.pop(id+"-x1", cue(1)); F(id+"-s1", {attr:{width:0}}, {attr:{width:600}, duration:.3}, cue(1));
IL.pop(id+"-c2", Math.min(c.t1-.3, cue(1)+.7));""", ["símbolos", "meses"]))
# 10
tiles = ["caballo", "faro", "lluvia", "tostada"]
B.append(beat("Cuatro palabras al azar le ganan a una clave corta llena de símbolos.",
              svg(PA, "".join(G(f"t{k}", R(150 + (k % 2) * 400, 660 + (k // 2) * 170, 380, 140, 30, "#FFF1F2") + T(340 + (k % 2) * 400, 750 + (k // 2) * 170, w, 50, DK, weight=800)) for k, w in enumerate(tiles))
                  + R(150, 1030, 780, 34, 17, "#2A0D13") + R(150, 1030, 0, 34, 17, OK, id="{id}-m1")
                  + field(150, 1150, 400, "Tr0b@!", "s", size=48) + R(150, 1310, 780, 34, 17, "#2A0D13") + R(150, 1310, 0, 34, 17, ACC, id="{id}-m2"), gy=1000),
              """for (let k=0;k<4;k++) F(id+"-t"+k, {y:-400, opacity:0}, {y:0, opacity:1, duration:.35, ease:"bounce.out"}, c.t0+k*.15);
F(id+"-m1", {attr:{width:0}}, {attr:{width:760}, duration:.7, ease:"power2.out"}, c.t0+.8);
IL.in(id+"-s", c.t0+.6, 0, 60); F(id+"-m2", {attr:{width:0}}, {attr:{width:220}, duration:.5}, c.t0+1.1);""", []))
# 11
locks = "".join(lock(540 + 330 * math.cos(a), 1000 + 360 * math.sin(a), 120, f"L{k}", "#FF9AA5", INK, "#2A0D13") for k, a in enumerate([math.radians(d) for d in (-150, -90, -30, 30, 150)]))
keyshape = G("key", C(540, 1000, 70, "#FFD54A") + C(540, 1000, 28, PAL[PA]["bg"][1]) + R(600, 985, 170, 30, 10, "#FFD54A") + R(720, 1015, 24, 40, 6, "#FFD54A") + R(680, 1015, 24, 30, 6, "#FFD54A"))
B.append(beat("Mandáselo a ese amigo que usa la misma clave para todo.",
              svg(PA, locks + keyshape, gy=1000),
              """IL.pop(id+"-key", c.t0, .4); IL.spin(id+"-key", c.t0+.3, c.t1-c.t0, 40);
for (let k=0;k<5;k++){ IL.pop(id+"-L"+k, c.t0+.15+k*.08); F(id+"-L"+k+"s", {y:0}, {y:-28, duration:.25, ease:"back.out(2)"}, c.t0+.9+k*.22); }""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más mitos de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Mitos de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """El que inventó las reglas de las contraseñas dice que se equivocó 🔐

En 2003, Bill Burr escribió para el NIST (el instituto de estándares de Estados Unidos) la guía que pedía mayúsculas, números, símbolos y cambiar la clave cada 90 días. Bancos, empresas y universidades la copiaron.

En 2017 le dijo al Wall Street Journal: "Mucho de lo que hice, hoy lo lamento".

La guía actual del NIST (2025) dice otra cosa:
✅ Lo que importa es el largo: mínimo 15 caracteres si la clave es tu única protección
❌ Nada de obligarte a usar símbolos
❌ Nada de cambiarla cada tantos meses (solo si se filtró)

Mandáselo a ese amigo que usa la misma clave para todo.

Fuentes: NIST SP 800-63B-4 (2025) · The Wall Street Journal (2017)
Video hecho con IA.

#contraseñas #ciberseguridad #seguridadinformatica #tecnologia #tips #mitos #privacidad #internet"""

g = {"etiqueta": "MITOS #2", "fuente": "NIST SP 800-63B-4 (2025) · The Wall Street Journal (2017)", "acento": ACC, "tema": "alarma", "musica": "urgente",
     "subtitulos": "karaoke", "transiciones": ["flash", "whip", "corte", "whip", "flash", "corte", "whip", "flash", "corte", "whip", "flash", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "contrasenas.json"), sys.argv[1:])

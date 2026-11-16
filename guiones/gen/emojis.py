# Reel corto de prueba: "Los primeros emojis entraban en una grilla de 12 x 12". Prueba de la skill ganchos-y-captions
# y de dos ideas del registro de HyperFrames adaptadas: grid-pixelate-wipe (transición de píxeles) y headline-slam.
# Los dibujitos de 12x12 son propios y genéricos (no copian el set original). Uso: python3 emojis.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = dict(bg=("#0B0B14", "#15122B", "#221640"), glow="#FFD23F", ink="#FFF6DA", soft="#B9A9FF", card="#FFFFFF", dark="#0B0B14", line="#2C2550", stars=False)
INK = PA["ink"]; SOFT = PA["soft"]; ACC = "#FFD23F"; PINK = "#FF4F8B"

ICONS = {  # 12x12 propios
    "heart": ["............", "..##....##..", ".####..####.", "############", "############", "############", ".##########.", "..########..",
              "...######...", "....####....", ".....##.....", "............"],
    "sun": [".....##.....", ".#...##...#.", "..#......#..", "....####....", "...######...", "##.######.##", "##.######.##", "...######...",
            "....####....", "..#......#..", ".#...##...#.", ".....##....."],
    "face": ["...######...", "..#......#..", ".#........#.", "#..##..##..#", "#..##..##..#", "#..........#", "#..........#", "#.#......#.#",
             "#..#....#..#", ".#..####..#.", "..#......#..", "...######..."],
    "drop": [".....##.....", ".....##.....", "....####....", "....####....", "...######...", "..########..", "..########..", ".##########.",
             ".##########.", ".#########..", "..#######...", "....###....."],
    "note": ["......######", "......######", "......#....#", "......#....#", "......#....#", "......#....#", "......#....#", "...###...###",
             "..####..####", "..####..####", "...##....##.", "............"],
    "star": [".....##.....", ".....##.....", "....####....", "############", ".##########.", "..########..", "...######...", "...######...",
             "..###..###..", "..##....##..", ".##......##.", "............"],
}


def pix(x, y, cell, icon, pid, on=ACC, grid=True, gap=.12):
    """Grilla de 12x12: cada punto encendido es {id}-pid-p{k} (k en orden desde el centro)."""
    on_cells = [(r, c) for r, row in enumerate(ICONS[icon]) for c, ch in enumerate(row) if ch == "#"]
    on_cells.sort(key=lambda rc: (rc[0] - 5.5) ** 2 + (rc[1] - 5.5) ** 2)
    g = "".join(R(x + c * cell, y + r * cell, cell * (1 - gap), cell * (1 - gap), cell * .14, "#ffffff", opacity=.06) for r in range(12) for c in range(12)) if grid else ""
    p = "".join(R(x + c * cell, y + r * cell, cell * (1 - gap), cell * (1 - gap), cell * .14, on, id=f"{{id}}-{pid}p{k}") for k, (r, c) in enumerate(on_cells))
    return G(pid, g + p), len(on_cells)


def wipe(sid="wp", cols=9, rows=16, color="#FFD23F"):
    """grid-pixelate-wipe adaptado: celdas que tapan la pantalla y se van desde los bordes."""
    w, h = 1080 / cols, 1920 / rows
    return "".join(R(c * w, r * h, w + 1, h + 1, 0, color, id=f"{{id}}-{sid}{r * cols + c}") for r in range(rows) for c in range(cols))


WIPE_JS = """for (let r=0;r<16;r++) for (let cc=0;cc<9;cc++){ const k=r*9+cc, d=Math.max(Math.abs(cc-4)/4, Math.abs(r-7.5)/7.5);
  F(id+"-wp"+k, {scale:1, transformOrigin:"50% 50%"}, {scale:0, duration:.28, ease:"power2.inOut"}, c.t0 + (1-d)*.0 + d*.32); }"""
# en las escenas con wipe, las celdas arrancan tapando y se van de afuera hacia adentro (d alto = borde = primero)
WIPE_JS = WIPE_JS.replace("c.t0 + (1-d)*.0 + d*.32", "c.t0 + (1-d)*.32")
SLAM_JS = """F(SEL, {scale:1.6, opacity:0, transformOrigin:"50% 50%"}, {scale:1, opacity:1, duration:.42, ease:"expo.out"}, T);
F(SEL, {x:0}, {x:12, duration:.034, yoyo:true, repeat:3}, T+.4);"""


def slam(sel, t):
    return SLAM_JS.replace("SEL", sel).replace("T", t)


B = []
# 1 — gancho (regla de dos tiempos)
heart, nh = pix(240, 640, 50, "heart", "h")
B.append(beat("Los primeros emojis entraban en una grilla de doce por doce. Y hoy están en un *museo*.",
              svg(PA, heart + G("t", T(540, 1330, "12 × 12", 150, INK, mono=True), op=0)
                  + G("fr", R(190, 590, 700, 700, 26, "none", stroke="#C9A14A", stroke_width=26) + R(214, 614, 652, 652, 14, "none", stroke="#8C6A2A", stroke_width=6), op=0)
                  + G("pl", R(340, 1390, 400, 70, 12, "#C9A14A") + T(540, 1437, "MUSEO", 34, "#2A1D06", mono=True), op=0), gy=950),
              f"""for (let k=0;k<{nh};k++) F(id+"-hp"+k, {{scale:0, transformOrigin:"50% 50%"}}, {{scale:1, duration:.18, ease:"back.out(3)"}}, c.t0+.1+k*Math.min(.018, 1.2/{nh}));
{slam('id+"-t"', 'c.t0+1.2')}
F(id+"-fr", {{opacity:0, scale:1.25, transformOrigin:"50% 50%"}}, {{opacity:1, scale:1, duration:.3, ease:"power4.in"}}, cue(0)-.1); IL.pop(id+"-pl", cue(0)+.15);
IL.zoom(id+"-glow", c.t0, c.t1-c.t0, 1.25);""", ["museo"]))
# 2 — Japón 1999, 176 dibujitos
icons = ["sun", "face", "drop", "note", "star", "heart"]
small = "".join(pix(395 + (k % 3) * 100, 820 + (k // 3) * 110, 7.5, ic, f"s{k}", [ACC, PINK, "#5BD1FF", "#7CFF9B", ACC, PINK][k], grid=False)[0] for k, ic in enumerate(icons))
phone_d = (R(350, 640, 380, 820, 60, "#2B2A3A", stroke="#4A476A", stroke_width=6) + R(385, 700, 310, 330, 14, "#C8D8A8") + small
           + "".join(R(395 + (k % 3) * 100, 1090 + (k // 3) * 80, 80, 56, 16, "#3E3C55") for k in range(9)))
B.append(beat("Japón, 1999: ciento setenta y seis dibujitos para celulares.",
              svg(PA, wipe() + G("ph", phone_d) + G("n", R(680, 560, 260, 120, 60, PINK) + T(810, 640, "176", 72, "#fff", mono=True), op=0)
                  + G("yr", T(230, 620, "1999", 64, SOFT, mono=True), op=0), gy=1000),
              WIPE_JS + """
IL.in(id+"-ph", c.t0+.15, 0, 120, .45); IL.fade(id+"-yr", c.t0+.3);
for (let k=0;k<6;k++) IL.pop(id+"-s"+k, c.t0+.6+k*.12, .2);""" + "\n" + slam('id+"-n"', 'cue(0)-.1'), ["setenta"]))
# 3 — Kurita, pocos puntos
sun, ns = pix(300, 700, 40, "sun", "su", ACC)
B.append(beat("Los diseñó Shigetaka Kurita, con los poquitos puntos que entraban en esas pantallas.",
              svg(PA, sun + G("tg", R(250, 1260, 580, 92, 46, ACC) + T(540, 1320, "SHIGETAKA KURITA", 36, "#1A1406", mono=True), op=0)
                  + G("mg", G(None, C(0, 0, 120, "none", stroke=INK, stroke_width=14) + L(85, 85, 170, 170, INK, 22), tr="translate(640 820)")), gy=950),
              f"""for (let k=0;k<{ns};k++) F(id+"-sup"+k, {{scale:0, transformOrigin:"50% 50%"}}, {{scale:1, duration:.15, ease:"back.out(3)"}}, c.t0+.15+k*Math.min(.03, (c.t1-c.t0-1)/{ns}));
IL.pop(id+"-tg", cue(0)-.1); F(id+"-mg", {{x:0, y:0}}, {{x:-260, y:120, duration:1.4, yoyo:true, repeat:1, ease:"sine.inOut"}}, c.t0+.4);""", ["Kurita"]))
# 4 — MoMA 2016
frames = "".join(G(f"f{k}", R(120 + k * 290, 760, 250, 300, 12, "#C9A14A") + R(140 + k * 290, 780, 210, 260, 8, "#14121F")
                       + pix(155 + k * 290, 830, 15, ic, f"fi{k}", [PINK, ACC, "#5BD1FF"][k], grid=False)[0], op=0) for k, ic in enumerate(["heart", "face", "drop"]))
B.append(beat("En 2016, el {MoMA|moma} de Nueva York los sumó a su *colección*.",
              svg(PA, wipe(color=PINK) + R(0, 600, 1080, 760, 0, "#1C1830") + P("M540 520 L170 1300 L910 1300 Z", "#FFF3C4", opacity=.1) + frames
                  + G("pl", R(330, 1180, 420, 80, 12, "#EDE6D3") + T(540, 1232, "MoMA · 2016", 36, "#1A1406", mono=True), op=0), gy=950),
              WIPE_JS + """
for (let k=0;k<3;k++) IL.in(id+"-f"+k, c.t0+.35+k*.15, 0, 60, .4); IL.pop(id+"-pl", cue(0)-.1); IL.pulse(id+"-f1", cue(0)+.2, 1, 1.05);""", ["colección"]))
# 5 — compartir
bub = "".join(G(f"b{k}", R(x, y, 260, 150, 40, c) + pix(x + 85, y + 30, 7.5, ic, f"bi{k}", "#fff", grid=False)[0], op=0)
              for k, (x, y, c, ic) in enumerate([(160, 700, PINK, "heart"), (620, 860, "#5BD1FF", "face"), (200, 1030, "#7CFF9B", "star"), (640, 1190, ACC, "sun")]))
B.append(beat("Mandáselo a quien contesta todo con emojis.",
              svg(PA, bub + G("pl", P("M480 1420 l140 -60 l-50 150 l-25 -60 z", ACC), op=0), gy=1000),
              """for (let k=0;k<4;k++) F(id+"-b"+k, {opacity:0, y:60, scale:.6, transformOrigin:"50% 50%"}, {opacity:1, y:0, scale:1, duration:.3, ease:"back.out(2)"}, c.t0+k*.22);
IL.pop(id+"-pl", c.t0+.9); F(id+"-pl", {x:0, y:0}, {x:260, y:-420, duration:.8, ease:"power2.in"}, c.t1-.9);""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev}.", "escena": {"tipo": "cierre", "sub": "Historias de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """Los primeros emojis entraban en una grilla de 12 × 12. Y hoy están en un museo 🖼️

En 1999, la telefónica japonesa NTT DOCOMO lanzó 176 emojis para celulares y beepers. Los diseñó Shigetaka Kurita, con los poquitos puntos que entraban en esas pantallas.

En 2016, el MoMA de Nueva York los sumó a su colección. Dato extra: las caritas amarillas que usamos hoy no vienen de ese set, salieron de otros que llegaron después.

Mandáselo a quien contesta todo con emojis 😅

Fuentes: MoMA (colección, "Emoji", 1998-1999) · Domus (2016)
Video hecho con IA. Los dibujitos del video son nuestros, no los originales.

#emojis #historia #tecnologia #diseño #curiosidades #japon #sabiasque #museo"""

g = {"etiqueta": "HISTORIAS #5", "fuente": "MoMA · Domus (2016)", "acento": ACC, "tema": "noche", "musica": "tech", "subtitulos": "bloque",
     "transiciones": ["corte", "corte", "flash", "corte", "corte"], "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "emojis.json"), sys.argv[1:])

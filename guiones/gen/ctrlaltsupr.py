# Reel "Bill Gates admitió que Control Alt Suprimir fue un error". Uso: python3 ctrlaltsupr.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = "retro"; INK = PAL[PA]["ink"]; SOFT = PAL[PA]["soft"]; ACC = "#39FF88"; BEIGE = "#E9E4D4"; BEIGE2 = "#C9C2AE"; SCR = "#03140A"; RED = "#FF5A6E"


def pc(cx, cy, s, pid, lines=()):
    txt = "".join(T(cx - s * .4, cy - s * .62 + k * s * .1, l, s * .065, ACC, "start", mono=True, weight=600, ls="0", tid=f"{pid}t{k}") for k, l in enumerate(lines))
    return G(pid, R(cx - s * .55, cy - s * .85, s * 1.1, s * .8, s * .06, BEIGE, stroke=BEIGE2, stroke_width=6) + R(cx - s * .46, cy - s * .76, s * .92, s * .6, s * .04, SCR) + txt
             + R(cx - s * .6, cy + s * .02, s * 1.2, s * .3, s * .04, BEIGE, stroke=BEIGE2, stroke_width=6) + R(cx + s * .1, cy + s * .12, s * .38, s * .05, 4, "#6E6A5C")
             + R(cx - s * .5, cy + s * .12, s * .2, s * .1, 4, "#4ADE80"))


def keys3(cx, cy, s, kid, labels=("CTRL", "ALT", "SUPR"), gap=None):
    gap = gap if gap is not None else s * 1.3
    return "".join(key(cx - gap + k * gap - s / 2, cy - s * .4, s, s * .8, l, f"{kid}{k}", BEIGE, BEIGE2, "#2B2A24", s * .2) for k, l in enumerate(labels))


B = []
# 1
B.append(beat("Bill Gates admitió que Control Alt Suprimir fue un *error*.",
              svg(PA, keys3(540, 980, 200, "k") + stamp(540, 1300, 420, 130, "ERROR", RED, "st", -6, 72), gy=980, grid=True),
              """for (let k=0;k<3;k++){ IL.in(id+"-k"+k, c.t0+k*.1, 0, 120, .35); F(id+"-k"+k+"t", {y:0}, {y:14, duration:.12, yoyo:true, repeat:1}, c.t0+.7+k*.12); }
F(id+"-st", {opacity:0, scale:1.8, rotation:-14, transformOrigin:"50% 50%"}, {opacity:1, scale:1, rotation:0, duration:.22, ease:"power4.in"}, cue(0)-.05); IL.shake(id+"-k1", cue(0)+.2, 4, 10);""", ["error"]))
# 2
B.append(beat("Todo empezó en 1981, en {IBM|i be eme}, mientras armaban su primera computadora personal.",
              svg(PA, pc(540, 1060, 620, "pc", ["C:\\>_", "IBM PERSONAL COMPUTER", "VERSION 1.00"]) + G("yr", R(390, 1340, 300, 100, 50, ACC) + T(540, 1410, "1981", 60, SCR, mono=True), op=0), gy=1000, grid=True),
              """IL.in(id+"-pc", c.t0, 0, 160, .5); for (let k=0;k<3;k++) IL.fade(id+"-pct"+k, c.t0+.5+k*.25, .05); IL.pop(id+"-yr", c.t0+.3);""", []))
# 3
B.append(beat("Cada vez que algo fallaba, reiniciar tardaba muchísimo por los *tests de memoria*.",
              svg(PA, pc(540, 1000, 620, "pc", ["MEMORY TEST", "", "", ""]) + R(318, 760, 440, 40, 8, "#0D3A1E") + R(318, 760, 0, 40, 8, ACC, id="{id}-bar")
                  + T(540, 870, "16K · 32K · 48K", 34, ACC, mono=True, tid="kb", op=0)
                  + G("clk", C(860, 1380, 80, BEIGE) + L(860, 1380, 860, 1320, SCR, 8) + L(860, 1380, 900, 1380, SCR, 8, id="{id}-hand")), gy=1000, grid=True),
              """IL.in(id+"-pc", c.t0, 0, 80, .4); F(id+"-bar", {attr:{width:0}}, {attr:{width:440}, duration:c.t1-c.t0-.4, ease:"none"}, c.t0+.3); IL.fade(id+"-kb", c.t0+.6);
IL.pop(id+"-clk", c.t0+.4); F(id+"-hand", {rotation:0, svgOrigin:"860 1380"}, {rotation:720, svgOrigin:"860 1380", duration:c.t1-c.t0, ease:"none"}, c.t0);""", ["tests"]))
# 4
B.append(beat("Un ingeniero, David Bradley, armó un atajo para reiniciar al toque.",
              svg(PA, G("tg", R(250, 700, 580, 96, 48, ACC) + T(540, 762, "DAVID BRADLEY · IBM", 36, SCR, mono=True)) + keys3(540, 1050, 200, "k")
                  + "".join(G(f"b{k}", P(f"M{480 + k * 60} 1250 l-40 90 l36 0 l-24 80 l70 -110 l-38 0 l22 -60 z", "#FFE45C"), op=0) for k in range(2)), gy=1000, grid=True),
              """IL.in(id+"-tg", c.t0, 0, -60); for (let k=0;k<3;k++) IL.pop(id+"-k"+k, c.t0+.4+k*.12);
const tz = Math.max(c.t0+1, cue(0)-.2); for (let k=0;k<3;k++) F(id+"-k"+k+"t", {y:0}, {y:14, duration:.1, yoyo:true, repeat:1}, tz);
for (let k=0;k<2;k++){ IL.pop(id+"-b"+k, tz+.15+k*.1); IL.shake(id+"-b"+k, tz+.4, 3, 6); }""", ["toque"]))
# 5
kb = R(90, 860, 900, 360, 30, BEIGE2) + "".join(R(120 + (k % 13) * 66, 890 + (k // 13) * 70, 58, 58, 10, BEIGE) for k in range(52))
B.append(beat("Eligió tres teclas separadas, para que nadie lo hiciera *sin querer*.",
              svg(PA, G("kb", G(None, kb + R(120, 1100, 124, 58, 10, ACC, id="{id}-c") + R(252, 1100, 124, 58, 10, ACC, id="{id}-a") + R(846, 960, 124, 58, 10, ACC, id="{id}-d")
                        + T(182, 1140, "CTRL", 26, SCR, mono=True) + T(314, 1140, "ALT", 26, SCR, mono=True) + T(908, 1000, "SUPR", 26, SCR, mono=True), tr="matrix(.9 0 0 .9 54 96)"))
                  + G("h1", C(250, 1330, 70, "#F2C9A0") + R(220, 1380, 60, 120, 30, "#F2C9A0"), op=0) + G("h2", C(900, 1330, 70, "#F2C9A0") + R(870, 1380, 60, 120, 30, "#F2C9A0"), op=0)
                  + P("M376 1060 Q610 920 846 990", id="{id}-arc", stroke=RED, stroke_width=8, stroke_dasharray="18 14", opacity=0), gy=1000, grid=True),
              """IL.in(id+"-kb", c.t0, 0, 120, .45); for (const s of ["c","a","d"]) IL.pulse(id+"-"+s, c.t0+.6, 2, 1.1);
IL.fade(id+"-arc", c.t0+.9); IL.in(id+"-h1", cue(0)-.3, 0, 120); IL.in(id+"-h2", cue(0)-.2, 0, 120);""", ["sin"]))
# 6
B.append(beat("Era para los programadores. Pero {Windows|uíndous} lo usó para *iniciar sesión*.",
              svg(PA, G("w", R(150, 720, 780, 560, 24, "#0E2A5C", filter="url(#{id}-sh)") + R(150, 720, 780, 80, 24, "#1B4A9C") + R(150, 770, 780, 30, 0, "#1B4A9C")
                        + T(540, 960, "Presioná", 44, "#E6F0FF", weight=700) + keys3(540, 1080, 150, "k", gap=190) + T(540, 1220, "para iniciar sesión", 40, "#E6F0FF", weight=700)), gy=1000, grid=True),
              """IL.pop(id+"-w", cue(0)-.3, .45, "back.out(1.4)"); for (let k=0;k<3;k++) IL.pulse(id+"-k"+k, cue(0)+.4+k*.12, 1, 1.12);""", ["iniciar"]))
# 7 — cita del motor
B.append({"texto": "Años después, Bradley dijo: «Yo lo habré inventado, pero Bill lo hizo famoso».",
          "escena": {"tipo": "cita", "texto": "Yo lo habré inventado, pero Bill lo hizo famoso.", "autor": "David Bradley", "cargo": "Ingeniero de IBM · 2001", "en": "Yo"}})
# 8
crowd = "".join(C(200 + (k % 9) * 85, 1350 + (k // 9) * 60, 28, "#1F5A35") for k in range(18))
B.append(beat("Y en 2013, en {Harvard|járvard}, Gates contestó: «Fue un *error*».",
              svg(PA, bubble(190, 740, 700, 260, "«Fue un error.»", "bb", BEIGE, SCR, 76) + T(540, 1130, "BILL GATES · HARVARD, 2013", 34, SOFT, mono=True, tid="lb", op=0) + G("cr", crowd), gy=1000, grid=True),
              """IL.in(id+"-cr", c.t0, 0, 100); IL.pop(id+"-bb", cue(0)-.4, .4); IL.fade(id+"-lb", cue(0)-.2); for (let k=0;k<3;k++) F(id+"-cr", {y:0}, {y:-14, duration:.1, yoyo:true, repeat:1}, cue(0)+.3+k*.25);""", ["error"]))
# 9
B.append(beat("Él quería un solo botón. Pero el que diseñó el teclado de {IBM|i be eme} no se lo *dio*.",
              svg(PA, G("btn", C(540, 860, 170, "#B9B2A0") + C(540, 845, 150, RED) + T(540, 870, "1", 90, "#fff", mono=True)) + cross(700, 720, 46, "x")
                  + keys3(540, 1290, 170, "k", gap=210), gy=1000, grid=True),
              """IL.pop(id+"-btn", c.t0, .45); F(id+"-btn", {y:0}, {y:10, duration:.12, yoyo:true, repeat:3}, c.t0+.6);
IL.pop(id+"-x", cue(0)-.1); IL.shake(id+"-btn", cue(0)+.1, 4, 10); for (let k=0;k<3;k++) IL.in(id+"-k"+k, cue(0)+.2+k*.1, 0, 80, .3);""", ["dio"]))
# 10
B.append(beat("Y por eso, más de cuarenta años después, seguimos apretando *tres teclas*.",
              svg(PA, keys3(540, 960, 200, "k") + G("n", T(540, 1330, "1981 → 2026", 64, ACC, mono=True), op=0), gy=1000, grid=True),
              """for (let k=0;k<3;k++) IL.in(id+"-k"+k, c.t0+k*.08, 0, 100, .3); IL.fade(id+"-n", c.t0+.4);
const n = Math.max(2, Math.floor((c.t1-c.t0-1)/.5)); for (let r=0;r<n;r++) for (let k=0;k<3;k++) F(id+"-k"+k+"t", {y:0}, {y:14, duration:.08, yoyo:true, repeat:1}, c.t0+.8+r*.5+k*.03);""", ["tres"]))
# 11
B.append(beat("Mandáselo a alguien que lo aprieta cada vez que la compu se tilda.",
              svg(PA, pc(540, 1020, 560, "pc", ["", "  NO RESPONDE", ""]) + G("spin", C(540, 880, 40, "none", stroke=ACC, stroke_width=10, stroke_dasharray="90 160"))
                  + G("pl", P("M780 1330 l140 -60 l-50 150 l-25 -60 z", "#FFE45C"), op=0), gy=1000, grid=True),
              """IL.in(id+"-pc", c.t0, 0, 100, .4); IL.spin(id+"-spin", c.t0, c.t1-c.t0, 900); IL.shake(id+"-pc", c.t0+.8, 4, 8);
IL.pop(id+"-pl", c.t0+.9); F(id+"-pl", {x:0, y:0}, {x:120, y:-420, duration:.9, ease:"power2.in"}, c.t1-1.1);""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más historias de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Historias de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """Bill Gates admitió que Ctrl + Alt + Supr fue un error ⌨️

En 1981, mientras IBM armaba su primera computadora personal, reiniciar tardaba muchísimo por los tests de memoria. El ingeniero David Bradley armó un atajo para reiniciar al toque y eligió tres teclas separadas para que nadie lo hiciera sin querer.

Era una herramienta para programadores, pero Windows terminó usándolo para iniciar sesión.

Bradley dijo años después: "Yo lo habré inventado, pero Bill lo hizo famoso". Y en 2013, en Harvard, Gates respondió: "Fue un error". Él quería un solo botón, pero el diseñador del teclado de IBM no se lo dio.

Más de 40 años después, seguimos apretando tres teclas.

Mandáselo a alguien que lo aprieta cada vez que la compu se tilda 😅

Fuentes: Harvard Campaign (2013) vía CBS News y ABC News · Mental Floss
Video hecho con IA.

#windows #billgates #ibm #historia #tecnologia #computacion #curiosidades #sabiasque"""

g = {"etiqueta": "HISTORIAS #4", "fuente": "Harvard (2013) vía CBS y ABC News · Mental Floss", "acento": ACC, "tema": "grilla", "musica": "retro",
     "subtitulos": "bloque", "transiciones": ["flash", "whip", "corte", "zoom", "corte", "whip", "flash", "corte", "whip", "flash", "corte", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "ctrlaltsupr.json"), sys.argv[1:])

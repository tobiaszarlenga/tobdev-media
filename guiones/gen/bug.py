# Reel "El primer bug de la historia fue un bicho de verdad". Uso: python3 bug.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = "sepia"; INK = PAL[PA]["ink"]; SOFT = PAL[PA]["soft"]; ACC = "#FFB547"; PAPER = "#F3E6CC"; PINK = "#7A5A36"; RED = "#D9483B"


def flap(mid, cx, cy, t, dur):  # aleteo de una polilla hecha con moth()
    n = max(2, int(dur / .14))
    return (f'F(id+"-{mid}l", {{scaleX:1, svgOrigin:"{cx} {cy}"}}, {{scaleX:.45, svgOrigin:"{cx} {cy}", duration:.07, yoyo:true, repeat:{n}}}, {t});'
            f'F(id+"-{mid}r", {{scaleX:1, svgOrigin:"{cx} {cy}"}}, {{scaleX:.45, svgOrigin:"{cx} {cy}", duration:.07, yoyo:true, repeat:{n}}}, {t});')


def cabinet(x, y, w, h, cid, lamps=True):
    ls = "".join(C(x + 30 + (k % 4) * (w - 60) / 3, y + 60 + (k // 4) * 70, 10, ACC) for k in range(16)) if lamps else ""
    return G(cid, R(x, y, w, h, 12, "#3B2A18", stroke="#6B4F2E", stroke_width=5) + G(cid + "L", ls) + "".join(R(x + 20, y + 380 + k * 40, w - 40, 14, 7, "#2A1D10") for k in range(4)))


def relay(cx, cy, s, rid):
    return G(rid, R(cx - s * .5, cy - s * .2, s, s * .6, 16, "#5C4026", stroke="#8C6A42", stroke_width=6)
             + "".join(R(cx - s * .4 + k * s * .1, cy - s * .15, s * .06, s * .5, 4, "#B07A3A") for k in range(9))
             + R(cx - s * .55, cy - s * .55, s * 1.1, s * .1, 6, "#C9C2B4") + R(cx - s * .55, cy - s * .3, s * 1.1, s * .1, 6, "#C9C2B4") + C(cx - s * .5, cy - s * .42, s * .07, "#E8E0CC"))


def logpage(x, y, w, h, pid, hand_id="hand", moth_on=True):
    lines = (T(x + 50, y + 110, "9/9  15:45", 32, "#6B4F2E", "start", mono=True, weight=600)
             + T(x + 50, y + 170, "Relay #70 Panel F", 34, "#3B2A18", "start", mono=True, weight=600)
             + T(x + 50, y + 220, "(moth) in relay.", 34, "#3B2A18", "start", mono=True, weight=600))
    m = moth(x + w / 2, y + 420, 120, "pm", "#9C8466", "#4A3826", "#6E5638") if moth_on else ""
    tape = R(x + w / 2 - 170, y + 360, 120, 40, 4, "#FFF6D8", opacity=.75, transform=f"rotate(-20 {x + w / 2 - 110} {y + 380})") + \
        R(x + w / 2 + 50, y + 360, 120, 40, 4, "#FFF6D8", opacity=.75, transform=f"rotate(20 {x + w / 2 + 110} {y + 380})")
    hand = (f'<clipPath id="{{id}}-hc"><rect id="{{id}}-hcr" x="{x + 30}" y="{y + 560}" width="0" height="120"/></clipPath>'
            f'<g clip-path="url(#{{id}}-hc)"><text x="{x + 50}" y="{y + 640}" font-size="{w * .052:.0f}" fill="#2B3A8C" font-family="Lora, serif" font-style="italic">First actual case of bug being found.</text></g>')
    return G(pid, R(x, y, w, h, 10, PAPER, filter="url(#{id}-sh)") + "".join(L(x + 30, y + 60 + k * 60, x + w - 30, y + 60 + k * 60, "#D8C7A4", 2) for k in range(int(h / 60) - 1))
             + lines + m + (tape if moth_on else "") + hand)


B = []
# 1
B.append(beat("El primer {bug|bag} de la historia fue un *bicho* de verdad.",
              svg(PA, G("txt", T(540, 1430, "BUG", 200, ACC, mono=True, op=.55)) + moth(540, 980, 260, "m"), gy=980),
              """IL.pop(id+"-m", c.t0, .45); """ + flap("m", 540, 980, "c.t0", 6) + """
F(id+"-m", {x:-60, y:30, rotation:-8, transformOrigin:"50% 50%"}, {x:60, y:-30, rotation:8, duration:1.3, yoyo:true, repeat:3, ease:"sine.inOut"}, c.t0+.2);
IL.in(id+"-txt", c.t0+.3, 0, 80); IL.pulse(id+"-txt", cue(0), 1, 1.06);""", ["bicho"]))
# 2
B.append(beat("Harvard, 1947. Una computadora gigante deja de *andar*.",
              svg(PA, "".join(cabinet(115 + k * 170, 720, 150, 600, f"c{k}") for k in range(5)) + G("yr", R(390, 580, 300, 100, 50, ACC) + T(540, 650, "1947", 60, "#2B1D10", mono=True), op=0)
                  + T(540, 1420, "HARVARD", 40, SOFT, mono=True, tid="h", op=0), gy=1000),
              """for (let k=0;k<5;k++) IL.in(id+"-c"+k, c.t0+k*.06, 0, 160, .4); IL.pop(id+"-yr", c.t0+.3); IL.fade(id+"-h", c.t0+.2);
for (let k=0;k<5;k++) F(id+"-c"+k+"L", {opacity:1}, {opacity:.35, duration:.18, yoyo:true, repeat:5}, c.t0+.4+k*.07);
const to = cue(0); for (let k=0;k<5;k++) F(id+"-c"+k+"L", {opacity:1}, {opacity:.06, duration:.12}, to+k*.05); IL.shake(id+"-c2", to+.2, 3, 8);""", ["andar"]))
# 3
grid = "".join(relay(250 + (k % 3) * 290, 760 + (k // 3) * 230, 180, f"r{k}") for k in range(6))
B.append(beat("Los técnicos la revisan, panel por panel.",
              svg(PA, R(110, 620, 860, 720, 20, "#2B1D10", stroke="#6B4F2E", stroke_width=6) + grid
                  + G("door", R(110, 620, 860, 720, 20, "#4A3420", stroke="#8C6A42", stroke_width=6) + C(900, 980, 22, ACC))
                  + P("M540 600 L240 1300 L840 1300 Z", "#FFE9B0", id="{id}-beam", opacity=0), gy=1000),
              """F(id+"-door", {scaleX:1, svgOrigin:"110 980"}, {scaleX:0, svgOrigin:"110 980", duration:.6, ease:"power2.inOut"}, c.t0+.3);
IL.fade(id+"-beam", c.t0+.8, .3, .18); F(id+"-beam", {rotation:-25, svgOrigin:"540 600"}, {rotation:25, svgOrigin:"540 600", duration:1.2, yoyo:true, repeat:3, ease:"sine.inOut"}, c.t0+.8);""", []))
# 4
B.append(beat("Y en el relé setenta encuentran una *polilla*.",
              svg(PA, relay(540, 1000, 620, "big") + G("mo", moth(540, 830, 95, "m", "#A88F6E", "#4A3826", "#6E5638"), op=0)
                  + G("tag", R(300, 1290, 480, 90, 45, ACC) + T(540, 1350, "RELÉ #70 · PANEL F", 34, "#2B1D10", mono=True)), gy=950),
              """IL.zoom(id+"-big", c.t0, c.t1-c.t0, 1.1); IL.in(id+"-tag", c.t0+.2, 0, 60);
IL.pop(id+"-mo", cue(0)-.1, .4); IL.shake(id+"-mo", cue(0)+.3, 4, 6); """ + flap("m", 540, 830, "cue(0)", 1.2), ["polilla"]))
# 5
tweez = G("tw", P("M700 380 L560 760 L572 764 L716 388 Z", "#C9C2B4") + P("M740 392 L590 768 L602 772 L756 400 Z", "#E8E0CC"))
B.append(beat("La sacan con una pinza y la pegan con cinta en el cuaderno de la máquina.",
              svg(PA, logpage(170, 600, 740, 820, "pg", moth_on=False) + G("mo", moth(540, 1020, 120, "m2", "#9C8466", "#4A3826", "#6E5638")) + tweez
                  + R(370, 960, 120, 40, 4, "#FFF6D8", opacity=0, id="{id}-t1", transform="rotate(-20 430 980)") + R(590, 960, 120, 40, 4, "#FFF6D8", opacity=0, id="{id}-t2", transform="rotate(20 650 980)"), gy=1000),
              """IL.in(id+"-pg", c.t0, 0, 120, .45);
F(id+"-mo", {y:-560, opacity:1}, {y:0, duration:.9, ease:"power2.inOut"}, c.t0+.3); F(id+"-tw", {y:-560}, {y:0, duration:.9, ease:"power2.inOut"}, c.t0+.3);
F(id+"-tw", {y:0, opacity:1}, {y:-700, opacity:0, duration:.5, ease:"power2.in"}, c.t0+1.4);
F(id+"-t1", {opacity:0, scale:1.6, transformOrigin:"50% 50%"}, {opacity:.85, scale:1, duration:.2}, c.t1-1.2); F(id+"-t2", {opacity:0, scale:1.6, transformOrigin:"50% 50%"}, {opacity:.85, scale:1, duration:.2}, c.t1-1.0);""", []))
# 6
B.append(beat("Al lado anotan: «primer caso *real* de {bug|bag} encontrado».",
              svg(PA, logpage(130, 600, 820, 820, "pg") + G("tr", R(170, 1460, 740, 0, 0, "none") + T(540, 1470, "«primer caso REAL de bug encontrado»", 30, SOFT, mono=True), op=0), gy=1000),
              """IL.in(id+"-pg", c.t0, 0, 80, .4); F(id+"-hcr", {attr:{width:0}}, {attr:{width:800}, duration:Math.min(1.8, c.t1-c.t0-.6), ease:"none"}, c.t0+.3);
IL.fade(id+"-tr", cue(0)-.2);""", ["real"]))
# 7
B.append(beat("¿Por qué real? Porque {bug|bag} ya era la palabra para decir *falla*.",
              svg(PA, T(540, 900, "actual", 180, "#2B3A8C", tid="w", weight=400) + E(540, 845, 330, 140, "none", id="{id}-circ", stroke=RED, stroke_width=12, stroke_dasharray=1600, stroke_dashoffset=1600)
                  + G("chip", R(250, 1120, 580, 140, 70, "#3B2A18", stroke="#6B4F2E", stroke_width=6) + T(540, 1210, "BUG = FALLA", 60, ACC, mono=True), op=0), gy=950),
              """IL.pop(id+"-w", c.t0, .4); IL.draw(id+"-circ", c.t0+.4, 1600, .7); IL.in(id+"-chip", cue(0)-.25, 0, 60); IL.pulse(id+"-chip", cue(0)+.2, 1, 1.05);""", ["falla"]))
# 8
warn = G("wa", P("M300 760 L470 1060 L130 1060 Z", "#FFB547", stroke="#2B1D10", stroke_width=10, stroke_linejoin="round") + T(300, 1030, "!", 150, "#2B1D10") + T(300, 1150, "FALLA", 44, INK, mono=True))
B.append(beat("El chiste era que esta vez la falla era un bicho *de verdad*.",
              svg(PA, warn + T(540, 960, "=", 120, SOFT, tid="eq", op=0) + G("mm", moth(780, 920, 130, "m3") + T(780, 1150, "BICHO", 44, INK, mono=True), op=0)
                  + G("ja", T(540, 1360, "JA", 120, ACC, mono=True), op=0), gy=1000),
              """IL.pop(id+"-wa", c.t0); IL.fade(id+"-eq", c.t0+.5); IL.pop(id+"-mm", c.t0+.8); """ + flap("m3", 780, 920, "c.t0+.8", 3) + """
IL.pop(id+"-ja", cue(0)); IL.shake(id+"-ja", cue(0)+.3, 5, 10);""", ["verdad"]))
# 9
bubbles = "".join(bubble(160 + k * 250, 1220 - (k % 2) * 90, 260, 110, "...la polilla", f"b{k}", PAPER, "#3B2A18", 30, "left") for k in range(3))
B.append(beat("La que hizo famosa la historia fue Grace Hopper, programadora de esa máquina.",
              svg(PA, P("M540 500 L240 1450 L840 1450 Z", "#FFE9B0", opacity=.12, id="{id}-sp") + G("card", R(170, 760, 740, 280, 30, PAPER, filter="url(#{id}-sh)")
                  + T(540, 880, "GRACE HOPPER", 72, "#2B1D10", mono=True) + T(540, 960, "programadora del Mark II", 40, "#6B4F2E")) + bubbles, gy=900),
              """IL.fade(id+"-sp", c.t0, .4, .12); IL.pop(id+"-card", c.t0+.1, .45); for (let k=0;k<3;k++) IL.pop(id+"-b"+k, cue(0)+.3+k*.3);
IL.float(id+"-card", c.t0+.5, c.t1-c.t0, 8);""", ["Hopper"]))
# 10
B.append(beat("Y esa hoja, con la polilla pegada, hoy está en un *museo*.",
              svg(PA, P("M540 480 L200 1440 L880 1440 Z", "#FFE9B0", opacity=.14) + G("fr", R(200, 640, 680, 760, 24, "#6B4F2E") + logpage(240, 680, 600, 680, "pg2")
                  + R(240, 680, 600, 680, 6, "#BFE9FF", opacity=.12)) + G("pl", R(300, 1420, 480, 70, 10, "#C9A14A") + T(540, 1468, "MUSEO · SMITHSONIAN", 28, "#2B1D10", mono=True), op=0), gy=1000),
              """IL.in(id+"-fr", c.t0, 0, 100, .5); F(id+"-hcr", {attr:{width:820}}, {attr:{width:820}, duration:.01}, c.t0); IL.pop(id+"-pl", cue(0)-.1); IL.zoom(id+"-fr", c.t0+.5, c.t1-c.t0, 1.04);""", ["museo"]))
# 11
code = "".join(R(250, 820 + k * 50, 200 + (k * 97) % 300, 20, 10, ["#C084FC", "#60A5FA", "#4ADE80", "#FFB547"][k % 4]) for k in range(7))
moths = "".join(G(f"f{k}", moth(540, 1000, 50, f"fm{k}"), op=0) for k in range(6))
B.append(beat("Mandáselo al que jura que su código no tiene {bugs|bags}.",
              svg(PA, G("lap", R(180, 760, 720, 470, 24, "#1E150C", stroke="#6B4F2E", stroke_width=8) + code + P("M120 1240 L960 1240 L900 1300 L180 1300 Z", "#6B4F2E")) + moths, gy=1000),
              """IL.in(id+"-lap", c.t0, 0, 120, .45);
const dirs = [[-380,-420],[0,-520],[380,-420],[-420,0],[420,40],[-200,-300]];
for (let k=0;k<6;k++){ const t = c.t0+.6+k*.18; F(id+"-f"+k, {opacity:0, x:0, y:0, scale:.4, transformOrigin:"50% 50%"}, {opacity:1, x:dirs[k][0], y:dirs[k][1], scale:1, duration:1.1, ease:"power2.out"}, t); }""" +
              "".join(flap(f"fm{k}", 540, 1000, f"c.t0+.6+{k}*.18", 3) for k in range(6)), []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más historias de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Historias de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """El primer bug de la historia fue un bicho de verdad 🦋

9 de septiembre de 1947, Universidad de Harvard. La computadora Mark II deja de andar. Los técnicos la revisan y, en el relé 70 del panel F, encuentran una polilla.

La sacan, la pegan con cinta en el cuaderno de la máquina y anotan: "First actual case of bug being found" (primer caso real de bug encontrado).

El chiste está en la palabra "real": "bug" ya se usaba para decir falla. Esta vez, la falla era un bicho de verdad.

La historia la hizo famosa Grace Hopper, programadora de esa máquina. La hoja, con la polilla, hoy está en el Museo Nacional de Historia Estadounidense (Smithsonian).

Mandáselo al que jura que su código no tiene bugs 🐛

Fuentes: Smithsonian · JSTOR Daily · Computing History
Video hecho con IA.

#programacion #historia #bug #tecnologia #computacion #programador #sabiasque #curiosidades"""

g = {"etiqueta": "HISTORIAS #2", "fuente": "Smithsonian · JSTOR Daily · Computing History", "acento": ACC, "tema": "editorial", "musica": "retro",
     "subtitulos": "clasico", "transiciones": ["zoom", "corte", "whip", "flash", "corte", "rise", "whip", "corte", "flash", "whip", "corte", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "bug.json"), sys.argv[1:])

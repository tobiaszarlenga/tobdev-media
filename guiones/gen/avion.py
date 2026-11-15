# Reel "¿Tu celular puede hacer caer un avión? No. Pero el modo avión no es un capricho". Uso: python3 avion.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = "cielo"; INK = PAL[PA]["ink"]; SOFT = PAL[PA]["soft"]; ACC = "#FFB547"; NAVY = "#0A2A4D"; RED = "#FF5A6E"; GRN = "#4ADE80"


def cloud(cx, cy, s, cid, op=.9):
    return G(cid, C(cx - s * .5, cy, s * .4, "#fff") + C(cx, cy - s * .25, s * .55, "#fff") + C(cx + s * .55, cy, s * .38, "#fff") + R(cx - s * .9, cy, s * 1.8, s * .4, s * .2, "#fff"), op=op)


def toggle(cx, cy, s, tid):
    return G(tid, R(cx - s, cy - s * .5, s * 2, s, s * .5, "#C9D6EA", id=f"{{id}}-{tid}bg") + C(cx - s * .5, cy, s * .42, "#fff", id=f"{{id}}-{tid}k"))


def mosquito(cx, cy, s, mid):
    return G(mid, E(cx, cy, s * .5, s * .16, "#3B3B4A") + C(cx + s * .55, cy - s * .05, s * .14, "#3B3B4A") + L(cx + s * .65, cy, cx + s * 1.05, cy + s * .2, "#3B3B4A", 4)
             + G(mid + "w", E(cx - s * .1, cy - s * .35, s * .38, s * .18, "#D5ECFF", opacity=.85, transform=f"rotate(-25 {cx} {cy})"))
             + "".join(L(cx - s * .2 + k * s * .2, cy + s * .1, cx - s * .35 + k * s * .25, cy + s * .55, "#3B3B4A", 3) for k in range(3)))


def ctower(cx, by, s, tid):
    return G(tid, R(cx - s * .12, by - s, s * .24, s, 6, "#E6EEF8") + P(f"M{cx - s * .3} {by - s} L{cx + s * .3} {by - s} L{cx + s * .22} {by - s * 1.25} L{cx - s * .22} {by - s * 1.25} Z", "#9CC3E8")
             + R(cx - s * .32, by - s * 1.32, s * .64, s * .08, 4, "#E6EEF8"))


def ground(gid="gr"):
    return G(gid, R(0, 1330, 1080, 600, 0, "#3E8E6B") + R(0, 1330, 1080, 18, 0, "#2F7357"))


B = []
# 1
B.append(beat("¿Tu celular puede hacer caer un avión? *No*.",
              svg(PA, cloud(300, 760, 160, "c1") + cloud(860, 1250, 130, "c2") + plane(540, 1000, 560, "pl", "#F4F6FF", "#60A5FA")
                  + G("no", C(540, 1000, 150, RED) + T(540, 1040, "NO", 110, "#fff", mono=True), op=0), gy=900),
              """IL.in(id+"-pl", c.t0, -700, 80, .7); IL.float(id+"-pl", c.t0+.7, c.t1-c.t0, 12);
F(id+"-c1", {x:0}, {x:-120, duration:c.t1-c.t0, ease:"none"}, c.t0); F(id+"-c2", {x:0}, {x:-160, duration:c.t1-c.t0, ease:"none"}, c.t0);
IL.pop(id+"-no", cue(0)-.05, .3, "back.out(2.4)");""", ["No"]))
# 2
B.append(beat("Pero el modo avión no es un *capricho*.",
              svg(PA, phone(330, 640, 420, 820, R(370, 760, 340, 120, 24, "#ffffff22") + plane(450, 820, 110, "ic", "#fff", "#fff")
                              + T(520, 835, "Modo avión", 32, "#fff", "start", weight=700) + toggle(560, 980, 70, "tg"), "ph", "#123B66"), gy=1000),
              """IL.in(id+"-ph", c.t0, 0, 140, .45);
F(id+"-tgk", {x:0}, {x:70, duration:.25, ease:"back.out(2)"}, cue(0)-.1); F(id+"-tgbg", {fill:"#C9D6EA"}, {fill:"#FFB547", duration:.25}, cue(0)-.1);""", ["capricho"]))
# 3
B.append(beat("Sin modo avión, el celular busca antenas *todo el tiempo*.",
              svg(PA, ground() + tower(250, 1330, 260, "t1", "#E6EEF8") + tower(830, 1330, 220, "t2", "#E6EEF8")
                  + phone(400, 700, 280, 540, "", "ph", "#123B66") + waves(540, 680, "w", 4, 60, 50, ACC, 10, -70, 70), gy=900),
              """IL.in(id+"-gr", c.t0, 0, 200, .4); IL.in(id+"-t1", c.t0+.1, 0, 200); IL.in(id+"-t2", c.t0+.2, 0, 200); IL.pop(id+"-ph", c.t0+.2);
const n = Math.max(2, Math.floor((c.t1-c.t0-.6)/.8)); for (let r=0;r<n;r++) for (let k=0;k<4;k++){ F(id+"-w"+k, {opacity:0}, {opacity:1, duration:.15}, c.t0+.5+r*.8+k*.12); F(id+"-w"+k, {opacity:1}, {opacity:0, duration:.3}, c.t0+.75+r*.8+k*.12); }""", ["todo"]))
# 4
B.append(beat("Cerca del suelo, al despegar o aterrizar, las encuentra.",
              svg(PA, ground() + tower(300, 1330, 240, "t1", "#E6EEF8") + tower(820, 1330, 200, "t2", "#E6EEF8") + plane(560, 760, 420, "pl")
                  + P("M600 800 L300 1090", id="{id}-l1", stroke=ACC, stroke_width=8, stroke_dasharray="16 14", opacity=0) + P("M640 800 L820 1130", id="{id}-l2", stroke=ACC, stroke_width=8, stroke_dasharray="16 14", opacity=0), gy=900),
              """F(id+"-pl", {x:-300, y:-260, rotation:8, transformOrigin:"50% 50%"}, {x:0, y:0, rotation:8, duration:Math.max(1, cue(0)-c.t0), ease:"power1.out"}, c.t0);
IL.fade(id+"-l1", cue(0)); IL.fade(id+"-l2", cue(0)+.15); IL.pulse(id+"-t1", cue(0)+.2, 1, 1.06); IL.pulse(id+"-t2", cue(0)+.3, 1, 1.06);""", ["encuentra"]))
# 5
B.append(beat("Y esas señales se pueden meter en los auriculares de los *pilotos*.",
              svg(PA, headset(540, 980, 420, "hs", "#F4F6FF", NAVY) + waves(540, 760, "w", 3, 60, 50, RED, 10, -40, 40)
                  + G("zz", T(820, 900, "bzz", 60, RED, mono=True) + T(240, 1060, "bzz", 50, RED, mono=True), op=0), gy=1000),
              """IL.pop(id+"-hs", c.t0, .45); for (let k=0;k<3;k++) IL.fade(id+"-w"+k, cue(0)-.2+k*.1);
IL.fade(id+"-zz", cue(0)+.1); IL.shake(id+"-hs", cue(0)+.1, 6, 8);""", ["pilotos"]))
# 6
B.append(beat("Ellos lo describen como un *mosquito* zumbando en el oído.",
              svg(PA, headset(540, 1050, 360, "hs", "#F4F6FF", NAVY) + mosquito(540, 760, 150, "m")
                  + P("M300 700 Q420 600 540 760 Q660 900 800 720", id="{id}-path", stroke="#ffffff55", stroke_width=4, stroke_dasharray="10 12"), gy=1000),
              """IL.pop(id+"-hs", c.t0, .4);
F(id+"-m", {x:-240, y:-60}, {x:260, y:-40, duration:.9, yoyo:true, repeat:Math.max(1, Math.floor((c.t1-c.t0)/.9)), ease:"sine.inOut"}, c.t0+.2);
F(id+"-mw", {scaleY:1, transformOrigin:"50% 100%"}, {scaleY:.3, duration:.04, yoyo:true, repeat:60}, c.t0); IL.pulse(id+"-m", cue(0), 2, 1.2);""", ["mosquito"]))
# 7
B.append(beat("Justo cuando están hablando con la *torre de control*.",
              svg(PA, ground() + ctower(760, 1330, 520, "ct") + bubble(130, 760, 420, 150, "Pista 2, autorizado", "bb", "#F4F6FF", NAVY, 34)
                  + G("st", "".join(L(180 + k * 36, 860 - (k * 37) % 40, 180 + k * 36, 880 + (k * 23) % 30, RED, 6) for k in range(10)), op=0), gy=900),
              """IL.in(id+"-gr", c.t0, 0, 200, .4); IL.in(id+"-ct", c.t0+.1, 0, 300, .5); IL.pop(id+"-bb", cue(0)-.2);
IL.fade(id+"-st", cue(0)+.4, .1); IL.shake(id+"-bb", cue(0)+.45, 6, 8);""", ["torre"]))
# 8
seats = "".join(R(200 + (k % 4) * 180 + (40 if k % 4 > 1 else 0), 700 + (k // 4) * 170, 120, 130, 26, "#5E9BD1") for k in range(16))
phones = "".join(R(240 + (k % 4) * 180 + (40 if k % 4 > 1 else 0), 720 + (k // 4) * 170, 40, 70, 8, ACC, id=f"{{id}}-p{k}", opacity=0) for k in range(16))
B.append(beat("Un celular solo no cambia nada. El problema es cuando son *muchos*.",
              svg(PA, R(150, 640, 820, 760, 60, "#0A2A4D") + seats + phones, gy=1000),
              """IL.fade(id+"-p5", c.t0+.4, .1); IL.pulse(id+"-p5", c.t0+.5, 2, 1.3);
for (let k=0;k<16;k++) if (k!=5) IL.fade(id+"-p"+k, cue(0)-.2+(k*7%16)*.05, .1);""", ["muchos"]))
# 9
B.append(beat("Así que ponelo. No por miedo: por los pilotos.",
              svg(PA, toggle(540, 820, 120, "tg") + headset(540, 1200, 260, "hs", "#F4F6FF", NAVY) + check(760, 1120, 44, "ok", GRN), gy=1000),
              """IL.pop(id+"-tg", c.t0, .4); F(id+"-tgk", {x:0}, {x:120, duration:.25, ease:"back.out(2)"}, c.t0+.4); F(id+"-tgbg", {fill:"#C9D6EA"}, {fill:"#FFB547", duration:.25}, c.t0+.4);
IL.in(id+"-hs", c.t0+.6, 0, 100); IL.pop(id+"-ok", c.t1-1.0);""", []))
# 10
B.append(beat("Mandáselo a quien nunca pone el modo avión.",
              svg(PA, cloud(260, 820, 150, "c1") + cloud(760, 1250, 120, "c2") + plane(540, 1000, 480, "pl") + G("ppl", P("M760 1350 l140 -60 l-50 150 l-25 -60 z", ACC), op=0), gy=900),
              """IL.in(id+"-pl", c.t0, -600, 0, .6); F(id+"-pl", {x:0}, {x:700, duration:.8, ease:"power2.in"}, c.t1-.9);
IL.pop(id+"-ppl", c.t0+.6); F(id+"-ppl", {x:0, y:0}, {x:120, y:-420, duration:.9, ease:"power2.in"}, c.t1-1.1);""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más mitos de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Mitos de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """¿Tu celular puede hacer caer un avión? No ✈️

Pero el modo avión no es un capricho. Sin él, el celular busca antenas todo el tiempo, y cerca del suelo (al despegar o aterrizar) las encuentra.

Esas señales se pueden meter en los auriculares de los pilotos: ellos lo describen como un mosquito zumbando en el oído, justo cuando están hablando con la torre de control. Un celular solo no cambia nada; el problema es cuando son muchos.

Así que ponelo. No por miedo: por los pilotos.

Mandáselo a quien nunca pone el modo avión.

Fuentes: CBS News (Minnesota Pilots Association) · Popular Science · FAA
Video hecho con IA.

#modoavion #aviones #pilotos #viajes #tecnologia #mitos #celular #curiosidades"""

g = {"etiqueta": "MITOS #4", "fuente": "CBS News · Popular Science · FAA", "acento": ACC, "tema": "noche", "musica": "suave",
     "subtitulos": "clasico", "transiciones": ["whip", "corte", "rise", "corte", "flash", "whip", "corte", "flash", "corte", "whip", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "avion.json"), sys.argv[1:])

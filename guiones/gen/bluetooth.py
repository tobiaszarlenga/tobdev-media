# Reel "El logo de Bluetooth es la firma de un rey vikingo". Uso: python3 bluetooth.py [voz1.mp3 voz2.mp3]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = "nordico"; INK = PAL[PA]["ink"]; SOFT = PAL[PA]["soft"]; ACC = "#4FC3F7"; BT = "#1E7BFF"


def logo_d(cx, cy, s):  # símbolo: ᚼ encima de ᛒ
    return f"M{cx - s * .5} {cy - s * .5} L{cx + s * .5} {cy + s * .5} L{cx} {cy + s} L{cx} {cy - s} L{cx + s * .5} {cy - s * .5} L{cx - s * .5} {cy + s * .5}"


def rune_h(cx, cy, s, rid, color=INK, sw=26):
    return G(rid, L(cx, cy - s, cx, cy + s, color, sw) + L(cx - s * .5, cy - s * .5, cx + s * .5, cy + s * .5, color, sw) + L(cx - s * .5, cy + s * .5, cx + s * .5, cy - s * .5, color, sw))


def rune_b(cx, cy, s, rid, color=INK, sw=26):
    return G(rid, L(cx, cy - s, cx, cy + s, color, sw) + P(f"M{cx} {cy - s} L{cx + s * .5} {cy - s * .5} L{cx} {cy} L{cx + s * .5} {cy + s * .5} L{cx} {cy + s}",
                                                           stroke=color, stroke_width=sw, stroke_linecap="round", stroke_linejoin="round"))


def ship(cx, cy, s, sid):
    stripes = "".join(R(cx - s * .32 + k * s * .128, cy - s * .78, s * .064, s * .56, 0, "#E04A3F") for k in range(5))
    return G(sid, P(f"M{cx - s * .7} {cy - s * .1} Q{cx} {cy + s * .35} {cx + s * .7} {cy - s * .1} L{cx + s * .55} {cy - s * .05} Q{cx} {cy + s * .12} {cx - s * .55} {cy - s * .05} Z", "#7A4A24")
             + P(f"M{cx - s * .78} {cy - s * .25} Q{cx - s * .72} {cy - s * .02} {cx - s * .6} {cy - s * .08}", stroke="#7A4A24", stroke_width=s * .05)
             + L(cx, cy - s * .08, cx, cy - s * .9, "#5A3518", s * .035) + R(cx - s * .34, cy - s * .8, s * .68, s * .6, 10, "#F3E6CC") + stripes
             + "".join(C(cx - s * .45 + k * s * .18, cy - s * .02, s * .05, "#C9A14A") for k in range(6)))


def sea(y, sid, color="#1B4E7A"):
    return G(sid, "".join(P(f"M{-40 + k * 140} {y + (k % 2) * 6} q35 -22 70 0 q35 22 70 0", stroke=color, stroke_width=10, stroke_linecap="round") for k in range(9))
             + R(0, y + 20, 1080, 260, 0, color, opacity=.35))


def king(cx, cy, s, kid, smile=False):
    crown = P(f"M{cx - s * .3} {cy - s * .26} L{cx - s * .3} {cy - s * .52} L{cx - s * .15} {cy - s * .38} L{cx} {cy - s * .58} L{cx + s * .15} {cy - s * .38} L{cx + s * .3} {cy - s * .52} L{cx + s * .3} {cy - s * .26} Z", "#FFC94A", stroke="#B8862A", stroke_width=4)
    beard = P(f"M{cx - s * .32} {cy + s * .06} Q{cx - s * .3} {cy + s * .62} {cx} {cy + s * .66} Q{cx + s * .3} {cy + s * .62} {cx + s * .32} {cy + s * .06} Q{cx} {cy + s * .34} {cx - s * .32} {cy + s * .06} Z", "#C76A2B")
    mouth = (R(cx - s * .12, cy + s * .16, s * .24, s * .1, s * .05, "#5A1E1E") + R(cx - s * .1, cy + s * .16, s * .2, s * .05, 3, "#fff")
             + R(cx + s * .02, cy + s * .16, s * .05, s * .05, 2, "#5B8BFF", id="{id}-tooth")) if smile else ""
    return person(cx, cy, s, kid, skin="#F0C39B", shirt="#3D5A80", hair="#C76A2B", extra=beard + crown + mouth)


def laptop(cx, cy, s, lid):
    return G(lid, R(cx - s * .6, cy - s * .7, s * 1.2, s * .78, 18, "#0C0F26", stroke="#3A4180", stroke_width=6) + R(cx - s * .52, cy - s * .62, s * 1.04, s * .62, 8, "url(#{id}-scr)")
             + P(f"M{cx - s * .78} {cy + s * .08} L{cx + s * .78} {cy + s * .08} L{cx + s * .7} {cy + s * .2} L{cx - s * .7} {cy + s * .2} Z", "#3A4180"))


B = []
# 1 — gancho
runes_bg = "".join(G(f"r{k}", (rune_h if k % 2 else rune_b)(x, y, 46, f"rr{k}", SOFT, 10), op=0) for k, (x, y) in enumerate([(200, 700), (880, 660), (170, 1260), (900, 1300), (300, 1450), (790, 1500)]))
B.append(beat("El logo de {Bluetooth|blútuz} es la firma de un *rey vikingo*.",
              svg(PA, runes_bg + G("ov", E(540, 1000, 200, 290, BT), op=0) + P(logo_d(540, 1000, 180), id="{id}-logo", stroke="#fff", stroke_width=36,
                  stroke_linecap="round", stroke_linejoin="round", stroke_dasharray=2400, stroke_dashoffset=2400), gy=1000, glow=BT),
              """IL.pop(id+"-ov", c.t0, .45); IL.draw(id+"-logo", c.t0+.2, 2400, 1.1);
for (let k=0;k<6;k++){ IL.fade(id+"-r"+k, c.t0+.3+k*.08, .4, .55); IL.float(id+"-r"+k, c.t0+.3, c.t1-c.t0, 14+k*3); }
IL.pulse(id+"-ov", cue(0), 2, 1.07); IL.zoom(id+"-glow", c.t0, c.t1-c.t0, 1.2);""", ["vikingo"]))
# 2 — rey Harald
B.append(beat("Hace más de mil años, Dinamarca tenía un *rey*: Harald.",
              svg(PA, sea(1330, "sea") + ship(380, 1300, 300, "ship") + king(620, 760, 270, "k") + G("tag", R(430, 1150, 380, 96, 48, ACC) + T(620, 1213, "HARALD", 50, "#04223A", mono=True), op=0), gy=900),
              """IL.in(id+"-sea", c.t0, 0, 60, .5); IL.in(id+"-ship", c.t0+.1, -500, 0, .7);
F(id+"-ship", {x:0}, {x:120, duration:c.t1-c.t0, ease:"none"}, c.t0+.8); IL.float(id+"-ship", c.t0+.8, c.t1-c.t0, 8);
IL.pop(id+"-k", Math.max(c.t0+.4, cue(0)-.1), .45); IL.pop(id+"-tag", cue(1)-.05);""", ["rey", "Harald"]))
# 3 — Diente Azul
teeth = "".join(R(330 + k * 72, 930, 62, 96, 16, "#FFF8EE", id=f"{{id}}-t{k}") for k in range(6))
B.append(beat("Le decían Harald *Diente Azul*. Se cree que por un diente muerto.",
              svg(PA, G("m", P("M240 900 Q540 820 840 900 Q820 1190 540 1210 Q260 1190 240 900 Z", "#5A1E1E") + teeth + P("M240 900 Q540 860 840 900", stroke="#C0504D", stroke_width=40, stroke_linecap="round")
                  + P("M250 940 Q540 1260 830 940", stroke="#C0504D", stroke_width=40, stroke_linecap="round"))
                  + G("lb", T(540, 1390, "BLÅTAND", 70, INK, mono=True) + T(540, 1450, "= DIENTE AZUL", 36, SOFT, mono=True), op=0) + G("sp", P("M660 840 l14 -40 l14 40 l40 14 l-40 14 l-14 40 l-14 -40 l-40 -14 Z", "#BFE9FF"), op=0), gy=1000, glow=BT),
              """IL.pop(id+"-m", c.t0, .4, "back.out(1.4)");
F(id+"-t3", {fill:"#FFF8EE"}, {fill:"#2F6BFF", duration:.35}, cue(0)); IL.pulse(id+"-t3", cue(0)+.1, 2, 1.15);
IL.pop(id+"-sp", cue(0)+.2); IL.spin(id+"-sp", cue(0)+.2, c.t1-cue(0), 180); IL.in(id+"-lb", cue(0)+.15, 0, 40);
IL.zoom(id+"-m", c.t0+.4, c.t1-c.t0, 1.05);""", ["Azul"]))
# 4 — unir Dinamarca y Noruega
dk = "M120 1060 Q160 900 300 930 Q420 950 430 1060 Q440 1200 300 1230 Q150 1240 120 1060 Z"
no = "M650 700 Q760 620 860 700 Q960 820 900 1000 Q860 1150 760 1120 Q660 1080 680 950 Q600 820 650 700 Z"
B.append(beat("Su gran logro fue *unir* Dinamarca y Noruega.",
              svg(PA, G("dk", P(dk, "#3E8E6B", stroke="#BFF2DA", stroke_width=6) + T(275, 1300, "DINAMARCA", 34, INK, mono=True))
                  + G("no", P(no, "#4E7FBF", stroke="#CFE3FF", stroke_width=6) + T(780, 1210, "NORUEGA", 34, INK, mono=True))
                  + G("crown", P("M450 860 L450 780 L495 820 L540 760 L585 820 L630 780 L630 860 Z", "#FFC94A", stroke="#B8862A", stroke_width=5), op=0), gy=1000),
              """IL.in(id+"-dk", c.t0, -400, 0, .5); IL.in(id+"-no", c.t0+.1, 400, 0, .5);
const tu = Math.max(c.t0+.6, cue(0));
F(id+"-dk", {x:0}, {x:110, duration:.5, ease:"power3.inOut"}, tu); F(id+"-no", {x:0}, {x:-90, duration:.5, ease:"power3.inOut"}, tu);
IL.pop(id+"-crown", tu+.45); IL.float(id+"-crown", tu+.8, c.t1-tu, 10);""", ["unir"]))
# 5 — sin cables
B.append(beat("A fines de los noventa, varias empresas querían conectar celulares y computadoras sin *cables*.",
              svg(PA, phone(120, 820, 260, 520, "", "ph") + laptop(760, 1110, 300, "lap")
                  + P("M380 1100 C 480 1300, 560 900, 640 1050", id="{id}-cab", stroke="#9AA6D9", stroke_width=14, stroke_linecap="round", stroke_dasharray=700, stroke_dashoffset=700)
                  + "".join(C(420 + k * 46, 1060 - 40 * math.sin(k / 4 * math.pi), 9, ACC, id=f"{{id}}-d{k}", opacity=0) for k in range(5))
                  + cross(510, 1280, 44, "x"), gy=1050),
              """IL.in(id+"-ph", c.t0, -300, 0); IL.in(id+"-lap", c.t0+.1, 300, 0); IL.draw(id+"-cab", c.t0+.5, 700, .6);
F(id+"-x", {opacity:0}, {opacity:0, duration:.01}, c.t0);
const tc = Math.max(c.t0+1.2, cue(0)-.2);
IL.pop(id+"-x", tc); IL.out(id+"-cab", tc+.35); IL.out(id+"-x", tc+.6);
for (let k=0;k<5;k++) IL.pop(id+"-d"+k, tc+.6+k*.08);""", ["cables"]))
# 6 — la novela
B.append(beat("Uno de los ingenieros venía leyendo una novela de vikingos.",
              svg(PA, G("book", R(250, 720, 580, 720, 26, "#7A2E2E", filter="url(#{id}-sh)") + R(250, 720, 40, 720, 10, "#5A1E1E") + R(320, 790, 440, 300, 16, "#0F2C48")
                  + ship(540, 1000, 240, "bs") + "".join(P(f"M{335 + k * 70} 1052 q17 -12 35 0 q17 12 35 0", stroke="#2A6FA8", stroke_width=8, stroke_linecap="round") for k in range(6)) + T(540, 1200, "NOVELA", 56, "#F3E6CC", mono=True) + T(540, 1260, "DE VIKINGOS", 40, "#E7C9A0", mono=True))
                  + G("pg", R(830, 760, 0, 640, 10, "#F3E6CC")), gy=1050),
              """IL.in(id+"-book", c.t0, 0, 120, .5); F(id+"-book", {rotation:-4, transformOrigin:"50% 50%"}, {rotation:2, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
IL.float(id+"-bs", c.t0+.4, c.t1-c.t0, 8);""", []))
# 7 — nombre provisorio
B.append(beat("Y propuso un nombre *provisorio*: {Bluetooth|blútuz}.",
              svg(PA, G("tag", R(190, 860, 700, 220, 40, "#F4F6FF", filter="url(#{id}-sh)") + C(260, 970, 26, "#0A2742") + T(570, 1000, "Bluetooth", 96, "#0A2742", tid="nm"))
                  + stamp(560, 1240, 520, 120, "PROVISORIO", "#FFB547", "st", -7, 54), gy=1000),
              """IL.pop(id+"-tag", c.t0, .45); F(id+"-tag", {rotation:-3, transformOrigin:"50% 0%"}, {rotation:3, duration:.9, yoyo:true, repeat:3, ease:"sine.inOut"}, c.t0+.4);
F(id+"-st", {opacity:0, scale:1.8, rotation:-14, transformOrigin:"50% 50%"}, {opacity:1, scale:1, rotation:0, duration:.22, ease:"power4.in"}, cue(0)-.05);""", ["provisorio"]))
# 8 — nunca lo cambiaron
years = "".join(G(f"y{k}", R(330, 820 - k * 8, 420, 300, 24, "#F4F6FF", stroke="#C9D6EA", stroke_width=4) + R(330, 820 - k * 8, 420, 70, 24, "#E25A4E") + R(330, 860 - k * 8, 420, 30, 0, "#E25A4E")
                                    + T(540, 1030 - k * 8, y, 110, "#0A2742", mono=True)) for k, y in enumerate(["2026", "2015", "2005", "1999"]))
B.append(beat("Iban a cambiarlo después. *Nunca* lo cambiaron.",
              svg(PA, G("note", R(300, 560, 480, 200, 12, "#FFE27A", transform="rotate(-4 540 660)") + T(540, 655, "cambiar el nombre", 38, "#3A2E00", weight=700) + R(370, 690, 0, 6, 3, "#3A2E00", id="{id}-strike"))
                  + years + stamp(540, 1290, 440, 130, "NUNCA", "#FF5A6E", "st", -6, 70), gy=1000),
              """IL.in(id+"-note", c.t0, 0, -80, .4);
const n = 3, d = Math.max(.25, (cue(0)-c.t0-.6)/n);
for (let k=0;k<n;k++){ const sel = id+"-y"+(3-k); F(sel, {y:0, rotation:0, opacity:1, transformOrigin:"50% 0%"}, {y:-500, rotation:-25, opacity:0, duration:d*.9, ease:"power2.in"}, c.t0+.5+k*d); }
F(id+"-st", {opacity:0, scale:1.8, rotation:-14, transformOrigin:"50% 50%"}, {opacity:1, scale:1, rotation:0, duration:.22, ease:"power4.in"}, cue(0)-.05);
IL.shake(id+"-y0", cue(0)+.15, 3, 10);""", ["Nunca"]))
# 9 — runas H y B
B.append(beat("Y el logo son sus iniciales en runas: la *H* y la *B*.",
              svg(PA, R(140, 760, 340, 520, 40, "#0A2742", stroke="#2A5A80", stroke_width=6) + R(600, 760, 340, 520, 40, "#0A2742", stroke="#2A5A80", stroke_width=6)
                  + G("h", rune_h(310, 990, 150, "hr", INK, 30), op=0) + G("b", rune_b(770, 990, 150, "br", INK, 30), op=0)
                  + T(310, 1240, "H", 64, ACC, mono=True, tid="hl", op=0) + T(770, 1240, "B", 64, ACC, mono=True, tid="bl", op=0), gy=1000),
              """IL.pop(id+"-h", cue(0)-.15); IL.fade(id+"-hl", cue(0)); IL.pop(id+"-b", cue(1)-.15); IL.fade(id+"-bl", cue(1));""", ["H", "B"]))
# 10 — encimalas
B.append(beat("Encimalas, y te queda *esto*.",
              svg(PA, G("ov", E(540, 1000, 200, 290, BT), op=0) + G("h", rune_h(540, 1000, 180, "hr", "#fff", 36)) + G("b", rune_b(540, 1000, 180, "br", "#fff", 36))
                  + "".join(C(540 + 300 * math.cos(k * .785), 1000 + 360 * math.sin(k * .785), 10, ACC, id=f"{{id}}-p{k}", opacity=0) for k in range(8)), gy=1000, glow=BT),
              """F(id+"-h", {x:-230, scale:.83, transformOrigin:"50% 50%"}, {x:0, scale:1, duration:.55, ease:"power3.inOut"}, c.t0);
F(id+"-b", {x:230, scale:.83, transformOrigin:"50% 50%"}, {x:0, scale:1, duration:.55, ease:"power3.inOut"}, c.t0);
const te = Math.max(c.t0+.6, cue(0)-.1);
IL.pop(id+"-ov", te, .4); for (let k=0;k<8;k++) F(id+"-p"+k, {opacity:0, scale:.2, transformOrigin:"50% 50%"}, {opacity:1, scale:1.4, duration:.5, ease:"power2.out"}, te+.05);
for (let k=0;k<8;k++) IL.out(id+"-p"+k, te+.6, .4); IL.zoom(id+"-glow", te, c.t1-te, 1.3); IL.pulse(id+"-ov", te+.6, 1, 1.05);""", ["esto"]))
# 11 — compartir
bud = lambda x, bid: G(bid, E(x, 1000, 70, 90, "#F4F6FF") + R(x - 22, 1060, 44, 170, 22, "#F4F6FF") + E(x, 985, 34, 44, "#C9D6EA"))
B.append(beat("Mandáselo a alguien que vive con los auriculares puestos.",
              svg(PA, bud(380, "e1") + bud(700, "e2") + "".join(G(f"n{k}", E(240 + k * 300, 800 - (k % 2) * 60, 30, 22, ACC, transform=f"rotate(-20 {240 + k * 300} {800 - (k % 2) * 60})") + R(262 + k * 300, 690 - (k % 2) * 60, 10, 110, 4, ACC), op=0) for k in range(3))
                  + G("pl", P("M480 1330 l140 -60 l-50 150 l-25 -60 z", "#FFB547"), op=0), gy=1000),
              """IL.in(id+"-e1", c.t0, -200, 0); IL.in(id+"-e2", c.t0+.1, 200, 0);
for (let k=0;k<3;k++){ IL.pop(id+"-n"+k, c.t0+.4+k*.15); IL.float(id+"-n"+k, c.t0+.5, c.t1-c.t0, 18); }
IL.pop(id+"-pl", c.t0+.8); F(id+"-pl", {x:0, y:0}, {x:260, y:-120, duration:.9, ease:"power2.in"}, c.t1-1.1);""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más historias de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Historias de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """El logo de Bluetooth es la firma de un rey vikingo 👑

Harald Gormsson gobernó Dinamarca hace más de mil años y lo apodaban "Blåtand": Diente Azul. Su gran logro fue unir Dinamarca y Noruega.

A fines de los 90, un ingeniero que estaba armando una tecnología para conectar celulares y computadoras sin cables venía leyendo una novela de vikingos y propuso "Bluetooth" como nombre provisorio. Nunca lo cambiaron.

¿Y el logo? Son sus iniciales en runas, la H (ᚼ) y la B (ᛒ), una encima de la otra.

Mandáselo a alguien que vive con los auriculares puestos 🎧

Fuente: Bluetooth SIG (bluetooth.com) · Jim Kardach (Intel)
Video hecho con IA.

#bluetooth #vikingos #historia #tecnologia #curiosidades #sabiasque #datoscuriosos #tech"""

g = {"etiqueta": "HISTORIAS #1", "fuente": "Bluetooth SIG · Jim Kardach (Intel)", "acento": ACC, "tema": "noche", "musica": "suspenso",
     "subtitulos": "bloque", "transiciones": ["whip", "corte", "flash", "whip", "corte", "corte", "flash", "whip", "corte", "flash", "whip", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "bluetooth.json"), sys.argv[1:])

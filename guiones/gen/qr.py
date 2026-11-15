# Reel "El código QR nació en una fábrica de autos, gracias a un juego de mesa". Uso: python3 qr.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = "papel"; INK = PAL[PA]["ink"]; SOFT = PAL[PA]["soft"]; ACC = "#E4572E"; BLUE = "#2F6BFF"; CARD = "#FFFFFF"


def barcode(x, y, w, h, bid, ink=INK):
    xs, out, k = x, [], 0
    while xs < x + w - 10:
        bw = [6, 10, 4, 14, 8][k % 5]
        out.append(R(xs, y, bw, h, 0, ink))
        xs += bw + [8, 5, 10, 6][k % 4]
        k += 1
    return G(bid, R(x - 30, y - 30, w + 60, h + 110, 18, CARD, filter="url(#{id}-sh)") + "".join(out) + T(x + w / 2, y + h + 60, "4 901234 567894", 34, ink, mono=True, weight=600))


def box(x, y, s, bid, label=True):
    return G(bid, R(x, y, s, s * .8, 10, "#D9A86C", stroke="#9C6B33", stroke_width=4) + R(x + s * .42, y, s * .16, s * .8, 0, "#C4914F")
             + (R(x + s * .15, y + s * .45, s * .7, s * .22, 4, CARD) + "".join(R(x + s * .2 + j * s * .07, y + s * .48, s * .03, s * .16, 0, INK) for j in range(8)) if label else ""))


def factory(cx, by, s, fid):
    roof = "".join(P(f"M{cx - s * .7 + k * s * .35} {by - s * .6} L{cx - s * .7 + k * s * .35} {by - s * .9} L{cx - s * .35 + k * s * .35} {by - s * .6} Z", "#8C98B8") for k in range(4))
    return G(fid, R(cx - s * .7, by - s * .6, s * 1.4, s * .6, 6, "#B8C2DA") + roof + R(cx + s * .45, by - s * 1.2, s * .14, s * .6, 4, "#8C98B8")
             + "".join(R(cx - s * .6 + k * s * .3, by - s * .45, s * .18, s * .16, 4, "#FFE29A") for k in range(4)) + R(cx - s * .12, by - s * .28, s * .24, s * .28, 4, "#6B7799"))


def car(cx, cy, s, cid, color=ACC):
    return G(cid, P(f"M{cx - s * .6} {cy} L{cx - s * .45} {cy - s * .25} L{cx + s * .2} {cy - s * .25} L{cx + s * .4} {cy} Z", color) + R(cx - s * .7, cy, s * 1.4, s * .3, s * .12, color)
             + C(cx - s * .38, cy + s * .32, s * .14, INK) + C(cx + s * .38, cy + s * .32, s * .14, INK) + R(cx - s * .38, cy - s * .2, s * .26, s * .17, 4, "#CFE3FF") + R(cx - s * .05, cy - s * .2, s * .22, s * .17, 4, "#CFE3FF"))


STONES = [(2, 3, 1), (3, 9, 0), (6, 6, 1), (9, 2, 0), (4, 4, 1), (8, 8, 0), (10, 10, 1), (5, 7, 0), (7, 3, 1), (2, 8, 0), (11, 5, 1), (6, 10, 0), (3, 5, 1), (9, 6, 0)]

B = []
# 1
B.append(beat("El código QR nació en una fábrica de autos, gracias a un *juego de mesa*.",
              svg(PA, qr(290, 640, 500, "q", seed=11) + G("cr", car(300, 1360, 230, "c"), op=0) + G("gb", goboard(720, 1250, 240, "g", 7, [(1, 1, 1), (3, 4, 0), (5, 2, 1), (2, 5, 0)]), op=0), gy=900),
              """IL.pop(id+"-q", c.t0, .45, "back.out(1.4)"); for (let k=0;k<6;k++) IL.fade(id+"-qm"+k, c.t0+.15+k*.06, .2);
IL.zoom(id+"-q", c.t0+.5, c.t1-c.t0, 1.05); IL.in(id+"-cr", c.t0+.6, -200, 0); IL.pop(id+"-gb", cue(0)-.1); F(id+"-gb", {rotation:-6, transformOrigin:"50% 50%"}, {rotation:6, duration:.4, yoyo:true, repeat:3}, cue(0)+.3);""", ["juego"]))
# 2
B.append(beat("Japón, principios de los noventa. Una empresa del grupo {Toyota|toióta} tenía un problema.",
              svg(PA, factory(540, 1150, 560, "f") + G("tg", R(330, 1210, 420, 90, 45, INK) + T(540, 1268, "DENSO WAVE", 40, "#fff", mono=True), op=0)
                  + G("sm", "".join(C(800 + k * 30, 420 - k * 50 + 380, 26 + k * 8, "#C9CDD8", opacity=.8) for k in range(3))), gy=950),
              """IL.in(id+"-f", c.t0, 0, 200, .5); IL.pop(id+"-tg", c.t0+.5); IL.float(id+"-sm", c.t0+.3, c.t1-c.t0, 30); IL.shake(id+"-f", cue(0), 3, 6);""", ["problema"]))
# 3
B.append(beat("Los códigos de barras guardaban muy poca información: unos *veinte* caracteres.",
              svg(PA, barcode(220, 760, 640, 300, "bc") + G("n", C(800, 1280, 110, ACC) + T(800, 1310, "20", 90, "#fff", mono=True), op=0)
                  + L(220, 900, 220, 900, ACC, 8, id="{id}-scan"), gy=950),
              """IL.in(id+"-bc", c.t0, 0, 100, .45); F(id+"-scan", {attr:{x2:220}}, {attr:{x2:860}, duration:.7, ease:"power1.inOut", yoyo:true, repeat:1}, c.t0+.5);
IL.pop(id+"-n", cue(0)-.1); IL.pulse(id+"-n", cue(0)+.3, 1, 1.1);""", ["veinte"]))
# 4
boxes = "".join(box(80 + k * 230, 1060, 190, f"b{k}") for k in range(6))
B.append(beat("Y en la fábrica había miles de piezas para *rastrear*.",
              svg(PA, R(40, 1240, 1000, 40, 20, "#6B7799") + "".join(C(90 + k * 100, 1260, 14, "#B8C2DA") for k in range(10)) + G("belt", boxes)
                  + "".join(G(f"s{k}", box(160 + (k % 4) * 200, 640 + (k // 4) * 170, 150, f"sb{k}", False), op=0) for k in range(8)), gy=1000),
              """F(id+"-belt", {x:0}, {x:-460, duration:c.t1-c.t0, ease:"none"}, c.t0);
for (let k=0;k<8;k++) IL.pop(id+"-s"+k, c.t0+.3+k*.1);""", ["rastrear"]))
# 5
B.append(beat("Un ingeniero, Masahiro Hara, jugaba al Go en el almuerzo.",
              svg(PA, goboard(190, 640, 700, "g", 13, STONES) + G("tg", R(290, 1380, 500, 86, 43, INK) + T(540, 1436, "MASAHIRO HARA", 36, "#fff", mono=True), op=0), gy=1000),
              """IL.in(id+"-g", c.t0, 0, 120, .45); for (let k=0;k<14;k++) IL.pop(id+"-gs"+k, c.t0+.4+k*(Math.max(1.2, c.t1-c.t0-1)/14), .2);
IL.pop(id+"-tg", cue(0)-.1);""", ["Hara"]))
# 6
B.append(beat("Y mirando el tablero se dio cuenta: puntos blancos y negros en una cuadrícula pueden *guardar datos*.",
              svg(PA, G("gb", goboard(190, 640, 700, "g", 13, STONES)) + G("qq", qr(240, 690, 600, "q", seed=5), op=0), gy=1000),
              """IL.zoom(id+"-gb", c.t0, 1.5, 1.04); const tq = Math.max(c.t0+.8, cue(0)-.6);
F(id+"-gb", {opacity:1, rotation:0, transformOrigin:"50% 50%"}, {opacity:0, rotation:8, duration:.5}, tq); IL.fade(id+"-qq", tq+.1, .3);
for (let k=0;k<6;k++) F(id+"-qm"+k, {opacity:0, scale:.5, transformOrigin:"50% 50%"}, {opacity:1, scale:1, duration:.3}, tq+.15+k*.07);""", ["guardar"]))
# 7
B.append(beat("Así nació el QR, en 1994.",
              svg(PA, qr(240, 640, 600, "q", seed=5) + G("yr", R(390, 1300, 300, 100, 50, ACC) + T(540, 1370, "1994", 60, "#fff", mono=True), op=0), gy=950),
              """IL.pop(id+"-q", c.t0, .4); IL.pop(id+"-yr", c.t0+.4); IL.pulse(id+"-yr", c.t0+.9, 1, 1.08);""", []))
# 8
corners = "".join(R(x, y, 210, 210, 30, "none", stroke=ACC, stroke_width=12, id=f"{{id}}-k{k}", opacity=0) for k, (x, y) in enumerate([(245, 645), (625, 645), (245, 1025)]))
brk = "".join(P(d, stroke=BLUE, stroke_width=14, stroke_linecap="round") for d in ["M180 640 L180 580 L240 580", "M840 580 L900 580 L900 640", "M180 1240 L180 1300 L240 1300", "M840 1300 L900 1300 L900 1240"])
B.append(beat("¿Y los tres cuadrados de las esquinas? Le dicen al lector *dónde* está el código y cómo está girado.",
              svg(PA, qr(240, 640, 600, "q", seed=5) + corners + G("brk", brk, op=0), gy=950),
              """IL.zoom(id+"-q", c.t0, c.t1-c.t0, 1.03); for (let k=0;k<3;k++){ IL.fade(id+"-k"+k, c.t0+.4+k*.2); IL.pulse(id+"-k"+k, c.t0+.6+k*.2, 2, 1.06); }
IL.fade(id+"-brk", cue(0)-.1); F(id+"-brk", {rotation:-18, transformOrigin:"50% 50%"}, {rotation:0, duration:.6, ease:"back.out(1.6)"}, cue(0));""", ["dónde"]))
# 9
B.append(beat("Hara eligió una proporción que casi nunca aparece impresa, para que no se *confunda* con nada.",
              svg(PA, "".join(G(f"r{k}", R(170 + k * 50, 1180 - k * 30, 0, 0, 0, "none") + doc(170 + k * 60, 650 + k * 40, 500, 640, f"d{k}", 6, CARD, "#B5AE9F", ["DIARIO", "REVISTA", "CARTEL"][k]), op=0) for k in range(3))
                  + G("fd", R(640, 1080, 260, 260, 34, INK) + R(680, 1120, 180, 180, 22, CARD) + R(720, 1160, 100, 100, 14, INK)) + T(770, 1420, "1 : 1 : 3 : 1 : 1", 34, ACC, mono=True, tid="rt", op=0), gy=1000),
              """for (let k=0;k<3;k++) IL.in(id+"-r"+k, c.t0+k*.15, -150, 0, .4); IL.pop(id+"-fd", c.t0+.7); IL.fade(id+"-rt", c.t0+.9);
IL.pulse(id+"-fd", cue(0), 2, 1.08);""", ["confunda"]))
# 10
uses = [(170, 640, "MENÚ"), (570, 640, "ENTRADA"), (170, 1040, "PAGOS"), (570, 1040, "WIFI")]
B.append(beat("Y la empresa decidió no cobrar por usarlo. Por eso hoy está en *todos lados*.",
              svg(PA, "".join(G(f"u{k}", R(x, y, 340, 360, 30, CARD, filter="url(#{id}-sh)") + qr(x + 80, y + 40, 180, f"uq{k}", 19, 3 + k) + T(x + 170, y + 300, t, 36, INK, mono=True), op=0)
                            for k, (x, y, t) in enumerate(uses)), gy=1000),
              """for (let k=0;k<4;k++) IL.pop(id+"-u"+k, c.t0+.2+k*.25); for (let k=0;k<4;k++) IL.pulse(id+"-u"+k, cue(0)+k*.08, 1, 1.06);""", ["todos"]))
# 11
B.append(beat("Mandáselo a alguien que escanea el menú del bar sin saber esto.",
              svg(PA, phone(330, 640, 420, 820, qr(400, 860, 280, "pq", 19, 9) + R(380, 1200, 320, 60, 30, ACC) + T(540, 1240, "Ver menú", 32, "#fff"), "ph", "#F7F3EA")
                  + G("pl", P("M780 1300 l140 -60 l-50 150 l-25 -60 z", ACC), op=0), gy=1000),
              """IL.in(id+"-ph", c.t0, 0, 140, .45); IL.pop(id+"-pl", c.t0+.9); F(id+"-pl", {x:0, y:0}, {x:120, y:-420, duration:.9, ease:"power2.in"}, c.t1-1.1);""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más historias de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Historias de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """El código QR nació en una fábrica de autos, gracias a un juego de mesa 🎲

A principios de los 90, en Denso Wave (del grupo Toyota) necesitaban rastrear miles de piezas, y los códigos de barras guardaban muy poca información.

Un ingeniero, Masahiro Hara, jugaba al Go en el almuerzo. Mirando el tablero se dio cuenta de que puntos blancos y negros en una cuadrícula podían guardar datos. Así nació el QR, en 1994.

Los tres cuadrados de las esquinas le dicen al lector dónde está el código y cómo está girado. Hara eligió una proporción que casi nunca aparece impresa, para que no se confunda con nada.

Y la empresa decidió no cobrar por usarlo. Por eso hoy está en todos lados.

Mandáselo a alguien que escanea el menú del bar sin saber esto 📱

Fuentes: Denso Wave · IEEE Spectrum · BBC World Service
Video hecho con IA.

#codigoqr #qr #japon #historia #tecnologia #curiosidades #sabiasque #inventos"""

g = {"etiqueta": "HISTORIAS #3", "fuente": "Denso Wave · IEEE Spectrum · BBC", "acento": ACC, "tema": "claro", "musica": "suave",
     "subtitulos": "karaoke", "transiciones": ["zoom", "whip", "corte", "rise", "whip", "corte", "flash", "corte", "whip", "rise", "corte", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "qr.json"), sys.argv[1:])

# Reel "¿Viste las rayitas de la F y la J?". Uso: python3 teclas-fj.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = dict(bg=("#03161A", "#0B3B40", "#125259"), glow="#2EE6C5", ink="#E6FFFA", soft="#8FD9CC", card="#F2FFFC", dark="#04181B", line="#1F5A5E", stars=True)
INK = PA["ink"]; SOFT = PA["soft"]; ACC = "#2EE6C5"; TOP = "#F1F5F4"; SIDE = "#AFC3BF"; KINK = "#21302F"; SKIN = "#F2C9A0"


def kcap(x, y, s, label, kid, bump=False, size=None):
    b = R(x + s * .34, y + s * .74, s * .32, s * .07, s * .035, KINK, id=f"{{id}}-{kid}b") if bump else ""
    return G(kid, R(x, y + s * .08, s, s, s * .14, SIDE) + R(x, y, s, s, s * .14, TOP, stroke=SIDE, stroke_width=3) + T(x + s / 2, y + s * .52, label, size or s * .38, KINK, mono=True, ls="0") + b)


def tip(cx, cy, r, tid, label=""):
    return G(tid, C(cx, cy, r, SKIN, stroke="#D9A57A", stroke_width=4) + E(cx, cy - r * .35, r * .55, r * .35, "#FFE3CC") + (T(cx, cy + r + 44, label, 30, INK, mono=True) if label else ""), op=0)


ROW = list("ASDFGHJKLÑ")
def homerow(y, s=76, gap=6, bumps=True, letters=ROW, pre="k"):
    x0 = 540 - (len(letters) * (s + gap) - gap) / 2
    return "".join(kcap(x0 + k * (s + gap), y, s, l, f"{pre}{k}", bumps and l in "FJ" and letters is ROW, s * .42) for k, l in enumerate(letters)), x0, s + gap


B = []
# 1
B.append(beat("¿Viste las rayitas de la F y la J en tu teclado? No son un *defecto*.",
              svg(PA, kcap(150, 820, 340, "F", "f", True) + kcap(590, 820, 340, "J", "j", True) + G("q", T(540, 1400, "?", 160, ACC, mono=True), op=0), gy=1000),
              """IL.in(id+"-f", c.t0, -300, 0, .45); IL.in(id+"-j", c.t0+.1, 300, 0, .45);
IL.pulse(id+"-fb", c.t0+.8, 3, 1.4); IL.pulse(id+"-jb", c.t0+.8, 3, 1.4); IL.pop(id+"-q", cue(0)-.1); IL.shake(id+"-q", cue(0)+.3, 4, 8);""", ["defecto"]))
# 2
B.append(beat("Son marcas para encontrar esas teclas *sin mirar*.",
              svg(PA, kcap(330, 900, 420, "F", "f", True) + G("fg", R(470, 1060, 140, 420, 70, SKIN) + E(540, 1070, 70, 40, "#FFE3CC"))
                  + C(540, 1220, 10, "none", id="{id}-rip", stroke=ACC, stroke_width=6, opacity=0) + G("ey", P("M300 640 Q540 520 780 640 Q540 760 300 640 Z", "#F2FFFC") + C(540, 640, 50, KINK)
                  + L(300, 520, 780, 760, "#FF5A6E", 14), op=0), gy=1000),
              """IL.pop(id+"-f", c.t0, .4); F(id+"-fg", {y:300, opacity:0}, {y:0, opacity:1, duration:.5, ease:"power2.out"}, c.t0+.3);
F(id+"-rip", {attr:{r:10}, opacity:1}, {attr:{r:160}, opacity:0, duration:.7}, c.t0+.8); IL.pop(id+"-ey", cue(0)-.1);""", ["sin"]))
# 3
row, x0, st = homerow(1000)
B.append(beat("Ahí van tus dedos índice: el izquierdo en la *F*, el derecho en la *J*.",
              svg(PA, G("row", row) + tip(x0 + 3 * st + 38, 1010, 40, "t3", "IZQ") + tip(x0 + 6 * st + 38, 1010, 40, "t6", "DER"), gy=1000),
              """IL.in(id+"-row", c.t0, 0, 120, .45); IL.pop(id+"-t3", cue(0)-.1); IL.pulse(id+"-k3", cue(0), 1, 1.08); IL.pop(id+"-t6", cue(1)-.1); IL.pulse(id+"-k6", cue(1), 1, 1.08);""", ["F", "J"]))
# 4
tips = "".join(tip(x0 + k * st + 38, 1010, 36 if k in (3, 6) else 32, f"t{k}") for k in (0, 1, 2, 3, 6, 7, 8, 9))
B.append(beat("Y los demás dedos se acomodan solos en la fila del *medio*.",
              svg(PA, G("row", homerow(860, letters=list("QWERTYUIOP"), pre="q")[0] + homerow(1000)[0] + homerow(1140, letters=list("ZXCVBNM,.-"), pre="z")[0]) + tips, gy=1000),
              """IL.fade(id+"-row", c.t0, .3); for (const k of [3,6]) IL.pop(id+"-t"+k, c.t0+.1);
const ord = [2,7,1,8,0,9]; for (let i=0;i<6;i++) IL.pop(id+"-t"+ord[i], c.t0+.6+i*.15);""", ["medio"]))
# 5
B.append(beat("Se llama escribir al *tacto*: así se tipea rápido sin mirar el teclado.",
              svg(PA, browser(130, 620, 820, 420, R(130, 710, 820, 330, 0, "#F2FFFC")
                              + f'<clipPath id="{{id}}-tc"><rect id="{{id}}-tcr" x="160" y="760" width="0" height="80"/></clipPath>'
                              + f'<g clip-path="url(#{{id}}-tc)">{T(180, 820, "Hola, ¿cómo va todo por allá?", 42, KINK, "start", weight=700, ls="0")}</g>'
                              + R(180, 840, 4, 0, 0, KINK), "w", "notas")
                  + G("row", homerow(1180, 74, 6)[0]), gy=1000),
              """IL.in(id+"-w", c.t0, 0, 100, .4); IL.in(id+"-row", c.t0+.1, 0, 120, .4);
F(id+"-tcr", {attr:{width:0}}, {attr:{width:760}, duration:Math.min(2.2, c.t1-c.t0-.6), ease:"steps(28)"}, c.t0+.5);
for (let k=0;k<10;k++) F(id+"-k"+k, {y:0}, {y:8, duration:.06, yoyo:true, repeat:1}, c.t0+.6+((k*7)%10)*.18);""", ["tacto"]))
# 6
pad = "".join(kcap(330 + (k % 3) * 145, 680 + (k // 3) * 145, 130, str(7 - (k // 3) * 3 + (k % 3)), f"n{k}", k == 4) for k in range(9))
B.append(beat("El cinco del teclado numérico también tiene su marca, por la misma razón.",
              svg(PA, G("pad", pad + kcap(330, 1115, 275, "0", "n9") + kcap(620, 1115, 130, ".", "n10")), gy=1000),
              """IL.in(id+"-pad", c.t0, 0, 120, .45); IL.pulse(id+"-n4", cue(0)-.1, 2, 1.1); IL.pulse(id+"-n4b", cue(0), 3, 1.5);""", ["cinco"]))
# 7
row2, x2, st2 = homerow(1000)
B.append(beat("Mandáselo a alguien que escribe con dos dedos mirando el teclado.",
              svg(PA, G("row", row2) + tip(x2 + 2 * st2 + 38, 900, 40, "a") + tip(x2 + 7 * st2 + 38, 900, 40, "b") + G("pl", P("M780 1330 l140 -60 l-50 150 l-25 -60 z", ACC), op=0), gy=1000),
              """IL.in(id+"-row", c.t0, 0, 120, .4); IL.fade(id+"-a", c.t0+.3); IL.fade(id+"-b", c.t0+.3);
const xs = [-300, 120, -60, 260, -200, 40]; for (let i=0;i<6;i++){ F(id+"-a", {x:i?xs[i-1]:0, y:0}, {x:xs[i], y:-40, duration:.12, yoyo:true, repeat:1}, c.t0+.6+i*.35); F(id+"-b", {x:i?-xs[i-1]:0, y:0}, {x:-xs[i], y:-40, duration:.12, yoyo:true, repeat:1}, c.t0+.78+i*.35); }
IL.pop(id+"-pl", c.t0+1.0); F(id+"-pl", {x:0, y:0}, {x:120, y:-420, duration:.9, ease:"power2.in"}, c.t1-1.1);""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más curiosidades de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Curiosidades de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """¿Viste las rayitas de la F y la J en tu teclado? No son un defecto ⌨️

Son marcas para encontrar esas teclas sin mirar. Ahí van tus dedos índice: el izquierdo en la F y el derecho en la J. Los demás dedos se acomodan solos en la fila del medio.

Se llama escribir al tacto: así se tipea rápido sin mirar el teclado. Y el 5 del teclado numérico también tiene su marca, por la misma razón.

Mandáselo a alguien que escribe con dos dedos mirando el teclado 😅

Video hecho con IA.

#teclado #tips #tecnologia #curiosidades #computacion #productividad #sabiasque #datoscuriosos"""

g = {"etiqueta": "CURIOSIDADES #1", "fuente": "Computer Hope · Mental Floss", "acento": ACC, "tema": "noche", "musica": "tech",
     "subtitulos": "bloque", "transiciones": ["whip", "corte", "flash", "corte", "whip", "flash", "corte", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "teclas-fj.json"), sys.argv[1:])

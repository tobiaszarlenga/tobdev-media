# Reel "El modo incógnito no te hace invisible". Uso: python3 incognito.py [voces...]
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plantilla"))
from ilu import *

PA = "espia"; INK = PAL[PA]["ink"]; SOFT = PAL[PA]["soft"]; ACC = "#B266FF"; DK = "#120A1F"; GRN = "#4ADE80"


def eye(cx, cy, s, eid, white="#F5F0FF", iris=ACC):
    return G(eid, P(f"M{cx - s} {cy} Q{cx} {cy - s * .9} {cx + s} {cy} Q{cx} {cy + s * .9} {cx - s} {cy} Z", white, stroke=DK, stroke_width=s * .08)
             + C(cx, cy, s * .38, iris) + C(cx, cy, s * .17, DK) + C(cx + s * .1, cy - s * .1, s * .07, "#fff"))


def spy(cx, cy, s, sid, color=INK):
    return G(sid, P(f"M{cx - s} {cy - s * .1} L{cx + s} {cy - s * .1} L{cx + s * .55} {cy - s * .25} L{cx + s * .4} {cy - s * .75} Q{cx} {cy - s * .9} {cx - s * .4} {cy - s * .75} L{cx - s * .55} {cy - s * .25} Z", color)
             + C(cx - s * .42, cy + s * .3, s * .3, "none", stroke=color, stroke_width=s * .1) + C(cx + s * .42, cy + s * .3, s * .3, "none", stroke=color, stroke_width=s * .1)
             + L(cx - s * .12, cy + s * .3, cx + s * .12, cy + s * .3, color, s * .08))


def router(cx, cy, s, rid):
    return G(rid, R(cx - s * .6, cy - s * .2, s * 1.2, s * .4, s * .1, "#2A1A45", stroke=SOFT, stroke_width=6) + L(cx - s * .4, cy - s * .2, cx - s * .5, cy - s * .7, SOFT, 10)
             + L(cx + s * .4, cy - s * .2, cx + s * .5, cy - s * .7, SOFT, 10) + "".join(C(cx - s * .35 + k * s * .18, cy, s * .05, GRN if k < 3 else "#FFB547") for k in range(5)))


def gavel(cx, cy, s, gid):
    return G(gid, R(cx - s * .5, cy - s * .2, s, s * .4, s * .1, "#C9A06A", transform=f"rotate(-30 {cx} {cy})") + R(cx - s * .06, cy, s * .12, s * .9, s * .05, "#8C6A42", transform=f"rotate(-30 {cx} {cy})"))


def court(cx, by, s, cid):
    return G(cid, P(f"M{cx - s * .7} {by - s * .95} L{cx} {by - s * 1.3} L{cx + s * .7} {by - s * .95} Z", "#E7DBFF") + "".join(R(cx - s * .58 + k * s * .3, by - s * .9, s * .14, s * .8, 4, "#E7DBFF") for k in range(5))
             + R(cx - s * .75, by - s * .12, s * 1.5, s * .12, 4, "#E7DBFF"))


B = []
# 1
B.append(beat("El modo incógnito no te hace *invisible*.",
              svg(PA, browser(140, 700, 800, 620, R(140, 790, 800, 530, 0, "#1E1233") + spy(540, 1010, 150, "sp") + T(540, 1230, "Estás en modo incógnito", 34, SOFT, weight=600), "w", "nueva pestaña", bar="#120A1F", body="#1E1233")
                  + "".join(G(f"e{k}", eye(x, y, 60, f"ee{k}"), op=0) for k, (x, y) in enumerate([(180, 560), (900, 600), (160, 1420), (920, 1400)])), gy=1000),
              """IL.in(id+"-w", c.t0, 0, 100, .45); IL.pop(id+"-sp", c.t0+.3);
for (let k=0;k<4;k++){ IL.pop(id+"-e"+k, cue(0)-.1+k*.1); F(id+"-ee"+k, {scaleY:1, transformOrigin:"50% 50%"}, {scaleY:.1, duration:.08, yoyo:true, repeat:1}, cue(0)+.6+k*.15); }""", ["invisible"]))
# 2
hist = "".join(G(f"h{k}", R(180, 860 + k * 100, 720, 76, 18, "#2A1A45") + C(225, 898 + k * 100, 16, SOFT) + R(260, 888 + k * 100, 300 + (k * 83) % 280, 20, 10, SOFT)) for k in range(5))
B.append(beat("Lo único que hace es no guardar el historial en *tu* dispositivo.",
              svg(PA, T(540, 800, "HISTORIAL", 44, INK, mono=True, tid="tt") + hist + check(540, 1430, 50, "ok", GRN), gy=1050),
              """IL.fade(id+"-tt", c.t0); for (let k=0;k<5;k++) IL.in(id+"-h"+k, c.t0+.1+k*.07, -200, 0, .35);
for (let k=0;k<5;k++) F(id+"-h"+k, {opacity:1, x:0}, {opacity:0, x:300, duration:.25, ease:"power2.in"}, c.t0+1.0+k*.12);
IL.pop(id+"-ok", cue(0));""", ["tu"]))
# 3
B.append(beat("Pero afuera de tu celular, hay muchos que te siguen *viendo*.",
              svg(PA, phone(380, 760, 320, 640, spy(540, 1080, 90, "ps"), "ph") + "".join(G(f"e{k}", eye(540 + 380 * math.cos(a), 1080 + 420 * math.sin(a), 70, f"ee{k}"), op=0)
                                                                                  for k, a in enumerate([math.radians(d) for d in (-150, -90, -30, 30, 150, 90)])), gy=1080),
              """IL.pop(id+"-ph", c.t0, .4); for (let k=0;k<6;k++) IL.pop(id+"-e"+k, cue(0)-.3+k*.08);
for (let k=0;k<6;k++) F(id+"-ee"+k, {x:0}, {x:k%2?10:-10, duration:.5, yoyo:true, repeat:3, ease:"sine.inOut"}, cue(0)+.4);""", ["viendo"]))
# 4
B.append(beat("Tu proveedor de internet sabe a qué *sitios* entrás.",
              svg(PA, router(540, 760, 300, "r") + waves(540, 660, "wv", 3, 50, 45, ACC, 10) + P("M540 860 L540 1060", id="{id}-ln", stroke=SOFT, stroke_width=8, stroke_dasharray="16 14")
                  + browser(220, 1080, 640, 330, "".join(T(540, 1230 + k * 60, u, 34, DK, mono=True, weight=700, tid=f"u{k}", op=0) for k, u in enumerate(["youtube.com", "mercadolibre.com"])), "b", "")
                  + G("ey", eye(860, 760, 70, "eye"), op=0) + T(540, 1475, "TU PROVEEDOR DE INTERNET", 34, INK, mono=True, tid="lb", op=0), gy=950),
              """IL.pop(id+"-r", c.t0); for (let k=0;k<3;k++) IL.fade(id+"-wv"+k, c.t0+.3+k*.12); IL.in(id+"-b", c.t0+.2, 0, 80); IL.fade(id+"-lb", c.t0+.2);
IL.pop(id+"-ey", cue(0)-.2); IL.fade(id+"-u0", cue(0)); IL.fade(id+"-u1", cue(0)+.4);""", ["sitios"]))
# 5
cap = G("cap", P("M640 860 L800 800 L960 860 L800 920 Z", "#E7DBFF") + R(720, 880, 160, 90, 20, "#E7DBFF") + L(930, 860, 930, 960, "#FFB547", 8))
office = G("of", R(190, 760, 260, 560, 12, "#3A2560") + "".join(R(215 + (k % 3) * 75, 790 + (k // 3) * 90, 55, 60, 6, "#FFD27A" if k % 4 else "#2A1A45") for k in range(15)))
B.append(beat("Si usás el {wifi|uaifai} del trabajo o de la facultad, ellos también.",
              svg(PA, office + T(320, 1380, "TRABAJO", 34, INK, mono=True) + cap + T(800, 1100, "FACULTAD", 34, INK, mono=True)
                  + waves(320, 700, "w1", 3, 40, 40, ACC, 9) + waves(800, 740, "w2", 3, 40, 40, ACC, 9) + G("ey", eye(590, 1250, 80, "eye"), op=0), gy=1000),
              """IL.in(id+"-of", c.t0, 0, 160); IL.pop(id+"-cap", c.t0+.2);
for (let k=0;k<3;k++){ IL.fade(id+"-w1"+k, c.t0+.4+k*.12); IL.fade(id+"-w2"+k, c.t0+.5+k*.12); }
IL.pop(id+"-ey", cue(0)); F(id+"-eye", {scaleY:1, transformOrigin:"50% 50%"}, {scaleY:.1, duration:.08, yoyo:true, repeat:1}, cue(0)+.6);""", ["también"]))
# 6
sites = "".join(G(f"s{k}", browser(150 + k * 80, 720 + k * 160, 620, 420, R(150 + k * 80, 810 + k * 160, 620, 330, 0, "#F5F0FF") + R(190 + k * 80, 850 + k * 160, 300, 30, 15, "#C9B8F0")
                                   + R(190 + k * 80, 900 + k * 160, 440, 20, 10, "#E1D6FA"), f"bw{k}", ["tienda.com", "noticias.com", "videos.com"][k]), op=0) for k in range(3))
B.append(beat("Y las páginas que visitás saben que *entraste*.",
              svg(PA, sites + G("ey", eye(800, 1300, 80, "eye"), op=0), gy=1000),
              """for (let k=0;k<3;k++) F(id+"-s"+k, {opacity:0, y:80}, {opacity:1, y:0, duration:.35, ease:"power3.out"}, c.t0+k*.2);
IL.pop(id+"-ey", cue(0)-.1);""", ["entraste"]))
# 7
rows = ["los sitios que visitás", "tu empleador o institución educativa", "tu proveedor de internet"]
B.append(beat("Lo avisa el propio {Chrome|crom} cuando abrís una pestaña de incógnito.",
              svg(PA, browser(110, 640, 860, 800, R(110, 730, 860, 710, 0, "#1E1233") + spy(540, 860, 80, "sp") + T(540, 1010, "Tu actividad podría seguir", 38, INK, weight=700)
                              + T(540, 1060, "siendo visible para:", 38, INK, weight=700)
                              + "".join(G(f"r{k}", C(190, 1150 + k * 80, 10, ACC) + T(220, 1162 + k * 80, t, 32, SOFT, "start", weight=600), op=0) for k, t in enumerate(rows)), "w", "incógnito", bar="#120A1F", body="#1E1233"), gy=1000),
              """IL.in(id+"-w", c.t0, 0, 100, .45); for (let k=0;k<3;k++) IL.in(id+"-r"+k, c.t0+.6+k*.3, -60, 0, .35);""", []))
# 8
recs = "".join(R(620 + (k % 3) * 70, 1180 - (k // 3) * 46, 60, 38, 6, "#E7DBFF", id=f"{{id}}-k{k}") for k in range(15))
B.append(beat("Y en 2024, {Google|gúgol} aceptó *borrar* miles de millones de registros de navegación en incógnito, para cerrar un juicio.",
              svg(PA, court(340, 1260, 300, "ct") + gavel(360, 780, 200, "gv") + recs + T(760, 1290, "REGISTROS", 30, SOFT, mono=True)
                  + G("yr", R(620, 600, 300, 100, 50, ACC) + T(770, 670, "2024", 56, "#fff", mono=True), op=0), gy=1000),
              """IL.in(id+"-ct", c.t0, 0, 160, .45); IL.pop(id+"-yr", c.t0+.2);
F(id+"-gv", {rotation:0, svgOrigin:"360 780"}, {rotation:-25, svgOrigin:"360 780", duration:.15, yoyo:true, repeat:3}, c.t0+.8);
const tb = cue(0); for (let k=14;k>=0;k--) F(id+"-k"+k, {opacity:1, y:0, rotation:0, transformOrigin:"50% 50%"}, {opacity:0, y:-200-(k%5)*40, rotation:(k%2?40:-40), duration:.45, ease:"power2.in"}, tb+(14-k)*.06);""", ["borrar"]))
# 9
B.append(beat("Sirve para no dejar rastro en una compu prestada. Para *esconderte*, no.",
              svg(PA, G("lp", R(150, 720, 380, 260, 18, "#2A1A45", stroke=SOFT, stroke_width=6) + P("M110 990 L570 990 L540 1030 L140 1030 Z", SOFT)) + check(340, 1150, 50, "ok", GRN)
                  + G("ey", eye(760, 850, 110, "eye")) + cross(760, 1150, 50, "no"), gy=1000),
              """IL.in(id+"-lp", c.t0, -200, 0); IL.pop(id+"-ok", c.t0+.5); IL.in(id+"-ey", c.t0+.6, 200, 0); IL.pop(id+"-no", cue(0)); IL.shake(id+"-ey", cue(0)+.2, 4, 10);""", ["esconderte"]))
# 10
B.append(beat("Mandáselo a quien cree que el incógnito lo protege de todo.",
              svg(PA, spy(540, 960, 200, "sp") + G("sh", P("M540 1180 L700 1250 L700 1360 Q700 1450 540 1500 Q380 1450 380 1360 L380 1250 Z", "none", stroke=ACC, stroke_width=12)) + cross(700, 1260, 40, "x")
                  + G("pl", P("M760 1330 l140 -60 l-50 150 l-25 -60 z", "#FFB547"), op=0), gy=1050),
              """IL.pop(id+"-sp", c.t0); IL.draw(id+"-sh", c.t0+.2); IL.pop(id+"-x", c.t0+.8); IL.pop(id+"-pl", c.t0+1.0);
F(id+"-pl", {x:0, y:0}, {x:120, y:-420, duration:.9, ease:"power2.in"}, c.t1-1.1);""", []))
B.append({"texto": "Seguí a {@tobdev.ia|tob dev} para más mitos de la tecnología.",
          "escena": {"tipo": "cierre", "sub": "Mitos de la tecnología", "cta": "Seguí a @tobdev.ia"}})

CAPTION = """El modo incógnito no te hace invisible 🕵️

Lo único que hace es no guardar tu historial, cookies y datos de formularios en tu dispositivo. Pero afuera de tu celular o compu te siguen viendo:

👁️ Tu proveedor de internet sabe a qué sitios entrás
👁️ Si usás el wifi del trabajo o de la facultad, ellos también
👁️ Las páginas que visitás saben que entraste

Lo avisa el propio Chrome cuando abrís una pestaña de incógnito. Y en 2024, Google aceptó borrar miles de millones de registros de navegación en incógnito para cerrar un juicio en Estados Unidos.

Sirve para no dejar rastro en una compu prestada. Para esconderte, no.

Mandáselo a quien cree que el incógnito lo protege de todo.

Fuentes: Ayuda de Google Chrome · Brown v. Google (acuerdo de abril de 2024)
Video hecho con IA.

#privacidad #incognito #google #chrome #ciberseguridad #tecnologia #mitos #internet"""

g = {"etiqueta": "MITOS #3", "fuente": "Ayuda de Google Chrome · Brown v. Google (2024)", "acento": ACC, "tema": "neon", "musica": "tech",
     "subtitulos": "bloque", "transiciones": ["whip", "flash", "corte", "whip", "corte", "flash", "whip", "corte", "flash", "whip", "corte"],
     "caption": CAPTION, "beats": B}
guardar(g, os.path.join(os.path.dirname(__file__), "..", "incognito.json"), sys.argv[1:])

"""Piezas para escenas `ilustracion` (SVG 1080x1920 + GSAP). Uso: from ilu import *.

Cada función devuelve un string SVG. `{id}` queda literal: el motor lo cambia por el id de la escena, así los
ids no chocan entre escenas. Las animaciones van en `anim` (JS) con F() o con los atajos IL.* del motor:
IL.pop(sel,t) · IL.in(sel,t,dx,dy) · IL.out(sel,t) · IL.fade(sel,t) · IL.draw(sel,t,largo,dur) · IL.shake(sel,t)
IL.float(sel,t,dur) · IL.spin(sel,t,dur,grados) · IL.zoom(sel,t,dur,k) · IL.pulse(sel,t,veces)
Selectores: id+"-algo" (id ya trae el #).
"""
import json, math, os, sys

PAL = {  # fondo (3 paradas), brillo, tinta, tinta suave, tarjeta, oscuro, línea
    "noche":   dict(bg=("#070A1F", "#161A44", "#2B1747"), glow="#6D5BFF", ink="#E8ECFF", soft="#8FA0FF", card="#F4F6FF", dark="#0C0F26", line="#3A4180", stars=True),
    "nordico": dict(bg=("#03101C", "#0A2742", "#10395A"), glow="#4FC3F7", ink="#E6F6FF", soft="#7FB9DA", card="#EAF6FF", dark="#06182A", line="#2A5A80", stars=True),
    "sepia":   dict(bg=("#160F08", "#2B1D10", "#3B2815"), glow="#FFB547", ink="#F6E7CF", soft="#C9A97A", card="#F3E6CC", dark="#1E150C", line="#6B4F2E", stars=False),
    "alarma":  dict(bg=("#110306", "#26090F", "#360C13"), glow="#FF3B4E", ink="#FFE8EA", soft="#FF9AA5", card="#FFF1F2", dark="#16070A", line="#6E1F2A", stars=False),
    "espia":   dict(bg=("#06030E", "#170D2A", "#27103C"), glow="#B266FF", ink="#F1E8FF", soft="#B9A2E0", card="#F5F0FF", dark="#0E0818", line="#4A2F70", stars=True),
    "papel":   dict(bg=("#F7F3EA", "#EFE8D8", "#E4D9C2"), glow="#FFC85A", ink="#1C1A16", soft="#6B6457", card="#FFFFFF", dark="#1C1A16", line="#CFC4AC", stars=False),
    "retro":   dict(bg=("#020904", "#061D10", "#0A2B17"), glow="#39FF88", ink="#D8FFE6", soft="#6FD39A", card="#E9E4D4", dark="#04140A", line="#1F5A35", stars=False),
    "cielo":   dict(bg=("#082C55", "#1F5E9E", "#6FB2E8"), glow="#FFFFFF", ink="#FFFFFF", soft="#D5ECFF", card="#FFFFFF", dark="#0A2A4D", line="#5E9BD1", stars=False),
}
COL = ["#FF6B6B", "#60A5FA", "#4ADE80", "#C084FC", "#F472B6", "#FFB547", "#22D3EE", "#F97316"]


def _a(kw):
    return "".join(f' {k.rstrip("_").replace("_", "-")}="{v}"' for k, v in kw.items() if v is not None)


def R(x, y, w, h, rx=0, fill="#fff", **kw): return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" fill="{fill}"{_a(kw)}/>'
def C(cx, cy, r, fill="#fff", **kw): return f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}"{_a(kw)}/>'
def E(cx, cy, rx, ry, fill="#fff", **kw): return f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" fill="{fill}"{_a(kw)}/>'
def P(d, fill="none", **kw): return f'<path d="{d}" fill="{fill}"{_a(kw)}/>'
def L(x1, y1, x2, y2, stroke="#fff", sw=6, **kw): return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"{_a(kw)}/>'


def G(gid, inner, op=None, tr=None):
    i = f' id="{{id}}-{gid}"' if gid else ""
    return f'<g{i}{f" opacity=\"{op}\"" if op is not None else ""}{f" transform=\"{tr}\"" if tr else ""}>{inner}</g>'


def T(x, y, txt, size=34, color="#E8ECFF", anchor="middle", tid="", weight=800, mono=False, op=None, ls=None):
    fam = "JetBrains Mono, monospace" if mono else "inherit"
    i = f' id="{{id}}-{tid}"' if tid else ""
    ls = ls if ls is not None else (".08em" if mono else "-.01em")
    return (f'<text{i} x="{x:g}" y="{y:g}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}" '
            f'font-family="{fam}" letter-spacing="{ls}"{f" opacity=\"{op}\"" if op is not None else ""}>{txt}</text>')


def svg(pal, body, gx=540, gy=1000, glow=None, grid=False):
    p = PAL[pal] if isinstance(pal, str) else pal
    stars = "".join(C((i * 397) % 1080, (i * 211) % 560 + 40, 1.2 + (i % 3) * .7, "#fff", opacity=round(.15 + (i % 4) * .1, 2))
                    for i in range(34)) if p.get("stars") else ""
    gr = "".join(L(x, 0, x, 1920, p["line"], 1.5, opacity=.35) for x in range(60, 1080, 120)) + \
         "".join(L(0, y, 1080, y, p["line"], 1.5, opacity=.35) for y in range(40, 1920, 120)) if grid else ""
    return (f'<svg viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg"><defs>'
            f'<linearGradient id="{{id}}-bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p["bg"][0]}"/>'
            f'<stop offset=".5" stop-color="{p["bg"][1]}"/><stop offset="1" stop-color="{p["bg"][2]}"/></linearGradient>'
            f'<radialGradient id="{{id}}-gl"><stop offset="0" stop-color="{glow or p["glow"]}" stop-opacity=".5"/>'
            f'<stop offset="1" stop-color="{glow or p["glow"]}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="{{id}}-scr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22307A"/><stop offset="1" stop-color="#3B2470"/></linearGradient>'
            f'<filter id="{{id}}-sh" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="24" stdDeviation="26" flood-color="#000" flood-opacity=".4"/></filter>'
            f'</defs><rect width="1080" height="1920" fill="url(#{{id}}-bg)"/>{gr}{stars}'
            f'<circle id="{{id}}-glow" cx="{gx}" cy="{gy}" r="620" fill="url(#{{id}}-gl)"/>{body}</svg>')


# ---------- objetos ----------
def phone(x, y, w=420, h=860, inner="", sid="ph", screen=None):
    fill = screen or "url(#{id}-scr)"
    return (f'<g id="{{id}}-{sid}" filter="url(#{{id}}-sh)">' + R(x, y, w, h, 64, "#0C0F26", stroke="#3A4180", stroke_width=6) +
            f'<clipPath id="{{id}}-{sid}c">{R(x + 18, y + 18, w - 36, h - 36, 48)}</clipPath>'
            f'<g clip-path="url(#{{id}}-{sid}c)">{R(x + 18, y + 18, w - 36, h - 36, 0, fill)}{inner}</g>'
            + R(x + w / 2 - 60, y + 30, 120, 30, 15, "#05060F") + '</g>')


def browser(x, y, w, h, inner="", sid="br", url="", bar="#1B1F3B", body="#F4F6FF", urlc="#9AA6D9"):
    return (f'<g id="{{id}}-{sid}" filter="url(#{{id}}-sh)">' + R(x, y, w, h, 28, body) +
            f'<clipPath id="{{id}}-{sid}c">{R(x, y, w, h, 28)}</clipPath><g clip-path="url(#{{id}}-{sid}c)">'
            + R(x, y, w, 90, 0, bar) + "".join(C(x + 44 + k * 34, y + 45, 10, c) for k, c in enumerate(("#FF6B6B", "#FFB547", "#4ADE80")))
            + R(x + 160, y + 22, w - 200, 46, 23, "#000", opacity=.25) + T(x + 190, y + 55, url, 24, urlc, "start", mono=True, weight=600, ls="0")
            + inner + '</g></g>')


def card(x, y, w, h, color, cid, extra=""):
    return (f'<g id="{{id}}-{cid}">' + R(x, y, w, h, 34, "#F4F6FF") + R(x, y, w, h * .2, 34, color) + R(x, y + h * .12, w, h * .08, 0, color) +
            R(x + 28, y + h * .3, w * .55, 22, 11, "#CBD2F0") + R(x + 28, y + h * .3 + 42, w * .75, 22, 11, "#E0E5FA") +
            R(x + 28, y + h * .3 + 84, w * .62, 22, 11, "#E0E5FA") + R(x + 28, y + h * .62, w - 56, h * .26, 22, color, opacity=.28) + extra + '</g>')


def doc(x, y, w, h, did, n=6, paper="#F3E6CC", ink="#9C8461", title=""):
    ls = "".join(R(x + 50, y + 130 + k * 62, (w - 100) * (.55 + ((k * 37) % 40) / 100), 16, 8, ink, opacity=.55) for k in range(n))
    return (f'<g id="{{id}}-{did}">' + R(x, y, w, h, 18, paper, filter="url(#{id}-sh)") +
            (T(x + 50, y + 90, title, 34, ink, "start", mono=True, weight=700) if title else "") + ls + '</g>')


def key(x, y, w, h, label, kid, top="#F2EEE3", side="#B9B2A0", ink="#3A372F", size=40):
    return (f'<g id="{{id}}-{kid}">' + R(x, y + 14, w, h, 22, side) + f'<g id="{{id}}-{kid}t">' + R(x, y, w, h, 22, top, stroke=side, stroke_width=3) +
            T(x + w / 2, y + h / 2 + size * .36, label, size, ink, weight=800, mono=True, ls="0") + '</g></g>')


def lock(cx, cy, s, lid, body="#FFB547", shackle="#E8ECFF", hole="#3A2600"):
    return (f'<g id="{{id}}-{lid}"><g id="{{id}}-{lid}s">' +
            P(f"M{cx - s * .3} {cy} V{cy - s * .35} A{s * .3} {s * .3} 0 0 1 {cx + s * .3} {cy - s * .35} V{cy}", stroke=shackle, stroke_width=s * .1) +
            '</g>' + R(cx - s * .45, cy - s * .05, s * .9, s * .7, s * .12, body) + C(cx, cy + s * .22, s * .08, hole) +
            R(cx - s * .03, cy + s * .25, s * .06, s * .16, s * .03, hole) + '</g>')


def waves(cx, cy, wid, n=3, r0=60, dr=55, color="#4FD1FF", sw=10, a0=-50, a1=50):
    out = []
    for k in range(n):
        r = r0 + k * dr
        x0, y0 = cx + r * math.sin(math.radians(a0)), cy - r * math.cos(math.radians(a0))
        x1, y1 = cx + r * math.sin(math.radians(a1)), cy - r * math.cos(math.radians(a1))
        out.append(P(f"M{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f}", id=f"{{id}}-{wid}{k}", stroke=color, stroke_width=sw, stroke_linecap="round", opacity=0))
    return "".join(out)


def tower(cx, by, h, tid, color="#C9D1FF"):
    return (f'<g id="{{id}}-{tid}">' + P(f"M{cx - h * .22} {by} L{cx} {by - h} L{cx + h * .22} {by}", stroke=color, stroke_width=10, stroke_linejoin="round") +
            "".join(L(cx - h * .22 * (1 - f), by - h * f, cx + h * .22 * (1 - f), by - h * f, color, 6) for f in (.25, .5, .75)) +
            C(cx, by - h, 14, color) + '</g>')


def plane(cx, cy, s, pid, color="#F4F6FF", accent="#60A5FA"):
    return (f'<g id="{{id}}-{pid}">' + E(cx, cy, s * .62, s * .1, color) + P(f"M{cx - s * .1} {cy} L{cx - s * .32} {cy - s * .42} L{cx - s * .18} {cy - s * .42} L{cx + s * .14} {cy} Z", color) +
            P(f"M{cx - s * .1} {cy} L{cx - s * .32} {cy + s * .42} L{cx - s * .18} {cy + s * .42} L{cx + s * .14} {cy} Z", color) +
            P(f"M{cx - s * .5} {cy} L{cx - s * .62} {cy - s * .2} L{cx - s * .54} {cy - s * .2} L{cx - s * .4} {cy} Z", color) +
            "".join(C(cx + s * (.12 + k * .09), cy - s * .02, s * .022, accent) for k in range(4)) + '</g>')


def headset(cx, cy, s, hid, color="#E8ECFF", pad="#2A3170"):
    return (f'<g id="{{id}}-{hid}">' + P(f"M{cx - s * .42} {cy + s * .05} A{s * .42} {s * .42} 0 0 1 {cx + s * .42} {cy + s * .05}", stroke=color, stroke_width=s * .08) +
            R(cx - s * .55, cy - s * .02, s * .22, s * .38, s * .08, pad, stroke=color, stroke_width=6) + R(cx + s * .33, cy - s * .02, s * .22, s * .38, s * .08, pad, stroke=color, stroke_width=6) +
            P(f"M{cx - s * .44} {cy + s * .36} Q{cx - s * .4} {cy + s * .62} {cx - s * .1} {cy + s * .6}", stroke=color, stroke_width=s * .04) + C(cx - s * .08, cy + s * .6, s * .05, color) + '</g>')


def person(cx, cy, s, pid, skin="#F2C9A0", shirt="#60A5FA", hair="#3A2A1A", extra=""):
    """Personaje plano genérico (no es nadie real): cabeza, pelo, torso."""
    return (f'<g id="{{id}}-{pid}">' + R(cx - s * .42, cy + s * .42, s * .84, s * .9, s * .36, shirt) + C(cx, cy, s * .34, skin) +
            P(f"M{cx - s * .34} {cy - s * .04} A{s * .34} {s * .34} 0 0 1 {cx + s * .34} {cy - s * .04} Q{cx} {cy - s * .2} {cx - s * .34} {cy - s * .04} Z", hair) +
            C(cx - s * .12, cy + s * .04, s * .035, "#1B1B24") + C(cx + s * .12, cy + s * .04, s * .035, "#1B1B24") +
            P(f"M{cx - s * .1} {cy + s * .16} Q{cx} {cy + s * .23} {cx + s * .1} {cy + s * .16}", stroke="#1B1B24", stroke_width=s * .025, stroke_linecap="round") + extra + '</g>')


def check(cx, cy, r, cid, color="#4ADE80", ink="#0C2A18"):
    return f'<g id="{{id}}-{cid}">' + C(cx, cy, r, color) + P(f"M{cx - r * .45} {cy} l{r * .32} {r * .34} l{r * .62} {r * .72 * -1}", stroke=ink, stroke_width=r * .2, stroke_linecap="round", stroke_linejoin="round") + '</g>'


def cross(cx, cy, r, cid, color="#FF5A6E", ink="#2A0A10"):
    return f'<g id="{{id}}-{cid}">' + C(cx, cy, r, color) + L(cx - r * .38, cy - r * .38, cx + r * .38, cy + r * .38, ink, r * .2) + L(cx + r * .38, cy - r * .38, cx - r * .38, cy + r * .38, ink, r * .2) + '</g>'


def stamp(cx, cy, w, h, txt, color, sid, rot=-6, size=56):
    return (f'<g id="{{id}}-{sid}" opacity="0"><g transform="rotate({rot} {cx} {cy})">' + R(cx - w / 2, cy - h / 2, w, h, 22, "none", stroke=color, stroke_width=10) +
            T(cx, cy + size * .36, txt, size, color, mono=True) + '</g></g>')


def bubble(x, y, w, h, txt, bid, fill="#F4F6FF", ink="#141833", size=40, tail="left"):
    tx = x + 60 if tail == "left" else x + w - 60
    return (f'<g id="{{id}}-{bid}">' + R(x, y, w, h, 34, fill) + P(f"M{tx - 24} {y + h - 2} L{tx} {y + h + 40} L{tx + 24} {y + h - 2} Z", fill) +
            T(x + w / 2, y + h / 2 + size * .36, txt, size, ink) + '</g>')


def arrow(x1, y1, x2, y2, aid, color="#FFB547", sw=10, dash=None):
    ang = math.atan2(y2 - y1, x2 - x1)
    hx1, hy1 = x2 - 34 * math.cos(ang - .5), y2 - 34 * math.sin(ang - .5)
    hx2, hy2 = x2 - 34 * math.cos(ang + .5), y2 - 34 * math.sin(ang + .5)
    ln = math.hypot(x2 - x1, y2 - y1)
    return (f'<g id="{{id}}-{aid}">' + P(f"M{x1:.0f} {y1:.0f} L{x2:.0f} {y2:.0f}", id=f"{{id}}-{aid}l", stroke=color, stroke_width=sw, stroke_linecap="round",
            stroke_dasharray=dash or f"{ln:.0f}", stroke_dashoffset=0 if dash else f"{ln:.0f}") +
            P(f"M{hx1:.0f} {hy1:.0f} L{x2:.0f} {y2:.0f} L{hx2:.0f} {hy2:.0f}", id=f"{{id}}-{aid}h", stroke=color, stroke_width=sw, stroke_linecap="round", stroke_linejoin="round", opacity=0) + '</g>')


def gear(cx, cy, r, gid, color="#9AA6FF", hole="#161A44"):
    teeth = "".join(R(cx - r * .14, cy - r * 1.22, r * .28, r * .4, 4, color, transform=f"rotate({k * 45} {cx} {cy})") for k in range(8))
    return f'<g id="{{id}}-{gid}">{teeth}' + C(cx, cy, r, color) + C(cx, cy, r * .42, hole) + '</g>'


def battery(x, y, w, h, level, color, bid, frame="#E8ECFF"):
    return (f'<g id="{{id}}-{bid}">' + R(x, y, w, h, h * .22, "#0C0F26", stroke=frame, stroke_width=10) + R(x + w + 6, y + h * .3, h * .16, h * .4, 6, frame) +
            R(x + 16, y + 16, (w - 32) * level, h - 32, h * .14, color, id=f"{{id}}-{bid}f") + '</g>')


def qr(x, y, size, qid, n=25, seed=7, fg="#111", bg="#fff", groups=6):
    """QR de mentira (no se puede escanear): 3 marcas de posición + módulos pseudoaleatorios en `groups` grupos (qid-m0..)."""
    m = size / (n + 2)
    def finder(cx, cy):
        return (R(x + m * (cx + 1), y + m * (cy + 1), m * 7, m * 7, m * .6, fg) + R(x + m * (cx + 2), y + m * (cy + 2), m * 5, m * 5, m * .4, bg) +
                R(x + m * (cx + 3), y + m * (cy + 3), m * 3, m * 3, m * .3, fg))
    gs = [[] for _ in range(groups)]
    s = seed
    for r in range(n):
        for c in range(n):
            if (r < 8 and c < 8) or (r < 8 and c >= n - 8) or (r >= n - 8 and c < 8):
                continue
            s = (s * 1103515245 + 12345) & 0x7fffffff
            if s % 100 < 47:
                gs[(r * 7 + c * 3) % groups].append(R(x + m * (c + 1), y + m * (r + 1), m * .92, m * .92, m * .18, fg))
    return (f'<g id="{{id}}-{qid}">' + R(x, y, size, size, 28, bg) + "".join(f'<g id="{{id}}-{qid}m{k}">{"".join(g)}</g>' for k, g in enumerate(gs)) +
            f'<g id="{{id}}-{qid}f">' + finder(0, 0) + finder(n - 7, 0) + finder(0, n - 7) + '</g></g>')


def goboard(x, y, size, gid, n=13, stones=(), wood="#E3B26B", line="#5B3A12"):
    m = size / (n + 1)
    grid = "".join(L(x + m, y + m * (k + 1), x + size - m, y + m * (k + 1), line, 3) + L(x + m * (k + 1), y + m, x + m * (k + 1), y + size - m, line, 3) for k in range(n))
    st = "".join(C(x + m * (c + 1), y + m * (r + 1), m * .46, "#15130F" if b else "#F7F2E8", id=f"{{id}}-{gid}s{k}", stroke="#00000033", stroke_width=2) for k, (r, c, b) in enumerate(stones))
    return f'<g id="{{id}}-{gid}">' + R(x, y, size, size, 24, wood, filter="url(#{id}-sh)") + grid + st + '</g>'


def moth(cx, cy, s, mid, wing="#B49A78", body="#5A4630", spot="#7D6448"):
    return (f'<g id="{{id}}-{mid}">' +
            f'<g id="{{id}}-{mid}l">' + P(f"M{cx} {cy} C{cx - s * .9} {cy - s * .9} {cx - s * 1.2} {cy - s * .1} {cx - s * .2} {cy + s * .1} Z", wing) +
            P(f"M{cx} {cy + s * .05} C{cx - s * .7} {cy + s * .3} {cx - s * .6} {cy + s * .8} {cx - s * .1} {cy + s * .3} Z", wing, opacity=.85) + C(cx - s * .55, cy - s * .2, s * .1, spot) + '</g>' +
            f'<g id="{{id}}-{mid}r">' + P(f"M{cx} {cy} C{cx + s * .9} {cy - s * .9} {cx + s * 1.2} {cy - s * .1} {cx + s * .2} {cy + s * .1} Z", wing) +
            P(f"M{cx} {cy + s * .05} C{cx + s * .7} {cy + s * .3} {cx + s * .6} {cy + s * .8} {cx + s * .1} {cy + s * .3} Z", wing, opacity=.85) + C(cx + s * .55, cy - s * .2, s * .1, spot) + '</g>' +
            E(cx, cy + s * .12, s * .09, s * .42, body) + P(f"M{cx - s * .04} {cy - s * .26} Q{cx - s * .2} {cy - s * .6} {cx - s * .32} {cy - s * .62}", stroke=body, stroke_width=s * .03) +
            P(f"M{cx + s * .04} {cy - s * .26} Q{cx + s * .2} {cy - s * .6} {cx + s * .32} {cy - s * .62}", stroke=body, stroke_width=s * .03) + '</g>')


def chip(cx, cy, s, cid, label="CPU", body="#1D2460", pin="#7C8BFF", ink="#C9D1FF"):
    x, y = cx - s / 2, cy - s / 2
    pins = "".join(R(x + s * .1 + k * s * .17, y - s * .1, s * .06, s * .12, 4, pin) + R(x + s * .1 + k * s * .17, y + s * .98, s * .06, s * .12, 4, pin) +
                   R(x - s * .1, y + s * .1 + k * s * .17, s * .12, s * .06, 4, pin) + R(x + s * .98, y + s * .1 + k * s * .17, s * .12, s * .06, 4, pin) for k in range(5))
    return f'<g id="{{id}}-{cid}">' + pins + R(x, y, s, s, s * .12, body, stroke=pin, stroke_width=6) + T(cx, cy + s * .09, label, s * .22, ink, mono=True) + '</g>'


# ---------- guion ----------
def beat(texto, svg_code, anim="", en=(), pantalla="completa"):
    return {"texto": texto, "escena": {"tipo": "ilustracion", "html": svg_code, "anim": anim, "en": list(en), "pantalla": pantalla}}


def guardar(guion, ruta_json, voces=None):
    """Escribe el guion; `voces` (lista de mp3) va a `voz_archivo`. Uso típico: guardar(g, ruta, sys.argv[1:])."""
    if voces:
        guion["voz_archivo"] = list(voces)
    import subprocess, tempfile
    js = "".join(f"function s{i}(c,p,id,cue){{\n{b['escena'].get('anim','')}\n}}\n" for i, b in enumerate(guion["beats"]) if b["escena"]["tipo"] == "ilustracion")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(js)
    r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
    if r.returncode:
        print("ERROR JS en anim:", r.stderr[:800]); sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(ruta_json)), exist_ok=True)
    json.dump(guion, open(ruta_json, "w"), ensure_ascii=False, indent=1)
    print("ok", ruta_json, len(guion["beats"]), "beats")

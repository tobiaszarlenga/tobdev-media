#!/usr/bin/env python3
"""Arma y renderiza un reel de noticias de tobdev (1080x1920, ~19,5 s).

Uso:
  python3 plantilla/make_reel.py noticia.json videos/2026-10-16.mp4

noticia.json:
{
  "fecha": "16 OCT",                      # etiqueta corta
  "titulo": "…",                          # 30–80 caracteres
  "puntos": ["…", "…", "…"],              # 3 puntos, hasta ~100 caracteres cada uno
  "negocio": "…",                         # qué significa para un negocio, hasta ~120 caracteres
  "fuente": "Anthropic (blog oficial)"    # medio o sitio de origen
}

Requisitos: Node 22, ffmpeg, Python con numpy+scipy, y un Chromium/headless_shell
(se busca solo en /opt/pw-browsers). Instala hyperframes con npx la primera vez.
"""
import glob, html, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 19.5
SCENES = [0.0, 4.5, 12.5, 16.5]
CARDS = [5.2, 7.2, 9.2]
HF = "hyperframes@0.8.157"


def esc(s):
    return html.escape(str(s), quote=True)


def size_for(text, steps):
    n = len(text)
    for limit, px in steps:
        if n <= limit:
            return px
    return steps[-1][1]


def lines(text, px, width=940, k=0.55):
    """Estima cuántas líneas ocupa text con word-wrap."""
    per = max(1, int(width / (px * k)))
    n, cur = 1, 0
    for w in text.split():
        add = len(w) + (1 if cur else 0)
        if cur + add > per:
            n, cur = n + 1, len(w)
        else:
            cur += add
    return n


def build_html(d):
    titulo = d["titulo"].strip()
    puntos = [p.strip() for p in d["puntos"]][:3]
    negocio = d["negocio"].strip()
    fuente = d["fuente"].strip()
    fecha = d.get("fecha", "").strip().upper()
    t_px = size_for(titulo, [(38, 120), (55, 106), (75, 94), (999, 82)])
    n_px = size_for(negocio, [(70, 80), (100, 70), (999, 62)])
    cards = "".join(
        f'<div class="card" id="c{i}" style="top:{560 + i*300}px"><div class="num">0{i+1}</div>'
        f'<div class="ct" style="font-size:{size_for(p, [(60, 48), (85, 44), (999, 40)])}px">{esc(p)}</div></div>'
        for i, p in enumerate(puntos))
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";font-weight:{w};font-style:normal;font-display:block;src:url("assets/fonts/{fn}-{w}.woff2") format("woff2");}}\n'
        for fam, fn in (("Space Grotesk", "SpaceGrotesk"), ("Inter", "Inter")) for w in (400, 500, 600, 700))
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
{fonts}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#F7F4EC; }}
#root {{ position:absolute; inset:0; font-family:"Inter", sans-serif; color:#16191F; }}
.scene {{ position:absolute; inset:0; }}
#bg {{ position:absolute; inset:0; background:#F7F4EC; }}
.eb {{ position:absolute; left:70px; top:330px; font-family:"Space Grotesk", sans-serif; font-weight:600; font-size:26px; letter-spacing:0.08em; color:#B04309; }}
.tag {{ position:absolute; left:70px; top:520px; height:64px; padding:0 28px; border-radius:32px; background:#E8590C; color:#F7F4EC; display:flex; align-items:center; font-family:"Space Grotesk", sans-serif; font-weight:700; font-size:28px; letter-spacing:0.06em; }}
.tit {{ position:absolute; left:70px; top:640px; width:940px; font-family:"Space Grotesk", sans-serif; font-weight:700; line-height:1.07; letter-spacing:-0.025em; }}
.tit .w {{ display:inline-block; margin-right:0.24em; }}
.h2 {{ position:absolute; left:70px; top:390px; width:940px; font-family:"Space Grotesk", sans-serif; font-weight:700; font-size:80px; letter-spacing:-0.02em; }}
.card {{ position:absolute; left:70px; width:940px; min-height:270px; padding:36px 40px; border-radius:26px; background:#FFFFFF; border:1px solid rgba(22,25,31,0.10); display:flex; gap:30px; align-items:flex-start; }}
.num {{ flex:none; font-family:"Space Grotesk", sans-serif; font-weight:700; font-size:56px; color:#E8590C; line-height:1; }}
.ct {{ font-weight:500; line-height:1.3; }}
.neg {{ position:absolute; left:70px; top:560px; width:940px; font-family:"Space Grotesk", sans-serif; font-weight:600; line-height:1.15; letter-spacing:-0.02em; }}
.src {{ position:absolute; left:70px; top:1340px; width:940px; font-size:30px; font-weight:500; color:#62666D; }}
.src b {{ color:#16191F; font-weight:600; }}
.wm {{ position:absolute; left:0; right:0; top:690px; text-align:center; font-family:"Space Grotesk", sans-serif; font-weight:700; font-size:180px; letter-spacing:-0.04em; line-height:1; }}
.wm span {{ color:#E8590C; }}
.sub {{ position:absolute; left:0; right:0; top:920px; text-align:center; font-size:46px; font-weight:500; color:#62666D; }}
.cta {{ position:absolute; left:50%; top:1060px; width:420px; height:108px; margin-left:-210px; border-radius:100px; background:#E8590C; color:#F7F4EC; display:flex; align-items:center; justify-content:center; font-family:"Space Grotesk", sans-serif; font-weight:600; font-size:46px; }}
.bar {{ position:absolute; left:70px; width:220px; height:12px; border-radius:6px; background:#E8590C; transform-origin:0 50%; }}
.big {{ position:absolute; right:-40px; bottom:300px; font-family:"Space Grotesk", sans-serif; font-weight:700; font-size:520px; line-height:1; color:rgba(232,89,12,0.07); letter-spacing:-0.05em; }}
#prog {{ position:absolute; left:0; bottom:0; width:100%; height:4px; background:#E8590C; transform-origin:0 50%; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
  <div id="bg" class="clip" data-start="0" data-duration="{DUR}" data-track-index="0"></div>
  <div id="s1" class="clip scene" data-start="0" data-duration="4.9" data-track-index="1">
    <div class="eb" id="s1-eb" style="top:440px">NOTICIAS IA{(" · " + esc(fecha)) if fecha else ""}</div>
    <div class="tag" id="s1-tag">HOY EN IA</div>
    <div class="big" id="s1-big">IA</div>
    <div class="tit" id="s1-tit" style="font-size:{t_px}px">{"".join(f'<span class="w tw">{esc(w)}</span>' for w in titulo.split())}</div>
    <div class="bar" id="s1-bar" style="top:{640 + int(t_px*1.07*lines(titulo, t_px)) + 60}px"></div>
  </div>
  <div id="s2" class="clip scene" data-start="4.5" data-duration="8.4" data-track-index="2">
    <div class="eb" id="s2-eb">LO IMPORTANTE</div>
    <div class="h2" id="s2-h">En 3 puntos:</div>
    {cards}
  </div>
  <div id="s3" class="clip scene" data-start="12.5" data-duration="4.4" data-track-index="1">
    <div class="eb" id="s3-eb">¿Y PARA TU NEGOCIO?</div>
    <div class="bar" id="s3-bar" style="top:470px"></div>
    <div class="neg" id="s3-neg" style="font-size:{n_px}px">{esc(negocio)}</div>
    <div class="src" id="s3-src">Fuente: <b>{esc(fuente)}</b></div>
  </div>
  <div id="s4" class="clip scene" data-start="16.5" data-duration="3.0" data-track-index="2">
    <div class="wm" id="s4-wm">tobdev<span>.</span></div>
    <div class="sub" id="s4-sub">Sistemas e IA para tu negocio</div>
    <div class="cta" id="s4-cta">Seguinos</div>
  </div>
  <div id="prog"></div>
  <audio id="el-bgm" src="assets/music.mp3" data-start="0" data-duration="{DUR}" data-track-index="11" data-volume="1"></audio>
</div>
<script>
(function () {{
  const tl = gsap.timeline({{ paused: true }});
  const rise = (el, at, y = 30, d = 0.55, stagger = 0) => tl.fromTo(el, {{ opacity: 0, y }}, {{ opacity: 1, y: 0, duration: d, ease: "power3.out", stagger }}, at);
  const xf = (out, inn, at) => {{ tl.fromTo(out, {{ opacity: 1 }}, {{ opacity: 0, duration: 0.4, ease: "power2.inOut", immediateRender: false }}, at);
                                tl.fromTo(inn, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.inOut" }}, at); }};
  tl.fromTo("#prog", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {DUR}, ease: "none" }}, 0);
  // escena 1
  rise("#s1-eb", 0.1, 16, 0.45);
  tl.fromTo("#s1-tag", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "power3.out" }}, 0.25);
  rise(".tw", 0.45, 40, 0.55, 0.07);
  tl.fromTo("#s1-big", {{ opacity: 0, x: 60 }}, {{ opacity: 1, x: 0, duration: 1.2, ease: "power2.out" }}, 0.2);
  tl.fromTo("#s1-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.6, ease: "power3.inOut" }}, 1.4);
  // escena 2
  xf("#s1", "#s2", 4.5);
  rise("#s2-eb", 4.6, 16, 0.45);
  rise("#s2-h", 4.7, 30, 0.5);
  {json.dumps(CARDS)}.forEach((t, i) => rise("#c" + i, t, 36, 0.55));
  // escena 3
  xf("#s2", "#s3", 12.5);
  rise("#s3-eb", 12.6, 16, 0.45);
  tl.fromTo("#s3-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: "power3.inOut" }}, 12.7);
  rise("#s3-neg", 12.75, 34, 0.6);
  rise("#s3-src", 13.6, 16, 0.45);
  // escena 4
  xf("#s3", "#s4", 16.5);
  tl.fromTo("#s4-wm", {{ scale: 0.82 }}, {{ scale: 1, duration: 0.6, ease: "power3.out" }}, 16.5);
  rise("#s4-sub", 17.0, 22, 0.5);
  tl.fromTo("#s4-cta", {{ opacity: 0, scale: 0.82 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" }}, 18.0);
  window.__timelines = window.__timelines || {{}};
  window.__timelines["main"] = tl;
}})();
</script>
</body>
</html>
"""


def find_browser():
    if os.environ.get("HYPERFRAMES_BROWSER_PATH"):
        return os.environ["HYPERFRAMES_BROWSER_PATH"]
    for pat in ("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux*/headless_shell",
                "/opt/pw-browsers/chromium-*/chrome-linux*/chrome", "/opt/pw-browsers/chromium*/chrome"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


def main():
    data = json.load(open(sys.argv[1]))
    out = os.path.abspath(sys.argv[2])
    assert len(data["puntos"]) == 3, "hacen falta exactamente 3 puntos"
    work = tempfile.mkdtemp(prefix="reel-")
    os.makedirs(os.path.join(work, "assets"))
    shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(work, "assets", "fonts"))
    shutil.copy(os.path.join(HERE, "gsap.min.js"), os.path.join(work, "assets", "gsap.min.js"))
    open(os.path.join(work, "index.html"), "w").write(build_html(data))
    open(os.path.join(work, "meta.json"), "w").write('{"id":"reel","name":"reel"}')
    wav = os.path.join(work, "music.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "music.py"), wav, str(DUR),
                    json.dumps({"scenes": SCENES, "cards": CARDS})], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-af",
                    "highpass=f=35,treble=g=3:f=4000,loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-c:a", "libmp3lame", "-b:a", "192k", os.path.join(work, "assets", "music.mp3")], check=True)
    env = dict(os.environ)
    br = find_browser()
    if br:
        env["HYPERFRAMES_BROWSER_PATH"] = br
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["npx", "--yes", HF, "render", "-o", out, "--quality", "high", "--video-bitrate", "10M"],
                   cwd=work, env=env, check=True)
    print("OK", out)


if __name__ == "__main__":
    main()

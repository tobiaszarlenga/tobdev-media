#!/usr/bin/env python3
"""Arma y renderiza un reel de noticias de TobDev (1080x1920, 19,5 s) con el sistema de diseño de la marca.

Uso:
  python3 plantilla/make_reel.py noticia.json videos/2026-10-16.mp4

noticia.json:
{
  "fecha": "16 OCT",                      # etiqueta corta
  "titulo": "…",                          # 30–75 caracteres, declarativo
  "destacado": "…",                       # opcional: palabras finales del título que van en degradé (2–4 palabras)
  "puntos": ["…", "…", "…"],              # 3 puntos, hasta ~100 caracteres cada uno
  "negocio": "…",                         # qué significa para un negocio, hasta ~110 caracteres
  "fuente": "Anthropic (blog oficial)"    # medio o sitio de origen
}

Sistema de diseño TobDev: fondo #0A0E1A con aurora violeta/cian y grano; títulos en FreeSans Bold
(la fuente del wordmark); detalles en JetBrains Mono; acento cian #11BFD6; degradé firma
#5B6FE4→#11BFD6 solo como acento (una frase, números, bordes, CTA); isotipo blanco; tarjetas glass.

Requisitos: Node 22, ffmpeg, Python con numpy+scipy y un Chromium/headless_shell
(se busca solo en /opt/pw-browsers). Instala hyperframes con npx la primera vez.
"""
import glob, html, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 19.5
SCENES = [0.0, 4.5, 12.5, 16.5]
CARDS = [5.2, 7.2, 9.2]
HF = "hyperframes@0.8.157"
GRAD = "linear-gradient(135deg, #5B6FE4 0%, #11BFD6 100%)"


def esc(s):
    return html.escape(str(s), quote=True)


def size_for(text, steps):
    n = len(text)
    for limit, px in steps:
        if n <= limit:
            return px
    return steps[-1][1]


def title_words(titulo, destacado):
    """Divide el título en palabras y marca cuáles van en degradé (las de `destacado`, o las 2 últimas)."""
    words = titulo.split()
    n_acc = len(destacado.split()) if destacado and titulo.rstrip(" .").endswith(destacado.rstrip(" .")) else 2
    n_acc = max(1, min(n_acc, 4, len(words) - 1))
    out = []
    for i, w in enumerate(words):
        cls = "w tw grad" if i >= len(words) - n_acc else "w tw"
        out.append(f'<span class="{cls}">{esc(w)}</span>')
    return "".join(out)


def build_html(d):
    titulo = d["titulo"].strip()
    puntos = [p.strip() for p in d["puntos"]][:3]
    negocio = d["negocio"].strip()
    fuente = d["fuente"].strip()
    fecha = d.get("fecha", "").strip().upper()
    t_px = size_for(titulo, [(38, 118), (55, 104), (75, 92), (999, 80)])
    n_px = size_for(negocio, [(70, 78), (100, 68), (999, 60)])
    cards = "".join(
        f'<div class="gb" id="c{i}"><div class="card"><div class="num">0{i+1}</div>'
        f'<div class="ct" style="font-size:{size_for(p, [(60, 46), (85, 42), (999, 39)])}px">{esc(p)}</div></div></div>'
        for i, p in enumerate(puntos))
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";font-weight:{w};font-style:normal;font-display:block;src:url("assets/fonts/{fn}-{w}.{ext}") format("{fmt}");}}\n'
        for fam, fn, ws, ext, fmt in (("FreeSans", "FreeSans", (400, 700), "ttf", "truetype"),
                                      ("JetBrains Mono", "JetBrainsMono", (400, 500, 700), "woff2", "woff2"))
        for w in ws)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
{fonts}
:root {{
  --bg:#0A0E1A; --surface:#111A2E; --text:#FFFFFF; --text-soft:#C6CFE0; --text-muted:#8A97B0;
  --accent:#11BFD6; --violet:#5B6FE4; --success:#21D07A;
  --border:rgba(255,255,255,.08); --border-strong:rgba(255,255,255,.14);
  --grad:{GRAD};
  --display:"FreeSans","Helvetica Neue",Helvetica,Arial,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,monospace;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:var(--bg); }}
#root {{ position:absolute; inset:0; font-family:var(--display); color:var(--text); }}
#bg {{ position:absolute; inset:0; background:var(--bg); overflow:hidden; }}
.blob {{ position:absolute; border-radius:50%; }}
#b1 {{ width:1400px; height:1400px; left:150px; top:-620px; background:radial-gradient(circle, rgba(91,111,228,.34) 0%, rgba(91,111,228,0) 62%); }}
#b2 {{ width:1300px; height:1300px; left:-560px; top:1050px; background:radial-gradient(circle, rgba(17,191,214,.26) 0%, rgba(17,191,214,0) 62%); }}
#b3 {{ width:900px; height:900px; left:420px; top:760px; background:radial-gradient(circle, rgba(91,111,228,.14) 0%, rgba(91,111,228,0) 62%); }}
#grain {{ position:absolute; inset:0; opacity:.05; background:url("assets/grain.png") repeat; }}
.scene {{ position:absolute; left:0; top:0; width:1080px; height:1920px; }}
.col {{ position:absolute; left:84px; right:84px; top:300px; bottom:420px; display:flex; flex-direction:column; justify-content:center; }}
.hdr {{ position:absolute; left:84px; right:84px; top:200px; height:64px; display:flex; align-items:center; gap:18px; }}
.hdr img {{ width:64px; height:64px; }}
.hdr .h {{ font-family:var(--mono); font-weight:500; font-size:28px; color:var(--text-soft); }}
.hdr .d {{ margin-left:auto; font-family:var(--mono); font-weight:500; font-size:26px; letter-spacing:.18em; color:var(--text-muted); }}
.eb {{ font-family:var(--mono); font-weight:500; font-size:28px; letter-spacing:.18em; text-transform:uppercase; color:var(--accent); }}
.badge {{ align-self:flex-start; display:flex; align-items:center; gap:16px; height:68px; padding:0 30px; border-radius:999px;
  background:rgba(17,26,46,.72); border:1px solid var(--border-strong); font-family:var(--mono); font-weight:500;
  font-size:26px; letter-spacing:.18em; color:var(--text); }}
.dot {{ width:16px; height:16px; border-radius:50%; background:var(--success); box-shadow:0 0 0 0 rgba(33,208,122,.5); }}
.tit {{ margin-top:44px; font-weight:700; line-height:1.06; letter-spacing:-.025em; }}
.tit .w {{ display:inline-block; margin-right:.22em; }}
.grad {{ background:var(--grad); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; padding-bottom:.06em; }}
.psub {{ margin-top:44px; font-family:var(--mono); font-size:32px; color:var(--accent); }}
.h2 {{ margin-top:22px; font-weight:700; font-size:88px; line-height:1.06; letter-spacing:-.025em; }}
.cards {{ margin-top:56px; display:flex; flex-direction:column; gap:30px; }}
.gb {{ --a:0deg; padding:2px; border-radius:26px;
  background:conic-gradient(from var(--a), rgba(91,111,228,.95), rgba(17,191,214,.95), rgba(91,111,228,.12) 40%, rgba(17,191,214,.12) 70%, rgba(91,111,228,.95));
  box-shadow:0 18px 50px -18px rgba(0,0,0,.85); }}
.card {{ display:flex; gap:30px; align-items:flex-start; padding:38px 40px; min-height:230px; border-radius:24px; background:rgba(14,20,36,.94); }}
.num {{ flex:none; font-family:var(--mono); font-weight:700; font-size:50px; line-height:1.05; color:var(--accent); }}
.ct {{ font-weight:400; line-height:1.3; color:var(--text); }}
.neg {{ margin-top:40px; font-weight:700; line-height:1.12; letter-spacing:-.02em; }}
.src {{ margin-top:60px; font-family:var(--mono); font-size:30px; color:var(--text-muted); }}
.src b {{ color:var(--text-soft); font-weight:500; }}
.bar {{ width:200px; height:10px; border-radius:5px; background:var(--grad); transform-origin:0 50%; margin-top:40px; }}
.end {{ position:absolute; left:84px; right:84px; top:300px; bottom:420px; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
.end img {{ width:300px; height:300px; }}
.wm {{ margin-top:10px; font-weight:700; font-size:150px; letter-spacing:-.03em; line-height:1; }}
.sub {{ margin-top:34px; font-size:46px; color:var(--text-soft); }}
.cta {{ margin-top:70px; display:flex; align-items:center; gap:18px; padding:30px 54px; border-radius:24px; background:var(--grad);
  font-weight:700; font-size:44px; color:#fff; box-shadow:0 10px 30px -8px rgba(91,111,228,.55); }}
.cta svg {{ width:40px; height:40px; }}
#prog {{ position:absolute; left:0; bottom:0; width:100%; height:6px; background:var(--grad); transform-origin:0 50%; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
  <div id="bg" class="clip" data-start="0" data-duration="{DUR}" data-track-index="0">
    <div class="blob" id="b1"></div><div class="blob" id="b2"></div><div class="blob" id="b3"></div>
    <div id="grain"></div>
  </div>
  <div id="hdr" class="clip hdr" data-start="0" data-duration="16.9" data-track-index="3">
    <img src="assets/mark-white.svg" alt="" /><div class="h">tobdev.ia</div><div class="d">{esc(fecha)}</div>
  </div>
  <div id="s1" class="clip scene" data-start="0" data-duration="4.9" data-track-index="1">
    <div class="col">
      <div class="badge" id="s1-badge"><span class="dot" id="s1-dot"></span>HOY EN IA</div>
      <div class="tit" id="s1-tit" style="font-size:{t_px}px">{title_words(titulo, d.get("destacado", ""))}</div>
      <div class="psub" id="s1-sub">&gt; resumen en 20 segundos</div>
    </div>
  </div>
  <div id="s2" class="clip scene" data-start="4.5" data-duration="8.4" data-track-index="2">
    <div class="col">
      <div class="eb" id="s2-eb">// Lo importante</div>
      <div class="h2" id="s2-h">En <span class="grad">3 puntos.</span></div>
      <div class="cards">{cards}</div>
    </div>
  </div>
  <div id="s3" class="clip scene" data-start="12.5" data-duration="4.4" data-track-index="1">
    <div class="col">
      <div class="eb" id="s3-eb">// ¿Y para tu negocio?</div>
      <div class="bar" id="s3-bar"></div>
      <div class="neg" id="s3-neg" style="font-size:{n_px}px">{esc(negocio)}</div>
      <div class="src" id="s3-src">$ fuente → <b>{esc(fuente)}</b></div>
    </div>
  </div>
  <div id="s4" class="clip scene" data-start="16.5" data-duration="3.0" data-track-index="2">
    <div class="end">
      <img id="s4-mark" src="assets/mark-white.svg" alt="TobDev" />
      <div class="wm" id="s4-wm">Tob<span class="grad">Dev</span></div>
      <div class="sub" id="s4-sub">Sistemas e IA para tu PyME</div>
      <div class="cta" id="s4-cta">Seguí a @tobdev.ia<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></div>
    </div>
  </div>
  <div id="prog"></div>
  <audio id="el-bgm" src="assets/music.mp3" data-start="0" data-duration="{DUR}" data-track-index="11" data-volume="1"></audio>
</div>
<script>
(function () {{
  const tl = gsap.timeline({{ paused: true }});
  const E = "power3.out";
  const rise = (el, at, y = 30, d = 0.6, stagger = 0) => tl.fromTo(el, {{ opacity: 0, y }}, {{ opacity: 1, y: 0, duration: d, ease: E, stagger }}, at);
  const xf = (out, inn, at) => {{
    tl.fromTo(out, {{ opacity: 1 }}, {{ opacity: 0, duration: 0.4, ease: "power2.inOut", immediateRender: false }}, at);
    tl.fromTo(inn, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.inOut" }}, at);
  }};
  // fondo aurora: deriva lenta
  tl.fromTo("#b1", {{ x: 0, y: 0 }}, {{ x: -160, y: 90, duration: {DUR}, ease: "sine.inOut" }}, 0);
  tl.fromTo("#b2", {{ x: 0, y: 0 }}, {{ x: 140, y: -110, duration: {DUR}, ease: "sine.inOut" }}, 0);
  tl.fromTo("#b3", {{ x: 0, y: 0 }}, {{ x: -120, y: -160, duration: {DUR}, ease: "sine.inOut" }}, 0);
  tl.fromTo("#prog", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {DUR}, ease: "none" }}, 0);
  rise("#hdr", 0.05, 14, 0.5);
  // escena 1
  tl.fromTo("#s1-badge", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: E, transformOrigin: "0% 50%" }}, 0.2);
  tl.fromTo("#s1-dot", {{ boxShadow: "0 0 0 0 rgba(33,208,122,.55)" }}, {{ boxShadow: "0 0 0 14px rgba(33,208,122,0)", duration: 1.1, ease: "power1.out", repeat: 3 }}, 0.5);
  rise(".tw", 0.45, 44, 0.6, 0.06);
  rise("#s1-sub", 1.7, 16, 0.5);
  // escena 2
  xf("#s1", "#s2", 4.5);
  rise("#s2-eb", 4.6, 16, 0.45);
  rise("#s2-h", 4.7, 30, 0.55);
  {json.dumps(CARDS)}.forEach((t, i) => rise("#c" + i, t, 40, 0.6));
  tl.fromTo(".gb", {{ "--a": "0deg" }}, {{ "--a": "360deg", duration: 8.0, ease: "none" }}, 4.5);
  // escena 3
  xf("#s2", "#s3", 12.5);
  rise("#s3-eb", 12.6, 16, 0.45);
  tl.fromTo("#s3-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: "power3.inOut" }}, 12.7);
  rise("#s3-neg", 12.8, 34, 0.6);
  rise("#s3-src", 13.7, 16, 0.45);
  // escena 4
  tl.fromTo("#hdr", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.4, ease: "power2.inOut", immediateRender: false }}, 16.5);
  xf("#s3", "#s4", 16.5);
  tl.fromTo("#s4-mark", {{ scale: 0.8, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.7, ease: E }}, 16.55);
  rise("#s4-wm", 16.8, 26, 0.55);
  rise("#s4-sub", 17.2, 20, 0.5);
  tl.fromTo("#s4-cta", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: E }}, 17.8);
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
    for f in ("mark-white.svg", "grain.png"):
        shutil.copy(os.path.join(HERE, "marca", f), os.path.join(work, "assets", f))
    shutil.copy(os.path.join(HERE, "gsap.min.js"), os.path.join(work, "assets", "gsap.min.js"))
    open(os.path.join(work, "index.html"), "w").write(build_html(data))
    open(os.path.join(work, "meta.json"), "w").write('{"id":"reel","name":"reel"}')
    if "--solo-html" in sys.argv:
        print(work)
        return
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

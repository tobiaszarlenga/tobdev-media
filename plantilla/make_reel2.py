#!/usr/bin/env python3
"""Reel de noticias v2 de TobDev: voz IA + subtítulos palabra por palabra + escenas animadas.

Uso:
  python3 plantilla/make_reel2.py guion.json videos/AAAA-MM-DD.mp4 --revisar   # valida + voz + HTML + hoja de contacto
  python3 plantilla/make_reel2.py guion.json videos/AAAA-MM-DD.mp4             # render final (reusa lo anterior) + verificación

El guion (ver plantilla/ESCENAS.md) es una lista de "beats": cada beat es una frase que dice la voz
y la escena que se ve mientras la dice. Marcado dentro de "texto":
  *palabras*      -> palabras clave: van con recuadro de selección en el color de acento
  {Texto|pron}    -> "Texto" se ve en pantalla, "pron" es lo que pronuncia la voz (siglas, marcas en inglés)

Requisitos: Node 22, ffmpeg, Python con numpy, scipy, soundfile y kokoro-onnx; Chromium en /opt/pw-browsers.
El modelo de voz (Kokoro, ~350 MB) se baja solo de GitHub la primera vez a ~/.cache/kokoro.
"""
import glob, html, json, os, re, shutil, subprocess, sys, tempfile, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
HF = "hyperframes@0.8.157"
SR = 24000
MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.expanduser("~/.cache/kokoro"))
MODEL_URLS = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
SCENE_TYPES = {"terminal", "linea_tiempo", "prompt", "capas", "flujo", "cursores", "chips", "frase", "lista", "reloj", "alerta", "numero",
               "navegador", "celular", "grafico", "comparacion", "particulas", "cierre"}
NOCAPS = {"frase", "cierre"}          # escenas que ya muestran el texto: sin subtítulos arriba
PUNCT_PAUSE = {",": 0.10, ";": 0.16, ":": 0.18, ".": 0.24, "?": 0.26, "!": 0.24, "…": 0.26}
BEAT_GAP = 0.14


def esc(s):
    return html.escape(str(s), quote=True)


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9@]+", "", s)


# ---------------------------------------------------------------- guion -> palabras
def parse_words(text):
    """Devuelve [{cap, pron, kw}] donde kw es el id del grupo de palabras clave (o None)."""
    words, cur_cap, cur_pron, kw, kw_id, cur_kw = [], "", "", False, -1, None
    i = 0

    def flush():
        nonlocal cur_cap, cur_pron, cur_kw
        if cur_cap.strip():
            words.append({"cap": cur_cap.strip(), "pron": cur_pron.strip(), "kw": cur_kw})
        cur_cap, cur_pron, cur_kw = "", "", None

    while i < len(text):
        c = text[i]
        if c == "*":
            if not kw:
                kw = True; kw_id += 1
            else:
                kw = False
            i += 1
            continue
        if c == "{":
            j = text.index("}", i)
            cap, pron = text[i + 1:j].split("|", 1)
            cur_cap += cap; cur_pron += pron
            if kw: cur_kw = kw_id
            i = j + 1
            continue
        if c.isspace():
            flush(); i += 1
            continue
        cur_cap += c; cur_pron += c
        if kw and c not in ",.;:?!…": cur_kw = kw_id
        i += 1
    flush()
    return words


def chunks_of(words):
    """Corta en frases para la voz: siempre en . ? ! : ; y en comas solo si ambos lados tienen 3+ palabras."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        last = w["cap"][-1]
        if last in ".?!:;…":
            out.append(cur); cur = []
        elif last == ",":
            rest = 0
            for x in words[i + 1:]:
                rest += 1
                if x["cap"][-1] in ".?!:;…":
                    break
            if len(cur) >= 3 and rest >= 3:
                out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- voz
def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for fn, url in MODEL_URLS.items():
        p = os.path.join(MODEL_DIR, fn)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            subprocess.run(["curl", "-sSL", "--retry", "3", "-o", p + ".part", url], check=True)
            os.replace(p + ".part", p)
    from kokoro_onnx import Kokoro
    return Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))


def to_phonemes(k, text, acento):
    ph = k.tokenizer.phonemize(text, "es-419")
    if acento == "rio":
        ph = ph.replace("ʝ", "ʃ").replace("ʎ", "ʃ")
    return ph


def trim(a, thr=0.012):
    import numpy as np
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(0.015 * SR)); e = min(len(a), idx[-1] + int(0.04 * SR))
    return a[s:e]


def synth(guion, beats):
    """Sintetiza cada frase, arma la pista de voz y devuelve tiempos por palabra (en segundos)."""
    import numpy as np
    k = ensure_model()
    voz = guion.get("voz", "em_alex")
    acento = guion.get("acento_voz", "rio")
    speed = float(guion.get("velocidad", 1.1))
    pieces, t = [], 0.12
    for bi, b in enumerate(beats):
        b["t_speech"] = t
        for ch in b["chunks"]:
            txt = " ".join(w["pron"] for w in ch)
            a, _ = k.create(to_phonemes(k, txt, acento), voice=voz, speed=speed, lang="es-419", is_phonemes=True)
            a = trim(a)
            dur = len(a) / SR
            pieces.append((t, a))
            weights = []
            for w in ch:
                p = re.sub(r"[ˈˌ\s,.;:?!¿¡…]", "", to_phonemes(k, w["pron"], acento))
                weights.append(len(p) + 1.2 + (2.5 if w["cap"][-1] in ",;:" and w is not ch[-1] else 0))
            tot = sum(weights); acc = 0.0
            for w, wt in zip(ch, weights):
                w["t0"] = t + dur * acc / tot
                acc += wt
                w["t1"] = t + dur * acc / tot
            t += dur + PUNCT_PAUSE.get(ch[-1]["cap"][-1], 0.05)
        b["t_end"] = t
        t += BEAT_GAP
    total = t + 0.1
    track = np.zeros(int((total + 3) * SR), dtype=np.float32)
    for st, a in pieces:
        i = int(st * SR)
        track[i:i + len(a)] += a
    return track, total


def synth_external(guion, beats, path):
    """Voz grabada aparte (ElevenLabs u otra): usa el audio tal cual y saca los tiempos por palabra
    alineando (DTW sobre MFCC) contra una referencia Kokoro del mismo texto, que sí tiene tiempos.
    El audio tiene que decir el texto del guion (la pronunciación de {Texto|pronunciación})."""
    import numpy as np, librosa
    ref, ref_total = synth(guion, beats)  # deja t0/t1/t_speech/t_end en la línea de tiempo de la referencia
    ref = ref[: int(ref_total * SR)]
    y, _ = librosa.load(path, sr=SR, mono=True)
    y, _ = librosa.effects.trim(y, top_db=40)
    lead = 0.12
    ext = np.concatenate([np.zeros(int(lead * SR), dtype=np.float32), y.astype(np.float32)])
    # mismo nivel que la voz Kokoro para que la cadena de mezcla (volumen, compresor) funcione igual
    def rms(a):
        v = a[np.abs(a) > 0.01]
        return float(np.sqrt(np.mean(v ** 2))) if len(v) else 1.0
    ext *= rms(ref) / max(rms(ext), 1e-6)
    peak = float(np.max(np.abs(ext)))
    if peak > 0.98:
        ext *= 0.98 / peak
    hop = 480  # 20 ms

    def feat(a):
        m = librosa.feature.mfcc(y=a, sr=SR, n_mfcc=20, hop_length=hop, n_fft=1024)
        return (m - m.mean(axis=1, keepdims=True)) / (m.std(axis=1, keepdims=True) + 1e-6)

    _, wp = librosa.sequence.dtw(X=feat(ref), Y=feat(ext), metric="euclidean")
    wp = wp[::-1]
    ri = np.arange(wp[:, 0].max() + 1)
    ej = np.array([wp[wp[:, 0] == i, 1].mean() for i in ri])
    ej = np.maximum.accumulate(ej)  # monótona

    def m(t):
        return float(np.interp(t * SR / hop, ri, ej) * hop / SR)

    for b in beats:
        b["t_speech"] = m(b["t_speech"])
        b["t_end"] = m(b["t_end"])
        for w in b["words"]:
            w["t0"], w["t1"] = m(w["t0"]), m(w["t1"])
    total = len(ext) / SR + 0.1
    track = np.zeros(int((total + 3) * SR), dtype=np.float32)
    track[: len(ext)] = ext
    return track, total


EL_API = "https://api.elevenlabs.io/v1/text-to-speech/"
EL_CACHE = os.environ.get("REEL_VOZ_CACHE", os.path.expanduser("~/.cache/reel-voz"))
VOICE_RMS = 0.09  # nivel de la voz Kokoro, para que la mezcla funcione igual con cualquier voz


def el_text(beats):
    """Texto hablado (pronunciaciones) y la posición de cada palabra dentro de él."""
    parts, spans, pos = [], [], 0
    for b in beats:
        for wi, w in enumerate(b["words"]):
            if parts:
                parts.append("\n" if wi == 0 else " "); pos += 1
            spans.append((w, pos, pos + len(w["pron"])))
            parts.append(w["pron"]); pos += len(w["pron"])
    return "".join(parts), spans


def el_post(path, body, out):
    """POST a la API de ElevenLabs con curl (la clave la agrega el secreto de red del entorno, o ELEVENLABS_API_KEY)."""
    cmd = ["curl", "-sS", "--max-time", "240", "-o", out, "-w", "%{http_code}", "-X", "POST", EL_API + path,
           "-H", "Content-Type: application/json", "--data-binary", "@-"]
    if os.environ.get("ELEVENLABS_API_KEY"):
        cmd += ["-H", "xi-api-key: " + os.environ["ELEVENLABS_API_KEY"]]
    r = subprocess.run(cmd, input=json.dumps(body).encode(), capture_output=True)
    code = r.stdout.decode().strip()
    detail = r.stderr.decode().strip()[-200:]
    if code != "200" and os.path.exists(out):
        try:
            detail = open(out, errors="replace").read()[:300]
        except OSError:
            pass
    return code, detail


def synth_elevenlabs(guion, beats):
    """Voz de ElevenLabs generada desde el guion. Usa los tiempos por carácter que devuelve la API
    (with-timestamps); si no vienen, alinea contra Kokoro como con voz_archivo. Cachea por texto+voz,
    así cambiar solo una escena no vuelve a gastar créditos."""
    import numpy as np, base64, hashlib, librosa
    cfg = guion["elevenlabs"]
    vid = cfg["voice_id"]
    model = cfg.get("model_id", "eleven_v4")
    vs = {"stability": float(cfg.get("stability", 0.5)), "similarity_boost": float(cfg.get("similarity_boost", 0.75))}
    if cfg.get("velocidad"):
        vs["speed"] = float(cfg["velocidad"])
    text, spans = el_text(beats)
    h = hashlib.sha256(json.dumps([text, vid, model, vs], sort_keys=True).encode()).hexdigest()[:16]
    os.makedirs(EL_CACHE, exist_ok=True)
    mp3, al_p = os.path.join(EL_CACHE, h + ".mp3"), os.path.join(EL_CACHE, h + ".json")
    if not (os.path.exists(mp3) and os.path.exists(al_p)):
        body = {"text": text, "model_id": model, "voice_settings": vs}
        resp_p = os.path.join(EL_CACHE, h + ".resp")
        code, detail = el_post(f"{vid}/with-timestamps?output_format=mp3_44100_128", body, resp_p)
        if code == "200":
            resp = json.load(open(resp_p))
            open(mp3, "wb").write(base64.b64decode(resp["audio_base64"]))
            json.dump(resp.get("alignment") or resp.get("normalized_alignment"), open(al_p, "w"))
            os.remove(resp_p)
        elif code in ("400", "422"):  # el modelo puede no dar tiempos: pedir solo el audio y alinear
            print(f"AVISO ElevenLabs sin tiempos ({code}): {detail}")
            code2, detail2 = el_post(f"{vid}?output_format=mp3_44100_128", body, mp3 + ".part")
            if code2 != "200":
                raise RuntimeError(f"ElevenLabs respondió {code2}: {detail2}")
            os.replace(mp3 + ".part", mp3)
            json.dump(None, open(al_p, "w"))
        else:
            raise RuntimeError(f"ElevenLabs respondió {code or 'sin conexión'}: {detail}")
    al = json.load(open(al_p))
    if not al or len(al.get("character_start_times_seconds", [])) != len(text):
        return synth_external(guion, beats, mp3)
    st, en = al["character_start_times_seconds"], al["character_end_times_seconds"]
    lead = 0.12
    for w, a, b_ in spans:
        w["t0"], w["t1"] = lead + st[a], lead + en[b_ - 1]
    for b in beats:
        b["t_speech"], b["t_end"] = b["words"][0]["t0"], b["words"][-1]["t1"]
    y, _ = librosa.load(mp3, sr=SR, mono=True)
    v = y[np.abs(y) > 0.01]
    if len(v):
        y = y * (VOICE_RMS / float(np.sqrt(np.mean(v ** 2))))
    peak = float(np.max(np.abs(y))) if len(y) else 0
    if peak > 0.98:
        y = y * (0.98 / peak)
    total = lead + len(y) / SR + 0.1
    track = np.zeros(int((total + 3) * SR), dtype=np.float32)
    i = int(lead * SR)
    track[i:i + len(y)] = y
    return track, total


# ---------------------------------------------------------------- tiempos de escenas y subtítulos
def layout_beats(guion):
    beats = []
    for b in guion["beats"]:
        words = parse_words(b["texto"])
        esc_ = dict(b.get("escena") or {})
        if esc_.get("tipo") not in SCENE_TYPES:
            esc_["tipo"] = "frase"
        beats.append({"words": words, "chunks": chunks_of(words), "escena": esc_})
    return beats


def caption_groups(beats):
    """Agrupa palabras para los subtítulos: hasta 6 palabras / 34 caracteres, cortando en puntuación."""
    groups = []
    for bi, b in enumerate(beats):
        if b["escena"]["tipo"] in NOCAPS:
            continue
        cur = []
        for w in b["words"]:
            n = sum(len(x["cap"]) + 1 for x in cur) + len(w["cap"])
            if cur and (len(cur) >= 6 or n > 34):
                groups.append(cur); cur = []
            cur.append(w)
            last = w["cap"][-1]
            if last in ".?!:;…" or (last == "," and len(cur) >= 4):
                groups.append(cur); cur = []
        if cur:
            groups.append(cur)
    for i, g in enumerate(groups):
        nxt = groups[i + 1][0]["t0"] if i + 1 < len(groups) else g[-1]["t1"] + 0.4
        g_end = min(nxt, g[-1]["t1"] + 0.55)
        groups[i] = {"words": g, "t0": g[0]["t0"] - 0.04, "t1": g_end}
    return groups


def find_cue(b, word, after=-1):
    if not word:
        return None, after
    target = norm(word)
    for i, w in enumerate(b["words"]):
        if i > after and norm(w["cap"]).startswith(target):
            return w["t0"], i
    return None, after


def scene_cues(b, keys, t0, t1):
    """Tiempos para una lista de palabras ('en'); las que no aparecen se reparten parejo."""
    out, after = [], -1
    for k in keys:
        t, after = find_cue(b, k, after)
        out.append(t)
    n = len(out)
    for i, t in enumerate(out):
        if t is None:
            out[i] = t0 + 0.35 + (t1 - t0 - 0.9) * (i / max(1, n))
    return [round(x, 3) for x in out]


# ---------------------------------------------------------------- HTML de escenas
def icon(name, size=56, color="currentColor"):
    paths = {
        "archivo": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
        "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
        "lista": '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1.2"/><circle cx="4.5" cy="12" r="1.2"/><circle cx="4.5" cy="18" r="1.2"/>',
        "check": '<path d="M5 12.5l4.2 4.2L19 7"/>',
        "alerta": '<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4.5M12 17.6v.1"/>',
        "candado": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0"/>',
        "rayo": '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
        "usuario": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
        "enviar": '<path d="M12 19V5M5 12l7-7 7 7"/>',
        "flecha": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "bajar": '<path d="M12 4v12M6 10l6 6 6-6M5 20h14"/>',
        "lupa": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
        "chip": '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
        "globo": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
        "escudo": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
        "grafico": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
        "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        "estrella": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
        "codigo": '<path d="M8 6l-6 6 6 6M16 6l6 6-6 6"/>',
        "dinero": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/>',
    }
    p = paths.get(name, paths["rayo"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{p}</svg>')


def kw_text(s):
    """Texto con *destacado* para escenas (no subtítulos)."""
    parts = re.split(r"(\*[^*]+\*)", s)
    return "".join(f'<span class="acc">{esc(p[1:-1])}</span>' if p.startswith("*") else esc(p) for p in parts)


def fit(text, steps):
    n = len(text)
    for lim, px in steps:
        if n <= lim:
            return px
    return steps[-1][1]


def slide_skel(i, title):
    v = i % 4
    if v == 0:
        body = '<div class="sk w80"></div><div class="sk w60"></div><div class="sk w70"></div>'
    elif v == 1:
        body = '<div class="skc">' + "".join(f'<i style="height:{h}%"></i>' for h in (40, 65, 52, 88, 70)) + '</div>'
    elif v == 2:
        body = '<div class="skn">72%</div><div class="sk w50"></div>'
    else:
        body = '<div class="sk2"><div><div class="sk w90"></div><div class="sk w70"></div></div><div><div class="sk w80"></div><div class="sk w60"></div></div></div>'
    return f'<div class="cp-t">{esc(title)}</div><div class="cp-b">{body}</div>'


def scene_html(sid, b, D):
    e = b["escena"]; t = e["tipo"]; p = sid
    if t == "prompt":
        chars = "".join(f'<span class="ch">{esc(c) if c != " " else "&nbsp;"}</span>' if c != " " else '<span class="ch sp"> </span>'
                        for c in e.get("texto", ""))
        fs = fit(e.get("texto", ""), [(50, 58), (80, 52), (999, 46)])
        return (f'<div class="pr-wrap"><div class="glass pr-box" id="{p}-box"><div class="eyebrow">{esc(e.get("etiqueta", "Tu mensaje"))}</div>'
                f'<div class="pr-text" style="font-size:{fs}px">{chars}</div>'
                f'<div class="pr-foot"><div class="pr-tools"><span>+</span><span class="mono">Adjuntar</span></div>'
                f'<div class="pr-send" id="{p}-send">{icon("enviar", 44, "#0A0E1A")}</div></div></div>'
                f'<div class="pr-status mono" id="{p}-st"><span class="pr-spin"></span>{esc(e.get("estado", "Generando…"))}</div></div>')
    if t == "capas":
        items = (e.get("items") or ["", "", "", ""])[:5]
        sl = "".join(f'<div class="cp-slide glass" id="{p}-l{i}">{slide_skel(i, it)}</div>' for i, it in enumerate(reversed(items)))
        return f'<div class="cp-scene" id="{p}-sc">{sl}</div>'
    if t == "flujo":
        ins = e.get("entradas", [])[:3]
        n = len(ins)
        xs = [540] if n == 1 else ([300, 780] if n == 2 else [180, 540, 900])
        chips = "".join(f'<div class="fl-in glass" id="{p}-i{i}" style="left:{x - 160}px">{icon(it.get("icono", "archivo"), 54, "var(--acc)")}'
                        f'<div class="fl-lab">{esc(it.get("texto", ""))}</div></div>' for i, (it, x) in enumerate(zip(ins, xs)))
        paths = "".join(f'<path d="M{x} 250 C {x} 400, 540 380, 540 520" class="fl-p" id="{p}-p{i}" pathLength="1000"/>'
                        f'<path d="M{x} 250 C {x} 400, 540 380, 540 520" class="fl-d" id="{p}-d{i}" pathLength="1000"/>'
                        for i, x in enumerate(xs))
        thumbs = "".join(f'<div class="fl-th" id="{p}-t{i}"><i></i><b></b><b class="s"></b></div>' for i in range(4))
        return (f'<svg class="fl-svg" viewBox="0 0 1080 1010">{paths}</svg>{chips}'
                f'<div class="fl-out glass" id="{p}-o"><div class="eyebrow">{esc(e.get("salida", "Resultado"))}</div><div class="fl-grid">{thumbs}</div></div>')
    if t == "cursores":
        ppl = (e.get("personas") or ["Sofi", "Martín"])[:2]
        av = "".join(f'<div class="cu-av c{i}">{esc(n[0])}</div>' for i, n in enumerate(ppl))
        curs = "".join(f'<div class="cu-cur c{i}" id="{p}-c{i}"><svg width="46" height="46" viewBox="0 0 24 24"><path d="M4 2l15 9-7 1.5L8.5 20z" '
                       f'fill="currentColor" stroke="#0A0E1A" stroke-width="1.2"/></svg><span>{esc(n)}</span></div>' for i, n in enumerate(ppl))
        ant = e.get("antes", ""); dsp = e.get("despues", "")
        return (f'<div class="cu-doc glass" id="{p}-doc"><div class="cu-bar"><div class="cu-dots"><i></i><i></i><i></i></div>'
                f'<div class="mono cu-ed">Editando · {len(ppl) + 1}</div><div class="cu-avs">{av}<div class="cu-av me">Vos</div></div></div>'
                f'<div class="cu-canvas"><div class="cu-title"><span class="cu-old" id="{p}-old" style="font-size:{fit(ant, [(30, 56), (50, 46), (999, 40)])}px">{esc(ant)}</span>'
                f'<span class="cu-new" id="{p}-new">{esc(dsp)}</span><div class="cu-sel" id="{p}-sel"></div></div>'
                f'<div class="sk w80"></div><div class="sk w60"></div><div class="skc sm">' + "".join(f'<i style="height:{h}%"></i>' for h in (35, 60, 48, 80)) + '</div></div></div>'
                f'{curs}<div class="cu-com glass" id="{p}-com"><div class="cu-av c1">{esc(ppl[-1][0])}</div><div>{_mention(e.get("comentario", ""))}</div></div>'
                f'<div class="cu-ok mono" id="{p}-ok">{icon("check", 30, "var(--acc)")}{esc(e.get("aplicado", "Cambio aplicado por IA"))}</div>')
    if t == "chips":
        it = e.get("items", [])[:4]
        if e.get("estilo") == "archivo":
            rows = "".join(f'<div class="ch-file glass" id="{p}-k{i}"><div class="ch-doc"><svg width="96" height="118" viewBox="0 0 96 118"><path d="M8 2h56l30 30v78a6 6 0 0 1-6 6H8a6 6 0 0 1-6-6V8a6 6 0 0 1 6-6z" fill="#141C31" stroke="rgba(255,255,255,.22)" stroke-width="3"/><path d="M64 2v30h30" fill="none" stroke="rgba(255,255,255,.22)" stroke-width="3"/></svg>'
                           f'<span class="ch-ext">{esc(x.get("sub", ""))}</span></div><div class="ch-name">{esc(x.get("texto", ""))}</div>'
                           f'<div class="ch-dl" id="{p}-dl{i}">{icon("bajar", 44, "var(--acc)")}</div></div>' for i, x in enumerate(it))
            return f'<div class="ch-col">{rows}</div>'
        rows = "".join(f'<div class="ch-tag glass" id="{p}-k{i}">{icon(x.get("icono", "estrella"), 50, "var(--acc)")}<span>{esc(x.get("texto", ""))}</span></div>' for i, x in enumerate(it))
        bar = ""
        if e.get("barra"):
            bar = (f'<div class="ch-bar" id="{p}-bar"><div class="mono ch-bl"><span>{esc(e["barra"].get("texto", ""))}</span><span id="{p}-pct">0%</span></div>'
                   f'<div class="ch-track"><div class="ch-fill" id="{p}-fill"></div></div></div>')
        return f'<div class="ch-col tags">{rows}{bar}</div>'
    if t == "frase":
        words = []
        for i, w in enumerate(b["words"]):
            cls = "fr-w acc" if w["kw"] is not None else "fr-w"
            words.append(f'<span class="{cls}" id="{p}-w{i}">{esc(w["cap"])}</span>')
        txt = " ".join(w["cap"] for w in b["words"])
        fs = fit(txt, [(14, 150), (24, 128), (40, 108), (60, 90), (999, 76)])
        return f'<div class="fr-ring" id="{p}-ring"></div><div class="fr-box" style="font-size:{fs}px">{" ".join(words)}</div>'
    if t == "lista":
        it = e.get("items", [])[:4]
        rows = "".join(f'<div class="li-row glass" id="{p}-k{i}"><div class="li-ck"><svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="#0A0E1A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.2 4.2L19 7" pathLength="100" class="li-path" id="{p}-ck{i}"/></svg></div>'
                       f'<div class="li-t">{esc(x.get("texto", ""))}</div></div>' for i, x in enumerate(it))
        tit = f'<div class="eyebrow li-h">{esc(e["titulo"])}</div>' if e.get("titulo") else ""
        return f'<div class="li-col">{tit}{rows}</div>'
    if t == "reloj":
        ticks = "".join(f'<i style="transform:rotate({a}deg) translateY(-226px)" class="{"big" if a % 90 == 0 else ""}"></i>' for a in range(0, 360, 30))
        return (f'<div class="rl-face" id="{p}-face">{ticks}<div class="rl-arc" id="{p}-arc"></div><div class="rl-h" id="{p}-h"></div><div class="rl-m" id="{p}-m"></div><div class="rl-c"></div></div>'
                f'<div class="rl-txt"><span class="rl-a" id="{p}-a">{esc(e.get("antes", ""))}</span><span class="rl-b" id="{p}-b">{esc(e.get("despues", ""))}</span></div>')
    if t == "alerta":
        filas = e.get("filas", [])[:5]
        rows = "".join(f'<div class="al-row{" mk" if i == e.get("marcar") else ""}" id="{p}-r{i}"><span>{esc(a)}</span><span class="al-dots"></span><span class="mono">{esc(v)}</span></div>'
                       for i, (a, v) in enumerate(filas))
        return (f'<div class="al-card glass" id="{p}-card"><div class="al-head"><div class="al-ic" id="{p}-ic">{icon("alerta", 54, "#0A0E1A")}</div>'
                f'<div class="al-tt">{esc(e.get("titulo", "Atención"))}</div></div><div class="al-rows">{rows}</div></div>'
                f'<div class="al-lens" id="{p}-lens">{icon("lupa", 150, "#FFFFFF")}</div>')
    if t == "numero":
        return (f'<div class="nu-glow"></div><div class="nu-box"><div class="nu-v"><span class="nu-pre">{esc(e.get("prefijo", ""))}</span>'
                f'<span id="{p}-n">0</span><span class="nu-suf">{esc(e.get("sufijo", ""))}</span></div>'
                f'<div class="nu-l" id="{p}-l">{kw_text(e.get("etiqueta", ""))}</div></div>')
    if t == "navegador":
        tabs = e.get("pestanas") or ["Inicio"]
        th = "".join(f'<div class="nv-tab{" on" if i == 0 else ""}" id="{p}-tb{i}">{esc(x)}</div>' for i, x in enumerate(tabs[:3]))
        cards = "".join(f'<div class="nv-card" id="{p}-cd{i}"><i></i><b class="sk w80"></b><b class="sk w50"></b></div>' for i in range(4))
        return (f'<div class="nv-win glass" id="{p}-win"><div class="nv-top"><div class="cu-dots"><i></i><i></i><i></i></div>{th}</div>'
                f'<div class="nv-url mono">{icon("candado", 26, "var(--text-muted)")}<span id="{p}-url">{esc(e.get("url", ""))}</span></div>'
                f'<div class="nv-body"><div class="nv-h">{kw_text(e.get("titulo", ""))}</div><div class="nv-grid">{cards}</div></div></div>'
                f'<div class="nv-cursor" id="{p}-cur"><svg width="54" height="54" viewBox="0 0 24 24"><path d="M4 2l15 9-7 1.5L8.5 20z" fill="#fff" stroke="#0A0E1A" stroke-width="1.2"/></svg></div>')
    if t == "celular":
        msgs = e.get("mensajes", [])[:4]
        bub = "".join(f'<div class="ph-m {"me" if m.get("de") == "yo" else "ia"}" id="{p}-m{i}">{esc(m.get("texto", ""))}</div>' for i, m in enumerate(msgs))
        return (f'<div class="ph" id="{p}-ph"><div class="ph-notch"></div><div class="ph-top"><div class="ph-av">{icon(e.get("icono", "chip"), 34, "#0A0E1A")}</div>'
                f'<div><div class="ph-n">{esc(e.get("app", "Asistente"))}</div><div class="ph-s mono">en línea</div></div></div><div class="ph-body">{bub}'
                f'<div class="ph-typing" id="{p}-ty"><i></i><i></i><i></i></div></div></div>')
    if t == "grafico":
        bars = e.get("barras", [])[:5]
        mx = max([float(x.get("valor", 0)) for x in bars] + [1])
        bh = "".join(f'<div class="gr-col"><div class="gr-v mono" id="{p}-v{i}">{esc(x.get("texto", x.get("valor", "")))}</div>'
                     f'<div class="gr-b{" hi" if i == e.get("marcar", len(bars) - 1) else ""}" id="{p}-b{i}" style="height:{int(560 * float(x.get("valor", 0)) / mx)}px"></div>'
                     f'<div class="gr-l">{esc(x.get("label", ""))}</div></div>' for i, x in enumerate(bars))
        return f'<div class="gr-wrap glass"><div class="eyebrow">{esc(e.get("titulo", ""))}</div><div class="gr-cols">{bh}</div></div>'
    if t == "comparacion":
        a = e.get("antes", {}); d = e.get("despues", {})
        col = lambda x, cls, ic: (f'<div class="cm-col {cls} glass" id="{p}-{cls}"><div class="eyebrow">{esc(x.get("titulo", ""))}</div>' +
                                  "".join(f'<div class="cm-it">{icon(ic, 34, "currentColor")}<span>{esc(s)}</span></div>' for s in x.get("items", [])[:4]) + '</div>')
        return f'<div class="cm-wrap">{col(a, "an", a.get("icono", "reloj"))}<div class="cm-vs mono" id="{p}-vs">VS</div>{col(d, "de", d.get("icono", "check"))}</div>'
    if t == "particulas":
        return (f'<canvas class="pa-cv" id="{p}-cv" width="1080" height="1010"></canvas><div class="pa-box"><div class="nu-v sm"><span class="nu-pre">{esc(e.get("prefijo", ""))}</span>'
                f'<span id="{p}-n">0</span><span class="nu-suf">{esc(e.get("sufijo", ""))}</span></div><div class="nu-l">{kw_text(e.get("etiqueta", ""))}</div></div>')
    if t == "terminal":
        rows = []
        for i, ln in enumerate(e.get("lineas", [])[:7]):
            k = ln.get("tipo", "out")
            txt = ln.get("texto", "")
            if k == "cmd":
                chars = "".join(f'<span class="ch">{esc(c)}</span>' for c in txt)
                rows.append(f'<div class="tm-l cmd" id="{p}-ln{i}"><span class="tm-pr">&gt;</span><span>{chars}</span></div>')
            elif k == "ok":
                rows.append(f'<div class="tm-l ok" id="{p}-ln{i}">{icon("check", 34, "var(--acc)")}<span>{esc(txt)}</span></div>')
            else:
                rows.append(f'<div class="tm-l out" id="{p}-ln{i}"><span class="tm-dot">⏺</span><span>{esc(txt)}</span></div>')
        return (f'<div class="tm-win" id="{p}-win"><div class="tm-top"><div class="cu-dots"><i></i><i></i><i></i></div>'
                f'<div class="mono tm-t">{esc(e.get("titulo", "claude — ~/mi-proyecto"))}</div></div>'
                f'<div class="tm-body mono">{"".join(rows)}<div class="tm-cur" id="{p}-cur"></div></div></div>')
    if t == "linea_tiempo":
        hs = e.get("hitos", [])[:4]
        n = max(1, len(hs))
        gap = 860 // n
        items = "".join(f'<div class="lt-h" id="{p}-h{i}" style="top:{60 + i * gap}px"><div class="lt-dot" id="{p}-d{i}"></div>'
                        f'<div class="lt-y">{esc(h.get("anio", ""))}</div><div class="lt-t">{kw_text(h.get("texto", ""))}</div></div>'
                        for i, h in enumerate(hs))
        return f'<div class="lt-rail"></div><div class="lt-fill" id="{p}-fill"></div>{items}'
    if t == "cierre":
        return (f'<div class="end"><img id="{p}-mark" src="assets/mark-white.svg" alt="TobDev"/>'
                f'<div class="wm" id="{p}-wm">Tob<span class="grad">Dev</span></div>'
                f'<div class="sub" id="{p}-sub">{esc(e.get("sub", "Sistemas e IA para tu PyME"))}</div>'
                f'<div class="cta" id="{p}-cta">{esc(e.get("cta", "Seguí a @tobdev.ia"))}{icon("flecha", 40, "#fff")}</div>'
                f'<div class="src mono" id="{p}-src">{esc(e.get("fuente_txt", ""))}</div></div>')
    return ""


def _mention(s):
    return re.sub(r"(@\w+)", lambda m: f'<b class="acc">{m.group(1)}</b>', esc(s))


def scene_params(b, t0, t1):
    e = b["escena"]; t = e["tipo"]; p = {"tipo": t}
    if t in ("chips", "lista"):
        p["cues"] = scene_cues(b, [x.get("en", x.get("texto", "")) for x in e.get("items", [])][:4], t0, t1)
        p["n"] = len(p["cues"])
        if e.get("barra"):
            p["bar"] = scene_cues(b, [e["barra"].get("en", "")], t0, t1)[0]
            p["val"] = float(e["barra"].get("valor", 0.5))
    elif t == "flujo":
        ins = e.get("entradas", [])[:3]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in ins], t0, t1)
        p["n"] = len(ins)
        p["out"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        if p["out"] <= p["cues"][-1]:
            p["out"] = p["cues"][-1] + 0.6
    elif t == "cursores":
        c, = scene_cues(b, [e.get("en_comentario", "")], t0, t1)
        d, = scene_cues(b, [e.get("en_cambio", "")], t0, t1)
        p.update(com=c, chg=max(d, c + 0.8), n=len((e.get("personas") or ["a", "b"])[:2]))
    elif t == "frase":
        p["cues"] = [round(w["t0"], 3) for w in b["words"]]
    elif t in ("reloj", "alerta"):
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        if t == "alerta":
            p["mk"] = e.get("marcar", -1); p["n"] = len(e.get("filas", [])[:5])
    elif t == "terminal":
        lns = e.get("lineas", [])[:7]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in lns], t0, t1)
        for i in range(1, len(p["cues"])):
            if p["cues"][i] <= p["cues"][i - 1] + 0.25:
                p["cues"][i] = round(p["cues"][i - 1] + 0.45, 3)
        p["tipos"] = [x.get("tipo", "out") for x in lns]
        p["lens"] = [len(x.get("texto", "")) for x in lns]
    elif t == "linea_tiempo":
        hs = e.get("hitos", [])[:4]
        p["cues"] = scene_cues(b, [x.get("en", x.get("anio", "")) for x in hs], t0, t1)
        p["n"] = len(hs)
    elif t in ("numero", "particulas"):
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p.update(val=float(e.get("valor", 100)), dec=int(e.get("decimales", 0)), desde=float(e.get("desde", 0)),
                 sep=bool(e.get("separador", True)))
    elif t == "navegador":
        p["n"] = len((e.get("pestanas") or ["x"])[:3])
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "celular":
        p["cues"] = scene_cues(b, [m.get("en", "") for m in e.get("mensajes", [])[:4]], t0, t1)
        p["me"] = [m.get("de") == "yo" for m in e.get("mensajes", [])[:4]]
    elif t == "grafico":
        p["n"] = len(e.get("barras", [])[:5])
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "comparacion":
        p["cues"] = scene_cues(b, [e.get("antes", {}).get("en", ""), e.get("despues", {}).get("en", "")], t0, t1)
    elif t == "prompt":
        p["n"] = len(e.get("texto", ""))
    elif t == "capas":
        p["n"] = len((e.get("items") or ["", "", "", ""])[:5])
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    return p


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def build_html(guion, beats, groups, D):
    acc = guion.get("acento", "#11BFD6")
    r, g, bl = hex_rgb(acc)
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";font-weight:{w};font-style:normal;font-display:block;src:url("assets/fonts/{fn}-{w}.{ext}") format("{fmt}");}}\n'
        for fam, fn, ws, ext, fmt in (("FreeSans", "FreeSans", (400, 700), "ttf", "truetype"),
                                      ("JetBrains Mono", "JetBrainsMono", (400, 500, 700), "woff2", "woff2"))
        for w in ws)
    css = (CSS.replace("__ACC__", acc).replace("__ACCRGB__", f"{r},{g},{bl}"))
    # escenas
    sc_html, calls = [], []
    n = len(beats)
    for i, b in enumerate(beats):
        t0 = 0.0 if i == 0 else round(b["t_speech"] - 0.32, 3)
        t1 = round(D, 3) if i == n - 1 else round(beats[i + 1]["t_speech"] + 0.08, 3)
        b["t0"], b["t1"] = t0, t1
        sid = f"s{i}"
        if b["escena"]["tipo"] == "cierre":
            b["escena"].setdefault("fuente_txt", f'Fuente: {guion.get("fuente", "")}' if guion.get("fuente") else "")
        sc_html.append(f'<div id="{sid}" class="clip scene t-{b["escena"]["tipo"]}" data-start="{t0}" data-duration="{round(t1 - t0, 3)}" data-track-index="{1 + i % 2}">'
                       f'<div class="stage"><div class="cam"><div class="drift">{scene_html(sid, b, D)}</div></div></div></div>')
        prm = scene_params(b, t0, t1)
        calls.append({"id": sid, "t0": t0, "t1": t1, "k": i, "first": i == 0, "last": i == n - 1, "p": prm})
    # subtítulos
    cap_html, cap_js = [], []
    for gi, g in enumerate(groups):
        spans, prev_kw = [], None
        ws = g["words"]
        j = 0
        while j < len(ws):
            w = ws[j]
            if w["kw"] is not None:
                k = j
                inner = []
                while k < len(ws) and ws[k]["kw"] == w["kw"]:
                    inner.append(f'<span class="w kwd" id="w{gi}_{k}">{esc(ws[k]["cap"])}</span>')
                    k += 1
                spans.append(f'<span class="kw" id="k{gi}_{j}"><span class="kb"><i></i><i></i><i></i><i></i></span>{" ".join(inner)}</span>')
                j = k
            else:
                spans.append(f'<span class="w" id="w{gi}_{j}">{esc(w["cap"])}</span>')
                j += 1
        cap_html.append(f'<div class="cap" id="g{gi}">{" ".join(spans)}</div>')
        cap_js.append({"g": gi, "t0": round(g["t0"], 3), "t1": round(g["t1"], 3),
                       "w": [[f"w{gi}_{k}", round(w["t0"], 3), round(ws[k + 1]["t0"] if k + 1 < len(ws) else g["t1"], 3), w["kw"] is not None] for k, w in enumerate(ws)],
                       "k": [[f"k{gi}_{k}", round(w["t0"], 3)] for k, w in enumerate(ws) if w["kw"] is not None and (k == 0 or ws[k - 1]["kw"] != w["kw"])]})
    end_t = beats[-1]["t0"] if beats[-1]["escena"]["tipo"] == "cierre" else D
    hdr = (f'<div id="hdr" class="clip hdr" data-start="0" data-duration="{round(end_t + 0.3, 3)}" data-track-index="4">'
           f'<img src="assets/mark-white.svg" alt=""/><span class="h">tobdev.ia</span><span class="d">{esc(guion.get("etiqueta", guion.get("fecha", "")))}</span></div>')
    js = (JS.replace("__ACC__", acc).replace("__D__", str(round(D, 3)))
          .replace("__CALLS__", json.dumps(calls)).replace("__CAPS__", json.dumps(cap_js))
          .replace("__ENDT__", str(round(end_t, 3))))
    return f"""<!doctype html>
<html lang="es"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<script src="assets/gsap.min.js"></script><style>{fonts}{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{round(D, 3)}" data-width="1080" data-height="1920">
<div id="bg" class="clip" data-start="0" data-duration="{round(D, 3)}" data-track-index="0">
  <div class="blob" id="b1"></div><div class="blob" id="b2"></div><div class="blob" id="b3"></div><div class="blob" id="b4"></div>
  <div id="floor"></div><div id="vig"></div><div id="grain"></div>
</div>
{"".join(sc_html)}
<div id="caps" class="clip" data-start="0" data-duration="{round(D, 3)}" data-track-index="3">{"".join(cap_html)}</div>
{hdr}
<div id="prog"></div>
<audio id="el-audio" src="assets/audio.mp3" data-start="0" data-duration="{round(D, 3)}" data-track-index="11" data-volume="1"></audio>
</div>
<script>{js}</script>
</body></html>"""


CSS = r"""
:root{--bg:#0A0E1A;--text:#FFFFFF;--text-soft:#C6CFE0;--text-muted:#8A97B0;--cyan:#11BFD6;--violet:#5B6FE4;
--acc:__ACC__;--acc-rgb:__ACCRGB__;--grad:linear-gradient(135deg,#5B6FE4 0%,#11BFD6 100%);
--display:"FreeSans","Helvetica Neue",Arial,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace;--warn:#FFB020}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:var(--bg)}
#root{position:absolute;inset:0;font-family:var(--display);color:var(--text)}
.mono{font-family:var(--mono)}
#bg{position:absolute;inset:0;background:var(--bg);overflow:hidden}
.blob{position:absolute;border-radius:50%}
#b1{width:1400px;height:1400px;left:150px;top:-640px;background:radial-gradient(circle,rgba(91,111,228,.30) 0%,rgba(91,111,228,0) 62%)}
#b2{width:1300px;height:1300px;left:-560px;top:1100px;background:radial-gradient(circle,rgba(17,191,214,.22) 0%,rgba(17,191,214,0) 62%)}
#b3{width:1100px;height:1100px;left:300px;top:520px;background:radial-gradient(circle,rgba(var(--acc-rgb),.16) 0%,rgba(var(--acc-rgb),0) 62%)}
#b4{width:800px;height:800px;left:-300px;top:200px;background:radial-gradient(circle,rgba(91,111,228,.12) 0%,rgba(91,111,228,0) 62%)}
#floor{position:absolute;left:-540px;right:-540px;top:1180px;height:1200px;transform:perspective(900px) rotateX(64deg);transform-origin:50% 0;
background-image:radial-gradient(circle,rgba(255,255,255,.16) 1.6px,transparent 2px);background-size:56px 56px;
-webkit-mask-image:linear-gradient(to bottom,rgba(0,0,0,.9),transparent 75%);mask-image:linear-gradient(to bottom,rgba(0,0,0,.9),transparent 75%)}
#vig{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,transparent 50%,rgba(0,0,0,.55) 100%)}
#grain{position:absolute;inset:0;opacity:.05;background:url("assets/grain.png") repeat}
.hdr{position:absolute;left:70px;right:70px;top:150px;height:44px;display:flex;align-items:center;gap:14px;opacity:.85}
.hdr img{width:40px;height:40px}.hdr .h{font-family:var(--mono);font-weight:500;font-size:24px;color:var(--text-soft)}
.hdr .d{margin-left:auto;font-family:var(--mono);font-weight:500;font-size:22px;letter-spacing:.18em;color:var(--text-muted)}
.cap{position:absolute;left:60px;right:60px;top:236px;text-align:center;font-weight:700;font-size:72px;line-height:1.16;letter-spacing:-.02em;opacity:0;
text-shadow:0 4px 24px rgba(0,0,0,.6)}
.cap .w{display:inline-block;opacity:0}
.kw{position:relative;display:inline-block;white-space:nowrap;padding:0 .1em;margin:0 .02em}
.kb{position:absolute;left:-8px;right:-8px;top:2px;bottom:-4px;border:3px solid var(--acc);border-radius:6px;background:rgba(var(--acc-rgb),.16);opacity:0}
.kb i{position:absolute;width:14px;height:14px;background:#fff;border:3px solid var(--acc);border-radius:3px}
.kb i:nth-child(1){left:-9px;top:-9px}.kb i:nth-child(2){right:-9px;top:-9px}.kb i:nth-child(3){left:-9px;bottom:-9px}.kb i:nth-child(4){right:-9px;bottom:-9px}
.scene{position:absolute;inset:0}
.stage{position:absolute;left:0;top:470px;width:1080px;height:1010px;perspective:1600px}
.cam,.drift{position:absolute;inset:0;transform-style:preserve-3d}
.glass{background:rgba(14,20,36,.93);border:1px solid rgba(255,255,255,.11);border-radius:28px;box-shadow:0 40px 90px -30px rgba(0,0,0,.95)}
.eyebrow{font-family:var(--mono);font-weight:500;font-size:26px;letter-spacing:.18em;text-transform:uppercase;color:var(--acc)}
.acc{color:var(--acc)}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.sk{height:22px;border-radius:11px;background:rgba(255,255,255,.12);margin-top:18px}
.w90{width:90%}.w80{width:80%}.w70{width:70%}.w60{width:60%}.w50{width:50%}
.skc{display:flex;align-items:flex-end;gap:14px;height:150px;margin-top:22px}.skc i{flex:1;border-radius:8px 8px 0 0;background:rgba(var(--acc-rgb),.75)}
.skc.sm{height:120px;width:60%}
.skn{font-weight:700;font-size:96px;color:var(--acc);letter-spacing:-.03em;margin-top:6px}
.sk2{display:flex;gap:30px}.sk2>div{flex:1}
/* prompt */
.pr-wrap{position:absolute;left:70px;right:70px;top:200px}
.pr-box{padding:44px 48px 36px;border:2px solid rgba(var(--acc-rgb),.45);box-shadow:0 0 0 10px rgba(var(--acc-rgb),.06),0 40px 90px -30px rgba(0,0,0,.95)}
.pr-text{margin-top:26px;min-height:260px;line-height:1.3;color:#fff}
.ch{opacity:0}
.pr-foot{margin-top:30px;display:flex;align-items:center;justify-content:space-between}
.pr-tools{display:flex;align-items:center;gap:16px;color:var(--text-muted);font-size:26px}.pr-tools span:first-child{font-size:44px;line-height:1}
.pr-send{width:84px;height:84px;border-radius:50%;background:var(--acc);display:flex;align-items:center;justify-content:center}
.pr-status{margin-top:40px;display:flex;align-items:center;gap:18px;font-size:30px;color:var(--text-soft);opacity:0;padding-left:8px}
.pr-spin{width:30px;height:30px;border-radius:50%;border:4px solid rgba(var(--acc-rgb),.25);border-top-color:var(--acc)}
/* capas */
.cp-scene{position:absolute;left:210px;top:310px;width:660px;height:380px;transform-style:preserve-3d;transform:rotateX(56deg) rotateZ(-30deg)}
.cp-slide{position:absolute;inset:0;padding:40px 44px;border:2px solid rgba(255,255,255,.14);opacity:0}
.cp-t{font-weight:700;font-size:44px;letter-spacing:-.02em}
/* flujo */
.fl-svg{position:absolute;inset:0;width:1080px;height:1010px;overflow:visible}
.fl-p{fill:none;stroke:rgba(255,255,255,.16);stroke-width:4;stroke-dasharray:1000;stroke-dashoffset:1000}
.fl-d{fill:none;stroke:var(--acc);stroke-width:7;stroke-linecap:round;stroke-dasharray:60 1000;stroke-dashoffset:60;opacity:0}
.fl-in{position:absolute;top:50px;width:320px;height:200px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;opacity:0}
.fl-lab{font-size:30px;font-weight:700;letter-spacing:-.01em;text-align:center;padding:0 16px}
.fl-out{position:absolute;left:150px;top:520px;width:780px;height:440px;padding:36px 40px;opacity:0;border:2px solid rgba(var(--acc-rgb),.45)}
.fl-grid{margin-top:26px;display:grid;grid-template-columns:1fr 1fr;gap:22px}
.fl-th{height:140px;border-radius:16px;background:#141C31;border:1px solid rgba(255,255,255,.1);padding:18px;opacity:0}
.fl-th i{display:block;width:50%;height:18px;border-radius:9px;background:rgba(var(--acc-rgb),.85)}
.fl-th b{display:block;width:85%;height:12px;border-radius:6px;background:rgba(255,255,255,.14);margin-top:16px}.fl-th b.s{width:60%}
/* cursores */
.cu-doc{position:absolute;left:60px;right:60px;top:80px;height:700px;overflow:hidden}
.cu-bar{height:96px;display:flex;align-items:center;gap:24px;padding:0 30px;border-bottom:1px solid rgba(255,255,255,.08)}
.cu-dots{display:flex;gap:10px}.cu-dots i{width:16px;height:16px;border-radius:50%;background:rgba(255,255,255,.18)}
.cu-ed{font-size:24px;color:var(--text-muted)}
.cu-avs{margin-left:auto;display:flex}
.cu-av{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:24px;color:#0A0E1A;border:3px solid #0E1424;margin-left:-12px;flex:none}
.cu-av.c0,.cu-cur.c0{background:#FF8A5B;color:#0A0E1A}.cu-av.c1,.cu-cur.c1{background:#B48CFF;color:#0A0E1A}
.cu-cur.c0{color:#FF8A5B;background:none}.cu-cur.c1{color:#B48CFF;background:none}
.cu-av.me{background:var(--acc);font-size:18px}
.cu-canvas{padding:50px 50px}
.cu-title{position:relative;min-height:150px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.cu-new{position:absolute;left:0;top:0;font-size:84px;opacity:0;color:#fff}
.cu-sel{position:absolute;left:-14px;top:-10px;width:640px;height:118px;border:3px solid var(--acc);border-radius:8px;opacity:0;background:rgba(var(--acc-rgb),.08)}
.cu-cur{position:absolute;left:0;top:0;display:flex;align-items:flex-start;gap:4px}
.cu-cur span{margin-top:34px;padding:6px 14px;border-radius:10px;font-weight:700;font-size:24px;color:#0A0E1A}
.cu-cur.c0 span{background:#FF8A5B}.cu-cur.c1 span{background:#B48CFF}
.cu-com{position:absolute;left:220px;right:40px;top:730px;padding:26px 30px;display:flex;gap:22px;align-items:center;font-size:36px;opacity:0;border:2px solid rgba(var(--acc-rgb),.35)}
.cu-com .cu-av{margin-left:0}
.cu-ok{position:absolute;left:90px;top:650px;display:flex;align-items:center;gap:12px;font-size:26px;color:var(--acc);opacity:0}
/* chips */
.ch-col{position:absolute;left:90px;right:90px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:34px}
.ch-file{height:200px;display:flex;align-items:center;gap:36px;padding:0 44px;opacity:0}
.ch-doc{position:relative;width:96px;height:118px;flex:none}
.ch-ext{position:absolute;left:-14px;bottom:12px;padding:5px 10px;border-radius:8px;background:var(--acc);color:#0A0E1A;font-family:var(--mono);font-weight:700;font-size:20px}
.ch-name{font-weight:700;font-size:56px;letter-spacing:-.02em}
.ch-dl{margin-left:auto;width:84px;height:84px;border-radius:50%;border:2px solid rgba(var(--acc-rgb),.5);display:flex;align-items:center;justify-content:center}
.ch-col.tags{align-items:center}
.ch-tag{display:flex;align-items:center;gap:26px;height:150px;padding:0 60px;font-weight:700;font-size:66px;letter-spacing:-.02em;opacity:0;border:2px solid rgba(var(--acc-rgb),.4)}
.ch-bar{width:100%;margin-top:30px;opacity:0}
.ch-bl{display:flex;justify-content:space-between;font-size:28px;color:var(--text-soft);letter-spacing:.08em;text-transform:uppercase}
.ch-track{margin-top:16px;height:22px;border-radius:11px;background:rgba(255,255,255,.1);overflow:hidden}
.ch-fill{height:100%;width:100%;border-radius:11px;background:var(--acc);transform-origin:0 50%;transform:scaleX(0)}
/* frase */
.fr-box{position:absolute;left:70px;right:70px;top:0;bottom:0;display:flex;flex-wrap:wrap;align-content:center;justify-content:center;gap:0 .26em;
font-weight:700;line-height:1.06;letter-spacing:-.03em;text-align:center}
.fr-w{display:inline-block;opacity:0}
.fr-ring{position:absolute;left:190px;top:155px;width:700px;height:700px;border-radius:50%;border:3px solid rgba(var(--acc-rgb),.35);
box-shadow:0 0 120px rgba(var(--acc-rgb),.25),inset 0 0 80px rgba(var(--acc-rgb),.12);opacity:0}
/* lista */
.li-col{position:absolute;left:90px;right:90px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:30px}
.li-h{margin-bottom:10px}
.li-row{display:flex;align-items:center;gap:34px;min-height:170px;padding:24px 44px;opacity:0}
.li-ck{width:84px;height:84px;border-radius:50%;background:var(--acc);display:flex;align-items:center;justify-content:center;flex:none}
.li-path{stroke-dasharray:100;stroke-dashoffset:100}
.li-t{font-weight:700;font-size:58px;letter-spacing:-.02em;line-height:1.1}
/* reloj */
.rl-face{position:absolute;left:290px;top:60px;width:500px;height:500px;border-radius:50%;background:rgba(14,20,36,.93);border:3px solid rgba(255,255,255,.14);
box-shadow:0 0 0 14px rgba(255,255,255,.03),0 40px 90px -30px rgba(0,0,0,.95)}
.rl-face i{position:absolute;left:246px;top:242px;width:8px;height:16px;border-radius:4px;background:rgba(255,255,255,.3)}.rl-face i.big{height:26px;background:#fff}
.rl-arc{position:absolute;inset:26px;border-radius:50%;background:conic-gradient(rgba(var(--acc-rgb),.35) 0deg,rgba(var(--acc-rgb),.35) var(--arc,0deg),transparent var(--arc,0deg))}
.rl-h,.rl-m{position:absolute;left:244px;bottom:250px;width:12px;border-radius:6px;transform-origin:50% 100%}
.rl-h{height:120px;background:#fff}.rl-m{height:190px;width:8px;left:246px;background:var(--acc)}
.rl-c{position:absolute;left:232px;top:232px;width:36px;height:36px;border-radius:50%;background:#fff;border:6px solid var(--acc)}
.rl-txt{position:absolute;left:0;right:0;top:640px;height:200px;text-align:center}
.rl-a,.rl-b{position:absolute;left:0;right:0;font-weight:700;letter-spacing:-.03em}
.rl-a{font-size:100px;color:var(--text-muted)}.rl-b{font-size:150px;color:var(--acc);opacity:0}
.rl-a::after{content:"";position:absolute;left:28%;right:28%;top:52%;height:8px;border-radius:4px;background:var(--warn);transform:scaleX(var(--st,0));transform-origin:0 50%}
/* alerta */
.al-card{position:absolute;left:70px;right:70px;top:170px;padding:44px 48px;border:2px solid rgba(255,176,32,.35)}
.al-head{display:flex;align-items:center;gap:26px}
.al-ic{width:92px;height:92px;border-radius:24px;background:var(--warn);display:flex;align-items:center;justify-content:center;flex:none}
.al-tt{font-weight:700;font-size:54px;letter-spacing:-.02em;line-height:1.05}
.al-rows{margin-top:38px}
.al-row{display:flex;align-items:baseline;gap:18px;font-size:40px;padding:26px 18px;border-top:1px solid rgba(255,255,255,.08);border-radius:14px}
.al-row .mono{font-size:38px;font-weight:700}
.al-dots{flex:1;border-bottom:3px dotted rgba(255,255,255,.18)}
.al-lens{position:absolute;left:700px;top:610px;opacity:0;filter:drop-shadow(0 10px 30px rgba(0,0,0,.6))}
/* numero */
.nu-glow{position:absolute;left:140px;top:110px;width:800px;height:800px;border-radius:50%;background:radial-gradient(circle,rgba(var(--acc-rgb),.28),transparent 65%)}
.nu-box{position:absolute;left:40px;right:40px;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.nu-v{font-weight:700;font-size:230px;letter-spacing:-.05em;line-height:1;white-space:nowrap}.nu-v.sm{font-size:170px}
.nu-pre,.nu-suf{color:var(--acc)}
.nu-l{margin-top:30px;font-size:52px;font-weight:700;color:var(--text-soft);text-align:center;letter-spacing:-.01em;line-height:1.15;max-width:900px}
/* navegador */
.nv-win{position:absolute;left:50px;right:50px;top:40px;height:880px;overflow:hidden}
.nv-top{height:84px;display:flex;align-items:flex-end;gap:12px;padding:0 26px;background:rgba(255,255,255,.03)}
.nv-top .cu-dots{align-self:center;margin-right:14px}
.nv-tab{height:62px;padding:0 26px;display:flex;align-items:center;border-radius:14px 14px 0 0;font-size:26px;color:var(--text-muted);background:rgba(255,255,255,.04)}
.nv-tab.on{background:#141C31;color:#fff}
.nv-url{margin:22px 26px 0;height:64px;border-radius:32px;background:#141C31;display:flex;align-items:center;gap:14px;padding:0 26px;font-size:26px;color:var(--text-soft)}
.nv-body{padding:40px 40px}
.nv-h{font-weight:700;font-size:60px;letter-spacing:-.02em;line-height:1.08}
.nv-grid{margin-top:36px;display:grid;grid-template-columns:1fr 1fr;gap:24px}
.nv-card{height:220px;border-radius:20px;background:#141C31;border:1px solid rgba(255,255,255,.08);padding:22px;opacity:0}
.nv-card i{display:block;height:90px;border-radius:12px;background:rgba(var(--acc-rgb),.35)}
.nv-cursor{position:absolute;left:600px;top:700px}
/* celular */
.ph{position:absolute;left:250px;top:-10px;width:580px;height:1030px;border-radius:70px;background:#0B1020;border:10px solid #1C2540;box-shadow:0 50px 100px -30px rgba(0,0,0,.95),0 0 0 2px rgba(255,255,255,.08);overflow:hidden}
.ph-notch{position:absolute;left:200px;top:18px;width:160px;height:40px;border-radius:20px;background:#000}
.ph-top{margin-top:84px;display:flex;align-items:center;gap:18px;padding:0 30px 24px;border-bottom:1px solid rgba(255,255,255,.08)}
.ph-av{width:66px;height:66px;border-radius:50%;background:var(--acc);display:flex;align-items:center;justify-content:center}
.ph-n{font-weight:700;font-size:32px}.ph-s{font-size:20px;color:var(--acc)}
.ph-body{padding:30px 26px;display:flex;flex-direction:column;gap:20px}
.ph-m{max-width:86%;padding:20px 24px;border-radius:26px;font-size:30px;line-height:1.3;opacity:0}
.ph-m.me{align-self:flex-end;background:var(--acc);color:#0A0E1A;border-bottom-right-radius:8px}
.ph-m.ia{align-self:flex-start;background:#18213A;border-bottom-left-radius:8px}
.ph-typing{align-self:flex-start;display:flex;gap:10px;padding:22px 26px;border-radius:26px;background:#18213A;opacity:0}
.ph-typing i{width:14px;height:14px;border-radius:50%;background:var(--text-muted)}
/* grafico */
.gr-wrap{position:absolute;left:60px;right:60px;top:40px;bottom:40px;padding:44px}
.gr-cols{position:absolute;left:44px;right:44px;bottom:44px;top:120px;display:flex;align-items:flex-end;gap:28px}
.gr-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.gr-b{width:100%;border-radius:16px 16px 6px 6px;background:rgba(255,255,255,.16);transform-origin:50% 100%;transform:scaleY(0)}
.gr-b.hi{background:var(--acc);box-shadow:0 0 50px rgba(var(--acc-rgb),.4)}
.gr-v{font-size:34px;font-weight:700;margin-bottom:14px;opacity:0}
.gr-l{margin-top:18px;font-size:28px;color:var(--text-soft);text-align:center}
/* comparacion */
.cm-wrap{position:absolute;left:50px;right:50px;top:30px;bottom:30px}
.cm-col{position:absolute;left:0;right:0;height:430px;padding:40px 44px;opacity:0}
.cm-col.an{top:0;color:var(--text-muted)}.cm-col.an .eyebrow{color:var(--text-muted)}
.cm-col.de{bottom:0;border:2px solid rgba(var(--acc-rgb),.5)}
.cm-it{display:flex;align-items:center;gap:20px;font-size:42px;font-weight:700;margin-top:24px;letter-spacing:-.01em}
.cm-col.de .cm-it svg{color:var(--acc)}
.cm-vs{position:absolute;left:470px;top:440px;width:100px;height:100px;border-radius:50%;background:#141C31;border:2px solid rgba(255,255,255,.18);
display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:700;opacity:0}
/* particulas */
.pa-cv{position:absolute;left:0;top:0;width:1080px;height:1010px}
.pa-box{position:absolute;left:60px;right:60px;top:300px;padding:40px;text-align:center;background:radial-gradient(ellipse,rgba(10,14,26,.92) 30%,transparent 72%)}
/* terminal */
.tm-win{position:absolute;left:50px;right:50px;top:150px;height:640px;border-radius:28px;background:#0B0F1C;border:1px solid rgba(255,255,255,.12);
box-shadow:0 40px 90px -30px rgba(0,0,0,.95),0 0 0 8px rgba(var(--acc-rgb),.05);overflow:hidden}
.tm-top{height:76px;display:flex;align-items:center;gap:24px;padding:0 28px;background:rgba(255,255,255,.04);border-bottom:1px solid rgba(255,255,255,.07)}
.tm-t{font-size:24px;color:var(--text-muted)}
.tm-body{padding:44px 44px;font-size:40px;line-height:1.38}
.tm-l{display:flex;gap:18px;align-items:flex-start;margin-bottom:26px;opacity:0}
.tm-l.cmd{color:#fff;font-weight:700}.tm-pr{color:var(--acc)}
.tm-l.out{color:var(--text-soft)}.tm-dot{color:var(--acc);font-size:26px;margin-top:6px}
.tm-l.ok{color:var(--acc);font-weight:700}.tm-l.ok svg{flex:none;margin-top:6px}
.tm-cur{width:20px;height:40px;background:var(--acc);opacity:0}
/* linea de tiempo */
.lt-rail,.lt-fill{position:absolute;left:170px;top:80px;width:6px;height:860px;border-radius:3px;background:rgba(255,255,255,.12)}
.lt-fill{background:var(--acc);transform-origin:50% 0;transform:scaleY(0);box-shadow:0 0 30px rgba(var(--acc-rgb),.5)}
.lt-h{position:absolute;left:0;right:60px;height:200px;opacity:0}
.lt-dot{position:absolute;left:153px;top:22px;width:40px;height:40px;border-radius:50%;background:#0A0E1A;border:6px solid var(--acc)}
.lt-y{position:absolute;left:230px;top:-6px;font-weight:700;font-size:92px;letter-spacing:-.04em;line-height:1;color:var(--acc)}
.lt-t{position:absolute;left:232px;right:0;top:100px;font-size:40px;font-weight:700;line-height:1.15;color:var(--text-soft);letter-spacing:-.01em}
/* cierre */
.end{position:absolute;left:84px;right:84px;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.end img{width:260px;height:260px}
.wm{margin-top:10px;font-weight:700;font-size:150px;letter-spacing:-.03em;line-height:1}
.sub{margin-top:30px;font-size:46px;color:var(--text-soft)}
.cta{margin-top:60px;display:flex;align-items:center;gap:18px;padding:30px 54px;border-radius:24px;background:var(--grad);font-weight:700;font-size:46px;color:#fff;box-shadow:0 10px 30px -8px rgba(91,111,228,.55)}
.src{margin-top:50px;font-size:26px;color:var(--text-muted)}
#prog{position:absolute;left:0;bottom:0;width:100%;height:6px;background:var(--grad);transform-origin:0 50%}
"""

JS = r"""
(function(){
const tl = gsap.timeline({paused:true});
const ACC = "__ACC__", D = __D__, MUT = "#7D8AA5";
const E = "power3.out";
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
function F(el, from, to, at){ to.immediateRender = false; return tl.fromTo(el, from, to, at); }
function show(el, at, d, from){ return F(el, Object.assign({opacity:0}, from||{y:40}), {opacity:1, x:0, y:0, scale:1, rotation:0, duration:d||.5, ease:E}, at); }
function pop(el, at){ return F(el, {opacity:0, scale:.6}, {opacity:1, scale:1, duration:.45, ease:"back.out(1.8)"}, at); }
function seeded(n){ let s = n*9301+49297; return () => { s = (s*9301+49297) % 233280; return s/233280; }; }
const fmt = (v, dec, sep) => sep === false ? v.toFixed(dec) : v.toLocaleString("es-AR", {minimumFractionDigits:dec, maximumFractionDigits:dec});

// fondo
tl.fromTo("#b1",{x:0,y:0},{x:-170,y:100,duration:D,ease:"sine.inOut"},0);
tl.fromTo("#b2",{x:0,y:0},{x:150,y:-120,duration:D,ease:"sine.inOut"},0);
tl.fromTo("#b3",{x:0,y:0,scale:1},{x:-120,y:-180,scale:1.15,duration:D,ease:"sine.inOut"},0);
tl.fromTo("#b4",{x:0,y:0},{x:160,y:120,duration:D,ease:"sine.inOut"},0);
tl.fromTo("#floor",{backgroundPosition:"0px 0px"},{backgroundPosition:"0px "+Math.round(D*40)+"px",duration:D,ease:"none"},0);
tl.fromTo("#prog",{scaleX:0},{scaleX:1,duration:D,ease:"none"},0);
tl.fromTo("#hdr",{opacity:0},{opacity:.85,duration:.4},0.05);
tl.fromTo("#hdr",{opacity:.85},{opacity:0,duration:.3,immediateRender:false},__ENDT__);

// cámara: entrada, deriva y salida de cada escena
const ENTERS = [
  [{opacity:0, scale:.86, filter:"blur(16px)"}, {opacity:1, scale:1, filter:"blur(0px)"}],
  [{opacity:0, y:160, filter:"blur(10px)"}, {opacity:1, y:0, filter:"blur(0px)"}],
  [{opacity:0, x:220, rotationY:-22, filter:"blur(10px)"}, {opacity:1, x:0, rotationY:0, filter:"blur(0px)"}],
  [{opacity:0, scale:1.18, filter:"blur(18px)"}, {opacity:1, scale:1, filter:"blur(0px)"}],
  [{opacity:0, rotationX:28, y:120, filter:"blur(10px)"}, {opacity:1, rotationX:0, y:0, filter:"blur(0px)"}],
];
function CAM(c){
  const cam = "#"+c.id+" .cam", dr = "#"+c.id+" .drift", Dd = c.t1 - c.t0;
  if (!c.first){ const [a,b] = ENTERS[c.k % ENTERS.length]; F(cam, a, Object.assign({duration:.6, ease:E}, b), c.t0); tl.set(cam, {filter:"none"}, c.t0+.62); }
  else F(cam, {scale:1.06}, {scale:1, duration:.8, ease:E}, 0);
  const dir = c.k % 2 ? 1 : -1;
  F(dr, {scale:1, y:0, x:0, rotation:0}, {scale:1.05, y:-22, x:dir*14, rotation:dir*.5, duration:Dd, ease:"none"}, c.t0);
  if (!c.last) F(cam, {opacity:1, filter:"blur(0px)", scale:1}, {opacity:0, filter:"blur(14px)", scale:1.08, duration:.42, ease:"power2.in"}, c.t1-.42);
}

const SC = {
prompt(c, p){
  const id = "#"+c.id, chs = $$(id+" .ch"), n = chs.length;
  const ts = c.t0 + .15, dur = Math.min(n*.034, (c.t1-c.t0)*.62), dt = dur/Math.max(1,n);
  chs.forEach((ch,i) => {
    const t = ts + i*dt;
    tl.set(ch, {opacity:1, boxShadow:"4px 0 0 0 "+ACC}, t);
    if (i < n-1) tl.set(ch, {boxShadow:"0 0 0 0 rgba(0,0,0,0)"}, t+dt);
  });
  const te = ts + dur;
  F(id+"-send", {scale:1}, {scale:.82, duration:.12, yoyo:true, repeat:1, ease:"power2.inOut"}, te+.2);
  F(id+"-box", {boxShadow:"0 0 0 10px rgba(0,0,0,0)"}, {boxShadow:"0 0 0 18px "+ACC+"33", duration:.35, yoyo:true, repeat:1}, te+.2);
  show(id+"-st", te+.4, .4, {y:20});
  F(id+" .pr-spin", {rotation:0}, {rotation:720, duration:Math.max(.5, c.t1-te-.4), ease:"none"}, te+.4);
},
capas(c, p){
  const id = "#"+c.id, n = p.n;
  for (let i=0;i<n;i++){
    F(id+"-l"+i, {opacity:0, z:-60, y:40}, {opacity:1, z:0, y:0, duration:.45, ease:E}, c.t0+.15+i*.07);
    F(id+"-l"+i, {z:0}, {z:(n-1-i)*-120+ (n-1)*60, duration:.9, ease:"power3.inOut"}, c.t0+.95);
  }
  F(id+"-sc", {rotationZ:-30, rotationX:56, transformPerspective:1800}, {rotationZ:-18, rotationX:50, transformPerspective:1800, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  const top = id+"-l"+(n-1);
  F(top, {borderColor:"rgba(255,255,255,.14)", boxShadow:"0 0 0 0 rgba(0,0,0,0)"}, {borderColor:ACC, boxShadow:"0 0 60px "+ACC+"66", duration:.4}, p.cue);
},
flujo(c, p){
  const id = "#"+c.id;
  for (let i=0;i<p.n;i++){
    const t = p.cues[i];
    pop(id+"-i"+i, t-.05);
    F(id+"-p"+i, {strokeDashoffset:1000}, {strokeDashoffset:0, duration:.6, ease:"power2.inOut"}, t+.1);
    F(id+"-d"+i, {strokeDashoffset:60, opacity:1}, {strokeDashoffset:-1000, duration:.9, ease:"power1.in", repeat:1, repeatDelay:.15}, t+.2);
  }
  F(id+"-o", {opacity:0, y:60, scale:.94}, {opacity:1, y:0, scale:1, duration:.55, ease:E}, p.out-.1);
  for (let i=0;i<4;i++) pop(id+"-t"+i, p.out+.2+i*.12);
},
cursores(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0;
  const paths = [[[620,340],[260,380],[420,560],[300,290]], [[880,660],[700,500],[840,370],[560,400]]];
  for (let i=0;i<p.n;i++){
    const pts = paths[i], seg = (Dd-.3)/pts.length;
    tl.set(id+"-c"+i, {x:pts[0][0], y:pts[0][1]}, c.t0);
    show(id+"-c"+i, c.t0+.2+i*.2, .3, {scale:.5});
    for (let j=1;j<pts.length;j++) F(id+"-c"+i, {x:pts[j-1][0], y:pts[j-1][1]}, {x:pts[j][0], y:pts[j][1], duration:seg*.8, ease:"power2.inOut"}, c.t0+.3+j*seg);
  }
  F(id+"-com", {opacity:0, y:40, scale:.9}, {opacity:1, y:0, scale:1, duration:.45, ease:"back.out(1.6)"}, p.com-.05);
  F(id+"-sel", {opacity:0, scale:1.08}, {opacity:1, scale:1, duration:.3, ease:E}, p.chg-.25);
  F(id+"-old", {opacity:1, filter:"blur(0px)"}, {opacity:0, filter:"blur(8px)", duration:.3}, p.chg);
  F(id+"-new", {opacity:0, y:20}, {opacity:1, y:0, duration:.4, ease:E}, p.chg+.15);
  show(id+"-ok", p.chg+.35, .4, {y:16});
},
chips(c, p){
  const id = "#"+c.id;
  for (let i=0;i<p.n;i++){
    F(id+"-k"+i, {opacity:0, x:i%2?-80:80, scale:.9, rotation:i%2?-3:3}, {opacity:1, x:0, scale:1, rotation:0, duration:.5, ease:"back.out(1.4)"}, p.cues[i]-.08);
    if ($(id+"-dl"+i)) F(id+"-dl"+i, {y:-14}, {y:6, duration:.35, yoyo:true, repeat:3, ease:"sine.inOut"}, p.cues[i]+.35);
  }
  if (p.bar !== undefined){
    show(id+"-bar", p.bar-.3, .4, {y:20});
    F(id+"-fill", {scaleX:0}, {scaleX:p.val, duration:.9, ease:"power2.out"}, p.bar);
    const o = {v:0};
    F(o, {v:0}, {v:p.val*100, duration:.9, ease:"power2.out", onUpdate:()=>{ $(id+"-pct").textContent = Math.round(o.v)+"%"; }}, p.bar);
  }
},
frase(c, p){
  const id = "#"+c.id;
  F(id+"-ring", {opacity:0, scale:.7}, {opacity:1, scale:1, duration:.8, ease:E}, c.t0+.1);
  F(id+"-ring", {rotation:0}, {rotation:40, duration:c.t1-c.t0, ease:"none"}, c.t0);
  p.cues.forEach((t,i) => F(id+"-w"+i, {opacity:0, y:60, scale:1.25, filter:"blur(10px)"}, {opacity:1, y:0, scale:1, filter:"blur(0px)", duration:.35, ease:E}, t-.06));
},
lista(c, p){
  const id = "#"+c.id;
  for (let i=0;i<p.n;i++){
    show(id+"-k"+i, p.cues[i]-.1, .45, {x:-90});
    F(id+"-ck"+i, {strokeDashoffset:100}, {strokeDashoffset:0, duration:.35, ease:"power2.out"}, p.cues[i]+.15);
  }
},
reloj(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0;
  F(id+"-m", {rotation:0}, {rotation:360*5, duration:Dd, ease:"power2.out"}, c.t0);
  F(id+"-h", {rotation:20}, {rotation:20+360*5/12, duration:Dd, ease:"power2.out"}, c.t0);
  F(id+"-arc", {"--arc":"0deg"}, {"--arc":"300deg", duration:Math.max(.4,p.cue-c.t0), ease:"power1.inOut"}, c.t0);
  F(id+"-arc", {"--arc":"300deg"}, {"--arc":"24deg", duration:.5, ease:"power3.out"}, p.cue);
  F(id+"-a", {"--st":0}, {"--st":1, duration:.35, ease:"power2.out"}, p.cue-.15);
  F(id+"-a", {opacity:1, y:0}, {opacity:0, y:-60, duration:.35, ease:"power2.in"}, p.cue+.15);
  F(id+"-b", {opacity:0, y:70, scale:.8}, {opacity:1, y:0, scale:1, duration:.5, ease:"back.out(1.6)"}, p.cue+.25);
},
alerta(c, p){
  const id = "#"+c.id;
  F(id+"-ic", {rotation:0}, {rotation:8, duration:.08, yoyo:true, repeat:5, ease:"sine.inOut"}, c.t0+.5);
  for (let i=0;i<p.n;i++) show(id+"-r"+i, c.t0+.35+i*.12, .35, {x:-40});
  if (p.mk >= 0){
    const r = id+"-r"+p.mk;
    show(id+"-lens", p.cue-.5, .4, {scale:.6});
    F(id+"-lens", {x:0, y:0}, {x:-430, y:-40, duration:1.1, ease:"power2.inOut"}, p.cue-.3);
    F(r, {backgroundColor:"rgba(255,176,32,0)", color:"#FFFFFF"}, {backgroundColor:"rgba(255,176,32,.16)", color:"#FFB020", duration:.3}, p.cue+.35);
    F(r, {scale:1}, {scale:1.04, duration:.15, yoyo:true, repeat:3}, p.cue+.4);
  }
},
numero(c, p){
  const id = "#"+c.id, o = {v:p.desde};
  F(o, {v:p.desde}, {v:p.val, duration:1.3, ease:"power3.out", onUpdate:()=>{ $(id+"-n").textContent = fmt(o.v, p.dec, p.sep); }}, p.cue-.1);
  show(id+"-l", p.cue+.4, .5, {y:30});
},
particulas(c, p){
  const id = "#"+c.id, cv = $(id+"-cv"), ctx = cv.getContext("2d"), rnd = seeded(7), N = 700, pts = [];
  for (let i=0;i<N;i++) pts.push([rnd()*1080, rnd()*1010, .6+rnd()*2.2, rnd()]);
  const o = {k:0, v:p.desde};
  F(o, {k:0}, {k:1, duration:Math.max(1,c.t1-c.t0-.2), ease:"power1.out", onUpdate:()=>{
    ctx.clearRect(0,0,1080,1010);
    for (const [x,y,r,a] of pts){ if (a > o.k) continue; ctx.globalAlpha = .35+.65*(1-a); ctx.fillStyle = a < .08 ? ACC : "#E6ECF7"; ctx.beginPath(); ctx.arc(x, y, r*1.6, 0, 6.283); ctx.fill(); }
  }}, c.t0);
  F(o, {v:p.desde}, {v:p.val, duration:1.6, ease:"power3.out", onUpdate:()=>{ $(id+"-n").textContent = fmt(o.v, p.dec); }}, p.cue-.1);
},
navegador(c, p){
  const id = "#"+c.id;
  for (let i=0;i<4;i++) pop(id+"-cd"+i, c.t0+.5+i*.12);
  F(id+"-cur", {x:0, y:0}, {x:-230, y:-560, duration:.9, ease:"power2.inOut"}, p.cue-.9);
  F(id+"-cur", {scale:1}, {scale:.8, duration:.1, yoyo:true, repeat:1}, p.cue);
  if (p.n > 1){
    F(id+"-tb0", {backgroundColor:"#141C31", color:"#FFFFFF"}, {backgroundColor:"rgba(255,255,255,.04)", color:"#8A97B0", duration:.15}, p.cue+.1);
    F(id+"-tb1", {backgroundColor:"rgba(255,255,255,.04)", color:"#8A97B0"}, {backgroundColor:"#141C31", color:"#FFFFFF", duration:.15}, p.cue+.1);
  }
},
celular(c, p){
  const id = "#"+c.id;
  F(id+"-ph", {rotationY:-18, rotationX:8}, {rotationY:10, rotationX:0, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  p.cues.forEach((t,i) => {
    if (!p.me[i]){ F(id+"-ty", {opacity:0}, {opacity:1, duration:.15}, t-.7); F(id+"-ty", {opacity:1}, {opacity:0, duration:.1}, t-.12); }
    show(id+"-m"+i, t-.1, .35, {y:30, scale:.9});
  });
},
grafico(c, p){
  const id = "#"+c.id;
  for (let i=0;i<p.n;i++){
    F(id+"-b"+i, {scaleY:0}, {scaleY:1, duration:.7, ease:"power3.out"}, c.t0+.35+i*.12);
    show(id+"-v"+i, c.t0+.75+i*.12, .3, {y:10});
  }
  F(id+" .gr-b.hi", {filter:"brightness(1)"}, {filter:"brightness(1.4)", duration:.3, yoyo:true, repeat:1}, p.cue);
},
comparacion(c, p){
  const id = "#"+c.id;
  show(id+"-an", p.cues[0]-.1, .5, {y:-50});
  pop(id+"-vs", (p.cues[0]+p.cues[1])/2);
  show(id+"-de", p.cues[1]-.1, .5, {y:60});
},
terminal(c, p){
  const id = "#"+c.id;
  F(id+"-win", {rotationX:10, rotationY:-8}, {rotationX:0, rotationY:4, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  p.cues.forEach((t, i) => {
    const ln = id+"-ln"+i;
    if (p.tipos[i] === "cmd"){
      tl.set(ln, {opacity:1}, t-.05);
      const chs = $$(ln+" .ch"), dt = Math.min(.06, .7/Math.max(1, chs.length));
      chs.forEach((ch, j) => { tl.set(ch, {opacity:1, boxShadow:"4px 0 0 0 "+ACC}, t+j*dt); if (j < chs.length-1) tl.set(ch, {boxShadow:"0 0 0 0 rgba(0,0,0,0)"}, t+(j+1)*dt); });
      if (chs.length) tl.set(chs[chs.length-1], {boxShadow:"0 0 0 0 rgba(0,0,0,0)"}, t+chs.length*dt+.25);
    } else {
      F(ln, {opacity:0, x:-24}, {opacity:1, x:0, duration:.3, ease:E}, t-.05);
    }
  });
  const last = p.cues.length ? p.cues[p.cues.length-1]+.5 : c.t0+.5;
  F(id+"-cur", {opacity:0}, {opacity:1, duration:.01, repeat:Math.max(1, Math.floor((c.t1-last)/.5)), yoyo:true, repeatDelay:.25}, last);
},
linea_tiempo(c, p){
  const id = "#"+c.id;
  const fr = (i) => p.n > 1 ? (60 + i*(860/p.n) + 42)/860 : .1;
  F(id+"-fill", {scaleY:0}, {scaleY:fr(0), duration:.5, ease:E}, c.t0+.2);
  p.cues.forEach((t, i) => {
    if (i > 0) F(id+"-fill", {scaleY:fr(i-1)}, {scaleY:fr(i), duration:.5, ease:"power2.inOut"}, t-.35);
    F(id+"-h"+i, {opacity:0, x:60}, {opacity:1, x:0, duration:.45, ease:E}, t-.1);
    F(id+"-d"+i, {scale:.3}, {scale:1, duration:.4, ease:"back.out(2.4)"}, t-.1);
    if (i > 0) F(id+"-h"+(i-1), {opacity:1}, {opacity:.45, duration:.3}, t);
  });
},
cierre(c, p){
  const id = "#"+c.id;
  F(id+"-mark", {scale:.8, opacity:0}, {scale:1, opacity:1, duration:.7, ease:E}, c.t0+.2);
  show(id+"-wm", c.t0+.45, .55, {y:26});
  show(id+"-sub", c.t0+.8, .5, {y:20});
  F(id+"-cta", {opacity:0, scale:.85}, {opacity:1, scale:1, duration:.5, ease:E}, c.t0+1.2);
  show(id+"-src", c.t0+1.5, .5, {y:10});
}
};

const CALLS = __CALLS__;
CALLS.forEach(c => { CAM(c); (SC[c.p.tipo] || (()=>{}))(c, c.p); });

// subtítulos palabra por palabra
const CAPS = __CAPS__;
CAPS.forEach(g => {
  const el = "#g"+g.g;
  F(el, {opacity:0}, {opacity:1, duration:.01}, g.t0);
  F(el, {opacity:1}, {opacity:0, duration:.1}, g.t1-.1);
  g.w.forEach(([w, t0, t1, kw]) => {
    F("#"+w, {opacity:0, y:16, scale:1.06}, {opacity:1, y:0, scale:1, duration:.14, ease:"power2.out"}, t0);
    if (!kw) F("#"+w, {color:"#FFFFFF"}, {color:MUT, duration:.18}, t1);
  });
  g.k.forEach(([k, t]) => F("#"+k+" .kb", {opacity:0, scale:.7}, {opacity:1, scale:1, duration:.22, ease:"back.out(2)"}, t));
});

window.__timelines = window.__timelines || {};
window.__timelines["main"] = tl;
})();
"""


# ---------------------------------------------------------------- audio
def mix_audio(work, voice, D, beats, groups):
    import numpy as np, soundfile as sf
    vw = os.path.join(work, "voz.wav")
    sf.write(vw, voice[: int((D + 0.2) * SR)], SR)
    scenes = [b["t0"] for b in beats]
    cards = []
    for b in beats:
        e = b["escena"]
        if e["tipo"] in ("chips", "lista", "flujo"):
            cards += scene_cues(b, [x.get("en", x.get("texto", "")) for x in (e.get("items") or e.get("entradas") or [])][:4], b["t0"], b["t1"])
    mw = os.path.join(work, "music.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "music.py"), mw, str(round(D + 0.2, 3)),
                    json.dumps({"scenes": scenes, "cards": cards})], check=True, stdout=subprocess.DEVNULL)
    out = os.path.join(work, "assets", "audio.mp3")
    fc = ("[0:a]aresample=44100,highpass=f=70,equalizer=f=3200:t=q:w=1.2:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=90,volume=2.0,"
          "aformat=channel_layouts=stereo,asplit=2[v][sc];"
          "[1:a]volume=0.20[m];[m][sc]sidechaincompress=threshold=0.025:ratio=7:attack=12:release=380[md];"
          "[v][md]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11[o]")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", vw, "-i", mw, "-filter_complex", fc, "-map", "[o]",
                    "-t", str(round(D, 3)), "-c:a", "libmp3lame", "-b:a", "192k", out], check=True)


def find_browser():
    if os.environ.get("HYPERFRAMES_BROWSER_PATH"):
        return os.environ["HYPERFRAMES_BROWSER_PATH"]
    for pat in ("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux*/headless_shell",
                "/opt/pw-browsers/chromium-*/chrome-linux*/chrome"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return None


REQUIRED = {"terminal": "lineas", "linea_tiempo": "hitos", "chips": "items", "lista": "items", "flujo": "entradas",
            "numero": "valor", "particulas": "valor", "comparacion": "despues", "grafico": "barras", "celular": "mensajes",
            "alerta": "filas", "reloj": "despues", "prompt": "texto", "cursores": "despues", "capas": "items"}
ENGLISH = {"claude", "chatgpt", "openai", "google", "microsoft", "gemini", "whatsapp", "iphone", "slides", "app", "apps",
           "prompt", "prompts", "code", "copilot", "meta", "apple", "android", "windows", "excel", "powerpoint", "notion",
           "canva", "youtube", "instagram", "tiktok", "linkedin", "email", "online", "software", "startup", "freelance",
           "skills", "hooks", "plugin", "plugins", "web", "chatbot", "deep", "blue", "watson", "anthropic", "nvidia",
           "github", "vercel", "supabase", "mercadolibre", "business", "pro", "enterprise", "team", "plus", "max", "agents"}


def validar(guion, historial=None):
    """Revisa el guion antes de gastar tiempo en voz y render. Devuelve (errores, avisos)."""
    err, warn = [], []
    beats = guion.get("beats") or []
    if not beats:
        return ["el guion no tiene beats"], []
    tipos = []
    for i, b in enumerate(beats, 1):
        e = b.get("escena") or {}
        t = e.get("tipo")
        tipos.append(t)
        if t not in SCENE_TYPES:
            err.append(f"beat {i}: escena '{t}' no existe (ver ESCENAS.md)")
            continue
        req = REQUIRED.get(t)
        if req and not e.get(req):
            err.append(f"beat {i}: la escena '{t}' necesita '{req}'")
        txt = b.get("texto", "")
        if not txt.strip():
            err.append(f"beat {i}: texto vacío")
        if txt.count("*") % 2:
            err.append(f"beat {i}: hay un '*' sin cerrar")
        if txt.count("{") != txt.count("}"):
            err.append(f"beat {i}: hay una llave {{ }} sin cerrar")
        if txt.count("*") // 2 > 2:
            warn.append(f"beat {i}: más de 2 palabras clave; si todo está destacado, nada lo está")
        plano = re.sub(r"\{[^}]*\}", " ", txt)
        for w in re.findall(r"[@\w./+-]+", plano):
            wl = w.strip(".,;:!?¿¡").lower()
            if (re.search(r"[a-záéíóú][A-Z]", w) or (len(w) > 1 and w.isupper() and w.isalpha()) or "@" in w
                    or re.search(r"\w\.\w", w) or wl in ENGLISH):
                warn.append(f"beat {i}: '{w}' sin pronunciación; usá {{{w}|cómo se dice}}")
    if tipos and tipos[-1] != "cierre":
        err.append("el último beat tiene que ser 'cierre'")
    for i in range(1, len(tipos)):
        if tipos[i] == tipos[i - 1]:
            warn.append(f"beats {i} y {i + 1}: misma escena '{tipos[i]}' seguida")
    if len(set(t for t in tipos if t != "cierre")) < 5:
        warn.append("menos de 5 tipos de escena distintos")
    if not 8 <= len(beats) <= 12:
        warn.append(f"{len(beats)} beats (lo recomendado es 8 a 12)")
    if historial:
        prev = [x for x in historial.get("publicados", []) if x.get("escenas")]
        if prev:
            last = prev[-1]
            if last["escenas"][0] == tipos[0]:
                warn.append(f"arranca con '{tipos[0]}', igual que el reel anterior")
            if last.get("acento", "").lower() == str(guion.get("acento", "")).lower():
                warn.append("mismo color de acento que el reel anterior")
    return err, warn


def browser_env():
    env = dict(os.environ)
    br = find_browser()
    if br:
        env["HYPERFRAMES_BROWSER_PATH"] = br
    return env


def main():
    """
    python3 make_reel2.py guion.json salida.mp4 --revisar   valida, arma voz y HTML y saca una hoja de contacto (sin render)
    python3 make_reel2.py guion.json salida.mp4             render final (reusa lo armado si el guion no cambió) y verifica
    python3 make_reel2.py guion.json salida.mp4 --solo-html arma voz y HTML sin hoja de contacto ni render
    """
    import hashlib
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    raw = open(args[0], "rb").read()
    guion = json.loads(raw)
    out = os.path.abspath(args[1])
    hist_p = os.path.join(os.path.dirname(HERE), "historial.json")
    hist = json.load(open(hist_p)) if os.path.exists(hist_p) else None
    if hist and os.path.basename(out).replace(".mp4", "") in {x.get("fecha") for x in hist.get("publicados", [])}:
        hist = {"publicados": [x for x in hist["publicados"] if x.get("fecha") != os.path.basename(out).replace(".mp4", "")]}
    err, warn = validar(guion, hist)
    for w in warn:
        print("AVISO", w)
    if err:
        for e in err:
            print("ERROR", e)
        sys.exit(2)
    if "--texto-voz" in sys.argv:  # texto hablado (pronunciaciones) para generar la voz afuera, p. ej. ElevenLabs
        print("TEXTO_VOZ_INICIO")
        print(el_text(layout_beats(guion))[0])
        print("TEXTO_VOZ_FIN")
        return
    voz_path = None
    if guion.get("voz_archivo"):
        voz_path = os.path.join(os.path.dirname(os.path.abspath(args[0])), guion["voz_archivo"])
        if not os.path.exists(voz_path):
            print("ERROR no existe el audio de voz_archivo:", voz_path)
            sys.exit(2)
        raw = raw + open(voz_path, "rb").read()
    key = hashlib.sha256(raw + open(os.path.abspath(__file__), "rb").read()).hexdigest()[:12]
    work = os.environ.get("REEL_WORK") or os.path.join(tempfile.gettempdir(), "reel2-" + key)
    ready = all(os.path.exists(os.path.join(work, f)) for f in ("index.html", "assets/audio.mp3", "tiempos.json")) \
        and open(os.path.join(work, ".key")).read() == key if os.path.exists(os.path.join(work, ".key")) else False
    if ready:
        D = json.load(open(os.path.join(work, "tiempos.json")))["duracion"]
        print("REUSO", work, "DUR", D)
    else:
        beats = layout_beats(guion)
        if voz_path:
            voice, D = synth_external(guion, beats, voz_path)
            print("VOZ archivo", os.path.basename(voz_path))
        elif guion.get("elevenlabs"):
            try:
                voice, D = synth_elevenlabs(guion, beats)
                print("VOZ elevenlabs", guion["elevenlabs"].get("voice_id"))
            except Exception as e:  # el reel sale igual: Kokoro de respaldo
                print("AVISO voz ElevenLabs falló, uso Kokoro:", str(e)[:300])
                beats = layout_beats(guion)
                voice, D = synth(guion, beats)
                print("VOZ kokoro (respaldo)")
        else:
            voice, D = synth(guion, beats)
            print("VOZ kokoro")
        if beats[-1]["escena"]["tipo"] == "cierre":
            D = max(D, beats[-1]["t_speech"] + 3.4)
        D = round(D + 0.5, 3)
        groups = caption_groups(beats)
        os.makedirs(os.path.join(work, "assets"), exist_ok=True)
        shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(work, "assets", "fonts"), dirs_exist_ok=True)
        for f in ("mark-white.svg", "grain.png"):
            shutil.copy(os.path.join(HERE, "marca", f), os.path.join(work, "assets", f))
        shutil.copy(os.path.join(HERE, "gsap.min.js"), os.path.join(work, "assets", "gsap.min.js"))
        open(os.path.join(work, "index.html"), "w").write(build_html(guion, beats, groups, D))
        open(os.path.join(work, "meta.json"), "w").write('{"id":"reel","name":"reel"}')
        mix_audio(work, voice, D, beats, groups)
        json.dump({"duracion": D, "escenas": [[b["escena"]["tipo"], b["t0"], b["t1"]] for b in beats]},
                  open(os.path.join(work, "tiempos.json"), "w"), indent=1)
        open(os.path.join(work, ".key"), "w").write(key)
        print("WORK", work, "DUR", D)
    if not 35 <= D <= 62:
        print(f"AVISO dura {D} s (lo recomendado es 40 a 55)")
    if "--solo-html" in sys.argv:
        return
    env = browser_env()
    if "--revisar" in sys.argv:
        esc_t = json.load(open(os.path.join(work, "tiempos.json")))["escenas"]
        ats = ",".join(str(round(t0 + (t1 - t0) * 0.72, 2)) for _, t0, t1 in esc_t)
        r = subprocess.run(["npx", "--yes", HF, "snapshot", "--at", ats], cwd=work, env=env, capture_output=True, text=True)
        sheets = re.findall(r"(\S+contact-sheet[^\s]*\.jpg)", r.stdout + r.stderr)
        if not sheets:
            print((r.stdout + r.stderr)[-1500:])
            sys.exit(3)
        for sh in sheets:
            print("REVISAR", sh if os.path.isabs(sh) else os.path.join(work, sh))
        print("Escenas:", ", ".join(f"{i + 1}.{t}" for i, (t, _, _) in enumerate(esc_t)))
        return
    os.makedirs(os.path.dirname(out), exist_ok=True)
    extra = ["--no-low-memory-mode", "--workers", "2"] if (os.cpu_count() or 1) >= 2 else []
    subprocess.run(["npx", "--yes", HF, "render", "-o", out, "--quality", "high", "--video-bitrate", "10M", "--quiet"] + extra,
                   cwd=work, env=env, check=True)
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height", "-of", "json", out],
                        capture_output=True, text=True, check=True)
    info = json.loads(pr.stdout)
    w_h = [(s_.get("width"), s_.get("height")) for s_ in info.get("streams", []) if s_.get("width")]
    dur = float(info["format"]["duration"])
    if w_h and w_h[0] == (1080, 1920) and abs(dur - D) < 1.0:
        print(f"OK {out} · {dur:.1f} s · 1080x1920")
    else:
        print(f"ERROR video inesperado: {w_h} {dur:.1f} s (esperado 1080x1920, {D} s)")
        sys.exit(4)


if __name__ == "__main__":
    main()

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
               "navegador", "celular", "grafico", "comparacion", "particulas", "cierre",
               # v2.1
               "imagen", "codigo", "pasos", "anillo", "titular", "cita", "tabla", "calendario", "planes",
               # v2.2
               "presentador",
               # v2.3
               "marcas", "impacto",
               # v2.4
               "llamada",
               # v2.5 (estilo marca: sitios reales, caos, planilla, notificaciones, logo, cuenta regresiva)
               "sitio", "carrusel", "muro", "notificaciones", "caos", "planilla", "logo", "cuenta",
               # v2.6 (looks nuevos: glitch, bandeja de correo, carta redactada, ranking con logos, documento triturado,
               # interruptor, censura, visor de cámara, onda de audio)
               "glitch", "bandeja", "carta", "ranking", "triturar", "interruptor", "censura", "visor", "onda",
               # v2.7 (galería: retrato con medidores, curva del valle, espectro de imágenes, diff, cerebros, balanza, firma)
               "retrato", "curva", "espectro", "diff", "cerebro", "balanza", "firma",
               # v2.8: boceto de una página (wireframe en un celular) con etiqueta de precio
               "boceto"}
LEAD = 0.12  # silencio al principio de la pista de voz
NOCAPS = {"frase", "cierre", "impacto", "muro", "logo", "glitch"}          # escenas que ya muestran el texto: sin subtítulos arriba
PUNCT_PAUSE = {",": 0.10, ";": 0.16, ":": 0.18, ".": 0.24, "?": 0.26, "!": 0.24, "…": 0.26}
BEAT_GAP = 0.14
# Temas visuales: cambian fondo, superficies, tipografía y subtítulos. El cierre y la cabecera son siempre de TobDev.
THEMES = {
    "noche": dict(bg="#0A0E1A", surface="rgba(14,20,36,.93)", surface2="#141C31", surface3="#18213A", ink="#0A0E1A", text="#FFFFFF",
                  soft="#C6CFE0", muted="#8A97B0", border="rgba(255,255,255,.11)", line="rgba(255,255,255,.12)", capdone="#C6CFE0",
                  display='"FreeSans","Helvetica Neue",Arial,sans-serif', radius="28px", mark="none", glow=".28"),
    "claro": dict(bg="#F3EFE6", surface="#FFFFFF", surface2="#ECE7DB", surface3="#E4DED0", ink="#0A0E1A", text="#0F1424",
                  soft="#3C4660", muted="#7A849A", border="rgba(10,14,26,.12)", line="rgba(10,14,26,.14)", capdone="#4A5470",
                  display='"Poppins","FreeSans",Arial,sans-serif', radius="24px", mark="brightness(0)", glow=".16"),
    "grilla": dict(bg="#060A12", surface="rgba(9,14,26,.96)", surface2="#0E1626", surface3="#121C30", ink="#060A12", text="#EAF2FF",
                   soft="#B8C6E0", muted="#7C8AA6", border="rgba(120,160,255,.22)", line="rgba(120,160,255,.18)", capdone="#B8C6E0",
                   display='"FreeSans","Helvetica Neue",Arial,sans-serif', radius="10px", mark="none", glow=".22"),
    "neon": dict(bg="#04050B", surface="rgba(8,9,20,.96)", surface2="#0D0F22", surface3="#12152C", ink="#04050B", text="#FFFFFF",
                 soft="#D5D9F2", muted="#8E95B8", border="rgba(var(--acc-rgb),.45)", line="rgba(var(--acc-rgb),.3)", capdone="#D5D9F2",
                 display='"FreeSans","Helvetica Neue",Arial,sans-serif', radius="20px", mark="none", glow=".4"),
    "editorial": dict(bg="#15120E", surface="#1F1A14", surface2="#2A2319", surface3="#332B1F", ink="#15120E", text="#F4ECDC",
                      soft="#D9CDB4", muted="#9A8E78", border="rgba(244,236,220,.14)", line="rgba(244,236,220,.16)", capdone="#D9CDB4",
                      display='"Lora","Georgia",serif', radius="6px", mark="none", glow=".2"),
    "estudio": dict(bg="#F4F3EF", surface="#FFFFFF", surface2="#ECEBE6", surface3="#E2E1DB", ink="#0A0E1A", text="#0E1B33",
                    soft="#3A4763", muted="#7B859A", border="rgba(14,27,51,.10)", line="rgba(14,27,51,.12)", capdone="#3A4763",
                    display='"Poppins","FreeSans",Arial,sans-serif', radius="22px", mark="brightness(0)", glow=".10"),
    # v2.6
    "alarma": dict(bg="#07070A", surface="rgba(18,13,16,.95)", surface2="#19131A", surface3="#231A23", ink="#07070A", text="#FFFFFF",
                   soft="#E6DADA", muted="#978A94", border="rgba(var(--acc-rgb),.38)", line="rgba(255,255,255,.12)", capdone="#D8CBCB",
                   display='"FreeSans","Helvetica Neue",Arial,sans-serif', radius="4px", mark="none", glow=".3"),
    "poster": dict(bg="#2A22E6", surface="rgba(8,6,80,.55)", surface2="#2119B8", surface3="#1A1496", ink="#0A0E1A", text="#FFFFFF",
                   soft="#E8E6FF", muted="#BDB9FF", border="rgba(255,255,255,.92)", line="rgba(255,255,255,.28)", capdone="#D6D3FF",
                   display='"Poppins","FreeSans",Arial,sans-serif', radius="0px", mark="none", glow=".18"),
    "cine": dict(bg="#050505", surface="rgba(22,22,22,.94)", surface2="#1B1B1B", surface3="#262626", ink="#050505", text="#F6F2E9",
                 soft="#DAD4C8", muted="#8F8A80", border="rgba(255,255,255,.14)", line="rgba(255,255,255,.12)", capdone="#CFC9BD",
                 display='"FreeSans","Helvetica Neue",Arial,sans-serif', radius="14px", mark="none", glow=".22"),
    # v2.7
    "galeria": dict(bg="#F1ECE4", surface="#FBF9F5", surface2="#E9E3D8", surface3="#DDD6C9", ink="#0A0E1A", text="#161412",
                    soft="#3F3A34", muted="#867E73", border="rgba(22,20,18,.14)", line="rgba(22,20,18,.16)", capdone="#5C5650",
                    display='"Lora","Georgia",serif', radius="6px", mark="brightness(0)", glow=".12"),
}
TRANSITIONS = ["zoom", "rise", "wipe", "slide", "iris", "flip", "push", "swing", "flash", "whip", "corte", "continuo"]
MUSIC_STYLES = ["tech", "suave", "urgente", "retro", "suspenso"]
IMG_MAGIC = {b"\xff\xd8\xff": "jpg", b"\x89PNG": "png", b"RIFF": "webp", b"GIF8": "gif"}


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
    y, _trim_idx = librosa.effects.trim(y, top_db=40)
    guion["_trim0"] = float(_trim_idx[0]) / SR  # segundos de silencio que se cortaron al principio del archivo
    lead = LEAD + float(guion.get("pausa_inicial", 0))  # `pausa_inicial`: segundos mudos antes de la voz (suspenso)
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
        for w in b["words"]:
            w["_low"] = b["escena"]["tipo"] == "presentador"
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
        groups[i] = {"words": g, "t0": g[0]["t0"] - 0.04, "t1": g_end, "low": bool(g[0].get("_low"))}
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
        "telefono": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8.1 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
        "play": '<path d="M7 4.5v15l12-7.5z" fill="currentColor"/>',
    }
    p = paths.get(name, paths["rayo"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{p}</svg>')


_LOGOS = None


def logos_db():
    global _LOGOS
    if _LOGOS is None:
        pth = os.path.join(HERE, "logos", "marcas.json")
        _LOGOS = json.load(open(pth)) if os.path.exists(pth) else {}
    return _LOGOS


def logo_key(name):
    if not name:
        return None
    db = logos_db()
    k = re.sub(r"[^a-z0-9]", "", str(name).lower())
    k = db.get("_alias", {}).get(k, k)
    return k if k in db and not k.startswith("_") else None


def logo_svg(name, size=120, blanco=False):
    """Logo de marca en línea (SVG). Monocromos en el color de la marca (o blanco); los `multi` traen sus colores."""
    k = logo_key(name)
    if not k:
        return ""
    m = logos_db()[k]
    raw = open(os.path.join(HERE, "logos", k + ".svg")).read()
    inner = re.sub(r"^.*?<svg[^>]*>", "", raw, flags=re.S).rsplit("</svg>", 1)[0]
    col = "#FFFFFF" if blanco else m["color"]
    fill = "" if m.get("multi") else f' fill="currentColor" style="color:{col}"'
    return f'<svg class="lg" width="{size}" height="{size}" viewBox="{m["viewBox"]}"{fill} xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


def logo_badge(name, size=120, cls=""):
    """Logo sobre una ficha blanca redondeada (se lee igual en cualquier tema)."""
    svg = logo_svg(name, int(size * 0.62))
    k = logo_key(name)
    bg = logos_db()[k].get("fondo", "#FFFFFF") if k else "#FFFFFF"
    return f'<div class="lg-badge {cls}" style="width:{size}px;height:{size}px;border-radius:{int(size * .26)}px;background:{bg}">{svg}</div>' if svg else ""


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


def _imgs(v):
    """Lista de imágenes [{img, en, toque, scroll}] desde un string, una lista de strings o una lista de dicts."""
    if not v:
        return []
    if isinstance(v, (str, dict)):
        v = [v]
    return [x if isinstance(x, dict) else {"img": x} for x in v]


def _wa_text(s):
    """Texto de un mensaje con saltos de línea y *negrita* estilo WhatsApp."""
    out = esc(s).replace("\n", "<br>")
    return re.sub(r"\*([^*<]+)\*", r"<b>\1</b>", out)


# geometría de los marcos de `sitio` / `carrusel` (ancho y alto visibles de la captura)
FRAMES = {"duo-d": (960, 600), "esc-d": (1020, 638), "duo-c": (294, 664), "cel-c": (392, 876)}
ANN_CURSOR = '<path d="M4 2l15 9-7 1.5L8.5 20z"'


def scene_html_marca(sid, b, D):
    e = b["escena"]; t = e["tipo"]; p = sid
    m = e.get("_m", {})
    if t == "sitio":
        dl, cl = _imgs(e.get("escritorio")), _imgs(e.get("celular"))
        lay = e.get("layout") or ("duo" if dl and cl else ("celular" if cl else "escritorio"))
        out = ""
        if lay in ("duo", "escritorio") and dl:
            imgs = "".join(f'<img class="st-img" id="{p}-d{i}" src="{m.get(x["img"], "")}" alt=""/>' for i, x in enumerate(dl))
            out += (f'<div class="st-br lay-{lay}" id="{p}-br"><div class="st-bar"><div class="cu-dots"><i></i><i></i><i></i></div>'
                    f'<div class="st-url mono">{icon("candado", 22, "currentColor")}<span>{esc(e.get("url", ""))}</span></div></div>'
                    f'<div class="st-shot">{imgs}</div></div>')
        if lay in ("duo", "celular") and cl:
            imgs = "".join(f'<img class="st-img" id="{p}-c{i}" src="{m.get(x["img"], "")}" alt=""/>' for i, x in enumerate(cl))
            taps = "".join(f'<div class="st-tap" id="{p}-t{i}" style="left:{float(x["toque"][0]) * 100:.1f}%;top:{float(x["toque"][1]) * 100:.1f}%"><i></i></div>'
                           for i, x in enumerate(cl) if x.get("toque"))
            out += f'<div class="st-ph lay-{lay}" id="{p}-ph"><div class="st-scr">{imgs}{taps}</div><div class="st-isl"></div></div>'
        chips = "".join(f'<div class="st-chip lay-{lay} c{i}" id="{p}-k{i}"><span class="st-dot"></span>{esc(x.get("texto", ""))}</div>'
                        for i, x in enumerate((e.get("chips") or [])[:3]))
        lab = ""
        if e.get("nombre"):
            rub = f'<div class="st-r mono">{esc(e["rubro"])}</div>' if e.get("rubro") else ""
            lab = f'<div class="st-lab lay-{lay}" id="{p}-lab"><div class="st-n">{esc(e["nombre"])}</div>{rub}</div>'
        return f'<div class="st-scene lay-{lay}">{out}{chips}{lab}</div>'
    if t == "carrusel":
        it = (e.get("items") or [])[:10]
        cel = e.get("marco") == "celular"
        imgs = "".join(f'<img class="st-img" id="{p}-i{k}" src="{m.get(x.get("img"), "")}" alt=""/>' for k, x in enumerate(it))
        labs = "".join(f'<div class="cr-lab" id="{p}-l{k}"><b>{esc(x.get("nombre", ""))}</b><span class="mono">{esc(x.get("rubro", ""))}</span></div>'
                       for k, x in enumerate(it))
        nums = "".join(f'<span id="{p}-n{k}">{k + 1:02d}</span>' for k in range(len(it)))
        urls = "".join(f'<span class="cr-u" id="{p}-u{k}">{esc(x.get("url", ""))}</span>' for k, x in enumerate(it))
        if cel:
            frame = f'<div class="st-ph lay-celular cr-fr" id="{p}-fr"><div class="st-scr">{imgs}</div><div class="st-isl"></div></div>'
        else:
            frame = (f'<div class="st-br lay-escritorio cr-fr" id="{p}-fr"><div class="st-bar"><div class="cu-dots"><i></i><i></i><i></i></div>'
                     f'<div class="st-url mono">{icon("candado", 22, "currentColor")}<span class="cr-us">{urls}</span></div></div>'
                     f'<div class="st-shot">{imgs}</div></div>')
        return (f'<div class="cr-scene{" m-cel" if cel else ""}">{frame}<div class="cr-foot" id="{p}-foot"><div class="cr-labs">{labs}</div>'
                f'<div class="cr-num mono"><span class="cr-nums">{nums}</span><em>/ {len(it):02d}</em></div></div></div>')
    if t == "muro":
        ims = [x if isinstance(x, str) else x.get("img") for x in (e.get("imagenes") or [])][:12]
        cols = [[], [], []]
        for k, x in enumerate(ims):
            cols[k % 3].append(x)
        colh = "".join(f'<div class="mu-col" id="{p}-c{j}">' + "".join(f'<div class="mu-it"><img src="{m.get(x, "")}" alt=""/></div>' for x in (col + col)) + "</div>"
                       for j, col in enumerate(cols))
        ws = []
        for i, w in enumerate(b["words"]):
            kw = w["kw"] is not None
            ws.append(f'<span class="ip-w mu-w{" kw" if kw else ""}" id="{p}-w{i}">{"<span class=ip-bg id=" + p + "-b" + str(i) + "></span>" if kw else ""}<span>{esc(w["cap"])}</span></span>')
        fs = fit(" ".join(w["cap"] for w in b["words"]), [(16, 128), (28, 106), (44, 86), (999, 70)])
        return (f'<div class="mu-wall"><div class="mu-grid">{colh}</div></div><div class="mu-shade"></div>'
                f'<div class="mu-txt" style="font-size:{fs}px">{" ".join(ws)}</div>')
    if t == "notificaciones":
        it = (e.get("items") or [])[:5]
        cards = []
        for i, x in enumerate(it):
            ic = logo_badge(x["logo"], 86) if logo_key(x.get("logo")) else f'<div class="nt-ico">{icon(x.get("icono", "check"), 46, "#FFFFFF")}</div>'
            body = f'<div class="nt-b">{esc(x["texto"])}</div>' if x.get("texto") else ""
            cards.append(f'<div class="nt-card" id="{p}-k{i}">{ic}<div class="nt-tx"><div class="nt-top"><span class="nt-app mono">{esc(x.get("app", ""))}</span>'
                         f'<span class="nt-ago mono">{esc(x.get("hora", "ahora"))}</span></div><div class="nt-t">{esc(x.get("titulo", ""))}</div>{body}</div></div>')
        return f'<div class="nt-col">{"".join(cards)}</div>'
    if t == "caos":
        apps = (e.get("apps") or [])[:6]
        notis = (e.get("notis") or [])[:8]
        APOS = [(60, 40), (880, 70), (30, 400), (900, 430), (90, 790), (850, 800)]
        NPOS = [(40, 230), (560, 170), (590, 560), (20, 600), (560, 860), (80, 950), (300, 0), (380, 990)]
        ah = []
        for i, x in enumerate(apps):
            if logo_key(x.get("logo")):
                bd = logo_badge(x["logo"], 120)
            else:
                bd = (f'<div class="lg-badge" style="width:120px;height:120px;border-radius:31px;background:{esc(x.get("color", "#1F7A4D"))}">'
                      f'{icon(x.get("icono", "lista"), 64, "#FFFFFF")}</div>')
            n = f'<span class="cz-n">{esc(str(x["n"]))}</span>' if x.get("n") else ""
            ah.append(f'<div class="cz-app" id="{p}-a{i}" style="left:{APOS[i][0]}px;top:{APOS[i][1]}px">{bd}{n}</div>')
        nh = []
        for i, x in enumerate(notis):
            v = f'<b>{esc(x["valor"])}</b>' if x.get("valor") else ""
            nh.append(f'<div class="cz-noti t-{esc(x.get("tono", "neutro"))}" id="{p}-n{i}" style="left:{NPOS[i][0]}px;top:{NPOS[i][1]}px">'
                      f'<span class="cz-dot"></span>{esc(x.get("texto", ""))}{v}</div>')
        foto = m.get(e.get("foto"), "")
        card = (f'<div class="cz-card" id="{p}-card"><img src="{foto}" alt=""/></div>' if foto
                else f'<div class="cz-card cz-empty" id="{p}-card">{icon("usuario", 200, "var(--text-muted)")}</div>')
        cred = f'<div class="cz-cred mono" id="{p}-cred">{esc(e["credito"])}</div>' if e.get("credito") else ""
        return card + "".join(ah) + "".join(nh) + cred
    if t == "planilla":
        import random
        rnd = random.Random(sum(map(ord, e.get("archivo", "x"))))
        cols = "ABCDEF"
        head = '<div class="pz-rn"></div>' + "".join(f'<div class="pz-ch mono">{c}</div>' for c in cols)
        rows = []
        for r_ in range(1, 15):
            cells = f'<div class="pz-rn mono">{r_}</div>'
            for _c in cols:
                v = rnd.random()
                cls = "pz-c rojo" if v < 0.09 else ("pz-c amar" if v < 0.17 else "pz-c")
                fill = f'<i style="width:{int(28 + rnd.random() * 60)}%"></i>' if rnd.random() < 0.64 else ""
                cells += f'<div class="{cls}">{fill}</div>'
            rows.append(f'<div class="pz-row" id="{p}-r{r_}">{cells}</div>')
        er = e.get("error") or {}
        dlg = (f'<div class="pz-dlg" id="{p}-dlg"><div class="pz-dh">{icon("alerta", 46, "#D93025")}<b>{esc(er.get("titulo", "No se pudo guardar"))}</b></div>'
               f'<div class="pz-dt">{esc(er.get("texto", ""))}</div><div class="pz-db"><span>Cancelar</span><span class="ok">Aceptar</span></div></div>')
        return (f'<div class="pz-win" id="{p}-win"><div class="pz-top"><span class="pz-ttl">{esc(e.get("archivo", "planilla_FINAL.xlsx"))}</span>'
                f'<span class="pz-wb"><i></i><i></i><i></i></span></div><div class="pz-fx mono"><span>fx</span><em>{esc(e.get("formula", "=SUMA(D2:D14)"))}</em></div>'
                f'<div class="pz-grid"><div class="pz-row hd">{head}</div>{"".join(rows)}</div></div>{dlg}')
    if t == "logo":
        sub = f'<div class="lo-sub" id="{p}-sub">{esc(e["sub"])}</div>' if e.get("sub") else ""
        lema = f'<div class="lo-lema mono" id="{p}-lema">{esc(e["lema"])}</div>' if e.get("lema") else ""
        return (f'<div class="lo-bg f-{esc(e.get("fondo", "degrade"))}" id="{p}-bg"></div><div class="lo-box">'
                f'<img class="lo-mark" id="{p}-mark" src="assets/mark-white.svg" alt=""/><div class="lo-wm" id="{p}-wm">Tob<span>Dev</span></div>{sub}{lema}</div>')
    if t == "cuenta":
        plano = e.get("modo") == "plano"
        ann = f'<div class="cu2-ann mono">{esc(e.get("nota", "boton.tsx · 0 clics"))}</div>' if plano else ""
        ok = f'<span class="cu2-ok" id="{p}-ok">{icon("check", 40, "currentColor")}{esc(e["confirmado"])}</span>' if e.get("confirmado") else ""
        card = (f'<div class="cu2-card{" plano" if plano else ""}" id="{p}-card"><div class="cu2-sk"><i></i><i class="s"></i></div>'
                f'<div class="cu2-btn" id="{p}-btn"><span class="cu2-bt" id="{p}-bt">{esc(e.get("boton", "Reservar"))}</span>{ok}</div>{ann}</div>')
        fill = "none" if plano else "var(--text)"
        stroke = "var(--acc)" if plano else "var(--bg)"
        cann = '<span class="cu2-cann mono">cursor.svg</span>' if plano else ""
        cur = (f'<div class="cu2-trail{" plano" if plano else ""}" id="{p}-tr"></div><div class="cu2-cur" id="{p}-cur">'
               f'<svg width="74" height="74" viewBox="0 0 24 24">{ANN_CURSOR} fill="{fill}" stroke="{stroke}" stroke-width="1.2"/></svg>{cann}</div>')
        import math
        sp = "".join(f'<i class="cu2-sp" id="{p}-sp{k}" style="transform:rotate({k * 30}deg)"></i>' for k in range(12))
        rip = f'<div class="cu2-rip" id="{p}-rip"></div><div class="cu2-sps" id="{p}-sps">{sp}</div>'
        cnt = (f'<div class="cu2-cnt"><div class="cu2-lab mono">{esc(e.get("etiqueta", "FRAMES PARA EL CLIC"))}</div>'
               f'<div class="cu2-num mono" id="{p}-num">{int(e.get("desde", 165)):03d}</div></div>')
        grid = '<div class="cu2-grid"></div>' if plano else ""
        return grid + card + rip + cur + cnt
    return ""


def fmt_py(v, dec=0, sep=True):
    """Mismo formato que el JS (es-AR): puntos de miles y coma decimal; sin separador para años."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not sep:
        return f"{v:.{dec}f}"
    s_ = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s_


def scene_html(sid, b, D):
    e = b["escena"]; t = e["tipo"]; p = sid
    if t in ("sitio", "carrusel", "muro", "notificaciones", "caos", "planilla", "logo", "cuenta"):
        return scene_html_marca(sid, b, D)
    if t == "boceto":
        return (f'<div class="bc-wrap"><div class="bc-ph" id="{p}-ph"><i class="bc-notch"></i>'
                f'<div class="bc-el bc-bar" id="{p}-e0"><b></b><b class="s"></b></div>'
                f'<div class="bc-el bc-h1" id="{p}-e1"></div><div class="bc-el bc-h2" id="{p}-e2"></div>'
                f'<div class="bc-el bc-btn" id="{p}-e3"><span class="mono">{esc(e.get("boton", "Ver más"))}</span></div>'
                f'<div class="bc-el bc-img" id="{p}-e4"><svg viewBox="0 0 120 80" width="120" height="80"><path d="M6 70 L40 30 L62 54 L80 40 L114 70 Z" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/><circle cx="92" cy="22" r="9" fill="none" stroke="currentColor" stroke-width="4"/></svg></div>'
                f'<div class="bc-el bc-row" id="{p}-e5"></div><div class="bc-el bc-row w" id="{p}-e6"></div></div>'
                f'<div class="bc-tag" id="{p}-tag"><i></i>{esc(e.get("etiqueta", "$0"))}</div></div>')
    if t == "retrato":
        src = e.get("_src", "")
        cred = f'<div class="rt-cred mono">{esc(e["credito"])}</div>' if e.get("credito") else ""
        m1, m2 = e.get("parecido") or {}, e.get("afinidad") or {}
        return (f'<div class="rt-wrap"><img class="rt-img" id="{p}-img" src="{src}" alt=""/><div class="rt-shade"></div>'
                f'<div class="rt-panel"><div class="rt-row"><span class="mono rt-l">{esc(m1.get("texto", "Parecido humano"))}</span>'
                f'<div class="rt-track"><div class="rt-fill" id="{p}-f1"></div></div><span class="mono rt-v" id="{p}-v1">0%</span></div>'
                f'<div class="rt-row"><span class="mono rt-l">{esc(m2.get("texto", "Afinidad"))}</span>'
                f'<div class="rt-track"><div class="rt-fill" id="{p}-f2"></div></div><span class="mono rt-v" id="{p}-v2">0%</span></div></div>{cred}</div>')
    if t == "curva":
        pts = (e.get("puntos") or [])[:6]
        labs = "".join(f'<div class="cv-lab" id="{p}-lb{i}" data-pos="{float(x.get("pos", .5))}"><i></i><span>{esc(x.get("texto", ""))}</span></div>' for i, x in enumerate(pts))
        ejes = e.get("ejes") or {}
        return (f'<div class="cv-wrap"><svg class="cv-svg" viewBox="0 0 1000 760" id="{p}-svg">'
                f'<defs><clipPath id="{p}-clipdip"><rect id="{p}-diprect" x="600" y="0" width="0" height="760"/></clipPath></defs>'
                f'<line x1="60" y1="700" x2="960" y2="700" class="cv-ax"/><line x1="60" y1="700" x2="60" y2="60" class="cv-ax"/>'
                f'<path id="{p}-area" class="cv-area" clip-path="url(#{p}-clipdip)" d="M60 700 C 250 650, 400 420, 560 330 C 640 290, 690 330, 720 560 C 740 700, 770 690, 800 520 C 850 300, 900 160, 960 120 L 960 700 Z"/>'
                f'<path id="{p}-path" class="cv-path" pathLength="1000" d="M60 700 C 250 650, 400 420, 560 330 C 640 290, 690 330, 720 560 C 740 700, 770 690, 800 520 C 850 300, 900 160, 960 120"/>'
                f'<path id="{p}-path2" class="cv-path2" pathLength="1000" d="M60 700 C 250 660, 400 440, 560 350 C 640 310, 690 380, 720 640 C 740 740, 770 720, 800 560 C 850 320, 900 170, 960 110"/>'
                f'<circle id="{p}-dot" class="cv-dot" cx="60" cy="700" r="11"/></svg>'
                f'<div class="cv-x mono">{esc(ejes.get("x", "parecido humano"))} →</div><div class="cv-y mono">{esc(ejes.get("y", "afinidad"))} ↑</div>'
                f'{labs}<div class="cv-valle" id="{p}-valle"><span>{esc(e.get("valle", "valle inquietante"))}</span></div>'
                f'<div class="cv-mov mono" id="{p}-mov">{esc(e.get("movimiento", "— — con movimiento"))}</div></div>')
    if t == "espectro":
        it = (e.get("items") or [])[:3]
        cells = "".join(f'<div class="sp-cell" id="{p}-c{i}"><div class="sp-ph"><img src="{x.get("_src", "")}" alt=""/></div><div class="sp-cap">{esc(x.get("texto", ""))}</div></div>' for i, x in enumerate(it))
        return (f'<div class="sp-strip">{cells}</div><div class="sp-rail"><div class="sp-knob" id="{p}-knob"></div></div>'
                f'<div class="sp-meter glass"><div class="eyebrow">{esc(e.get("medidor", "Afinidad"))}</div><div class="sp-num" id="{p}-num">0%</div>'
                f'<div class="sp-track"><div class="sp-fill" id="{p}-fill"></div></div></div>')
    if t == "diff":
        import difflib
        lns = (e.get("lineas") or [])[:4]
        def _mark(a, b):
            wa, wb = a.split(), b.split()
            sm = difflib.SequenceMatcher(None, [w.lower() for w in wa], [w.lower() for w in wb])
            out, k = [], 0
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                seg = " ".join(wb[j1:j2])
                if op == "equal":
                    out.append(esc(seg))
                elif seg:
                    out.append(f'<span class="df-chg"><i class="df-bar"></i>{esc(seg)}</span>'); k += 1
            return " ".join(out), k
        rows_a, rows_b = [], []
        for i, x in enumerate(lns):
            rows_a.append(f'<div class="df-ln" id="{p}-a{i}">{esc(x.get("a", ""))}</div>')
            h, _ = _mark(x.get("a", ""), x.get("b", ""))
            rows_b.append(f'<div class="df-ln" id="{p}-b{i}">{h}</div>')
        return (f'<div class="df-cols"><div class="df-col glass"><div class="eyebrow">{esc(e.get("titulo_a", "Vos"))}</div>{"".join(rows_a)}</div>'
                f'<div class="df-col glass b"><div class="eyebrow">{esc(e.get("titulo_b", "Casi vos"))}</div>{"".join(rows_b)}</div></div>')
    if t == "cerebro":
        import random, math
        rnd = random.Random(e.get("semilla", 7))
        def _head(k, tit):
            nodes = []
            while len(nodes) < 22:
                x, y = rnd.uniform(70, 300), rnd.uniform(60, 260)
                if ((x - 185) / 125) ** 2 + ((y - 160) / 105) ** 2 <= 1:
                    nodes.append((x, y))
            edges = []
            for i, (x, y) in enumerate(nodes):
                d = sorted(((math.hypot(x - nx, y - ny), j) for j, (nx, ny) in enumerate(nodes) if j != i))[:2]
                for _, j in d:
                    if (j, i) not in edges and (i, j) not in edges:
                        edges.append((i, j))
            lines = "".join(f'<line class="cb-e" id="{p}-{k}e{n}" x1="{nodes[i][0]:.0f}" y1="{nodes[i][1]:.0f}" x2="{nodes[j][0]:.0f}" y2="{nodes[j][1]:.0f}" pathLength="100"/>' for n, (i, j) in enumerate(edges))
            dots = "".join(f'<circle class="cb-n" cx="{x:.0f}" cy="{y:.0f}" r="5"/>' for x, y in nodes)
            return (f'<div class="cb-head" id="{p}-{k}"><svg viewBox="0 0 370 400"><path class="cb-sil" d="M190 18 C 280 18, 340 90, 335 175 C 332 225, 352 238, 340 258 L 318 268 L 322 312 C 322 345, 284 360, 240 348 L 190 365 L 135 365 L 125 310 C 65 290, 22 230, 22 160 C 22 85, 95 18, 190 18 Z"/>'
                    f'{lines}{dots}</svg><div class="cb-t">{esc(tit)}</div></div>'), len(edges)
        ha, na = _head("a", (e.get("a") or {}).get("titulo", "Sin IA"))
        hb, nb = _head("b", (e.get("b") or {}).get("titulo", "Con ChatGPT"))
        e["_na"], e["_nb"] = na, nb
        num = f'<div class="cb-num"><span id="{p}-n">0</span><span class="cb-suf">{esc(e.get("sufijo", "%"))}</span></div>' if e.get("valor") is not None else ""
        lab = f'<div class="cb-l{"" if e.get("valor") is not None else " solo"}" id="{p}-l">{kw_text(e.get("etiqueta", ""))}</div>' if e.get("etiqueta") else ""
        return f'<div class="cb-row">{ha}{hb}</div>{num}{lab}'
    if t == "balanza":
        a, b_ = e.get("a") or {}, e.get("b") or {}
        nota = f'<div class="bz-nota mono" id="{p}-nota">{esc(e["nota"])}</div>' if e.get("nota") else ""
        return (f'<div class="bz-wrap"><div class="bz-beam" id="{p}-beam"><div class="bz-pan l" id="{p}-pl"><div class="bz-chain"></div><div class="bz-plate glass"><span class="bz-arrow" id="{p}-ar1">{esc(a.get("flecha", "↑"))}</span>{esc(a.get("texto", ""))}</div></div>'
                f'<div class="bz-pan r" id="{p}-pr"><div class="bz-chain"></div><div class="bz-plate glass"><span class="bz-arrow" id="{p}-ar2">{esc(b_.get("flecha", "↓"))}</span>{esc(b_.get("texto", ""))}</div></div><div class="bz-bar"></div></div>'
                f'<div class="bz-pivot"></div><div class="bz-base"></div>{nota}</div>')
    if t == "firma":
        lns = (e.get("lineas") or [])[:3]
        rows = "".join(f'<div class="fm-ln" id="{p}-l{i}">{esc(x)}</div>' for i, x in enumerate(lns))
        return (f'<div class="fm-doc glass"><div class="fm-top"><div class="eyebrow">{esc(e.get("titulo", "Documento"))}</div></div>{rows}'
                f'<div class="fm-sk"><i style="width:82%"></i><i style="width:64%"></i><i style="width:71%"></i></div>'
                f'<div class="fm-sign"><div class="mono fm-lab">{esc(e.get("etiqueta", "Revisado por"))}</div>'
                f'<svg class="fm-svg" viewBox="0 0 520 140"><path id="{p}-sig" pathLength="1000" d="M14 96 C 40 40, 70 30, 72 70 C 74 110, 40 120, 60 92 C 90 50, 150 30, 170 60 C 190 90, 150 120, 140 96 C 130 70, 200 40, 250 66 C 290 88, 230 112, 240 90 C 255 60, 330 30, 370 64 C 400 90, 350 120, 360 96 C 372 68, 430 44, 480 60 C 500 68, 505 80, 498 88"/></svg>'
                f'<div class="fm-line"></div><div class="fm-name" id="{p}-name">{esc(e.get("nombre", "vos"))}</div></div></div>')
    if t == "glitch":
        words = b["words"]
        ln, lines = [], []
        for i, w in enumerate(words):
            ln.append((i, w))
            if len(ln) >= int(e.get("por_linea", 2)) or w["cap"][-1] in ".,:;?!":
                lines.append(ln); ln = []
        if ln:
            lines.append(ln)
        longest = max((sum(len(w["cap"]) for _, w in l) + len(l) - 1) for l in lines) if lines else 8
        fs = max(90, min(220, int(940 / (max(5, longest) * 0.62))))
        def _gw(i, w):
            up = esc(w["cap"].upper())
            return (f'<span class="gl-w{" kw" if w["kw"] is not None else ""}" id="{p}-w{i}"><span class="gl-l r">{up}</span><span class="gl-l b">{up}</span>'
                    f'<span class="gl-m">{up}<i class="gl-bar" id="{p}-b{i}"></i></span></span>')
        rows = "".join('<div class="gl-ln">' + "".join(_gw(i, w) for i, w in l) + '</div>' for l in lines)
        tag = f'<div class="gl-tag" id="{p}-tag">{esc(e["etiqueta"])}</div>' if e.get("etiqueta") else ""
        return f'<div class="gl-tear" id="{p}-tear"></div>{tag}<div class="gl-box" style="font-size:{fs}px">{rows}</div>'
    if t == "bandeja":
        it = e.get("items", [])[:5]; mk = e.get("marcar", -1)
        rows = "".join(f'<div class="bj-row{" mk" if i == mk else ""}" id="{p}-r{i}"><div class="bj-av">{esc((x.get("de") or "?")[0].upper())}</div>'
                       f'<div class="bj-txt"><div class="bj-de">{esc(x.get("de", ""))}</div><div class="bj-as">{esc(x.get("asunto", ""))}</div>'
                       f'<div class="bj-pv">{esc(x.get("texto", ""))}</div></div><div class="bj-h mono">{esc(x.get("hora", ""))}</div>'
                       f'<div class="bj-scan" id="{p}-sc{i}"></div></div>' for i, x in enumerate(it))
        stamp = f'<div class="bj-stamp" id="{p}-st">{esc(e["sello"])}</div>' if e.get("sello") else ""
        return (f'<div class="bj-win glass"><div class="bj-top"><div class="cu-dots"><i></i><i></i><i></i></div>'
                f'<span class="mono">{esc(e.get("app", "Bandeja de entrada"))} · {len(it)}</span></div>{rows}</div>{stamp}')
    if t == "carta":
        txt = e.get("texto", "")[:260]
        parts = re.split(r"(\[\[.*?\]\])", txt)
        html, k = [], 0
        for seg in parts:
            if seg.startswith("[[") and seg.endswith("]]"):
                inner = "".join(f'<span class="ch">{esc(c_) if c_ != " " else "&nbsp;"}</span>' for c_ in seg[2:-2])
                html.append(f'<span class="ct-red"><i class="ct-bar" id="{p}-rb{k}"></i>{inner}</span>'); k += 1
            else:
                html.append("".join(f'<span class="ch">{esc(c_)}</span>' if c_ != " " else '<span class="ch sp"> </span>' for c_ in seg))
        fs = fit(re.sub(r"\[\[|\]\]", "", txt), [(120, 40), (180, 36), (999, 32)])
        firma = f'<div class="ct-firma mono">{esc(e["firma"])}</div>' if e.get("firma") else ""
        return (f'<div class="ct-win glass" id="{p}-win"><div class="ct-who">{esc(e.get("remitente", "Redactando…"))}</div><div class="ct-head">'
                f'<div class="ct-row"><span class="mono">Para</span><b>{esc(e.get("para", ""))}</b></div>'
                f'<div class="ct-row"><span class="mono">Asunto</span><b>{esc(e.get("asunto", ""))}</b></div></div>'
                f'<div class="ct-body" style="font-size:{fs}px">{"".join(html)}{firma}</div>'
                f'<div class="ct-foot"><div class="ct-send" id="{p}-send">{esc(e.get("boton", "Enviar"))}</div>'
                f'<div class="ct-st" id="{p}-st">{icon("check", 28, "var(--acc)")}{esc(e.get("estado", "Enviado"))}</div></div></div>')
    if t == "ranking":
        filas = e.get("filas", [])[:6]; mk = e.get("marcar", 0)
        suf = e.get("sufijo", "%")
        def _lg(x):
            return logo_badge(x["logo"], 76) if logo_key(x.get("logo")) else f'<div class="rk-ini">{esc((x.get("texto") or "?")[0].upper())}</div>'
        rows = "".join(f'<div class="rk-row{" mk" if i == mk else ""}" id="{p}-r{i}"><div class="rk-logo">{_lg(x)}</div><div class="rk-txt">{esc(x.get("texto", ""))}</div>'
                       f'<div class="rk-track"><div class="rk-fill" id="{p}-f{i}"></div></div><div class="rk-v" id="{p}-v{i}">0{esc(suf)}</div></div>'
                       for i, x in enumerate(filas))
        tit = f'<div class="eyebrow" id="{p}-tit">{esc(e["titulo"])}</div>' if e.get("titulo") else ""
        note = f'<div class="rk-note" id="{p}-note">{esc(e["nota"])}</div>' if e.get("nota") else ""
        return f'<div class="rk-wrap glass">{tit}{rows}{note}</div>'
    if t == "triturar":
        lns = e.get("lineas", [])[:5]
        rows = "".join(f'<div class="tr-ln" id="{p}-l{i}">{esc(x)}</div>' for i, x in enumerate(lns))
        cnt = f'<div class="tr-cnt" id="{p}-cnt">&nbsp;</div>' if e.get("contador") else ""
        return (f'<canvas class="tr-cv" width="1080" height="1010" id="{p}-cv"></canvas>'
                f'<div class="tr-doc" id="{p}-doc"><div class="tr-name">{icon("archivo", 30, "var(--acc)")}{esc(e.get("archivo", "documento.xlsx"))}</div>{rows}</div>'
                f'<div class="tr-core"><div class="tr-ring" id="{p}-ring"></div><div class="tr-ring2" id="{p}-ring2"></div>{cnt}'
                f'<div class="tr-lab" id="{p}-lab">{esc(e.get("destino", "Entrenamiento del modelo"))}</div></div>')
    if t == "interruptor":
        on_first = e.get("desde", "on") == "on"
        return (f'<div class="sw-card glass"><div class="sw-ruta" id="{p}-ruta">{esc(e.get("ruta", "Ajustes"))}</div>'
                f'<div class="sw-tit" id="{p}-tit">{esc(e.get("titulo", ""))}</div><div class="sw-sub" id="{p}-sub">{esc(e.get("sub", ""))}</div>'
                f'<div class="sw-row" id="{p}-row"><div class="sw-state"><span class="on" id="{p}-on">{esc(e.get("texto_on", "ACTIVADO"))}</span>'
                f'<span class="off" id="{p}-off">{esc(e.get("texto_off", "DESACTIVADO"))}</span></div>'
                f'<div class="sw-track{"" if on_first else " off"}" id="{p}-track"><div class="sw-thumb" id="{p}-thumb"></div></div></div>'
                f'<div class="sw-ok" id="{p}-ok">{icon("check", 30, "var(--acc)")}{esc(e.get("nota", "Guardado"))}</div></div>'
                f'<div class="sw-finger" id="{p}-fg"></div>')
    if t == "censura":
        lns = e.get("lineas", [])[:6]
        def _ln(i, x):
            parts = re.split(r"(\[\[.*?\]\])", x.get("texto", "") if isinstance(x, dict) else str(x))
            out, k = [], 0
            for seg in parts:
                if seg.startswith("[[") and seg.endswith("]]"):
                    out.append(f'<span class="cs-red"><i class="cs-bar" id="{p}-b{i}_{k}"></i>{esc(seg[2:-2])}</span>'); k += 1
                else:
                    out.append(esc(seg))
            return f'<div class="cs-ln" id="{p}-l{i}">{"".join(out)}</div>'
        rows = "".join(_ln(i, x) for i, x in enumerate(lns))
        head = (f'<div class="cs-h" id="{p}-h"><div class="eyebrow">{esc(e.get("titulo", ""))}</div><div class="mono cs-n">{esc(e.get("archivo", ""))}</div></div>'
                if e.get("titulo") or e.get("archivo") else "")
        stamp = f'<div class="cs-stamp" id="{p}-st"><span>{esc(e["sello"])}</span></div>' if e.get("sello") else ""
        return f'<div class="cs-sheet glass">{head}{rows}</div>{stamp}'
    if t == "visor":
        tags = e.get("etiquetas", [])[:5]
        W, H = 900, 950
        els = []
        for i, x in enumerate(tags):
            px, py = int(float(x.get("x", .5)) * W), int(float(x.get("y", .4)) * H)
            tw = int(len(x.get("texto", "")) * 15.8 + 86)  # ancho estimado de la etiqueta (mono 26px + punto + relleno)
            if px + 70 + tw <= W - 20:
                style = f'left:{px + 70}px;top:{py - 30}px'
            elif px - 70 - tw >= 20:
                style = f'right:{W - px + 70}px;top:{py - 30}px'
            else:
                style = f'left:{max(20, min(W - 20 - tw, px - tw // 2))}px;top:{py + 70}px'
            els.append(f'<div class="vs-box" id="{p}-bx{i}" style="left:{px}px;top:{py}px"></div>'
                       f'<div class="vs-tag{" ok" if x.get("ok") else ""}" id="{p}-tg{i}" style="{style}"><i></i>{esc(x.get("texto", ""))}</div>')
        pts = [(450, 175), (300, 300), (600, 300), (330, 350), (390, 352), (515, 352), (575, 350), (450, 420), (412, 455), (488, 455),
               (385, 525), (450, 545), (515, 525), (450, 612), (320, 470), (580, 470), (355, 565), (545, 565)]
        seg = [(0, 1), (0, 2), (1, 3), (2, 6), (3, 4), (5, 6), (4, 7), (5, 7), (7, 8), (7, 9), (8, 10), (9, 12), (10, 11), (11, 12),
               (10, 13), (12, 13), (1, 14), (2, 15), (14, 16), (15, 17), (16, 13), (17, 13), (14, 8), (15, 9), (3, 14), (6, 15)]
        mesh = "".join(f'<line x1="{pts[a][0]}" y1="{pts[a][1]}" x2="{pts[b][0]}" y2="{pts[b][1]}"/>' for a, b in seg) + \
               "".join(f'<circle cx="{x}" cy="{y}" r="4"/>' for x, y in pts)
        stamp = f'<div class="vs-stamp" id="{p}-st"><span>{esc(e["sello"])}</span></div>' if e.get("sello") else ""
        return (f'<div class="vs-frame"><div class="vs-img" id="{p}-img"><div class="vs-sh"></div><div class="vs-sil"></div></div>'
                f'<svg class="vs-mesh" id="{p}-mesh" viewBox="0 0 {W} {H}">{mesh}</svg><div class="vs-scan" id="{p}-scan"></div>'
                f'<div class="vs-corner tl"></div><div class="vs-corner tr"></div><div class="vs-corner bl"></div><div class="vs-corner br"></div>'
                f'<div class="vs-rec" id="{p}-rec"><i></i>{esc(e.get("rec", "REC"))}</div><div class="vs-tc" id="{p}-tc">00:00:00:00</div>'
                f'{"".join(els)}{stamp}</div>')
    if t == "onda":
        import math
        tags = e.get("etiquetas", [])[:4]
        rng = (e.get("marcar") or [0.5, 0.68])
        a, b_ = int(float(rng[0]) * 56), int(float(rng[1]) * 56)
        bars = "".join(f'<div class="on-b{" hi" if a <= k < b_ else ""}" id="{p}-b{k}" style="transform:scaleY({0.18 + 0.78 * abs(math.sin(k * 1.37) * math.cos(k * .61)):.3f})"></div>' for k in range(56))
        chips = "".join(f'<div class="on-chip{" ok" if x.get("ok") else " no"}" id="{p}-c{i}"><i></i>{esc(x.get("texto", ""))}</div>' for i, x in enumerate(tags))
        stamp = f'<div class="on-stamp" id="{p}-st"><span>{esc(e["sello"])}</span></div>' if e.get("sello") else ""
        return (f'<div class="on-card glass"><div class="on-h"><div class="eyebrow">{esc(e.get("titulo", "Audio"))}</div><div class="mono on-d">{esc(e.get("duracion", ""))}</div></div>'
                f'<div class="on-wave">{bars}<div class="on-ph" id="{p}-ph"></div></div><div class="on-chips">{chips}</div></div>{stamp}')
    if t == "prompt":
        chars = "".join(f'<span class="ch">{esc(c) if c != " " else "&nbsp;"}</span>' if c != " " else '<span class="ch sp"> </span>'
                        for c in e.get("texto", ""))
        fs = fit(e.get("texto", ""), [(50, 58), (80, 52), (999, 46)])
        return (f'<div class="pr-wrap"><div class="glass pr-box" id="{p}-box"><div class="eyebrow">{esc(e.get("etiqueta", "Tu mensaje"))}</div>'
                f'<div class="pr-text" style="font-size:{fs}px">{chars}</div>'
                f'<div class="pr-foot"><div class="pr-tools"><span>+</span><span class="mono">Adjuntar</span></div>'
                f'<div class="pr-send" id="{p}-send">{icon("enviar", 44, "var(--ink)")}</div></div></div>'
                f'<div class="pr-status mono" id="{p}-st"><span class="pr-spin"></span>{esc(e.get("estado", "Generando…"))}</div></div>')
    if t == "capas":
        items = (e.get("items") or ["", "", "", ""])[:5]
        sl = "".join(f'<div class="cp-slide glass" id="{p}-l{i}">{slide_skel(i, it)}</div>' for i, it in enumerate(reversed(items)))
        return f'<div class="cp-scene" id="{p}-sc">{sl}</div>'
    if t == "flujo":
        ins = e.get("entradas", [])[:3]
        n = len(ins)
        xs = [540] if n == 1 else ([300, 780] if n == 2 else [180, 540, 900])
        chips = "".join(f'<div class="fl-in glass{" solo" if n == 1 else ""}" id="{p}-i{i}" style="left:{x - (230 if n == 1 else 160)}px">{icon(it.get("icono", "archivo"), 54, "var(--acc)")}'
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
                       f'fill="currentColor" stroke="var(--bg)" stroke-width="1.2"/></svg><span>{esc(n)}</span></div>' for i, n in enumerate(ppl))
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
            rows = "".join(f'<div class="ch-file glass" id="{p}-k{i}"><div class="ch-doc"><svg width="96" height="118" viewBox="0 0 96 118"><path d="M8 2h56l30 30v78a6 6 0 0 1-6 6H8a6 6 0 0 1-6-6V8a6 6 0 0 1 6-6z" fill="var(--surface2)" stroke="var(--line)" stroke-width="3"/><path d="M64 2v30h30" fill="none" stroke="var(--line)" stroke-width="3"/></svg>'
                           f'<span class="ch-ext">{esc(x.get("sub", ""))}</span></div><div class="ch-name">{esc(x.get("texto", ""))}</div>'
                           f'<div class="ch-dl" id="{p}-dl{i}">{icon("bajar", 44, "var(--acc)")}</div></div>' for i, x in enumerate(it))
            return f'<div class="ch-col">{rows}</div>'
        rows = "".join(f'<div class="ch-tag glass" id="{p}-k{i}">{logo_badge(x["logo"], 84) if logo_key(x.get("logo")) else icon(x.get("icono", "estrella"), 50, "var(--acc)")}<span>{esc(x.get("texto", ""))}</span></div>' for i, x in enumerate(it))
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
        rows = "".join(f'<div class="li-row glass" id="{p}-k{i}"><div class="li-ck"><svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke="var(--ink)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.2 4.2L19 7" pathLength="100" class="li-path" id="{p}-ck{i}"/></svg></div>'
                       f'<div class="li-t">{esc(x.get("texto", ""))}</div></div>' for i, x in enumerate(it))
        tit = f'<div class="eyebrow li-h">{esc(e["titulo"])}</div>' if e.get("titulo") else ""
        return f'<div class="li-col">{tit}{rows}</div>'
    if t == "reloj":
        ticks = "".join(f'<i style="transform:rotate({a}deg) translateY(-226px)" class="{"big" if a % 90 == 0 else ""}"></i>' for a in range(0, 360, 30))
        ant, dsp = e.get("antes", ""), e.get("despues", "")
        fa = fit(ant, [(12, 100), (18, 80), (26, 64), (999, 52)])
        fb = fit(dsp, [(10, 150), (16, 112), (22, 88), (999, 70)])
        return (f'<div class="rl-face" id="{p}-face">{ticks}<div class="rl-arc" id="{p}-arc"></div><div class="rl-h" id="{p}-h"></div><div class="rl-m" id="{p}-m"></div><div class="rl-c"></div></div>'
                f'<div class="rl-txt"><span class="rl-a" id="{p}-a" style="font-size:{fa}px">{esc(ant)}</span><span class="rl-b" id="{p}-b" style="font-size:{fb}px">{esc(dsp)}</span></div>')
    if t == "alerta":
        filas = e.get("filas", [])[:5]
        rows = "".join(f'<div class="al-row{" mk" if i == e.get("marcar") else ""}" id="{p}-r{i}"><span>{esc(a)}</span><span class="al-dots"></span><span class="mono">{esc(v)}</span></div>'
                       for i, (a, v) in enumerate(filas))
        return (f'<div class="al-card glass" id="{p}-card"><div class="al-head"><div class="al-ic" id="{p}-ic">{icon("alerta", 54, "var(--ink)")}</div>'
                f'<div class="al-tt">{esc(e.get("titulo", "Atención"))}</div></div><div class="al-rows">{rows}</div></div>'
                f'<div class="al-lens" id="{p}-lens">{icon("lupa", 150, "#FFFFFF")}</div>')
    if t == "numero":
        _ln = len(e.get("prefijo", "")) + len(fmt_py(e.get("valor", 0), int(e.get("decimales", 0)), e.get("separador", True))) + len(e.get("sufijo", ""))
        _sz = "" if _ln <= 7 else (" sm" if _ln <= 9 else " xs")
        return (f'<div class="nu-glow"></div><div class="nu-box"><div class="nu-v{_sz}"><span class="nu-pre">{esc(e.get("prefijo", ""))}</span>'
                f'<span id="{p}-n">0</span><span class="nu-suf">{esc(e.get("sufijo", ""))}</span></div>'
                f'<div class="nu-l" id="{p}-l">{kw_text(e.get("etiqueta", ""))}</div></div>')
    if t == "navegador":
        tabs = e.get("pestanas") or ["Inicio"]
        th = "".join(f'<div class="nv-tab{" on" if i == 0 else ""}" id="{p}-tb{i}">{esc(x)}</div>' for i, x in enumerate(tabs[:3]))
        cards = "".join(f'<div class="nv-card" id="{p}-cd{i}"><i></i><b class="sk w80"></b><b class="sk w50"></b></div>' for i in range(4))
        return (f'<div class="nv-win glass" id="{p}-win"><div class="nv-top"><div class="cu-dots"><i></i><i></i><i></i></div>{th}</div>'
                f'<div class="nv-url mono">{icon("candado", 26, "var(--text-muted)")}<span id="{p}-url">{esc(e.get("url", ""))}</span></div>'
                f'<div class="nv-body"><div class="nv-h">{kw_text(e.get("titulo", ""))}</div><div class="nv-grid">{cards}</div></div></div>'
                f'<div class="nv-cursor" id="{p}-cur"><svg width="54" height="54" viewBox="0 0 24 24"><path d="M4 2l15 9-7 1.5L8.5 20z" fill="var(--text)" stroke="var(--bg)" stroke-width="1.2"/></svg></div>')
    if t == "celular":
        msgs = e.get("mensajes", [])[:4]
        def _bars():
            import math
            return "".join(f'<i style="height:{int(18 + 34 * abs(math.sin(k * 1.7) * math.cos(k * .43)))}px"></i>' for k in range(26))
        def _msg(i, m):
            cls = "me" if m.get("de") == "yo" else "ia"
            if m.get("audio"):
                return (f'<div class="ph-m {cls} au" id="{p}-m{i}"><span class="au-play">{icon("play", 30, "currentColor")}</span>'
                        f'<div class="au-w"><div class="au-bars">{_bars()}</div><div class="au-bars on" id="{p}-ap{i}">{_bars()}</div></div>'
                        f'<span class="au-t mono">{esc(m["audio"])}</span></div>')
            hora = f'<span class="ph-h mono">{esc(m["hora"])}</span>' if m.get("hora") else ""
            return f'<div class="ph-m {cls}" id="{p}-m{i}">{_wa_text(m.get("texto", ""))}{hora}</div>'
        bub = "".join(_msg(i, m) for i, m in enumerate(msgs))
        wa = " wa" if e.get("estilo") == "whatsapp" else ""
        return (f'<div class="ph{wa}" id="{p}-ph"><div class="ph-notch"></div><div class="ph-top"><div class="ph-av">{icon(e.get("icono", "chip"), 34, "var(--ink)")}</div>'
                f'<div><div class="ph-n">{esc(e.get("app", "Asistente"))}</div><div class="ph-s mono">{esc(e.get("estado", "en línea"))}</div></div></div><div class="ph-body">{bub}'
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
        col = lambda x, cls, ic: (f'<div class="cm-col {cls} glass" id="{p}-{cls}">'
                                  + (f'<div class="cm-head">{logo_badge(x["logo"], 96)}<div class="eyebrow">{esc(x.get("titulo", ""))}</div></div>' if logo_key(x.get("logo")) else f'<div class="eyebrow">{esc(x.get("titulo", ""))}</div>') +
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
    if t == "llamada":
        nom = e.get("nombre", "Mamá")
        stamp = f'<div class="ll-stamp" id="{p}-st">{esc(e["estado"])}</div>' if e.get("estado") else ""
        lg = f'<div class="ll-app">{logo_svg(e["logo"], 34, blanco=True)}<span>{esc(e.get("sub", "Llamada"))}</span></div>' if logo_key(e.get("logo")) else f'<div class="ll-app"><span>{esc(e.get("sub", "Llamada"))}</span></div>'
        return (f'<div class="ll-ph" id="{p}-ph"><div class="ph-notch"></div>{lg}'
                f'<div class="ll-avw"><i class="ll-ring" id="{p}-r0"></i><i class="ll-ring" id="{p}-r1"></i><i class="ll-ring" id="{p}-r2"></i>'
                f'<div class="ll-av">{esc(nom[:1].upper())}</div></div><div class="ll-name">{esc(nom)}</div>'
                f'<div class="ll-num mono">{esc(e.get("numero", ""))}</div>'
                f'<div class="ll-btns"><div class="ll-b no">{icon("telefono", 52, "#fff")}</div><div class="ll-b si" id="{p}-si">{icon("telefono", 52, "#fff")}</div></div>'
                f'{stamp}</div>')
    if t == "marcas":
        lg = [x for x in (e.get("logos") or []) if logo_key(x.get("marca"))][:4]
        n = len(lg)
        size = {1: 380, 2: 300, 3: 230, 4: 200}.get(n, 200)
        union = e.get("union", "vs")
        cells = []
        for i, x in enumerate(lg):
            est = x.get("estado")
            pill = ""
            if est:
                ok = x.get("ok", True)
                pill = (f'<div class="mk-pill {"ok" if ok else "no"}" id="{p}-pl{i}">{icon("check" if ok else "alerta", 30, "currentColor")}'
                        f'<span>{esc(est)}</span></div>')
            m = logos_db()[logo_key(x["marca"])]
            cells.append(f'<div class="mk-it" id="{p}-k{i}" style="--bc:{m["color"]}"><div class="mk-glow"></div>{logo_badge(x["marca"], size)}'
                         f'<div class="mk-name">{esc(x.get("texto", m["nombre"]))}</div>{pill}</div>')
            if i < n - 1 and n == 2:
                mid = {"vs": "VS", "flecha": "→", "y": "+", "x": "×"}.get(union, union)
                cells.append(f'<div class="mk-mid mono" id="{p}-mid">{esc(mid)}</div>')
        tit = f'<div class="mk-tit eyebrow" id="{p}-tit">{esc(e["titulo"])}</div>' if e.get("titulo") else ""
        return f'<div class="mk-wrap n{n}">{tit}<div class="mk-row">{"".join(cells)}</div></div><div class="mk-burst" id="{p}-burst"></div>'
    if t == "impacto":
        words = b["words"]
        ln, lines = [], []
        for i, w in enumerate(words):
            ln.append((i, w))
            if len(ln) >= int(e.get("por_linea", 2)) or w["cap"][-1] in ".,:;?!":
                lines.append(ln); ln = []
        if ln:
            lines.append(ln)
        longest = max((sum(len(w["cap"]) for _, w in l) + len(l) - 1) for l in lines) if lines else 8
        fs = max(96, min(250, int(930 / (max(5, longest) * 0.64))))
        rows = "".join('<div class="im-ln">' + " ".join(
            f'<span class="ip-w{" kw" if w["kw"] is not None else ""}" id="{p}-w{i}"><i class="ip-bg" id="{p}-b{i}"></i><span>{esc(w["cap"].upper())}</span></span>'
            for i, w in l) + '</div>' for l in lines)
        lg = f'<div class="ip-logo" id="{p}-logo">{logo_badge(e["logo"], 170)}</div>' if logo_key(e.get("logo")) else ""
        return f'<div class="ip-box" style="font-size:{fs}px">{lg}{rows}</div>'
    if t == "presentador":
        # Clip de avatar (sincronización labial) a pantalla completa. El video va mudo: la voz sale de voz_archivo,
        # y data-media-start lo alinea con esa pista (ver prepare_presentador).
        t0, t1 = b["t0"], b["t1"]
        m = round(t0 - LEAD + float(e.get("_trim0", 0)) - float(e.get("video_desde", 0)), 3)
        start = t0 if m >= 0 else round(t0 - m, 3)
        m = max(0.0, m)
        dur = round(max(0.1, min(t1 - start, float(e.get("_dur", t1 - t0)) - m)), 3)
        name = (f'<div class="pv-name" id="{p}-name"><i></i><div><b>{esc(e["nombre"])}</b>'
                f'<span class="mono">{esc(e.get("cargo", ""))}</span></div></div>') if e.get("nombre") else ""
        live = f'<div class="pv-live mono" id="{p}-live"><i></i>{esc(e.get("marca", "EN VIVO"))}</div>' if e.get("marca") is not False else ""
        return (f'<div class="pv-wrap" id="{p}-wrap"><img class="pv-poster" src="{e.get("_poster", "")}" alt=""/>'
                f'<video class="pv-vid" id="{p}-v" src="{e.get("_src", "")}" muted playsinline data-start="{start}" '
                f'data-duration="{dur}" data-media-start="{m}" data-track-index="6" data-volume="0"></video></div>'
                f'<div class="pv-shade"></div>{live}{name}')
    if t == "imagen":
        src = e.get("_src", "")
        tit = f'<div class="im-tit" id="{p}-tit" style="font-size:{fit(re.sub(r"[*]", "", e.get("titulo", "")), [(18, 84), (30, 68), (999, 54)])}px">{kw_text(e.get("titulo", ""))}</div>' if e.get("titulo") else ""
        cred = f'<div class="im-cred mono" id="{p}-cred">{esc(e["credito"])}</div>' if e.get("credito") else ""
        if e.get("encuadre") == "tarjeta":
            return (f'<div class="im-card" id="{p}-card"><div class="im-cf"><img src="{src}" id="{p}-img" alt=""/></div>'
                    f'<div class="im-cap">{kw_text(e.get("titulo", ""))}</div>{cred}</div>')
        return (f'<div class="im-full" id="{p}-f"><img src="{src}" id="{p}-img" alt=""/><div class="im-shade"></div></div>{tit}{cred}')
    if t == "codigo":
        lns = e.get("lineas", [])[:9]
        rows = "".join(f'<div class="cd-l" id="{p}-ln{i}"><span class="cd-n">{i + 1}</span>'
                       f'<span class="cd-t">{code_html(ln.get("texto", ""))}</span></div>' for i, ln in enumerate(lns))
        return (f'<div class="cd-win" id="{p}-win"><div class="cd-top"><div class="cu-dots"><i></i><i></i><i></i></div>'
                f'<div class="cd-tab mono">{esc(e.get("archivo", "main.py"))}</div></div><div class="cd-body mono">{rows}</div></div>')
    if t == "pasos":
        ps = e.get("pasos", [])[:4]
        items = "".join(f'<div class="ps-it" id="{p}-k{i}"><div class="ps-n" id="{p}-n{i}">{i + 1}</div><div class="ps-tx"><div class="ps-t">{kw_text(x.get("titulo", ""))}</div>'
                        f'{"<div class=ps-s>" + esc(x["sub"]) + "</div>" if x.get("sub") else ""}</div></div>' for i, x in enumerate(ps))
        return f'<div class="ps-col"><div class="ps-rail"></div><div class="ps-fill" id="{p}-fill"></div>{items}</div>'
    if t == "anillo":
        return (f'<div class="an-box"><svg class="an-svg" viewBox="0 0 400 400"><circle cx="200" cy="200" r="170" class="an-bg"/>'
                f'<circle cx="200" cy="200" r="170" class="an-fg" id="{p}-ring" pathLength="100"/></svg>'
                f'<div class="an-v"><span id="{p}-n">0</span><span class="an-suf">{esc(e.get("sufijo", "%"))}</span></div></div>'
                f'<div class="an-l" id="{p}-l">{kw_text(e.get("etiqueta", ""))}</div>')
    if t == "titular":
        words = parse_words(e.get("titulo", ""))
        ws = " ".join(f'<span class="ti-w{" acc" if w["kw"] is not None else ""}" id="{p}-w{i}">{esc(w["cap"])}</span>' for i, w in enumerate(words))
        fs = fit(re.sub(r"[*]", "", e.get("titulo", "")), [(24, 104), (40, 86), (60, 70), (999, 58)])
        baj = f'<div class="ti-baj" id="{p}-baj">{esc(e["bajada"])}</div>' if e.get("bajada") else ""
        lg = f'<div class="ti-logo" id="{p}-logo">{logo_badge(e["logo"], 150)}</div>' if logo_key(e.get("logo")) else ""
        return (f'{lg}<div class="ti-card{" con-logo" if lg else ""}" id="{p}-card"><div class="ti-top mono"><span class="ti-tag" id="{p}-tag">{esc(e.get("etiqueta", "ÚLTIMO"))}</span>'
                f'<span>{esc(e.get("medio", ""))}</span><span class="ti-fe">{esc(e.get("fecha", ""))}</span></div>'
                f'<div class="ti-h" style="font-size:{fs}px">{ws}</div>{baj}<div class="ti-rule" id="{p}-rule"></div></div>')
    if t == "cita":
        own = not e.get("texto")
        src_words = [w["cap"] for w in b["words"]] if own else re.findall(r"\S+", e["texto"])
        ws = " ".join(f'<span class="ci-w" id="{p}-w{i}">{esc(w)}</span>' for i, w in enumerate(src_words))
        fs = fit(" ".join(src_words), [(30, 72), (60, 60), (100, 50), (999, 42)])
        return (f'<div class="ci-card" id="{p}-card"><div class="ci-q">“</div><div class="ci-t" style="font-size:{fs}px">{ws}</div>'
                f'<div class="ci-a" id="{p}-a"><div class="ci-av">{esc((e.get("autor") or "?")[0])}</div><div><div class="ci-n">{esc(e.get("autor", ""))}</div>'
                f'<div class="ci-c mono">{esc(e.get("cargo", ""))}</div></div></div></div>')
    if t == "tabla":
        cols = (e.get("columnas") or [])[:3]
        filas = e.get("filas", [])[:5]
        head = "".join(f'<span>{esc(c)}</span>' for c in cols)
        rows = "".join(f'<div class="tb-r{" mk" if i == e.get("marcar") else ""}" id="{p}-r{i}">' + "".join(f'<span>{esc(v)}</span>' for v in f[:3]) + '</div>'
                       for i, f in enumerate(filas))
        return (f'<div class="tb-card" id="{p}-card" style="--cols:{max(1, len(cols) or len(filas[0]) if filas else 2)}">'
                f'{"<div class=eyebrow>" + esc(e["titulo"]) + "</div>" if e.get("titulo") else ""}'
                f'<div class="tb-h mono">{head}</div>{rows}</div>')
    if t == "calendario":
        n = int(e.get("cantidad", 30)); start = int(e.get("inicio", 0)) % 7
        marks = {int(m.get("dia", 0)): m for m in e.get("marcas", [])[:4]}
        cells = "".join('<div class="ca-c off"></div>' for _ in range(start))
        for d in range(1, n + 1):
            m = marks.get(d)
            cells += (f'<div class="ca-c{" mk" if m else ""}" id="{p}-d{d}"><span>{d}</span>' +
                      (f'<b id="{p}-b{d}">{esc(m.get("texto", ""))}</b>' if m else "") + '</div>')
        dow = "".join(f'<span>{d}</span>' for d in ("L", "M", "M", "J", "V", "S", "D"))
        return (f'<div class="ca-card" id="{p}-card"><div class="ca-top"><span class="ca-mes">{esc(e.get("mes", ""))}</span>'
                f'<span class="mono ca-y">{esc(e.get("anio", ""))}</span></div><div class="ca-dow mono">{dow}</div><div class="ca-grid">{cells}</div></div>')
    if t == "planes":
        pl = e.get("planes", [])[:3]
        cards = "".join(f'<div class="pl-c{" hi" if x.get("destacado") else ""}" id="{p}-c{i}"><div class="pl-n mono">{esc(x.get("nombre", ""))}</div>'
                        f'<div class="pl-p">{esc(x.get("precio", ""))}</div><div class="pl-d">{esc(x.get("detalle", ""))}</div>'
                        f'{"<div class=pl-tag>" + esc(x.get("tag", "Recomendado")) + "</div>" if x.get("destacado") else ""}</div>' for i, x in enumerate(pl))
        return f'<div class="pl-row n{len(pl)}">{cards}</div>'
    if t == "cierre":
        return (f'<div class="end"><img id="{p}-mark" src="assets/mark-white.svg" alt="TobDev"/>'
                f'<div class="wm" id="{p}-wm">Tob<span class="grad">Dev</span></div>'
                + (f'<div class="lema mono" id="{p}-lema">{esc(e["lema"])}</div>' if e.get("lema") else "") +
                f'<div class="sub" id="{p}-sub">{esc(e.get("sub", "Sistemas e IA para tu PyME"))}</div>'
                f'<div class="cta" id="{p}-cta">{esc(e.get("cta", "Seguí a @tobdev.ia"))}{icon("flecha", 40, "#fff")}</div>'
                f'<div class="src mono" id="{p}-src">{esc(e.get("fuente_txt", ""))}</div></div>')
    return ""


def _mention(s):
    return re.sub(r"(@\w+)", lambda m: f'<b class="acc">{m.group(1)}</b>', esc(s))


CODE_KW = {"def", "return", "import", "from", "if", "else", "elif", "for", "while", "const", "let", "var", "function", "async", "await",
           "export", "class", "new", "true", "false", "null", "None", "True", "False", "with", "as", "in", "not", "and", "or", "print",
           "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "fetch", "yield", "try", "except", "catch", "lambda", "npm", "npx", "pip", "git", "claude"}


def code_html(s):
    """Coloreado simple para la escena `codigo`: comentarios, strings, números, palabras clave y símbolos."""
    out = []
    for m in re.finditer(r'(#.*$|//.*$)|("[^"]*"|\'[^\']*\'|`[^`]*`)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_@][\w.-]*)|(\s+)|(.)', s):
        com, st, num, ident, sp, other = m.groups()
        if com is not None:
            out.append(f'<span class="c-c">{esc(com)}</span>')
        elif st is not None:
            out.append(f'<span class="c-s">{esc(st)}</span>')
        elif num is not None:
            out.append(f'<span class="c-n">{esc(num)}</span>')
        elif ident is not None:
            cls = "c-k" if ident in CODE_KW else ("c-f" if ident.startswith(("/", "@")) else "")
            out.append(f'<span class="{cls}">{esc(ident)}</span>' if cls else esc(ident))
        elif sp is not None:
            out.append(sp.replace(" ", "&nbsp;"))
        else:
            out.append(f'<span class="c-o">{esc(other)}</span>')
    return "".join(out)


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
        p["au"] = [bool(m.get("audio")) for m in e.get("mensajes", [])[:4]]
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
    elif t == "presentador":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "llamada":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["stamp"] = bool(e.get("estado"))
    elif t == "marcas":
        lg = [x for x in (e.get("logos") or []) if logo_key(x.get("marca"))][:4]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in lg], t0, t1)
        p["n"] = len(lg)
        p["pills"] = [bool(x.get("estado")) for x in lg]
    elif t == "boceto":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "retrato":
        m1, m2 = e.get("parecido") or {}, e.get("afinidad") or {}
        p["c1"] = scene_cues(b, [m1.get("en", "")], t0, t1)[0]; p["v1"] = float(m1.get("valor", 92))
        p["c2"] = scene_cues(b, [m2.get("en", "")], t0, t1)[0]; p["v2"] = float(m2.get("valor", 18)); p["v2a"] = float(m2.get("desde", 72))
    elif t == "curva":
        pts = (e.get("puntos") or [])[:6]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in pts], t0, t1); p["n"] = len(pts)
        p["pos"] = [float(x.get("pos", .5)) for x in pts]
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["mov"] = scene_cues(b, [e.get("en_movimiento", "")], t0, t1)[0] if e.get("en_movimiento") else -1
    elif t == "espectro":
        it = (e.get("items") or [])[:3]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in it], t0, t1); p["n"] = len(it)
        p["vals"] = [float(x.get("afinidad", 50)) for x in it]
    elif t == "diff":
        lns = (e.get("lineas") or [])[:4]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in lns], t0, t1); p["n"] = len(lns)
    elif t == "cerebro":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["na"], p["nb"] = e.get("_na", 0), e.get("_nb", 0)
        p["da"], p["db"] = [float(x) for x in (e.get("densidad") or [1.0, 0.35])][:2]
        p["val"] = float(e["valor"]) if e.get("valor") is not None else None
        p["cv"] = scene_cues(b, [e.get("en_valor", "")], t0, t1)[0]
    elif t == "balanza":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["ang"] = float(e.get("angulo", -11))
    elif t == "firma":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["n"] = len((e.get("lineas") or [])[:3])
    elif t == "glitch":
        p["cues"] = [round(w["t0"], 3) for w in b["words"]]
        p["kw"] = [w["kw"] is not None for w in b["words"]]
    elif t == "bandeja":
        it = e.get("items", [])[:5]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in it], t0, t1)
        p["n"] = len(it); p["mk"] = e.get("marcar", -1); p["sello"] = bool(e.get("sello"))
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "carta":
        txt = e.get("texto", "")[:260]
        reds, k = [], 0
        for seg in re.split(r"(\[\[.*?\]\])", txt):
            if seg.startswith("[[") and seg.endswith("]]"):
                k += len(seg) - 4; reds.append(k - 1)
            else:
                k += len(seg)
        p["n"] = k; p["reds"] = reds
    elif t == "ranking":
        filas = e.get("filas", [])[:6]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in filas], t0, t1)
        p["n"] = len(filas); p["vals"] = [float(x.get("valor", 0)) for x in filas]
        p["max"] = max(p["vals"] + [1.0]) if e.get("escala") != "100" else 100.0
        p["mk"] = e.get("marcar", 0); p["suf"] = e.get("sufijo", "%"); p["dec"] = int(e.get("decimales", 0))
    elif t == "triturar":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["n"] = len(e.get("lineas", [])[:5])
        p["total"] = float(e["contador"]) if e.get("contador") else 0
        p["unidad"] = e.get("unidad", "fragmentos")
    elif t == "interruptor":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["on"] = e.get("desde", "on") == "on"
    elif t == "censura":
        lns = e.get("lineas", [])[:6]
        p["cues"] = scene_cues(b, [(x.get("en", "") if isinstance(x, dict) else "") for x in lns], t0, t1)
        p["n"] = len(lns)
        p["reds"] = [len(re.findall(r"\[\[.*?\]\]", x.get("texto", "") if isinstance(x, dict) else str(x))) for x in lns]
        p["sello"] = bool(e.get("sello")); p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "visor":
        tags = e.get("etiquetas", [])[:5]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in tags], t0, t1)
        p["n"] = len(tags); p["sello"] = bool(e.get("sello")); p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "onda":
        tags = e.get("etiquetas", [])[:4]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in tags], t0, t1)
        p["n"] = len(tags); p["sello"] = bool(e.get("sello")); p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "impacto":
        p["cues"] = [round(w["t0"], 3) for w in b["words"]]
        p["kw"] = [w["kw"] is not None for w in b["words"]]
        p["logo"] = bool(logo_key(e.get("logo")))
    elif t == "imagen":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p["modo"] = "tarjeta" if e.get("encuadre") == "tarjeta" else "cover"
        p["mov"] = e.get("movimiento", "")
    elif t == "codigo":
        lns = e.get("lineas", [])[:9]
        p["cues"] = scene_cues(b, [x.get("en", "") for x in lns], t0, t1)
        for i in range(1, len(p["cues"])):
            if p["cues"][i] <= p["cues"][i - 1] + 0.18:
                p["cues"][i] = round(p["cues"][i - 1] + 0.3, 3)
        p["n"] = len(lns)
        p["mk"] = [i for i, x in enumerate(lns) if x.get("marcar") or i == e.get("marcar")]
    elif t == "pasos":
        ps = e.get("pasos", [])[:4]
        p["cues"] = scene_cues(b, [x.get("en", x.get("titulo", "")) for x in ps], t0, t1)
        p["n"] = len(ps)
    elif t == "anillo":
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
        p.update(val=float(e.get("valor", 50)), desde=float(e.get("desde", 0)), dec=int(e.get("decimales", 0)))
    elif t == "titular":
        p["n"] = len(parse_words(e.get("titulo", "")))
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "cita":
        if e.get("texto"):
            n = len(re.findall(r"\S+", e["texto"]))
            st = scene_cues(b, [e.get("en", "")], t0, t1)[0]
            st = min(st, t0 + (t1 - t0) * 0.2)
            p["cues"] = [round(st + i * max(0.05, min(0.16, (t1 - st - 1.0) / max(1, n))), 3) for i in range(n)]
        else:
            p["cues"] = [round(w["t0"], 3) for w in b["words"]]
        p["autor"] = scene_cues(b, [e.get("en_autor", "")], t0, t1)[0] if e.get("en_autor") else p["cues"][-1] + 0.5
    elif t == "tabla":
        p["n"] = len(e.get("filas", [])[:5])
        p["mk"] = e.get("marcar", -1)
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0]
    elif t == "calendario":
        ms = e.get("marcas", [])[:4]
        p["dias"] = [int(m.get("dia", 0)) for m in ms]
        p["cues"] = scene_cues(b, [m.get("en", m.get("texto", "")) for m in ms], t0, t1)
        p["n"] = int(e.get("cantidad", 30))
    elif t == "planes":
        pl = e.get("planes", [])[:3]
        p["cues"] = scene_cues(b, [x.get("en", x.get("nombre", "")) for x in pl], t0, t1)
        p["n"] = len(pl)
        p["hi"] = [i for i, x in enumerate(pl) if x.get("destacado")]
    elif t == "sitio":
        dl, cl = _imgs(e.get("escritorio")), _imgs(e.get("celular"))
        lay = e.get("layout") or ("duo" if dl and cl else ("celular" if cl else "escritorio"))
        dims = e.get("_dims", {})

        def stack(lst, key):
            W, V = FRAMES[key]
            cues = scene_cues(b, [x.get("en", "") for x in lst], t0, t1)
            out = []
            for x, cue in zip(lst, cues):
                w, h = dims.get(x["img"], (1, 1))
                avail = max(0.0, h * W / w - V)
                frac = x.get("scroll", e.get("scroll"))
                if frac is None:
                    frac = 0.35 if avail > V * 0.6 else 0
                out.append({"cue": cue, "scroll": round(avail * float(frac), 1), "tap": bool(x.get("toque"))})
            return out
        p["lay"] = lay
        p["desk"] = stack(dl, "duo-d" if lay == "duo" else "esc-d") if lay in ("duo", "escritorio") else []
        p["cel"] = stack(cl, "duo-c" if lay == "duo" else "cel-c") if lay in ("duo", "celular") else []
        p["chips"] = scene_cues(b, [x.get("en", "") for x in (e.get("chips") or [])[:3]], t0, t1)
    elif t == "carrusel":
        it = (e.get("items") or [])[:10]
        p["cues"] = scene_cues(b, [x.get("en", x.get("nombre", "")) for x in it], t0, t1)
        p["n"] = len(it)
    elif t == "muro":
        p["cues"] = [round(w["t0"], 3) for w in b["words"]]
        p["kw"] = [w["kw"] is not None for w in b["words"]]
    elif t == "notificaciones":
        p["cues"] = scene_cues(b, [x.get("en", "") for x in (e.get("items") or [])[:5]], t0, t1)
    elif t == "caos":
        p["apps"] = scene_cues(b, [x.get("en", "") for x in (e.get("apps") or [])[:6]], t0, t1)
        p["notis"] = scene_cues(b, [x.get("en", "") for x in (e.get("notis") or [])[:8]], t0, t1)
    elif t == "planilla":
        p["cue"] = scene_cues(b, [(e.get("error") or {}).get("en", "")], t0, t1)[0]
    elif t == "logo":
        pass
    elif t == "cuenta":
        pr = e.get("progreso") or [0, 1]
        p.update(p0=float(pr[0]), p1=float(pr[1]), desde=int(e.get("desde", 165)), hasta=int(e.get("hasta", 0)),
                 rojo=int(e.get("rojo", 30)), clic=bool(e.get("clic")), plano=e.get("modo") == "plano")
        p["cue"] = scene_cues(b, [e.get("en", "")], t0, t1)[0] if e.get("clic") else None
    return p


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def seed_of(guion):
    """Semilla estable del reel (para transiciones, deriva de cámara y música): `semilla` del guion o un hash de etiqueta+fuente+texto."""
    import hashlib
    if guion.get("semilla") is not None:
        return int(guion["semilla"])
    base = json.dumps([guion.get("etiqueta", ""), guion.get("fuente", ""), [b.get("texto", "") for b in guion.get("beats", [])]], ensure_ascii=False)
    return int(hashlib.sha256(base.encode()).hexdigest()[:8], 16)


def pick_transitions(guion, n, seed):
    """Una transición por cambio de escena. `transiciones` del guion (lista o un nombre) o un orden barajado con la semilla,
    sin repetir dos seguidas ni usar la misma más de dos veces por reel."""
    import random
    tr = guion.get("transiciones")
    if isinstance(tr, str):
        tr = [tr]
    if tr:
        tr = [t if t in TRANSITIONS else "zoom" for t in tr]
        return [tr[i % len(tr)] for i in range(n)]
    rnd = random.Random(seed)
    pool = [t for t in TRANSITIONS if t not in ("corte", "continuo")]
    out, uses = [], {}
    for i in range(n):
        cands = [t for t in pool if (not out or t != out[-1]) and uses.get(t, 0) < 2]
        if not cands:
            cands = pool
        t = rnd.choice(cands)
        out.append(t); uses[t] = uses.get(t, 0) + 1
    return out


def theme_css(tema, acc):
    th = THEMES.get(tema, THEMES["noche"])
    return (f":root{{--bg:{th['bg']};--surface:{th['surface']};--surface2:{th['surface2']};--surface3:{th['surface3']};--ink:{th['ink']};"
            f"--text:{th['text']};--text-soft:{th['soft']};--text-muted:{th['muted']};--border:{th['border']};--line:{th['line']};"
            f"--cap-done:{th['capdone']};--display:{th['display']};--radius:{th['radius']};--mark-filter:{th['mark']};--glow:{th['glow']}}}\n")


def bg_html(tema):
    if tema == "claro":
        return ('<div class="blob" id="b1"></div><div class="blob" id="b2"></div><div class="blob" id="b3"></div>'
                '<div id="lines"></div><div id="vig"></div><div id="grain"></div>')
    if tema == "grilla":
        return ('<div id="grid"></div><div class="blob" id="b3"></div><div id="scan"></div><div id="vig"></div><div id="grain"></div>')
    if tema == "neon":
        return ('<div class="blob" id="b3"></div><div class="blob" id="b4"></div><div id="stripes"></div><div id="floor"></div><div id="vig"></div><div id="grain"></div>')
    if tema == "editorial":
        return ('<div class="blob" id="b3"></div><div id="rules"></div><div id="vig"></div><div id="grain"></div>')
    if tema == "estudio":
        return ('<div class="blob" id="b1"></div><div class="blob" id="b3"></div><div id="sgrid"></div><div id="vig"></div><div id="grain"></div>')
    if tema == "alarma":
        return ('<div id="al-red"></div><div class="blob" id="b3"></div><div id="scanlines"></div><div id="al-stripe"></div><div id="vig"></div><div id="grain"></div>')
    if tema == "poster":
        return ('<div id="ring2"></div><div id="dots"></div><div id="ring"></div><div id="grain"></div>')
    if tema == "cine":
        return ('<div class="blob" id="b3"></div><div id="cine-light"></div><div id="vig"></div><div id="grain"></div><div id="lb-t"></div><div id="lb-b"></div>')
    if tema == "galeria":
        return ('<div id="paper"></div><div class="blob" id="b3"></div><div id="hair-t"></div><div id="hair-b"></div><div id="grain"></div>')
    return ('<div class="blob" id="b1"></div><div class="blob" id="b2"></div><div class="blob" id="b3"></div><div class="blob" id="b4"></div>'
            '<div id="floor"></div><div id="vig"></div><div id="grain"></div>')


def build_html(guion, beats, groups, D):
    acc = guion.get("acento", "#11BFD6")
    r, g, bl = hex_rgb(acc)
    tema = guion.get("tema") if guion.get("tema") in THEMES else "noche"
    seed = seed_of(guion)
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";font-weight:{w};font-style:normal;font-display:block;src:url("assets/fonts/{fn}-{w}.{ext}") format("{fmt}");}}\n'
        for fam, fn, ws, ext, fmt in (("FreeSans", "FreeSans", (400, 700), "ttf", "truetype"),
                                      ("JetBrains Mono", "JetBrainsMono", (400, 500, 700), "woff2", "woff2"),
                                      ("Poppins", "Poppins", (400, 700), "ttf", "truetype"))
        for w in ws)
    fonts += '@font-face{font-family:"Lora";font-weight:400 700;font-style:normal;font-display:block;src:url("assets/fonts/Lora-Variable.ttf") format("truetype");}\n'
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * bl) / 255
    on_acc = "#0A0E1A" if lum > 0.55 else "#FFFFFF"  # texto legible sobre el color de acento
    br, bg_, bb = hex_rgb(THEMES[tema]["bg"])
    css = theme_css(tema, acc) + f":root{{--on-acc:{on_acc};--bg-rgb:{br},{bg_},{bb}}}\n" + (CSS.replace("__ACC__", acc).replace("__ACCRGB__", f"{r},{g},{bl}"))
    # escenas: la saliente termina antes de que la entrante empiece (sin solapes), ambas alrededor del arranque de la voz
    sc_html, calls = [], []
    n = len(beats)
    trans = pick_transitions(guion, n, seed)
    for i, b in enumerate(beats):
        t0 = 0.0 if i == 0 else round(b["t_speech"] - 0.22, 3)
        t1 = round(D, 3) if i == n - 1 else round(beats[i + 1]["t_speech"] - 0.18, 3)
        b["t0"], b["t1"] = t0, t1
        sid = f"s{i}"
        if b["escena"]["tipo"] == "cierre":
            b["escena"].setdefault("fuente_txt", f'Fuente: {guion.get("fuente", "")}' if guion.get("fuente") else "")
        _tp = b["escena"]["tipo"]
        full = " full" if _tp in ("presentador", "logo", "muro") else (" libre" if _tp == "cuenta" else "")
        sc_html.append(f'<div id="{sid}" class="clip scene t-{b["escena"]["tipo"]}" data-start="{t0}" data-duration="{round(t1 - t0, 3)}" data-track-index="{1 + i % 2}">'
                       f'<div class="stage{full}"><div class="safe"><div class="cam"><div class="drift">{scene_html(sid, b, D)}</div></div></div></div></div>')
        prm = scene_params(b, t0, t1)
        kwt, prev = [], None
        for w in b["words"]:
            if w["kw"] is not None and w["kw"] != prev:
                kwt.append(round(w["t0"], 3))
            prev = w["kw"]
        calls.append({"id": sid, "t0": t0, "t1": t1, "k": i, "first": i == 0, "last": i == n - 1, "p": prm, "kw": kwt,
                      "tin": trans[i], "tout": trans[i + 1] if i + 1 < n else "zoom"})
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
        cap_html.append(f'<div class="cap{" low" if g.get("low") else ""}" id="g{gi}">{" ".join(spans)}</div>')
        cap_js.append({"g": gi, "t0": round(g["t0"], 3), "t1": round(g["t1"], 3), "low": bool(g.get("low")),
                       "w": [[f"w{gi}_{k}", round(w["t0"], 3), round(ws[k + 1]["t0"] if k + 1 < len(ws) else g["t1"], 3), w["kw"] is not None] for k, w in enumerate(ws)],
                       "k": [[f"k{gi}_{k}", round(w["t0"], 3)] for k, w in enumerate(ws) if w["kw"] is not None and (k == 0 or ws[k - 1]["kw"] != w["kw"])]})
    end_t = beats[-1]["t0"] if beats[-1]["escena"]["tipo"] == "cierre" else D
    marca = guion.get("estilo") == "marca"
    hdr = "" if marca else (f'<div id="hdr" class="clip hdr" data-start="0" data-duration="{round(end_t + 0.3, 3)}" data-track-index="4">'
           f'<img src="assets/mark-white.svg" alt=""/><span class="h">tobdev.ia</span><span class="d">{esc(guion.get("etiqueta", guion.get("fecha", "")))}</span></div>')
    js = (JS.replace("__ACC__", acc).replace("__D__", str(round(D, 3)))
          .replace("__CALLS__", json.dumps(calls)).replace("__CAPS__", json.dumps(cap_js))
          .replace("__ENDT__", str(round(end_t, 3))).replace("__SEED__", str(seed % 100000)).replace("__TEMA__", tema)
          .replace("__MARCA__", "true" if marca else "false"))
    return f"""<!doctype html>
<html lang="es" data-tema="{tema}"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<script src="assets/gsap.min.js"></script><style>{fonts}{css}</style></head>
<body class="tema-{tema}{" estilo-marca" if marca else ""}{" fondo-liso" if guion.get("fondo") == "liso" else ""}">
<div id="root" data-composition-id="main" data-start="0" data-duration="{round(D, 3)}" data-width="1080" data-height="1920">
<div id="bg" class="clip" data-start="0" data-duration="{round(D, 3)}" data-track-index="0">
  {bg_html(tema)}
</div>
{"".join(sc_html)}
<div id="caps" class="clip" data-start="0" data-duration="{round(D, 3)}" data-track-index="3">{"".join(cap_html)}</div>
{hdr}
<div id="flash" class="clip" data-start="0" data-duration="{round(D, 3)}" data-track-index="5"></div>
<div id="prog"></div>
<audio id="el-audio" src="assets/audio.mp3" data-start="0" data-duration="{round(D, 3)}" data-track-index="11" data-volume="1"></audio>
</div>
<script>{js}</script>
</body></html>"""


CSS = r"""
:root{--cyan:#11BFD6;--violet:#5B6FE4;--acc:__ACC__;--acc-rgb:__ACCRGB__;--grad:linear-gradient(135deg,#5B6FE4 0%,#11BFD6 100%);
--mono:"JetBrains Mono",ui-monospace,monospace;--warn:#FFB020;--shadow:0 40px 90px -30px rgba(0,0,0,.95)}
.tema-claro{--shadow:0 30px 70px -30px rgba(20,24,40,.35);--warn:#D98E00}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:var(--bg)}
#root{position:absolute;inset:0;font-family:var(--display);color:var(--text)}
.mono{font-family:var(--mono)}
#bg{position:absolute;inset:0;background:var(--bg);overflow:hidden}
.blob{position:absolute;border-radius:50%}
#b1{width:1400px;height:1400px;left:150px;top:-640px;background:radial-gradient(circle,rgba(91,111,228,.30) 0%,rgba(91,111,228,0) 62%)}
#b2{width:1300px;height:1300px;left:-560px;top:1100px;background:radial-gradient(circle,rgba(17,191,214,.22) 0%,rgba(17,191,214,0) 62%)}
#b3{width:1100px;height:1100px;left:300px;top:520px;background:radial-gradient(circle,rgba(var(--acc-rgb),var(--glow)) 0%,rgba(var(--acc-rgb),0) 62%)}
#b4{width:800px;height:800px;left:-300px;top:200px;background:radial-gradient(circle,rgba(91,111,228,.12) 0%,rgba(91,111,228,0) 62%)}
#floor{position:absolute;left:-540px;right:-540px;top:1180px;height:1200px;transform:perspective(900px) rotateX(64deg);transform-origin:50% 0;
background-image:radial-gradient(circle,rgba(255,255,255,.16) 1.6px,transparent 2px);background-size:56px 56px;
-webkit-mask-image:linear-gradient(to bottom,rgba(0,0,0,.9),transparent 75%);mask-image:linear-gradient(to bottom,rgba(0,0,0,.9),transparent 75%)}
#vig{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,transparent 50%,rgba(0,0,0,.55) 100%)}
#grain{position:absolute;inset:0;opacity:.05;background:url("assets/grain.png") repeat}
/* tema claro: papel cálido, líneas finas, manchas suaves */
.tema-claro #b1{background:radial-gradient(circle,rgba(91,111,228,.14) 0%,rgba(91,111,228,0) 62%)}
.tema-claro #b2{background:radial-gradient(circle,rgba(17,191,214,.12) 0%,rgba(17,191,214,0) 62%)}
.tema-claro #vig{background:radial-gradient(ellipse at 50% 45%,transparent 62%,rgba(60,50,30,.12) 100%)}
.tema-claro #grain{opacity:.09;mix-blend-mode:multiply}
#lines{position:absolute;inset:0;background-image:repeating-linear-gradient(-32deg,rgba(10,14,26,.045) 0 2px,transparent 2px 46px)}
/* tema grilla: plano técnico */
#grid{position:absolute;inset:-200px;background-image:linear-gradient(rgba(120,160,255,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(120,160,255,.10) 1px,transparent 1px),
linear-gradient(rgba(120,160,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(120,160,255,.05) 1px,transparent 1px);background-size:120px 120px,120px 120px,24px 24px,24px 24px;
-webkit-mask-image:radial-gradient(ellipse at 50% 50%,#000 30%,transparent 80%);mask-image:radial-gradient(ellipse at 50% 50%,#000 30%,transparent 80%)}
#scan{position:absolute;left:0;right:0;top:-120px;height:120px;background:linear-gradient(to bottom,transparent,rgba(var(--acc-rgb),.14) 70%,rgba(var(--acc-rgb),.3));opacity:.9}
.tema-grilla .hdr .d,.tema-grilla .eyebrow{letter-spacing:.26em}
/* tema neon: negro, brillo fuerte, franjas en diagonal */
#stripes{position:absolute;inset:-300px;background-image:repeating-linear-gradient(-55deg,transparent 0 160px,rgba(var(--acc-rgb),.055) 160px 220px)}
.tema-neon #floor{background-image:linear-gradient(rgba(var(--acc-rgb),.22) 2px,transparent 2px),linear-gradient(90deg,rgba(var(--acc-rgb),.22) 2px,transparent 2px);background-size:90px 90px}
.tema-neon .glass,.tema-neon .cd-win,.tema-neon .tm-win,.tema-neon .ph{box-shadow:0 0 0 1px rgba(var(--acc-rgb),.35),0 0 60px rgba(var(--acc-rgb),.22),var(--shadow)}
.tema-neon .cap{text-shadow:0 0 30px rgba(var(--acc-rgb),.55),0 4px 24px rgba(0,0,0,.6)}
/* tema editorial: serif, reglas finas, papel oscuro */
#rules{position:absolute;inset:0;background-image:linear-gradient(90deg,rgba(244,236,220,.07) 1px,transparent 1px);background-size:270px 100%;
-webkit-mask-image:linear-gradient(to bottom,transparent,#000 30%,#000 70%,transparent);mask-image:linear-gradient(to bottom,transparent,#000 30%,#000 70%,transparent)}
.tema-editorial #grain{opacity:.09}
.tema-editorial .cap{font-weight:600;letter-spacing:-.01em;line-height:1.14}
.tema-editorial .eyebrow{letter-spacing:.24em}
.hdr{position:absolute;left:100px;right:100px;top:150px;height:44px;display:flex;align-items:center;gap:14px;opacity:.85}
.hdr img{width:40px;height:40px;filter:var(--mark-filter)}.hdr .h{font-family:var(--mono);font-weight:500;font-size:24px;color:var(--text-soft)}
.hdr .d{margin-left:auto;font-family:var(--mono);font-weight:500;font-size:22px;letter-spacing:.18em;color:var(--text-muted)}
.cap{position:absolute;left:100px;right:100px;top:236px;text-align:center;font-weight:700;font-size:72px;line-height:1.16;letter-spacing:-.02em;opacity:0;
text-shadow:0 4px 24px rgba(0,0,0,.6)}
.tema-claro .cap,.tema-estudio .cap{text-shadow:none}
.cap .w{display:inline-block;opacity:0}
.kw{position:relative;display:inline-block;white-space:nowrap;padding:0 .1em;margin:0 .02em}
.kb{position:absolute;left:-8px;right:-8px;top:2px;bottom:-4px;border:3px solid var(--acc);border-radius:6px;background:rgba(var(--acc-rgb),.16);opacity:0}
.kb i{position:absolute;width:14px;height:14px;background:var(--text);border:3px solid var(--acc);border-radius:3px}
.kb i:nth-child(1){left:-9px;top:-9px}.kb i:nth-child(2){right:-9px;top:-9px}.kb i:nth-child(3){left:-9px;bottom:-9px}.kb i:nth-child(4){right:-9px;bottom:-9px}
.scene{position:absolute;inset:0}
.stage{position:absolute;left:0;top:470px;width:1080px;height:1010px;perspective:1600px;clip-path:inset(-24px 0px -40px 0px)}
/* zona segura: Instagram agranda el video y corta los costados en celulares más altos que 9:16;
   las escenas se achican hacia el centro (con la deriva de cámara, el texto queda a 100 px o más del borde) */
.safe{position:absolute;inset:0;transform:scale(.86);transform-origin:50% 50%;transform-style:preserve-3d}
.stage.full>.safe{transform:none}
.cam,.drift{position:absolute;inset:0;transform-style:preserve-3d}
.glass{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.eyebrow{font-family:var(--mono);font-weight:500;font-size:26px;letter-spacing:.18em;text-transform:uppercase;color:var(--acc)}
.acc{color:var(--acc)}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.sk{height:22px;border-radius:11px;background:var(--line);margin-top:18px}
.w90{width:90%}.w80{width:80%}.w70{width:70%}.w60{width:60%}.w50{width:50%}
.skc{display:flex;align-items:flex-end;gap:14px;height:150px;margin-top:22px}.skc i{flex:1;border-radius:8px 8px 0 0;background:rgba(var(--acc-rgb),.75)}
.skc.sm{height:120px;width:60%}
.skn{font-weight:700;font-size:96px;color:var(--acc);letter-spacing:-.03em;margin-top:6px}
.sk2{display:flex;gap:30px}.sk2>div{flex:1}
/* prompt */
.pr-wrap{position:absolute;left:70px;right:70px;top:200px}
.pr-box{padding:44px 48px 36px;border:2px solid rgba(var(--acc-rgb),.45);box-shadow:0 0 0 10px rgba(var(--acc-rgb),.06),0 40px 90px -30px rgba(0,0,0,.95)}
.pr-text{margin-top:26px;min-height:260px;line-height:1.3;color:var(--text)}
.ch{opacity:0}
.pr-foot{margin-top:30px;display:flex;align-items:center;justify-content:space-between}
.pr-tools{display:flex;align-items:center;gap:16px;color:var(--text-muted);font-size:26px}.pr-tools span:first-child{font-size:44px;line-height:1}
.pr-send{width:84px;height:84px;border-radius:50%;background:var(--acc);display:flex;align-items:center;justify-content:center}
.pr-status{margin-top:40px;display:flex;align-items:center;gap:18px;font-size:30px;color:var(--text-soft);opacity:0;padding-left:8px}
.pr-spin{width:30px;height:30px;border-radius:50%;border:4px solid rgba(var(--acc-rgb),.25);border-top-color:var(--acc)}
/* capas */
.cp-scene{position:absolute;left:190px;top:300px;width:700px;height:400px;transform-style:preserve-3d;transform:rotateX(48deg) rotateZ(-22deg)}
.cp-slide{position:absolute;inset:0;padding:40px 44px;border:2px solid var(--line);opacity:0;background:var(--surface2)}
.cp-t{font-weight:700;font-size:50px;letter-spacing:-.02em;line-height:1.05}
/* flujo */
.fl-svg{position:absolute;inset:0;width:1080px;height:1010px;overflow:visible}
.fl-p{fill:none;stroke:var(--line);stroke-width:4;stroke-dasharray:1000;stroke-dashoffset:1000}
.fl-d{fill:none;stroke:var(--acc);stroke-width:7;stroke-linecap:round;stroke-dasharray:60 1000;stroke-dashoffset:60;opacity:0}
.fl-in{position:absolute;top:40px;width:320px;height:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;opacity:0}
.fl-in.solo{width:460px;height:240px}
.fl-lab{font-size:34px;font-weight:700;letter-spacing:-.01em;text-align:center;padding:0 16px;line-height:1.1}
.fl-out{position:absolute;left:150px;top:520px;width:780px;height:440px;padding:36px 40px;opacity:0;border:2px solid rgba(var(--acc-rgb),.45)}
.fl-grid{margin-top:26px;display:grid;grid-template-columns:1fr 1fr;gap:22px}
.fl-th{height:140px;border-radius:16px;background:var(--surface2);border:1px solid var(--line);padding:18px;opacity:0}
.fl-th i{display:block;width:50%;height:18px;border-radius:9px;background:rgba(var(--acc-rgb),.85)}
.fl-th b{display:block;width:85%;height:12px;border-radius:6px;background:var(--line);margin-top:16px}.fl-th b.s{width:60%}
/* cursores */
.cu-doc{position:absolute;left:60px;right:60px;top:80px;height:700px;overflow:hidden}
.cu-bar{height:96px;display:flex;align-items:center;gap:24px;padding:0 30px;border-bottom:1px solid var(--line)}
.cu-dots{display:flex;gap:10px}.cu-dots i{width:16px;height:16px;border-radius:50%;background:var(--line)}
.cu-ed{font-size:24px;color:var(--text-muted)}
.cu-avs{margin-left:auto;display:flex}
.cu-av{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:24px;color:var(--ink);border:3px solid var(--surface);margin-left:-12px;flex:none}
.cu-av.c0,.cu-cur.c0{background:#FF8A5B;color:var(--ink)}.cu-av.c1,.cu-cur.c1{background:#B48CFF;color:var(--ink)}
.cu-cur.c0{color:#FF8A5B;background:none}.cu-cur.c1{color:#B48CFF;background:none}
.cu-av.me{background:var(--acc);font-size:18px}
.cu-canvas{padding:50px 50px}
.cu-title{position:relative;min-height:150px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.cu-new{position:absolute;left:0;top:0;font-size:84px;opacity:0;color:var(--text)}
.cu-sel{position:absolute;left:-14px;top:-10px;width:640px;height:118px;border:3px solid var(--acc);border-radius:8px;opacity:0;background:rgba(var(--acc-rgb),.08)}
.cu-cur{position:absolute;left:0;top:0;display:flex;align-items:flex-start;gap:4px}
.cu-cur span{margin-top:34px;padding:6px 14px;border-radius:10px;font-weight:700;font-size:24px;color:var(--ink)}
.cu-cur.c0 span{background:#FF8A5B}.cu-cur.c1 span{background:#B48CFF}
.cu-com{position:absolute;left:220px;right:40px;top:730px;padding:26px 30px;display:flex;gap:22px;align-items:center;font-size:36px;opacity:0;border:2px solid rgba(var(--acc-rgb),.35)}
.cu-com .cu-av{margin-left:0}
.cu-ok{position:absolute;left:90px;top:650px;display:flex;align-items:center;gap:12px;font-size:26px;color:var(--acc);opacity:0}
/* chips */
.ch-col{position:absolute;left:90px;right:90px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:34px}
.ch-file{height:200px;display:flex;align-items:center;gap:36px;padding:0 44px;opacity:0}
.ch-doc{position:relative;width:96px;height:118px;flex:none}
.ch-ext{position:absolute;left:-14px;bottom:12px;padding:5px 10px;border-radius:8px;background:var(--acc);color:var(--ink);font-family:var(--mono);font-weight:700;font-size:20px}
.ch-name{font-weight:700;font-size:56px;letter-spacing:-.02em}
.ch-dl{margin-left:auto;width:84px;height:84px;border-radius:50%;border:2px solid rgba(var(--acc-rgb),.5);display:flex;align-items:center;justify-content:center}
.ch-col.tags{align-items:center}
.ch-tag{display:flex;align-items:center;gap:26px;height:150px;padding:0 60px;font-weight:700;font-size:66px;letter-spacing:-.02em;opacity:0;border:2px solid rgba(var(--acc-rgb),.4)}
.ch-bar{width:100%;margin-top:30px;opacity:0}
.ch-bl{display:flex;justify-content:space-between;font-size:28px;color:var(--text-soft);letter-spacing:.08em;text-transform:uppercase}
.ch-track{margin-top:16px;height:22px;border-radius:11px;background:var(--line);overflow:hidden}
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
.rl-face{position:absolute;left:290px;top:60px;width:500px;height:500px;border-radius:50%;background:var(--surface);border:3px solid var(--line);
box-shadow:0 0 0 14px rgba(255,255,255,.03),0 40px 90px -30px rgba(0,0,0,.95)}
.rl-face i{position:absolute;left:246px;top:242px;width:8px;height:16px;border-radius:4px;background:var(--text-muted)}.rl-face i.big{height:26px;background:var(--text)}
.rl-arc{position:absolute;inset:26px;border-radius:50%;background:conic-gradient(rgba(var(--acc-rgb),.35) 0deg,rgba(var(--acc-rgb),.35) var(--arc,0deg),transparent var(--arc,0deg))}
.rl-h,.rl-m{position:absolute;left:244px;bottom:250px;width:12px;border-radius:6px;transform-origin:50% 100%}
.rl-h{height:120px;background:var(--text)}.rl-m{height:190px;width:8px;left:246px;background:var(--acc)}
.rl-c{position:absolute;left:232px;top:232px;width:36px;height:36px;border-radius:50%;background:var(--text);border:6px solid var(--acc)}
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
.al-row{display:flex;align-items:baseline;gap:18px;font-size:40px;padding:26px 18px;border-top:1px solid var(--line);border-radius:14px}
.al-row .mono{font-size:38px;font-weight:700}
.al-dots{flex:1;border-bottom:3px dotted var(--line)}
.al-lens{position:absolute;left:700px;top:610px;opacity:0;filter:drop-shadow(0 10px 30px rgba(0,0,0,.6))}
/* numero */
.nu-glow{position:absolute;left:140px;top:110px;width:800px;height:800px;border-radius:50%;background:radial-gradient(circle,rgba(var(--acc-rgb),.28),transparent 65%)}
.nu-box{position:absolute;left:40px;right:40px;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.nu-v{font-weight:700;font-size:230px;letter-spacing:-.05em;line-height:1;white-space:nowrap}.nu-v.sm{font-size:170px}.nu-v.xs{font-size:124px}
.nu-pre,.nu-suf{color:var(--acc)}
.nu-l{margin-top:30px;font-size:52px;font-weight:700;color:var(--text-soft);text-align:center;letter-spacing:-.01em;line-height:1.15;max-width:900px}
/* navegador */
.nv-win{position:absolute;left:50px;right:50px;top:40px;height:880px;overflow:hidden}
.nv-top{height:84px;display:flex;align-items:flex-end;gap:12px;padding:0 26px;background:rgba(128,128,128,.06)}
.nv-top .cu-dots{align-self:center;margin-right:14px}
.nv-tab{height:62px;padding:0 26px;display:flex;align-items:center;border-radius:14px 14px 0 0;font-size:26px;color:var(--text-muted);background:rgba(128,128,128,.08)}
.nv-tab.on{background:var(--surface2);color:var(--text)}
.nv-url{margin:22px 26px 0;height:64px;border-radius:32px;background:var(--surface2);display:flex;align-items:center;gap:14px;padding:0 26px;font-size:26px;color:var(--text-soft)}
.nv-body{padding:40px 40px}
.nv-h{font-weight:700;font-size:60px;letter-spacing:-.02em;line-height:1.08}
.nv-grid{margin-top:36px;display:grid;grid-template-columns:1fr 1fr;gap:24px}
.nv-card{height:220px;border-radius:20px;background:var(--surface2);border:1px solid var(--line);padding:22px;opacity:0}
.nv-card i{display:block;height:90px;border-radius:12px;background:rgba(var(--acc-rgb),.35)}
.nv-cursor{position:absolute;left:600px;top:700px}
/* celular */
.ph{position:absolute;left:250px;top:-10px;width:580px;height:1030px;border-radius:70px;background:var(--surface2);border:10px solid var(--surface3);box-shadow:var(--shadow),0 0 0 2px var(--line);overflow:hidden}
.ph-notch{position:absolute;left:200px;top:18px;width:160px;height:40px;border-radius:20px;background:#000}
.ph-top{margin-top:84px;display:flex;align-items:center;gap:18px;padding:0 30px 24px;border-bottom:1px solid var(--line)}
.ph-av{width:66px;height:66px;border-radius:50%;background:var(--acc);display:flex;align-items:center;justify-content:center}
.ph-n{font-weight:700;font-size:32px}.ph-s{font-size:20px;color:var(--acc)}
.ph-body{padding:30px 26px;display:flex;flex-direction:column;gap:20px}
.ph-m{max-width:86%;padding:20px 24px;border-radius:26px;font-size:30px;line-height:1.3;opacity:0}
.ph-m.me{align-self:flex-end;background:var(--acc);color:var(--ink);border-bottom-right-radius:8px}
.ph-m.ia{align-self:flex-start;background:var(--surface3);border-bottom-left-radius:8px}
.ph-typing{align-self:flex-start;display:flex;gap:10px;padding:22px 26px;border-radius:26px;background:var(--surface3);opacity:0}
.ph-typing i{width:14px;height:14px;border-radius:50%;background:var(--text-muted)}
/* grafico */
.gr-wrap{position:absolute;left:60px;right:60px;top:40px;bottom:40px;padding:44px}
.gr-cols{position:absolute;left:44px;right:44px;bottom:44px;top:120px;display:flex;align-items:flex-end;gap:28px}
.gr-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}
.gr-b{width:100%;border-radius:16px 16px 6px 6px;background:var(--line);transform-origin:50% 100%;transform:scaleY(0)}
.gr-b.hi{background:var(--acc);box-shadow:0 0 50px rgba(var(--acc-rgb),.4)}
.gr-v{font-size:34px;font-weight:700;margin-bottom:14px;opacity:0}
.gr-l{margin-top:18px;font-size:28px;color:var(--text-soft);text-align:center}
/* comparacion */
.cm-wrap{position:absolute;left:50px;right:50px;top:30px;bottom:30px;display:flex;flex-direction:column;justify-content:center;align-items:stretch;gap:26px}
.cm-col{position:relative;padding:40px 44px;opacity:0}
.cm-col.an{color:var(--text-muted)}.cm-col.an .eyebrow{color:var(--text-muted)}
.cm-col.de{border:2px solid rgba(var(--acc-rgb),.5)}
.cm-head{display:flex;align-items:center;gap:26px}.cm-head .eyebrow{font-size:34px}
.cm-col.an .lg-badge{filter:grayscale(1);opacity:.75}
.cm-it{display:flex;align-items:center;gap:20px;font-size:46px;font-weight:700;margin-top:24px;letter-spacing:-.01em;line-height:1.12}
.cm-col.de .cm-it svg{color:var(--acc)}
.cm-vs{align-self:center;width:100px;height:100px;border-radius:50%;background:var(--surface2);border:2px solid var(--line);
display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:700;opacity:0;flex:none}
/* particulas */
.pa-cv{position:absolute;left:0;top:0;width:1080px;height:1010px}
.pa-box{position:absolute;left:60px;right:60px;top:300px;padding:40px;text-align:center;background:radial-gradient(ellipse,rgba(10,14,26,.92) 30%,transparent 72%)}
/* terminal */
.tm-win{position:absolute;left:50px;right:50px;top:150px;height:640px;border-radius:var(--radius);background:var(--surface2);border:1px solid var(--line);
box-shadow:var(--shadow),0 0 0 8px rgba(var(--acc-rgb),.05);overflow:hidden}
.tm-top{height:76px;display:flex;align-items:center;gap:24px;padding:0 28px;background:rgba(128,128,128,.08);border-bottom:1px solid var(--line)}
.tm-t{font-size:24px;color:var(--text-muted)}
.tm-body{padding:44px 44px;font-size:40px;line-height:1.38}
.tm-l{display:flex;gap:18px;align-items:flex-start;margin-bottom:26px;opacity:0}
.tm-l.cmd{color:var(--text);font-weight:700}.tm-pr{color:var(--acc)}
.tm-l.out{color:var(--text-soft)}.tm-dot{color:var(--acc);font-size:26px;margin-top:6px}
.tm-l.ok{color:var(--acc);font-weight:700}.tm-l.ok svg{flex:none;margin-top:6px}
.tm-cur{width:20px;height:40px;background:var(--acc);opacity:0}
/* linea de tiempo */
.lt-rail,.lt-fill{position:absolute;left:170px;top:80px;width:6px;height:860px;border-radius:3px;background:var(--line)}
.lt-fill{background:var(--acc);transform-origin:50% 0;transform:scaleY(0);box-shadow:0 0 30px rgba(var(--acc-rgb),.5)}
.lt-h{position:absolute;left:0;right:60px;height:200px;opacity:0}
.lt-dot{position:absolute;left:153px;top:22px;width:40px;height:40px;border-radius:50%;background:var(--bg);border:6px solid var(--acc)}
.lt-y{position:absolute;left:230px;top:-6px;font-weight:700;font-size:92px;letter-spacing:-.04em;line-height:1;color:var(--acc)}
.lt-t{position:absolute;left:232px;right:0;top:100px;font-size:40px;font-weight:700;line-height:1.15;color:var(--text-soft);letter-spacing:-.01em}
/* cierre */
.end{position:absolute;left:84px;right:84px;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.end img{width:260px;height:260px;filter:var(--mark-filter)}
.wm{margin-top:10px;font-weight:700;font-size:150px;letter-spacing:-.03em;line-height:1}
.sub{margin-top:30px;font-size:46px;color:var(--text-soft)}
.cta{margin-top:60px;display:flex;align-items:center;gap:18px;padding:30px 54px;border-radius:24px;background:var(--grad);font-weight:700;font-size:46px;color:#fff;box-shadow:0 10px 30px -8px rgba(91,111,228,.55)}
.src{margin-top:50px;font-size:26px;color:var(--text-muted)}

/* audios de WhatsApp */
.ph-m.au{display:flex;align-items:center;gap:14px;min-width:420px;padding:18px 22px}
.au-play{width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.14);flex:none}
.ph-m.me .au-play{background:rgba(0,0,0,.12)}
.au-w{position:relative;flex:1;height:56px}
.au-bars{position:absolute;inset:0;display:flex;align-items:center;gap:4px}
.au-bars i{flex:1;border-radius:3px;background:currentColor;opacity:.35}
.au-bars.on{clip-path:inset(0 100% 0 0)}.au-bars.on i{opacity:1;background:var(--acc)}
.ph-m.me .au-bars.on i{background:var(--on-acc)}
.au-t{font-size:22px;opacity:.75;flex:none}
/* llamada entrante */
.ll-ph{position:absolute;left:250px;top:-10px;width:580px;height:1030px;border-radius:70px;overflow:hidden;
background:radial-gradient(ellipse at 50% 30%,#2A3A5C 0%,#0E1424 60%,#05070D 100%);border:10px solid #1C2540;box-shadow:var(--shadow);color:#fff}
.ll-app{position:absolute;left:0;right:0;top:96px;display:flex;align-items:center;justify-content:center;gap:12px;font-size:26px;color:rgba(255,255,255,.75)}
.ll-avw{position:absolute;left:150px;top:220px;width:260px;height:260px}
.ll-ring{position:absolute;inset:0;border-radius:50%;border:3px solid rgba(255,255,255,.5);opacity:0}
.ll-av{position:absolute;inset:20px;border-radius:50%;background:var(--acc);color:var(--on-acc);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:110px}
.ll-name{position:absolute;left:20px;right:20px;top:520px;text-align:center;font-weight:700;font-size:62px;letter-spacing:-.02em}
.ll-num{position:absolute;left:20px;right:20px;top:605px;text-align:center;font-size:26px;color:rgba(255,255,255,.6)}
.ll-btns{position:absolute;left:70px;right:70px;bottom:110px;display:flex;justify-content:space-between}
.ll-b{width:130px;height:130px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.ll-b.no{background:#EF4444}.ll-b.no svg{transform:rotate(135deg)}.ll-b.si{background:#22C55E}
.ll-stamp{position:absolute;left:40px;right:40px;top:655px;padding:18px 10px;text-align:center;font-weight:700;font-size:58px;letter-spacing:.02em;color:#EF4444;
border:7px solid #EF4444;border-radius:18px;background:rgba(10,0,0,.55);transform:rotate(-10deg);opacity:0}
/* logos */
.lg-badge{display:flex;align-items:center;justify-content:center;background:#FFFFFF;box-shadow:0 20px 50px -18px rgba(0,0,0,.6),0 0 0 1px rgba(0,0,0,.06);flex:none}
.lg-badge .lg{display:block}
/* marcas */
.mk-wrap{position:absolute;left:40px;right:40px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:50px}
.mk-row{display:flex;align-items:center;justify-content:center;gap:40px;flex-wrap:wrap;width:100%}
.mk-wrap.n3 .mk-row,.mk-wrap.n4 .mk-row{gap:36px 50px}
.mk-wrap.n4 .mk-row{display:grid;grid-template-columns:1fr 1fr;justify-items:center}
.mk-it{position:relative;display:flex;flex-direction:column;align-items:center;gap:26px;opacity:0}
.mk-glow{position:absolute;left:50%;top:0;width:520px;height:520px;margin-left:-260px;margin-top:-80px;border-radius:50%;
background:radial-gradient(circle,color-mix(in srgb,var(--bc) 55%,transparent) 0%,transparent 62%);opacity:.0;pointer-events:none}
.mk-name{font-weight:700;font-size:52px;letter-spacing:-.02em}
.mk-wrap.n1 .mk-name{font-size:84px}
.mk-pill{display:flex;align-items:center;gap:12px;padding:12px 24px;border-radius:999px;font-weight:700;font-size:32px;opacity:0}
.mk-pill.ok{background:rgba(34,197,94,.16);color:#22C55E;border:2px solid rgba(34,197,94,.5)}
.mk-pill.no{background:rgba(239,68,68,.16);color:#EF4444;border:2px solid rgba(239,68,68,.5)}
.mk-mid{font-size:60px;font-weight:700;color:var(--acc);opacity:0;align-self:center;margin-top:-90px}
.mk-tit{font-size:30px}
.mk-burst{position:absolute;left:540px;top:505px;width:40px;height:40px;margin:-20px 0 0 -20px;border-radius:50%;border:6px solid var(--acc);opacity:0}
/* impacto */
.ip-box{position:absolute;left:60px;right:60px;top:-120px;bottom:-60px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;
font-weight:700;line-height:.98;letter-spacing:-.045em}
.im-ln{white-space:nowrap}
.ip-w{position:relative;display:inline-block;padding:0 .08em;margin-right:.04em;opacity:0}
.ip-w>span{position:relative}
.ip-bg{position:absolute;left:0;right:0;top:.06em;bottom:.02em;background:var(--acc);transform-origin:0 50%;transform:scaleX(0);border-radius:.06em}
.ip-w.kw>span{color:var(--text)}
.ip-logo{margin-bottom:40px;opacity:0}
#flash{position:absolute;inset:0;background:#fff;opacity:0;pointer-events:none}
/* presentador */
.stage.full{top:0;height:1920px;clip-path:none}
.pv-wrap{position:absolute;inset:-40px;overflow:hidden;background:#000}
.pv-poster,.pv-vid{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}
.pv-shade{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.55) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 52%,rgba(0,0,0,.72) 82%,rgba(0,0,0,.8) 100%)}
.pv-name{position:absolute;left:70px;top:1500px;display:flex;align-items:center;gap:18px;opacity:0}
.pv-name i{width:8px;height:74px;border-radius:4px;background:var(--acc)}
.pv-name b{display:block;font-weight:700;font-size:40px;color:#fff;letter-spacing:-.01em}
.pv-name span{display:block;margin-top:4px;font-size:24px;color:rgba(255,255,255,.75);letter-spacing:.12em;text-transform:uppercase}
.pv-live{position:absolute;right:70px;top:226px;display:flex;align-items:center;gap:10px;padding:10px 18px;border-radius:999px;background:rgba(0,0,0,.45);
font-size:22px;letter-spacing:.16em;color:#fff;opacity:0}
.pv-live i{width:14px;height:14px;border-radius:50%;background:var(--acc);box-shadow:0 0 14px var(--acc)}
.cap.low{top:1180px;color:#fff;text-shadow:0 4px 24px rgba(0,0,0,.85)}
/* imagen */
.im-full{position:absolute;left:40px;right:40px;top:0;bottom:0;border-radius:var(--radius);overflow:hidden;background:var(--surface2);box-shadow:var(--shadow)}
.im-full img{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;transform-origin:50% 50%}
.im-shade{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.05) 40%,rgba(0,0,0,.72) 100%)}
.im-tit{position:absolute;left:90px;right:90px;bottom:80px;font-weight:700;color:#fff;line-height:1.08;letter-spacing:-.02em;text-shadow:0 4px 24px rgba(0,0,0,.6);opacity:0}
.im-cred{position:absolute;right:70px;bottom:28px;font-size:20px;color:rgba(255,255,255,.75);letter-spacing:.06em;opacity:0}
.im-card{position:absolute;left:130px;top:40px;width:820px;padding:30px 30px 44px;background:#FBF8F1;border-radius:14px;box-shadow:0 60px 100px -30px rgba(0,0,0,.8);opacity:0}
.im-cf{height:700px;border-radius:8px;overflow:hidden;background:#111}
.im-cf img{width:100%;height:100%;object-fit:cover;transform-origin:50% 50%}
.im-cap{margin-top:30px;font-weight:700;font-size:44px;color:#1A1712;letter-spacing:-.02em;line-height:1.1}
.im-card .im-cred{position:static;margin-top:10px;color:#7A7262}
/* codigo */
.cd-win{position:absolute;left:50px;right:50px;top:120px;min-height:420px;border-radius:var(--radius);background:var(--surface2);border:1px solid var(--line);box-shadow:var(--shadow);overflow:hidden}
.cd-top{height:76px;display:flex;align-items:center;gap:24px;padding:0 28px;background:rgba(128,128,128,.08);border-bottom:1px solid var(--line)}
.cd-tab{font-size:24px;color:var(--text-soft);padding:12px 20px;border-radius:10px 10px 0 0;background:var(--surface3);align-self:flex-end;margin-bottom:-1px}
.cd-body{padding:34px 30px;font-size:34px;line-height:1.5}
.cd-l{display:flex;gap:22px;align-items:flex-start;padding:4px 14px;border-radius:10px;opacity:0;white-space:nowrap}
.cd-n{width:46px;flex:none;text-align:right;color:var(--text-muted);font-size:26px;padding-top:6px}
.cd-t{color:var(--text-soft)}
.cd-l.mk{background:rgba(var(--acc-rgb),.14);box-shadow:inset 4px 0 0 var(--acc)}
.c-k{color:var(--acc);font-weight:700}.c-s{color:#7FD28A}.c-n{color:#F2B76B}.c-c{color:var(--text-muted);font-style:italic}.c-f{color:#9DB7FF}.c-o{color:var(--text)}
.tema-claro .c-s{color:#2E8B46}.tema-claro .c-n{color:#B86A00}.tema-claro .c-f{color:#3B5BD6}
/* pasos */
.ps-col{position:absolute;left:110px;right:80px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;gap:54px}
.ps-rail,.ps-fill{position:absolute;left:52px;top:120px;bottom:120px;width:6px;border-radius:3px;background:var(--line)}
.ps-fill{background:var(--acc);transform-origin:50% 0;transform:scaleY(0);box-shadow:0 0 24px rgba(var(--acc-rgb),.5)}
.ps-it{display:flex;align-items:center;gap:40px;opacity:0}
.ps-n{width:110px;height:110px;flex:none;border-radius:50%;background:var(--surface2);border:3px solid var(--line);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:54px;color:var(--text-muted)}
.ps-n.on{background:var(--acc);color:var(--on-acc);border-color:var(--acc);box-shadow:0 0 40px rgba(var(--acc-rgb),.45)}
.ps-t{font-weight:700;font-size:54px;letter-spacing:-.02em;line-height:1.08}
.ps-s{margin-top:8px;font-size:30px;color:var(--text-muted)}
/* anillo */
.an-box{position:absolute;left:190px;top:60px;width:700px;height:700px}
.an-svg{position:absolute;inset:0;width:700px;height:700px;transform:rotate(-90deg)}
.an-bg{fill:none;stroke:var(--line);stroke-width:34}
.an-fg{fill:none;stroke:var(--acc);stroke-width:34;stroke-linecap:round;stroke-dasharray:100;stroke-dashoffset:100;filter:drop-shadow(0 0 24px rgba(var(--acc-rgb),.6))}
.an-v{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:200px;letter-spacing:-.05em;line-height:1}
.an-suf{font-size:100px;color:var(--acc);margin-left:8px;margin-top:40px}
.an-l{position:absolute;left:60px;right:60px;top:790px;text-align:center;font-weight:700;font-size:52px;color:var(--text-soft);line-height:1.15;opacity:0}
/* titular */
.ti-logo{position:absolute;left:70px;top:0;z-index:2;opacity:0}
.ti-card.con-logo{top:190px}
.ti-card{position:absolute;left:50px;right:50px;top:110px;padding:40px 50px 50px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);opacity:0}
.ti-top{display:flex;align-items:center;gap:22px;font-size:24px;letter-spacing:.16em;text-transform:uppercase;color:var(--text-muted)}
.ti-tag{padding:8px 16px;border-radius:8px;background:var(--acc);color:var(--on-acc);font-weight:700;opacity:0}
.ti-fe{margin-left:auto}
.ti-h{margin-top:36px;font-weight:700;line-height:1.06;letter-spacing:-.03em}
.ti-w{display:inline-block;opacity:0;margin-right:.24em}
.ti-baj{margin-top:30px;font-size:36px;line-height:1.3;color:var(--text-soft)}
.ti-rule{margin-top:40px;height:4px;background:var(--acc);transform-origin:0 50%;transform:scaleX(0)}
.tema-editorial .ti-h{font-weight:600}
/* cita */
.ci-card{position:absolute;left:60px;right:60px;top:90px;padding:60px 60px 50px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);opacity:0}
.ci-q{position:absolute;left:44px;top:-50px;font-size:240px;line-height:1;color:var(--acc);font-family:"Lora",Georgia,serif;font-weight:700}
.ci-t{margin-top:40px;font-weight:700;line-height:1.22;letter-spacing:-.01em}
.tema-editorial .ci-t{font-weight:500;font-style:italic}
.ci-w{display:inline-block;opacity:0;margin-right:.26em}
.ci-a{margin-top:44px;display:flex;align-items:center;gap:22px;opacity:0}
.ci-av{width:76px;height:76px;border-radius:50%;background:var(--acc);color:var(--ink);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:34px;flex:none}
.ci-n{font-weight:700;font-size:34px}.ci-c{margin-top:4px;font-size:22px;color:var(--text-muted);letter-spacing:.1em;text-transform:uppercase}
/* tabla */
.tb-card{position:absolute;left:50px;right:50px;top:60px;padding:40px 44px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.tb-h,.tb-r{display:grid;grid-template-columns:1.4fr repeat(calc(var(--cols) - 1),1fr);gap:20px;padding:22px 20px;align-items:center}
.tb-h{font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:var(--text-muted);border-bottom:2px solid var(--line);margin-top:20px}
.tb-r{font-size:36px;font-weight:700;border-bottom:1px solid var(--line);opacity:0;border-radius:12px}
.tb-r span:not(:first-child){font-family:var(--mono);font-weight:500;font-size:32px;color:var(--text-soft)}
.tb-r.mk.on{background:rgba(var(--acc-rgb),.16);box-shadow:inset 4px 0 0 var(--acc)}
.tb-r.mk.on span{color:var(--text)}
/* calendario */
.ca-card{position:absolute;left:50px;right:50px;top:60px;padding:40px 40px 44px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.ca-top{display:flex;align-items:baseline;gap:20px}.ca-mes{font-weight:700;font-size:60px;letter-spacing:-.02em}.ca-y{font-size:28px;color:var(--text-muted)}
.ca-dow{margin-top:30px;display:grid;grid-template-columns:repeat(7,1fr);gap:10px;font-size:22px;color:var(--text-muted);text-align:center;letter-spacing:.1em}
.ca-grid{margin-top:14px;display:grid;grid-template-columns:repeat(7,1fr);gap:10px}
.ca-c{height:118px;border-radius:14px;background:var(--surface2);position:relative;padding:12px 14px;font-size:30px;font-weight:700;color:var(--text-soft);border:1px solid transparent}
.ca-c.off{background:transparent}
.ca-c b{position:absolute;left:8px;right:8px;bottom:10px;font-size:19px;line-height:1.1;font-weight:700;color:var(--ink);background:var(--acc);border-radius:8px;padding:6px 8px;opacity:0;text-align:center}
.ca-c.mk.on{border-color:var(--acc);background:rgba(var(--acc-rgb),.14);color:var(--text)}
/* planes */
.pl-row{position:absolute;left:50px;right:50px;top:120px;display:flex;gap:24px;align-items:stretch}
.pl-c{flex:1;padding:40px 30px 44px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);opacity:0;position:relative;min-height:560px}
.pl-row.n2 .pl-c{padding:48px 40px}
.pl-n{font-size:24px;letter-spacing:.16em;text-transform:uppercase;color:var(--text-muted)}
.pl-p{margin-top:30px;font-weight:700;font-size:72px;letter-spacing:-.04em;line-height:1}
.pl-row.n3 .pl-p{font-size:56px}
.pl-d{margin-top:24px;font-size:30px;line-height:1.3;color:var(--text-soft)}
.pl-c.hi{border:2px solid var(--acc);box-shadow:0 0 0 10px rgba(var(--acc-rgb),.08),var(--shadow)}
.pl-c.hi .pl-p{color:var(--acc)}
.pl-tag{position:absolute;left:30px;top:-22px;padding:8px 18px;border-radius:999px;background:var(--acc);color:var(--ink);font-weight:700;font-size:22px}
#prog{position:absolute;left:0;bottom:0;width:100%;height:6px;background:var(--grad);transform-origin:0 50%}

/* ===== v2.5 estilo marca ===== */
#sgrid{position:absolute;inset:0;background-image:linear-gradient(rgba(14,27,51,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(14,27,51,.055) 1px,transparent 1px);background-size:54px 54px;
-webkit-mask-image:radial-gradient(ellipse at 50% 45%,#000 35%,transparent 85%);mask-image:radial-gradient(ellipse at 50% 45%,#000 35%,transparent 85%)}
.tema-estudio #b1{background:radial-gradient(circle,rgba(91,111,228,.10) 0%,rgba(91,111,228,0) 62%)}
.tema-estudio #vig{background:radial-gradient(ellipse at 50% 45%,transparent 60%,rgba(14,27,51,.10) 100%)}
.tema-estudio #grain{opacity:.07;mix-blend-mode:multiply}
.tema-estudio{--shadow:0 34px 80px -34px rgba(14,27,51,.42);--warn:#D98E00}
.fondo-liso #lines,.fondo-liso .blob{display:none}
.estilo-marca .cap{font-weight:700;font-size:68px;letter-spacing:-.03em;line-height:1.14}
.estilo-marca .kb{border:none;background:var(--acc);border-radius:10px;left:-12px;right:-12px;top:6px;bottom:-2px}
.estilo-marca .kb i{display:none}
.estilo-marca .kw .w{position:relative}
.lema{margin-top:22px;font-size:26px;letter-spacing:.42em;color:var(--text-muted);text-transform:uppercase}
/* sitio: capturas reales en navegador y celular */
.st-scene{position:absolute;inset:0;perspective:1800px;transform-style:preserve-3d}
.st-br{position:absolute;left:30px;width:1020px;border-radius:22px;overflow:hidden;background:#fff;box-shadow:0 50px 100px -40px rgba(0,0,0,.55),0 0 0 1px rgba(0,0,0,.08);opacity:0}
.st-br.lay-duo{top:40px;left:54px;width:960px}.st-br.lay-duo .st-shot{width:960px;height:600px}.st-br.lay-escritorio{top:110px}
.st-bar{height:58px;display:flex;align-items:center;gap:22px;padding:0 24px;background:#F1F1F3;border-bottom:1px solid #E1E1E6}
.st-bar .cu-dots i{background:#D5D5DB}
.st-url{flex:1;display:flex;align-items:center;gap:10px;height:38px;border-radius:19px;background:#fff;color:#5B6070;font-size:22px;padding:0 18px;border:1px solid #E1E1E6;position:relative;overflow:hidden}
.st-shot{position:relative;width:1020px;height:638px;overflow:hidden;background:#eee}
.st-img{position:absolute;left:0;top:0;width:100%;height:auto;opacity:0;display:block}
.st-ph{position:absolute;border-radius:58px;background:#0B0B0F;padding:12px;box-shadow:0 50px 100px -30px rgba(0,0,0,.6),0 0 0 2px rgba(255,255,255,.06) inset;opacity:0}
.st-ph.lay-duo{left:690px;top:262px;width:318px;height:688px}
.st-ph.lay-celular{left:332px;top:0px;width:416px;height:900px;border-radius:64px}
.st-scr{position:relative;width:100%;height:100%;border-radius:46px;overflow:hidden;background:#fff}
.st-ph.lay-celular .st-scr{border-radius:52px}
.st-isl{position:absolute;left:50%;top:26px;width:110px;height:32px;margin-left:-55px;border-radius:16px;background:#0B0B0F}
.st-ph.lay-celular .st-isl{width:130px;height:36px;top:30px;margin-left:-65px}
.st-tap{position:absolute;width:0;height:0;opacity:0;z-index:5}
.st-tap::before{content:"";position:absolute;left:-34px;top:-34px;width:68px;height:68px;border-radius:50%;background:rgba(255,255,255,.55);border:4px solid rgba(20,20,30,.55);box-shadow:0 6px 18px rgba(0,0,0,.35)}
.st-tap i{position:absolute;left:-46px;top:-46px;width:92px;height:92px;border-radius:50%;border:5px solid rgba(255,255,255,.95);box-shadow:0 0 0 3px rgba(20,20,30,.35)}
.st-chip{position:absolute;display:flex;align-items:center;gap:14px;padding:16px 26px;border-radius:999px;background:#fff;color:#0E1B33;font-weight:700;font-size:30px;
box-shadow:0 20px 44px -16px rgba(0,0,0,.45),0 0 0 1px rgba(0,0,0,.06);opacity:0;white-space:nowrap;z-index:6}
.st-dot{width:16px;height:16px;border-radius:50%;background:#22C55E;box-shadow:0 0 0 6px rgba(34,197,94,.18)}
.st-chip.lay-duo.c0{left:50px;top:590px}.st-chip.lay-duo.c1{left:330px;top:500px}.st-chip.lay-duo.c2{left:50px;top:680px}
.st-chip.lay-escritorio.c0{left:60px;top:60px}.st-chip.lay-escritorio.c1{right:60px;top:690px}.st-chip.lay-escritorio.c2{left:60px;top:740px}
.st-chip.lay-celular.c0{left:80px;top:170px}.st-chip.lay-celular.c1{right:80px;top:470px}.st-chip.lay-celular.c2{left:80px;top:740px}
.st-lab{position:absolute;opacity:0}
.st-lab.lay-duo{left:60px;top:770px;width:600px}
.st-lab.lay-escritorio{left:60px;right:60px;top:850px;text-align:center}
.st-lab.lay-celular{left:0;right:0;top:930px;text-align:center}
.st-n{font-weight:700;font-size:56px;letter-spacing:-.03em;line-height:1.05}
.st-r{margin-top:12px;font-size:24px;letter-spacing:.16em;text-transform:uppercase;color:var(--text-muted)}
/* carrusel */
.cr-scene{position:absolute;inset:0;perspective:1800px}
.cr-fr.st-br{top:60px}
.cr-scene.m-cel .cr-fr{top:0;height:840px;width:388px;left:346px}
.cr-foot{position:absolute;left:60px;right:60px;top:760px;height:120px;opacity:0}
.cr-scene.m-cel .cr-foot{top:870px}
.cr-labs{position:absolute;left:0;right:220px;top:0;height:120px}
.cr-lab{position:absolute;left:0;top:0;opacity:0}
.cr-lab b{display:block;font-size:58px;letter-spacing:-.03em;line-height:1.05}
.cr-lab span{display:block;margin-top:10px;font-size:24px;letter-spacing:.16em;text-transform:uppercase;color:var(--acc)}
.cr-num{position:absolute;right:0;top:6px;font-size:40px;color:var(--text-muted);display:flex;gap:10px;align-items:baseline}
.cr-nums{position:relative;display:inline-block;width:56px;height:48px;color:var(--text)}
.cr-nums span{position:absolute;left:0;top:0;opacity:0}
.cr-num em{font-style:normal;font-size:30px}
.cr-us{position:relative;flex:1;height:30px}
.cr-u{position:absolute;left:0;top:0;opacity:0;white-space:nowrap}
/* muro */
.stage.libre{clip-path:none}
.mu-wall{position:absolute;left:-240px;right:-240px;top:-200px;bottom:-200px;perspective:1600px;overflow:hidden}
.mu-grid{position:absolute;left:0;right:0;top:0;bottom:0;display:flex;gap:34px;justify-content:center;transform:rotateX(32deg) rotateZ(-16deg) scale(1.08);transform-origin:50% 50%}
.mu-col{width:460px;display:flex;flex-direction:column;gap:34px}
.mu-it{width:460px;height:300px;border-radius:20px;overflow:hidden;background:#ddd;box-shadow:0 30px 60px -24px rgba(0,0,0,.55);flex:none}
.mu-it img{width:100%;height:100%;object-fit:cover;object-position:50% 0}
.mu-shade{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 52%,rgba(var(--bg-rgb),.96) 22%,rgba(var(--bg-rgb),.72) 48%,rgba(var(--bg-rgb),0) 80%)}
.mu-txt{position:absolute;left:60px;right:60px;top:0;bottom:0;display:flex;flex-wrap:wrap;align-content:center;justify-content:center;gap:0 .22em;
font-weight:700;letter-spacing:-.04em;line-height:1.02;text-align:center}
/* notificaciones */
.nt-col{position:absolute;left:60px;right:60px;top:40px;display:flex;flex-direction:column;gap:24px}
.nt-card{display:flex;gap:26px;align-items:center;padding:26px 30px;border-radius:40px;background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow);opacity:0}
.tema-noche .nt-card,.tema-grilla .nt-card,.tema-neon .nt-card,.tema-editorial .nt-card{background:rgba(255,255,255,.08);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px)}
.nt-ico{width:86px;height:86px;border-radius:22px;background:var(--grad);display:flex;align-items:center;justify-content:center;flex:none}
.nt-tx{flex:1;min-width:0}
.nt-top{display:flex;justify-content:space-between;font-size:21px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-muted)}
.nt-t{margin-top:6px;font-weight:700;font-size:36px;letter-spacing:-.02em;line-height:1.15}
.nt-b{margin-top:4px;font-size:29px;color:var(--text-soft);line-height:1.25}
/* caos */
.cz-card{position:absolute;left:330px;top:170px;width:420px;height:560px;border-radius:30px;overflow:hidden;background:var(--surface2);box-shadow:var(--shadow);opacity:0}
.cz-card img{width:100%;height:100%;object-fit:cover}
.cz-empty{display:flex;align-items:center;justify-content:center}
.cz-app{position:absolute;opacity:0;z-index:3}
.cz-n{position:absolute;right:-12px;top:-12px;min-width:46px;height:46px;padding:0 10px;border-radius:23px;background:#EF3B36;color:#fff;font-weight:700;font-size:26px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 4px var(--bg)}
.cz-noti{position:absolute;display:flex;align-items:center;gap:12px;padding:14px 22px;border-radius:18px;background:#fff;color:#0E1B33;font-weight:700;font-size:27px;white-space:nowrap;
box-shadow:0 18px 40px -16px rgba(0,0,0,.5),0 0 0 1px rgba(0,0,0,.06);opacity:0;z-index:4}
.cz-noti b{margin-left:6px;padding:4px 12px;border-radius:10px;background:#E8F7EE;color:#167C3E}
.cz-noti.t-rojo b{background:#FDE8E8;color:#C62828}.cz-noti.t-amarillo b{background:#FFF4D6;color:#9A6B00}
.cz-dot{width:14px;height:14px;border-radius:50%;background:#EF3B36;flex:none}
.cz-noti.t-amarillo .cz-dot{background:#F2B200}.cz-noti.t-verde .cz-dot{background:#22C55E}.cz-noti.t-neutro .cz-dot{background:#5B6FE4}
.cz-cred{position:absolute;left:330px;top:742px;width:420px;text-align:right;font-size:18px;color:var(--text-muted);letter-spacing:.06em;opacity:0}
/* planilla */
.pz-win{position:absolute;left:40px;right:40px;top:40px;height:880px;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 50px 100px -40px rgba(0,0,0,.6),0 0 0 1px rgba(0,0,0,.08);opacity:0;color:#1F2937}
.pz-top{height:70px;background:#1D6F42;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 28px;font-family:var(--display);font-weight:700;font-size:28px}
.pz-wb{display:flex;gap:16px}.pz-wb i{width:18px;height:18px;border-radius:4px;border:2px solid rgba(255,255,255,.7)}
.pz-fx{height:56px;display:flex;align-items:center;gap:20px;padding:0 22px;border-bottom:1px solid #DADCE0;font-size:24px;color:#5F6368}
.pz-fx span{font-style:italic;color:#1D6F42;font-weight:700}.pz-fx em{font-style:normal;color:#202124}
.pz-grid{display:flex;flex-direction:column}
.pz-row{display:grid;grid-template-columns:64px repeat(6,1fr);height:52px;border-bottom:1px solid #E3E5E8}
.pz-row.hd{height:44px;background:#F3F4F6}
.pz-rn,.pz-ch{display:flex;align-items:center;justify-content:center;font-size:20px;color:#6B7280;background:#F3F4F6;border-right:1px solid #E3E5E8}
.pz-c{border-right:1px solid #E3E5E8;display:flex;align-items:center;padding:0 12px}
.pz-c i{display:block;height:14px;border-radius:7px;background:#D1D5DB}
.pz-c.rojo{background:#FDE2E1}.pz-c.rojo i{background:#F19C99}
.pz-c.amar{background:#FFF3C4}.pz-c.amar i{background:#E9C86A}
.pz-dlg{position:absolute;left:170px;width:740px;top:300px;padding:40px 44px 34px;border-radius:22px;background:#fff;color:#202124;box-shadow:0 40px 90px -20px rgba(0,0,0,.6),0 0 0 1px rgba(0,0,0,.08);opacity:0;z-index:5}
.pz-dh{display:flex;align-items:center;gap:20px;font-family:var(--display);font-size:40px;letter-spacing:-.02em}
.pz-dt{margin-top:20px;font-family:var(--display);font-size:30px;line-height:1.35;color:#3C4043}
.pz-db{margin-top:34px;display:flex;justify-content:flex-end;gap:18px;font-family:var(--display);font-weight:700;font-size:28px}
.pz-db span{padding:14px 30px;border-radius:12px;color:#1D6F42}.pz-db .ok{background:#1D6F42;color:#fff}
/* logo (marca a pantalla completa) */
.lo-bg{position:absolute;inset:0;background:var(--grad)}
.lo-bg.f-navy{background:#122A4D}.lo-bg.f-oscuro{background:#0A0E1A}
.lo-box{position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff}
.lo-mark{width:300px;height:300px}
.lo-wm{margin-top:8px;font-family:"FreeSans","Helvetica Neue",Arial,sans-serif;font-weight:700;font-size:176px;letter-spacing:-.04em;line-height:1}
.lo-wm span{opacity:.82}
.lo-sub{margin-top:34px;font-size:48px;font-weight:700;letter-spacing:-.01em;opacity:.95}
.lo-lema{margin-top:26px;font-size:26px;letter-spacing:.42em;opacity:.8}
/* cuenta regresiva */
.cu2-grid{position:absolute;left:-60px;right:-60px;top:-470px;bottom:-470px;background-image:linear-gradient(rgba(var(--acc-rgb),.12) 1px,transparent 1px),linear-gradient(90deg,rgba(var(--acc-rgb),.12) 1px,transparent 1px);background-size:40px 40px}
.cu2-card{position:absolute;left:220px;top:120px;width:640px;height:420px;border-radius:34px;background:var(--surface);box-shadow:var(--shadow);border:1px solid var(--border)}
.cu2-card.plano{background:transparent;box-shadow:none;border:3px dashed rgba(var(--acc-rgb),.75)}
.cu2-sk{position:absolute;left:60px;top:58px;right:60px}
.cu2-sk i{display:block;height:24px;width:62%;border-radius:12px;background:var(--line)}.cu2-sk i.s{margin-top:18px;width:40%}
.cu2-card.plano .cu2-sk i{background:transparent;border:2px dashed rgba(var(--acc-rgb),.6)}
.cu2-btn{position:absolute;left:130px;top:220px;width:380px;height:110px;border-radius:55px;background:var(--acc);color:var(--on-acc);display:flex;align-items:center;justify-content:center;
font-weight:700;font-size:40px;letter-spacing:-.01em;box-shadow:0 18px 40px -14px rgba(var(--acc-rgb),.75)}
.cu2-card.plano .cu2-btn{background:transparent;color:var(--acc);border:3px dashed var(--acc);box-shadow:none}
.cu2-bt,.cu2-ok{position:absolute;display:flex;align-items:center;gap:12px;white-space:nowrap}
.cu2-ok{opacity:0}
.cu2-ann{position:absolute;left:0;top:-52px;font-size:22px;color:var(--acc);letter-spacing:.08em}
.cu2-cur{position:absolute;left:0;top:0;width:74px;height:74px;z-index:4}
.cu2-cur svg{filter:drop-shadow(0 8px 14px rgba(0,0,0,.28))}
.cu2-cann{position:absolute;left:70px;top:58px;font-size:20px;color:var(--acc);white-space:nowrap}
.cu2-trail{position:absolute;left:0;top:405px;height:4px;width:0;border-radius:2px;background:linear-gradient(90deg,rgba(var(--acc-rgb),0),rgba(var(--acc-rgb),.55));z-index:3}
.cu2-trail.plano{background:repeating-linear-gradient(90deg,var(--acc) 0 14px,transparent 14px 26px);opacity:.7}
.cu2-rip{position:absolute;left:540px;top:395px;width:120px;height:120px;margin:-60px 0 0 -60px;border-radius:50%;border:6px solid var(--acc);opacity:0;z-index:5}
.cu2-sps{position:absolute;left:540px;top:395px;width:0;height:0;z-index:5}
.cu2-sp{position:absolute;left:-4px;top:-4px;width:8px;height:44px;border-radius:4px;background:var(--acc);transform-origin:4px 4px;opacity:0}
.cu2-sp::after{content:""}
.cu2-cnt{position:absolute;left:0;right:0;top:640px;text-align:center}
.cu2-lab{font-size:24px;letter-spacing:.32em;color:var(--text-muted)}
.cu2-num{margin-top:10px;font-size:150px;font-weight:500;letter-spacing:-.02em;line-height:1;color:var(--text)}
/* whatsapp en la escena celular */
.ph.wa{background:#EFEAE2;border-color:#1B1B1F}
.ph.wa .ph-top{margin-top:0;padding:96px 30px 24px;background:#008069;color:#fff;border-bottom:none}
.ph.wa .ph-av{background:#DFE5E7}.ph.wa .ph-s{color:rgba(255,255,255,.85)}
.ph.wa .ph-body{padding:26px 22px}
.ph.wa .ph-m{font-size:26px;line-height:1.36;color:#111B21;box-shadow:0 2px 2px rgba(0,0,0,.08);position:relative;padding-bottom:40px}
.ph.wa .ph-m.ia{background:#fff;max-width:92%}.ph.wa .ph-m.me{background:#D9FDD3;color:#111B21;max-width:92%}
.ph.wa .ph-m b{font-weight:700}
.ph-h{position:absolute;right:18px;bottom:10px;font-size:18px;color:#667781}
.ph.wa .ph-typing{background:#fff}
/* ===== v2.6: temas alarma, poster y cine ===== */
.tema-alarma{--shadow:0 30px 80px -30px rgba(0,0,0,.9);--warn:#FF8A3D}
#al-red{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 16%,rgba(255,45,45,.22),transparent 58%)}
#scanlines{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.045) 0 2px,transparent 2px 7px)}
#al-stripe{position:absolute;left:-200px;right:-200px;top:1588px;height:46px;opacity:.26;background:repeating-linear-gradient(-45deg,rgba(var(--acc-rgb),.95) 0 34px,transparent 34px 68px)}
.tema-alarma .cap{text-transform:uppercase;font-size:62px;letter-spacing:.01em}
.tema-alarma .eyebrow{letter-spacing:.3em}
.tema-alarma .hdr .d{color:var(--acc)}
.tema-alarma .glass{border-radius:4px}
.tema-poster{--shadow:16px 16px 0 rgba(0,0,0,.35);--warn:#F5FF4A}
#dots{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.17) 2.2px,transparent 2.9px);background-size:30px 30px}
#ring{position:absolute;left:-280px;top:1150px;width:920px;height:920px;border-radius:50%;border:28px solid rgba(255,255,255,.10)}
#ring2{position:absolute;left:640px;top:-360px;width:820px;height:820px;border-radius:50%;background:rgba(0,0,0,.16)}
.tema-poster .cap{font-size:76px;letter-spacing:-.03em;text-shadow:none;line-height:1.08}
.tema-poster .glass{border:3px solid rgba(255,255,255,.92)}
.tema-poster .hdr{opacity:1}.tema-poster .hdr .h,.tema-poster .hdr .d{color:#fff}
.tema-poster #grain{opacity:.08}
.tema-cine{--shadow:0 40px 90px -30px rgba(0,0,0,.95);--warn:#FFB020}
#lb-t,#lb-b{position:absolute;left:0;right:0;height:118px;background:#000}
#lb-t{top:0;border-bottom:1px solid rgba(255,255,255,.08)}#lb-b{bottom:0;border-top:1px solid rgba(255,255,255,.08)}
#cine-light{position:absolute;left:-300px;top:200px;width:1500px;height:1500px;border-radius:50%;background:radial-gradient(circle,rgba(var(--acc-rgb),.14),transparent 60%)}
.tema-cine #grain{opacity:.14}
.tema-cine .cap{letter-spacing:-.01em;text-shadow:0 6px 30px rgba(0,0,0,.9)}
.tema-cine .eyebrow{letter-spacing:.28em}
/* glitch */
.gl-box{position:absolute;left:50px;right:30px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;font-weight:700;line-height:1;letter-spacing:-.03em;text-transform:uppercase}
.gl-ln{white-space:nowrap;margin:.03em 0}
.gl-w{position:relative;display:inline-block;opacity:0;margin-right:.24em}
.gl-l{position:absolute;left:0;top:0;opacity:0;pointer-events:none}
.gl-l.r{color:#FF2E2E;mix-blend-mode:screen}.gl-l.b{color:#2EB8FF;mix-blend-mode:screen}
.tema-claro .gl-l,.tema-estudio .gl-l{mix-blend-mode:multiply}
.gl-m{position:relative;display:inline-block}
.gl-w.kw .gl-m{color:var(--acc)}
.gl-bar{position:absolute;left:-.04em;right:-.04em;bottom:-.06em;height:.14em;background:var(--acc);transform:scaleX(0);transform-origin:0 50%}
.gl-tear{position:absolute;left:-100px;right:-100px;height:110px;top:0;background:linear-gradient(to bottom,transparent,rgba(var(--acc-rgb),.2),transparent);opacity:0}
.gl-tag{position:absolute;left:60px;top:30px;font-family:var(--mono);font-size:26px;letter-spacing:.3em;color:var(--acc);opacity:0}
/* bandeja */
.bj-win{position:absolute;left:60px;right:60px;top:50px;overflow:hidden}
.bj-top{display:flex;align-items:center;gap:18px;padding:26px 34px;border-bottom:1px solid var(--line)}
.bj-top .mono{font-size:26px;color:var(--text-muted);letter-spacing:.08em}
.bj-row{position:relative;display:flex;align-items:center;gap:24px;padding:26px 34px;border-bottom:1px solid var(--line);opacity:0;overflow:hidden}
.bj-av{width:72px;height:72px;border-radius:50%;background:var(--surface3);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:32px;flex:none;color:var(--text-soft)}
.bj-txt{flex:1;min-width:0}
.bj-de{font-weight:700;font-size:33px;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bj-as{font-size:31px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:4px}
.bj-pv{font-size:26px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:4px}
.bj-h{font-size:24px;color:var(--text-muted);flex:none;align-self:flex-start;margin-top:6px}
.bj-row.mk .bj-av{background:var(--acc);color:var(--on-acc)}
.bj-scan{position:absolute;left:0;right:0;top:-12px;height:12px;background:linear-gradient(90deg,transparent,var(--acc),transparent);box-shadow:0 0 34px var(--acc);opacity:0}
.bj-stamp{position:absolute;right:70px;top:30px;padding:12px 26px;border:5px solid var(--acc);color:var(--acc);font-family:var(--mono);font-weight:700;font-size:34px;letter-spacing:.2em;opacity:0;background:rgba(var(--bg-rgb),.75);white-space:nowrap}
/* carta */
.ct-win{position:absolute;left:60px;right:60px;top:30px;overflow:hidden;opacity:0}
.ct-head{padding:28px 36px 18px;border-bottom:1px solid var(--line)}
.ct-row{display:flex;gap:18px;font-size:30px;padding:8px 0;color:var(--text-soft);align-items:baseline}
.ct-row .mono{color:var(--text-muted);width:140px;flex:none;font-size:24px;letter-spacing:.12em;text-transform:uppercase}
.ct-row b{font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ct-body{padding:30px 36px 26px;line-height:1.42;min-height:360px;word-wrap:break-word;white-space:pre-wrap}
.ct-body .ch{opacity:0}
.ct-red{position:relative;display:inline-block;white-space:nowrap}
.ct-bar{position:absolute;left:-.06em;right:-.06em;top:.04em;bottom:-.02em;background:var(--acc);transform:scaleX(0);transform-origin:0 50%;border-radius:4px;z-index:2}
.tema-claro .ct-bar,.tema-estudio .ct-bar,.tema-poster .ct-bar,.tema-claro .cs-bar,.tema-estudio .cs-bar,.tema-poster .cs-bar{background:#000}
.ct-firma{margin-top:22px;font-size:26px;color:var(--text-muted)}
.ct-foot{display:flex;align-items:center;gap:24px;padding:22px 36px 30px;border-top:1px solid var(--line)}
.ct-send{padding:16px 36px;border-radius:12px;background:var(--acc);color:var(--on-acc);font-weight:700;font-size:32px}
.ct-st{font-family:var(--mono);font-size:26px;color:var(--text-muted);letter-spacing:.08em;opacity:0;display:flex;align-items:center;gap:12px}
.ct-who{position:absolute;right:36px;top:28px;font-family:var(--mono);font-size:22px;color:var(--acc);letter-spacing:.2em;text-transform:uppercase}
/* ranking */
.rk-wrap{position:absolute;left:60px;right:60px;top:30px;padding:34px 40px 30px}
.rk-wrap .eyebrow{margin-bottom:14px;opacity:0}
.rk-row{display:flex;align-items:center;gap:22px;padding:16px 0;opacity:0}
.rk-logo{width:76px;height:76px;flex:none;display:flex;align-items:center;justify-content:center}
.rk-ini{width:76px;height:76px;border-radius:20px;background:var(--surface3);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:34px}
.rk-txt{width:250px;flex:none;font-weight:700;font-size:30px;letter-spacing:-.01em;line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rk-track{flex:1;height:34px;border-radius:17px;background:var(--surface3);overflow:hidden;position:relative}
.rk-fill{position:absolute;left:0;top:0;bottom:0;width:100%;border-radius:17px;background:var(--text-muted);transform:scaleX(0);transform-origin:0 50%}
.rk-row.mk .rk-fill{background:var(--acc);box-shadow:0 0 30px rgba(var(--acc-rgb),.6)}
.rk-v{width:140px;flex:none;text-align:right;font-family:var(--mono);font-weight:700;font-size:38px}
.rk-row.mk .rk-v{color:var(--acc)}
.rk-note{margin-top:22px;font-family:var(--mono);font-size:23px;color:var(--text-muted);letter-spacing:.08em;opacity:0;line-height:1.4}
/* triturar */
.tr-cv{position:absolute;left:0;top:0;width:1080px;height:1010px}
.tr-doc{position:absolute;left:250px;top:40px;width:580px;padding:32px 36px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow);transform-origin:50% 100%}
.tr-name{font-family:var(--mono);font-size:24px;color:var(--acc);letter-spacing:.1em;margin-bottom:18px;display:flex;gap:12px;align-items:center}
.tr-ln{font-size:28px;line-height:1.5;color:var(--text-soft);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:0}
.tr-core{position:absolute;left:240px;top:560px;width:600px;height:440px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end}
.tr-ring{position:absolute;left:150px;top:0;width:300px;height:300px;border-radius:50%;border:6px solid rgba(var(--acc-rgb),.7);box-shadow:0 0 60px rgba(var(--acc-rgb),.35),inset 0 0 80px rgba(var(--acc-rgb),.25)}
.tr-ring2{position:absolute;left:190px;top:40px;width:220px;height:220px;border-radius:50%;background:radial-gradient(circle,rgba(var(--acc-rgb),.9),rgba(var(--acc-rgb),.15) 60%,transparent 70%);opacity:.6}
.tr-lab{position:relative;font-family:var(--mono);font-size:26px;letter-spacing:.22em;text-transform:uppercase;color:var(--text);text-align:center;margin-bottom:10px;opacity:0}
.tr-cnt{position:relative;font-weight:700;font-size:50px;color:var(--acc);letter-spacing:-.02em;margin-bottom:12px;opacity:0;white-space:nowrap}
/* interruptor */
.sw-card{position:absolute;left:70px;right:70px;top:50px;padding:40px 44px 46px}
.sw-ruta{font-family:var(--mono);font-size:23px;letter-spacing:.14em;color:var(--text-muted);text-transform:uppercase;margin-bottom:22px;opacity:0}
.sw-tit{font-weight:700;font-size:46px;letter-spacing:-.02em;line-height:1.08;opacity:0}
.sw-sub{font-size:28px;color:var(--text-soft);line-height:1.35;margin-top:14px;opacity:0;min-height:76px}
.sw-row{display:flex;align-items:center;justify-content:space-between;margin-top:40px;opacity:0}
.sw-state{font-family:var(--mono);font-weight:700;font-size:32px;letter-spacing:.2em;position:relative;height:44px;width:440px}
.sw-state span{position:absolute;left:0;top:0;white-space:nowrap}
.sw-state .on{color:var(--acc)}.sw-state .off{color:var(--text-muted);opacity:0}
.sw-track{position:relative;width:360px;height:190px;border-radius:95px;background:var(--acc);flex:none;box-shadow:inset 0 6px 20px rgba(0,0,0,.25)}
.sw-track.off{background:var(--text-muted)}
.sw-thumb{position:absolute;left:14px;top:14px;width:162px;height:162px;border-radius:50%;background:#fff;box-shadow:0 10px 30px rgba(0,0,0,.4)}
.sw-finger{position:absolute;width:120px;height:120px;border-radius:50%;background:rgba(255,255,255,.3);border:4px solid rgba(255,255,255,.95);left:810px;top:372px;opacity:0}
.sw-ok{display:flex;align-items:center;gap:16px;margin-top:40px;font-family:var(--mono);font-size:28px;letter-spacing:.1em;color:var(--acc);opacity:0}
/* censura */
.cs-sheet{position:absolute;left:70px;right:70px;top:50px;padding:36px 44px 30px}
.cs-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;opacity:0}
.cs-n{font-size:24px;color:var(--text-muted);letter-spacing:.08em}
.cs-ln{font-size:35px;line-height:1.45;padding:14px 0;border-bottom:1px solid var(--line);opacity:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cs-red{position:relative;display:inline-block;padding:0 .12em}
.cs-bar{position:absolute;left:0;right:0;top:.08em;bottom:0;background:var(--acc);transform:scaleX(0);transform-origin:0 50%;border-radius:4px}
.cs-stamp{position:absolute;left:0;right:0;top:430px;text-align:center;opacity:0}
.cs-stamp span{display:inline-block;padding:16px 36px;border:6px solid var(--acc);color:var(--acc);font-family:var(--mono);font-weight:700;font-size:44px;letter-spacing:.2em;background:rgba(var(--bg-rgb),.82);white-space:nowrap}
/* visor */
.vs-frame{position:absolute;left:90px;right:90px;top:30px;height:950px;border-radius:18px;overflow:hidden;background:#0B0B0E;box-shadow:var(--shadow)}
.vs-img{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 38%,#2A2D3A 0%,#15161D 55%,#0B0B0E 100%)}
.vs-sil{position:absolute;left:50%;top:150px;width:360px;height:440px;margin-left:-180px;border-radius:180px 180px 150px 150px;background:linear-gradient(180deg,#3A3E4E,#20232E)}
.vs-sh{position:absolute;left:50%;top:560px;width:720px;height:420px;margin-left:-360px;border-radius:360px 360px 0 0;background:linear-gradient(180deg,#2B2E3B,#15161D)}
.vs-mesh{position:absolute;left:0;top:0;width:100%;height:100%;opacity:0}
.vs-mesh line{stroke:rgba(var(--acc-rgb),.55);stroke-width:1.5}.vs-mesh circle{fill:var(--acc)}
.vs-corner{position:absolute;width:70px;height:70px;border:5px solid rgba(255,255,255,.9)}
.vs-corner.tl{left:28px;top:28px;border-right:0;border-bottom:0}.vs-corner.tr{right:28px;top:28px;border-left:0;border-bottom:0}
.vs-corner.bl{left:28px;bottom:28px;border-right:0;border-top:0}.vs-corner.br{right:28px;bottom:28px;border-left:0;border-top:0}
.vs-rec{position:absolute;left:120px;top:44px;display:flex;align-items:center;gap:12px;font-family:var(--mono);font-size:26px;letter-spacing:.2em;color:#fff}
.vs-rec i{width:22px;height:22px;border-radius:50%;background:#FF3B3B}
.vs-tc{position:absolute;right:120px;top:44px;font-family:var(--mono);font-size:26px;letter-spacing:.12em;color:rgba(255,255,255,.85)}
.vs-scan{position:absolute;left:0;right:0;top:0;height:120px;background:linear-gradient(to bottom,transparent,rgba(var(--acc-rgb),.22),rgba(var(--acc-rgb),.55));opacity:.9}
.vs-box{position:absolute;width:110px;height:110px;border:4px solid var(--acc);border-radius:10px;opacity:0;margin:-55px 0 0 -55px;box-shadow:0 0 30px rgba(var(--acc-rgb),.6)}
.vs-tag{position:absolute;padding:12px 22px;border-radius:12px;background:rgba(10,10,14,.86);border:2px solid var(--acc);font-family:var(--mono);font-size:26px;letter-spacing:.06em;color:#fff;opacity:0;white-space:nowrap;display:flex;gap:12px;align-items:center}
.vs-tag i{width:14px;height:14px;border-radius:50%;background:var(--acc)}
.vs-tag.ok{border-color:#22C55E}.vs-tag.ok i{background:#22C55E}
.vs-stamp{position:absolute;left:0;right:0;top:400px;text-align:center;opacity:0}
.vs-stamp span{display:inline-block;padding:18px 40px;border:7px solid #FF3B3B;color:#FF3B3B;font-weight:700;font-size:64px;letter-spacing:.14em;text-transform:uppercase;background:rgba(0,0,0,.55);border-radius:10px}
/* onda */
.on-card{position:absolute;left:60px;right:60px;top:70px;padding:40px 44px 44px}
.on-h{display:flex;justify-content:space-between;align-items:center}
.on-d{font-size:24px;color:var(--text-muted);letter-spacing:.1em}
.on-wave{position:relative;height:300px;margin-top:40px;display:flex;align-items:center;gap:6px}
.on-b{flex:1;height:100%;border-radius:4px;background:var(--text-muted);transform-origin:50% 50%}
.on-b.hi{background:var(--acc)}
.on-ph{position:absolute;left:0;top:-20px;bottom:-20px;width:4px;background:#fff;box-shadow:0 0 20px #fff}
.tema-poster .on-ph{background:var(--acc);box-shadow:0 0 20px var(--acc)}
.on-chips{display:flex;flex-wrap:wrap;gap:16px;margin-top:40px}
.on-chip{display:flex;align-items:center;gap:12px;padding:16px 26px;border-radius:14px;border:2px solid var(--line);font-family:var(--mono);font-size:25px;letter-spacing:.04em;opacity:0;background:var(--surface2)}
.on-chip i{width:14px;height:14px;border-radius:50%;background:var(--acc)}
.on-chip.ok{border-color:#22C55E}.on-chip.ok i{background:#22C55E}
.on-chip.no{border-color:var(--acc)}
.on-stamp{position:absolute;left:0;right:0;top:300px;text-align:center;opacity:0}
.on-stamp span{display:inline-block;padding:14px 34px;border:6px solid var(--acc);color:var(--acc);font-weight:700;font-size:54px;letter-spacing:.14em;text-transform:uppercase;background:rgba(var(--bg-rgb),.82);border-radius:10px}

/* ===== v2.7: tema galeria ===== */
.tema-galeria{--shadow:0 26px 60px -30px rgba(40,30,20,.38);--warn:#B8860B}
#paper{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 30%,rgba(255,255,255,.55),transparent 60%)}
#hair-t,#hair-b{position:absolute;left:70px;right:70px;height:2px;background:rgba(22,20,18,.14)}
#hair-t{top:214px}#hair-b{top:1500px}
.tema-galeria .cap{font-weight:600;letter-spacing:-.01em;text-shadow:none;font-size:66px;line-height:1.14}
.tema-galeria .eyebrow{letter-spacing:.3em}
.tema-galeria .hdr .d{color:var(--acc)}
.tema-galeria #grain{opacity:.1;mix-blend-mode:multiply}
.tema-galeria .kb{background:rgba(var(--acc-rgb),.10)}
/* boceto */
.bc-wrap{position:absolute;left:0;top:0;width:1080px;height:1010px}
.bc-ph{position:absolute;left:300px;top:40px;width:480px;height:930px;border:5px solid var(--text);border-radius:56px;background:rgba(var(--acc-rgb),.04);opacity:0}
.bc-notch{position:absolute;left:150px;top:18px;width:170px;height:30px;border-radius:15px;background:var(--text);opacity:.85}
.bc-el{position:absolute;left:40px;right:40px;border:3px solid var(--text);border-radius:12px;opacity:0}
.bc-bar{top:90px;height:70px;display:flex;align-items:center;gap:14px;padding:0 20px}
.bc-bar b{display:block;height:14px;width:120px;border-radius:7px;background:var(--text)}.bc-bar b.s{width:60px;margin-left:auto;opacity:.5}
.bc-h1{top:200px;height:44px;border:0;border-radius:8px;background:var(--text)}
.bc-h2{top:258px;height:44px;left:40px;right:140px;border:0;border-radius:8px;background:var(--text);opacity:0}
.bc-btn{top:338px;height:84px;border-color:var(--acc);background:var(--acc);display:flex;align-items:center;justify-content:center;color:var(--on-acc);font-size:30px;letter-spacing:.14em;text-transform:uppercase}
.bc-img{top:460px;height:260px;display:flex;align-items:center;justify-content:center;color:var(--acc)}
.bc-row{top:760px;height:40px;border:0;border-radius:8px;background:var(--text);opacity:0}
.bc-row.w{top:820px;right:170px}
.bc-tag{position:absolute;left:720px;top:120px;padding:18px 34px;border-radius:18px;background:var(--acc);color:var(--on-acc);font-weight:700;font-size:64px;letter-spacing:-.02em;box-shadow:0 20px 50px rgba(0,0,0,.35);opacity:0}
.bc-tag i{position:absolute;left:-22px;top:50%;margin-top:-14px;width:0;height:0;border-top:14px solid transparent;border-bottom:14px solid transparent;border-right:22px solid var(--acc)}
/* retrato */
.rt-wrap{position:absolute;left:40px;right:40px;top:0;bottom:0;border-radius:var(--radius);overflow:hidden;background:var(--surface2);box-shadow:var(--shadow)}
.rt-img{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;transform-origin:50% 40%}
.rt-shade{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0) 45%,rgba(0,0,0,.72) 100%)}
.rt-panel{position:absolute;left:40px;right:40px;bottom:44px;display:flex;flex-direction:column;gap:26px}
.rt-row{display:flex;align-items:center;gap:22px;color:#fff}
.rt-l{width:300px;flex:none;font-size:24px;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.85)}
.rt-track{flex:1;height:14px;border-radius:7px;background:rgba(255,255,255,.22);overflow:hidden}
.rt-fill{height:100%;width:100%;background:#fff;transform:scaleX(0);transform-origin:0 50%;border-radius:7px}
.rt-v{width:110px;text-align:right;font-weight:700;font-size:40px}
.rt-cred{position:absolute;right:28px;top:24px;font-size:20px;color:rgba(255,255,255,.7);letter-spacing:.06em}
/* curva */
.cv-wrap{position:absolute;left:40px;right:40px;top:40px;height:900px}
.cv-svg{position:absolute;left:0;top:0;width:1000px;height:760px}
.cv-ax{stroke:var(--line);stroke-width:3}
.cv-path{fill:none;stroke:var(--text);stroke-width:7;stroke-linecap:round;stroke-dasharray:1000;stroke-dashoffset:1000}
.cv-path2{fill:none;stroke:var(--acc);stroke-width:5;stroke-linecap:round;stroke-dasharray:14 16;opacity:0}
.cv-area{fill:rgba(var(--acc-rgb),.16)}
.cv-dot{fill:var(--acc);stroke:var(--bg);stroke-width:4}
.cv-x{position:absolute;left:0;right:0;top:716px;text-align:center;font-size:24px;letter-spacing:.2em;text-transform:uppercase;color:var(--text-muted)}
.cv-y{position:absolute;left:-250px;top:380px;width:600px;text-align:center;transform:rotate(-90deg);font-size:24px;letter-spacing:.2em;text-transform:uppercase;color:var(--text-muted)}
.cv-lab{position:absolute;display:flex;align-items:center;gap:12px;font-size:27px;font-weight:600;white-space:nowrap;opacity:0;transform:translate(-50%,-50%)}
.cv-lab i{width:14px;height:14px;border-radius:50%;background:var(--text)}
.cv-lab span{padding:6px 14px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow)}
.cv-valle{position:absolute;left:0;right:0;top:770px;text-align:center;opacity:0}
.cv-valle span{display:inline-block;padding:12px 30px;border:2px solid var(--acc);color:var(--acc);font-family:var(--mono);font-size:30px;letter-spacing:.2em;text-transform:uppercase;border-radius:var(--radius)}
.cv-mov{position:absolute;right:0;top:40px;font-size:24px;letter-spacing:.12em;color:var(--acc);opacity:0}
/* espectro */
.sp-strip{position:absolute;left:40px;right:40px;top:30px;display:flex;gap:24px}
.sp-cell{flex:1;display:flex;flex-direction:column;gap:16px;align-items:center}
.sp-ph{width:100%;height:440px;border-radius:var(--radius);overflow:hidden;background:var(--surface2);box-shadow:var(--shadow)}
.sp-ph img{width:100%;height:100%;object-fit:cover}
.sp-cap{font-size:28px;font-weight:600;text-align:center;line-height:1.15}
.sp-rail{position:absolute;left:60px;right:60px;top:580px;height:6px;border-radius:3px;background:var(--line)}
.sp-knob{position:absolute;left:0;top:-19px;width:44px;height:44px;margin-left:-22px;border-radius:50%;background:var(--acc);box-shadow:0 10px 30px rgba(0,0,0,.35);border:4px solid var(--bg)}
.sp-meter{position:absolute;left:40px;right:40px;top:650px;padding:30px 40px;display:flex;align-items:center;gap:30px}
.sp-num{font-weight:700;font-size:92px;letter-spacing:-.04em;width:260px;text-align:right;line-height:1}
.sp-track{flex:1;height:22px;border-radius:11px;background:var(--surface3);overflow:hidden}
.sp-fill{height:100%;width:100%;background:var(--text);transform:scaleX(0);transform-origin:0 50%;border-radius:11px}
/* diff */
.df-cols{position:absolute;left:40px;right:40px;top:60px;display:flex;gap:22px;align-items:flex-start}
.df-col{flex:1;padding:30px 30px 20px;min-height:560px}
.df-col .eyebrow{margin-bottom:18px}
.df-col.b .eyebrow{color:var(--acc)}
.df-ln{font-size:30px;line-height:1.45;padding:14px 0;border-top:1px solid var(--line);opacity:0}
.df-chg{position:relative;display:inline;font-weight:700;color:var(--acc)}
.df-bar{position:absolute;left:-.1em;right:-.1em;bottom:-.02em;height:.22em;background:rgba(var(--acc-rgb),.22);transform:scaleX(0);transform-origin:0 50%;z-index:-1}
/* cerebro */
.cb-row{position:absolute;left:40px;right:40px;top:40px;display:flex;gap:30px;justify-content:center}
.cb-head{flex:1;max-width:485px;display:flex;flex-direction:column;align-items:center;gap:14px}
.cb-head svg{width:100%;height:auto}
.cb-sil{fill:var(--surface2);stroke:var(--line);stroke-width:3}
.cb-e{stroke:var(--text-muted);stroke-width:2.5;opacity:.18;stroke-dasharray:100;stroke-dashoffset:100}
.cb-n{fill:var(--text-muted);opacity:.5}
.cb-t{font-size:30px;font-weight:600;letter-spacing:-.01em}
.cb-num{position:absolute;left:0;right:0;top:600px;text-align:center;font-weight:700;font-size:190px;letter-spacing:-.05em;line-height:1}
.cb-suf{color:var(--acc)}
.cb-l{position:absolute;left:90px;right:90px;top:810px;text-align:center;font-size:40px;line-height:1.2;color:var(--text-soft);opacity:0}
.cb-l.solo{top:640px;font-size:46px}
/* balanza */
.bz-wrap{position:absolute;left:40px;right:40px;top:0;bottom:0}
.bz-beam{position:absolute;left:90px;right:90px;top:360px;height:0;transform-origin:50% 50%}
.bz-bar{position:absolute;left:0;right:0;top:-8px;height:16px;border-radius:8px;background:var(--text)}
.bz-pan{position:absolute;top:0;width:360px;display:flex;flex-direction:column;align-items:center}
.bz-pan.l{left:-40px}.bz-pan.r{right:-40px}
.bz-chain{width:3px;height:120px;background:var(--text-muted)}
.bz-plate{width:100%;padding:28px 24px;text-align:center;font-size:30px;font-weight:600;line-height:1.2;display:flex;flex-direction:column;align-items:center;gap:10px}
.bz-arrow{font-size:72px;line-height:1;color:var(--acc);opacity:0}
.bz-pivot{position:absolute;left:50%;top:360px;width:0;height:0;margin-left:-60px;border-left:60px solid transparent;border-right:60px solid transparent;border-bottom:150px solid var(--surface3)}
.bz-base{position:absolute;left:50%;top:508px;width:460px;margin-left:-230px;height:16px;border-radius:8px;background:var(--text-soft)}
.bz-nota{position:absolute;left:0;right:0;top:720px;text-align:center;font-size:24px;letter-spacing:.12em;color:var(--text-muted);opacity:0;line-height:1.5}
/* firma */
.fm-doc{position:absolute;left:90px;right:90px;top:40px;padding:40px 48px 44px}
.fm-top{margin-bottom:20px}
.fm-ln{font-size:34px;line-height:1.4;padding:10px 0;opacity:0}
.fm-sk{margin:22px 0 40px;display:flex;flex-direction:column;gap:14px}
.fm-sk i{display:block;height:16px;border-radius:8px;background:var(--surface3)}
.fm-sign{position:relative;padding-top:10px}
.fm-lab{font-size:22px;letter-spacing:.2em;text-transform:uppercase;color:var(--text-muted)}
.fm-svg{display:block;width:520px;height:140px;margin-top:6px}
.fm-svg path{fill:none;stroke:var(--acc);stroke-width:5;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1000;stroke-dashoffset:1000}
.fm-line{height:2px;background:var(--line);width:560px;margin-top:-10px}
.fm-name{margin-top:12px;font-size:30px;font-weight:600;opacity:0}
"""

JS = r"""
(function(){
const tl = gsap.timeline({paused:true});
const ACC = "__ACC__", D = __D__;
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
if ($("#hdr")){ tl.fromTo("#hdr",{opacity:0},{opacity:.85,duration:.4},0.05);
tl.fromTo("#hdr",{opacity:.85},{opacity:0,duration:.3,immediateRender:false},__ENDT__); }

// cámara: transiciones (una por cambio de escena, elegidas por semilla), deriva y salida de cada escena
const FULL = "inset(0% 0% 0% 0%)";
const TR = {
  zoom:  {in:[{opacity:0, scale:.86, filter:"blur(16px)"}, {opacity:1, scale:1, filter:"blur(0px)"}],
          out:[{opacity:1, scale:1, filter:"blur(0px)"}, {opacity:0, scale:1.08, filter:"blur(14px)"}]},
  rise:  {in:[{opacity:0, y:160, filter:"blur(10px)"}, {opacity:1, y:0, filter:"blur(0px)"}],
          out:[{opacity:1, y:0}, {opacity:0, y:-120}]},
  wipe:  {in:[{clipPath:"inset(0% 100% 0% 0%)"}, {clipPath:FULL}],
          out:[{clipPath:FULL}, {clipPath:"inset(0% 0% 0% 100%)"}]},
  slide: {in:[{x:1080, opacity:1}, {x:0, opacity:1}],
          out:[{x:0}, {x:-1080}]},
  iris:  {in:[{clipPath:"circle(0% at 50% 50%)"}, {clipPath:"circle(80% at 50% 50%)"}],
          out:[{opacity:1, scale:1}, {opacity:0, scale:.92}]},
  flip:  {in:[{opacity:0, rotationY:70, transformOrigin:"50% 50% -300px"}, {opacity:1, rotationY:0}],
          out:[{opacity:1, rotationY:0, transformOrigin:"50% 50% -300px"}, {opacity:0, rotationY:-70}]},
  push:  {in:[{y:1010, opacity:1}, {y:0, opacity:1}],
          out:[{y:0}, {y:-1010}]},
  swing: {in:[{opacity:0, rotationX:28, y:120, filter:"blur(10px)"}, {opacity:1, rotationX:0, y:0, filter:"blur(0px)"}],
          out:[{opacity:1, rotationX:0, y:0}, {opacity:0, rotationX:-22, y:-90}]},
  flash: {in:[{opacity:1, scale:1.12}, {opacity:1, scale:1}], out:[{opacity:1, scale:1}, {opacity:1, scale:1.06}], fx:"flash"},
  whip:  {in:[{x:420, opacity:0, filter:"blur(22px)"}, {x:0, opacity:1, filter:"blur(0px)"}],
          out:[{x:0, opacity:1, filter:"blur(0px)"}, {x:-420, opacity:0, filter:"blur(22px)"}]},
  corte: {in:[{opacity:0}, {opacity:1}], out:[{opacity:1}, {opacity:0}]},
  continuo: {in:[{opacity:1}, {opacity:1}], out:[{opacity:1}, {opacity:1}]},
};
const DRIFTS = [
  [{scale:1, y:0, x:0, rotation:0}, {scale:1.035, y:-22, x:14, rotation:.5}],
  [{scale:1, y:0, x:0, rotation:0}, {scale:1.035, y:-22, x:-14, rotation:-.5}],
  [{scale:1.03, y:10, x:-10}, {scale:1, y:-10, x:10}],
  [{scale:1, y:0, x:0}, {scale:1.04, y:14, x:0}],
  [{scale:1.03, y:-8, x:12, rotation:-.4}, {scale:1.03, y:8, x:-12, rotation:.4}],
];
const SEED = __SEED__;
function CAM(c){
  const cam = "#"+c.id+" .cam", dr = "#"+c.id+" .drift", Dd = c.t1 - c.t0;
  const tin = TR[c.tin] || TR.zoom, tout = TR[c.tout] || TR.zoom;
  const din = c.tin === "corte" ? .08 : (c.tin === "flash" || c.tin === "whip" ? .32 : (c.tin === "wipe" || c.tin === "slide" || c.tin === "push" ? .45 : .5));
  if (!c.first && tin.fx === "flash"){ F("#flash", {opacity:0}, {opacity:.85, duration:.05, ease:"none"}, c.t0-.02); F("#flash", {opacity:.85}, {opacity:0, duration:.28, ease:"power2.out"}, c.t0+.03); }
  const cin = c.tin === "continuo" && !c.first, cout = c.tout === "continuo" && !c.last;
  if (!c.first && !cin){ F(cam, tin.in[0], Object.assign({duration:din, ease:(c.tin === "slide" || c.tin === "push") ? "power3.out" : E}, tin.in[1]), c.t0); tl.set(cam, {filter:"none", clipPath:"none"}, c.t0+din+.02); }
  else if (c.first && !cout) F(cam, {scale:1.06}, {scale:1, duration:.8, ease:E}, 0);
  const d = DRIFTS[(c.k + SEED) % DRIFTS.length];
  if (!cin && !cout) F(dr, d[0], Object.assign({duration:Dd, ease:"none"}, d[1]), c.t0);
  if (!c.last && !cout){
    const dout = c.tout === "corte" ? .06 : (c.tout === "flash" || c.tout === "whip" ? .22 : .34);
    F(cam, tout.out[0], Object.assign({duration:dout, ease:(c.tout === "slide" || c.tout === "push") ? "power3.in" : "power2.in"}, tout.out[1]), c.t1-dout);
  }
}
// golpe de cámara cuando la voz dice una palabra clave (le da ritmo a la edición)
function PUNCH(c, times){ (times||[]).forEach(t => { if (t > c.t0+.75 && t < c.t1-.45) F("#"+c.id+" .stage", {scale:1}, {scale:1.035, duration:.09, yoyo:true, repeat:1, ease:"power2.out"}, t); }); }
// elementos que dependen de la voz: nunca dejar la escena vacía (lo primero aparece como muy tarde `max` s después de arrancar)
const early = (c, t, max) => Math.min(t, c.t0 + (max === undefined ? .55 : max));
function stagger(c, cues, gap, first){ const out = []; let prev = c.t0; cues.forEach((t, i) => { let v = i ? Math.max(t, prev + (gap||.22)) : early(c, t, first); out.push(v); prev = v; }); return out; }


// ---- v2.6
const TXTC = getComputedStyle(document.documentElement).getPropertyValue("--text").trim() || "#FFFFFF";
const MUTC = getComputedStyle(document.documentElement).getPropertyValue("--text-muted").trim() || "#8A97B0";
const ACCRGB = (h => { h = h.replace("#", ""); return [0,2,4].map(i => parseInt(h.slice(i, i+2), 16)).join(","); })(ACC);
if ($("#al-red")) tl.fromTo("#al-red", {opacity:.75}, {opacity:1, duration:.7, yoyo:true, repeat:Math.max(1, Math.floor(D/.7)), ease:"sine.inOut"}, 0);
if ($("#scanlines")) tl.fromTo("#scanlines", {y:0}, {y:14, duration:D, ease:"none"}, 0);
if ($("#ring")) tl.fromTo("#ring", {rotation:0, scale:1}, {rotation:40, scale:1.08, duration:D, ease:"sine.inOut"}, 0);
if ($("#ring2")) tl.fromTo("#ring2", {x:0, y:0}, {x:-90, y:120, duration:D, ease:"sine.inOut"}, 0);
if ($("#cine-light")) tl.fromTo("#cine-light", {x:0, y:0}, {x:260, y:-200, duration:D, ease:"sine.inOut"}, 0);
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
  F(id+"-sc", {rotationZ:-22, rotationX:48, transformPerspective:1800}, {rotationZ:-12, rotationX:42, transformPerspective:1800, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  const top = id+"-l"+(n-1);
  F(top, {boxShadow:"0 0 0 0 rgba(0,0,0,0)"}, {borderColor:ACC, boxShadow:"0 0 60px "+ACC+"66", duration:.4}, early(c, p.cue, 1.4));
},
flujo(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .3, .25);
  for (let i=0;i<p.n;i++){
    const t = cues[i];
    pop(id+"-i"+i, t-.05);
    F(id+"-p"+i, {strokeDashoffset:1000}, {strokeDashoffset:0, duration:.6, ease:"power2.inOut"}, t+.1);
    F(id+"-d"+i, {strokeDashoffset:60, opacity:1}, {strokeDashoffset:-1000, duration:.9, ease:"power1.in", repeat:1, repeatDelay:.15}, t+.2);
  }
  const out = Math.max(cues[cues.length-1]+.5, Math.min(p.out, c.t0 + (c.t1-c.t0)*.6));
  F(id+"-o", {opacity:0, y:60, scale:.94}, {opacity:1, y:0, scale:1, duration:.55, ease:E}, out-.1);
  for (let i=0;i<4;i++) pop(id+"-t"+i, out+.2+i*.12);
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
  const com = early(c, p.com, 1.2), chg = Math.max(p.chg, com+.8);
  F(id+"-com", {opacity:0, y:40, scale:.9}, {opacity:1, y:0, scale:1, duration:.45, ease:"back.out(1.6)"}, com-.05);
  F(id+"-sel", {opacity:0, scale:1.08}, {opacity:1, scale:1, duration:.3, ease:E}, chg-.25);
  F(id+"-old", {opacity:1, filter:"blur(0px)"}, {opacity:0, filter:"blur(8px)", duration:.3}, chg);
  F(id+"-new", {opacity:0, y:20}, {opacity:1, y:0, duration:.4, ease:E}, chg+.15);
  show(id+"-ok", chg+.35, .4, {y:16});
},
chips(c, p){
  // aparecen apagadas enseguida y se encienden cuando la voz las nombra
  const id = "#"+c.id;
  for (let i=0;i<p.n;i++){
    const k = id+"-k"+i, t = Math.max(p.cues[i], c.t0+.3+i*.14);
    F(k, {opacity:0, x:i%2?-80:80, scale:.9, rotation:i%2?-3:3}, {opacity:.42, x:0, scale:1, rotation:0, duration:.45, ease:"back.out(1.4)"}, c.t0+.25+i*.12);
    F(k, {opacity:.42, scale:1}, {opacity:1, scale:1.04, duration:.22, ease:"power2.out"}, t);
    F(k, {scale:1.04}, {scale:1, duration:.3, ease:"power2.out"}, t+.22);
    if ($(id+"-dl"+i)) F(id+"-dl"+i, {y:-14}, {y:6, duration:.35, yoyo:true, repeat:3, ease:"sine.inOut"}, t+.35);
  }
  if (p.bar !== undefined){
    const tb = early(c, p.bar, 1.6);
    show(id+"-bar", tb-.3, .4, {y:20});
    F(id+"-fill", {scaleX:0}, {scaleX:p.val, duration:.9, ease:"power2.out"}, tb);
    const o = {v:0};
    F(o, {v:0}, {v:p.val*100, duration:.9, ease:"power2.out", onUpdate:()=>{ $(id+"-pct").textContent = Math.round(o.v)+"%"; }}, tb);
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
    const t = Math.max(p.cues[i], c.t0+.35+i*.14);
    F(id+"-k"+i, {opacity:0, x:-90}, {opacity:.45, x:0, duration:.45, ease:E}, c.t0+.2+i*.12);
    F(id+"-k"+i, {opacity:.45}, {opacity:1, duration:.25}, t-.05);
    F(id+"-ck"+i, {strokeDashoffset:100}, {strokeDashoffset:0, duration:.35, ease:"power2.out"}, t+.1);
  }
},
reloj(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, cue = Math.max(c.t0+.9, Math.min(p.cue, c.t1-.9));
  F(id+"-m", {rotation:0}, {rotation:360*5, duration:Dd, ease:"power2.out"}, c.t0);
  F(id+"-h", {rotation:20}, {rotation:20+360*5/12, duration:Dd, ease:"power2.out"}, c.t0);
  F(id+"-arc", {"--arc":"0deg"}, {"--arc":"300deg", duration:Math.max(.4,cue-c.t0), ease:"power1.inOut"}, c.t0);
  F(id+"-arc", {"--arc":"300deg"}, {"--arc":"24deg", duration:.5, ease:"power3.out"}, cue);
  F(id+"-a", {"--st":0}, {"--st":1, duration:.35, ease:"power2.out"}, cue-.15);
  F(id+"-a", {opacity:1, y:0}, {opacity:0, y:-60, duration:.35, ease:"power2.in"}, cue+.15);
  F(id+"-b", {opacity:0, y:70, scale:.8}, {opacity:1, y:0, scale:1, duration:.5, ease:"back.out(1.6)"}, cue+.25);
},
alerta(c, p){
  const id = "#"+c.id;
  F(id+"-ic", {rotation:0}, {rotation:8, duration:.08, yoyo:true, repeat:5, ease:"sine.inOut"}, c.t0+.5);
  for (let i=0;i<p.n;i++) show(id+"-r"+i, c.t0+.35+i*.12, .35, {x:-40});
  if (p.mk >= 0){
    const r = id+"-r"+p.mk, cue = Math.max(c.t0+1.2, Math.min(p.cue, c.t1-.8));
    show(id+"-lens", cue-.5, .4, {scale:.6});
    F(id+"-lens", {x:0, y:0}, {x:-430, y:-40, duration:1.1, ease:"power2.inOut"}, cue-.3);
    F(r, {backgroundColor:"rgba(255,176,32,0)"}, {backgroundColor:"rgba(255,176,32,.16)", color:"#FFB020", duration:.3}, cue+.35);
    F(r, {scale:1}, {scale:1.04, duration:.15, yoyo:true, repeat:3}, cue+.4);
  }
},
numero(c, p){
  // cuenta desde que arranca la escena y aterriza en el valor justo cuando la voz lo dice
  const id = "#"+c.id, o = {v:p.desde}, land = Math.max(c.t0+1.0, Math.min(p.cue+.15, c.t1-.6));
  F(o, {v:p.desde}, {v:p.val, duration:land-c.t0-.1, ease:"power3.out", onUpdate:()=>{ $(id+"-n").textContent = fmt(o.v, p.dec, p.sep); }}, c.t0+.1);
  F(id+"-n", {scale:1}, {scale:1.06, duration:.18, yoyo:true, repeat:1, ease:"power2.inOut"}, land-.1);
  show(id+"-l", c.t0+.5, .5, {y:30});
},
particulas(c, p){
  const id = "#"+c.id, cv = $(id+"-cv"), ctx = cv.getContext("2d"), rnd = seeded(7+SEED), N = 700, pts = [];
  const bright = document.body.classList.contains("tema-claro") ? "#1A2238" : "#E6ECF7";
  for (let i=0;i<N;i++) pts.push([rnd()*1080, rnd()*1010, .6+rnd()*2.2, rnd()]);
  const o = {k:0, v:p.desde}, land = Math.max(c.t0+1.2, Math.min(p.cue+.15, c.t1-.6));
  F(o, {k:0}, {k:1, duration:Math.max(1,c.t1-c.t0-.2), ease:"power1.out", onUpdate:()=>{
    ctx.clearRect(0,0,1080,1010);
    for (const [x,y,r,a] of pts){ if (a > o.k) continue; ctx.globalAlpha = .35+.65*(1-a); ctx.fillStyle = a < .08 ? ACC : bright; ctx.beginPath(); ctx.arc(x, y, r*1.6, 0, 6.283); ctx.fill(); }
  }}, c.t0);
  F(o, {v:p.desde}, {v:p.val, duration:land-c.t0-.1, ease:"power3.out", onUpdate:()=>{ $(id+"-n").textContent = fmt(o.v, p.dec); }}, c.t0+.1);
},
navegador(c, p){
  const id = "#"+c.id, cue = Math.max(c.t0+1.3, Math.min(p.cue, c.t1-.5));
  for (let i=0;i<4;i++) pop(id+"-cd"+i, c.t0+.35+i*.12);
  F(id+"-cur", {x:0, y:0}, {x:-230, y:-560, duration:.9, ease:"power2.inOut"}, cue-.9);
  F(id+"-cur", {scale:1}, {scale:.8, duration:.1, yoyo:true, repeat:1}, cue);
  if (p.n > 1){
    tl.set(id+"-tb0", {className:"nv-tab"}, cue+.1); tl.set(id+"-tb1", {className:"nv-tab on"}, cue+.1);
  }
},
celular(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .9);
  F(id+"-ph", {rotationY:-18, rotationX:8}, {rotationY:10, rotationX:0, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  cues.forEach((t,i) => {
    if (!p.me[i] && t-.7 > c.t0+.1){ F(id+"-ty", {opacity:0}, {opacity:1, duration:.15}, t-.7); F(id+"-ty", {opacity:1}, {opacity:0, duration:.1}, t-.12); }
    show(id+"-m"+i, t-.1, .35, {y:30, scale:.9});
    if (p.au && p.au[i]) F(id+"-ap"+i, {clipPath:"inset(0 100% 0 0)"}, {clipPath:"inset(0 0% 0 0)", duration:Math.max(1.2, Math.min(3.2, c.t1-t-.4)), ease:"none"}, t+.25);
  });
},
llamada(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, n = Math.max(1, Math.floor((Dd-.2)/1.1));
  F(id+"-ph", {y:60, rotation:-3}, {y:0, rotation:2, duration:Dd, ease:"sine.inOut"}, c.t0);
  for (let k=0;k<3;k++) F(id+"-r"+k, {opacity:.8, scale:1}, {opacity:0, scale:1.9, duration:1.1, repeat:n-1, ease:"power1.out"}, c.t0+.1+k*.36);
  F(id+"-si", {y:0}, {y:-18, duration:.22, yoyo:true, repeat:Math.max(1, n*2-1), ease:"power2.out"}, c.t0+.3);
  if (p.stamp){ const t = Math.max(c.t0+1.0, Math.min(p.cue, c.t1-.9)); F(id+"-st", {opacity:0, scale:2.4, rotation:-25}, {opacity:1, scale:1, rotation:-10, duration:.3, ease:"power4.out"}, t);
    F("#"+c.id+" .stage", {x:0}, {x:10, duration:.05, yoyo:true, repeat:3, ease:"none"}, t+.25); }
},
grafico(c, p){
  const id = "#"+c.id;
  for (let i=0;i<p.n;i++){
    F(id+"-b"+i, {scaleY:0}, {scaleY:1, duration:.7, ease:"power3.out"}, c.t0+.35+i*.12);
    show(id+"-v"+i, c.t0+.75+i*.12, .3, {y:10});
  }
  F(id+" .gr-b.hi", {filter:"brightness(1)"}, {filter:"brightness(1.4)", duration:.3, yoyo:true, repeat:1}, Math.max(p.cue, c.t0+1.2));
},
comparacion(c, p){
  const id = "#"+c.id, a = early(c, p.cues[0], .5), d = Math.max(a+.9, Math.min(p.cues[1], c.t0+(c.t1-c.t0)*.55));
  show(id+"-an", a-.1, .5, {y:-50});
  pop(id+"-vs", (a+d)/2);
  show(id+"-de", d-.1, .5, {y:60});
},
terminal(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .45);
  F(id+"-win", {rotationX:10, rotationY:-8}, {rotationX:0, rotationY:4, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  cues.forEach((t, i) => {
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
  const last = cues.length ? cues[cues.length-1]+.5 : c.t0+.5;
  F(id+"-cur", {opacity:0}, {opacity:1, duration:.01, repeat:Math.max(1, Math.floor((c.t1-last)/.5)), yoyo:true, repeatDelay:.25}, last);
},
linea_tiempo(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .6);
  const fr = (i) => p.n > 1 ? (60 + i*(860/p.n) + 42)/860 : .1;
  F(id+"-fill", {scaleY:0}, {scaleY:fr(0), duration:.5, ease:E}, c.t0+.2);
  cues.forEach((t, i) => {
    if (i > 0) F(id+"-fill", {scaleY:fr(i-1)}, {scaleY:fr(i), duration:.5, ease:"power2.inOut"}, t-.35);
    F(id+"-h"+i, {opacity:0, x:60}, {opacity:1, x:0, duration:.45, ease:E}, t-.1);
    F(id+"-d"+i, {scale:.3}, {scale:1, duration:.4, ease:"back.out(2.4)"}, t-.1);
    if (i > 0) F(id+"-h"+(i-1), {opacity:1}, {opacity:.45, duration:.3}, t);
  });
},
marcas(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .35, .3);
  for (let i=0;i<p.n;i++){
    const t = cues[i];
    F(id+"-k"+i, {opacity:0, scale:.4, y:60, rotation:i%2?8:-8}, {opacity:1, scale:1, y:0, rotation:0, duration:.55, ease:"back.out(1.9)"}, t-.08);
    F(id+"-k"+i+" .mk-glow", {opacity:0, scale:.6}, {opacity:1, scale:1, duration:.7, ease:E}, t);
    F(id+"-k"+i+" .lg-badge", {rotation:0}, {rotation:i%2?-2:2, duration:Math.max(.5, c.t1-t), ease:"sine.inOut"}, t+.5);
    if (p.pills[i]) F(id+"-pl"+i, {opacity:0, y:20, scale:.8}, {opacity:1, y:0, scale:1, duration:.35, ease:"back.out(2)"}, t+.45);
  }
  if ($(id+"-mid")) F(id+"-mid", {opacity:0, scale:2.2}, {opacity:1, scale:1, duration:.35, ease:"power3.out"}, (cues[0]+(cues[1]||cues[0]))/2);
  if ($(id+"-tit")) show(id+"-tit", c.t0+.2, .4, {y:-20});
  F(id+"-burst", {opacity:.9, scale:1}, {opacity:0, scale:16, duration:.7, ease:"power2.out"}, cues[0]);
},
boceto(c, p){
  const id = "#"+c.id, cue = Math.max(c.t0+1.3, Math.min(p.cue, c.t1-.8));
  F(id+"-ph", {opacity:0, scale:.9, y:30}, {opacity:1, scale:1, y:0, duration:.5, ease:E}, c.t0+.05);
  for (let i=0;i<7;i++) F(id+"-e"+i, {opacity:0, clipPath:"inset(0 100% 0 0)"}, {opacity:i===2||i===5||i===6 ? .45 : 1, clipPath:"inset(0 0% 0 0)", duration:.32, ease:"power2.out"}, c.t0+.35+i*.14);
  F(id+"-ph", {y:0}, {y:-10, duration:1.4, yoyo:true, repeat:Math.max(1, Math.floor((c.t1-c.t0)/1.4)), ease:"sine.inOut"}, c.t0+.6);
  F(id+"-tag", {opacity:0, scale:.4, rotation:-16, x:-30}, {opacity:1, scale:1, rotation:0, x:0, duration:.4, ease:"back.out(2)"}, cue);
  F("#"+c.id+" .stage", {scale:1}, {scale:1.03, duration:.1, yoyo:true, repeat:1, ease:"power2.out"}, cue+.05);
},
retrato(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0;
  F(id+"-img", {scale:1}, {scale:1.09, duration:Dd, ease:"none"}, c.t0);
  const c1 = early(c, p.c1, .9), c2 = Math.max(c1+1.0, Math.min(p.c2, c.t1-.8));
  const o1 = {v:0}, o2 = {v:0};
  F(id+"-f1", {scaleX:0}, {scaleX:p.v1/100, duration:1.1, ease:"power2.out"}, c1);
  F(o1, {v:0}, {v:p.v1, duration:1.1, ease:"power2.out", onUpdate:()=>{ $(id+"-v1").textContent = Math.round(o1.v)+"%"; }}, c1);
  F(id+"-f2", {scaleX:0}, {scaleX:p.v2a/100, duration:.9, ease:"power2.out"}, c1+.35);
  F(o2, {v:0}, {v:p.v2a, duration:.9, ease:"power2.out", onUpdate:()=>{ $(id+"-v2").textContent = Math.round(o2.v)+"%"; }}, c1+.35);
  F(id+"-f2", {scaleX:p.v2a/100, backgroundColor:"#FFFFFF"}, {scaleX:p.v2/100, backgroundColor:ACC, duration:.5, ease:"power3.in"}, c2);
  F(o2, {v:p.v2a}, {v:p.v2, duration:.5, ease:"power3.in", onUpdate:()=>{ $(id+"-v2").textContent = Math.round(o2.v)+"%"; }}, c2);
  F(id+"-v2", {color:"#FFFFFF"}, {color:ACC, duration:.3}, c2+.3);
  F("#"+c.id+" .stage", {x:0}, {x:-6, duration:.05, yoyo:true, repeat:3, ease:"none"}, c2+.4);
},
curva(c, p){
  const id = "#"+c.id, path = $(id+"-path"), L = path.getTotalLength(), dot = $(id+"-dot");
  const draw = Math.min(2.4, (c.t1-c.t0)*.5), o = {k:0};
  const svg = $(id+"-svg"), sx = 1000/svg.getBoundingClientRect().width || 1;
  F(id+"-path", {strokeDashoffset:1000}, {strokeDashoffset:0, duration:draw, ease:"power1.inOut"}, c.t0+.2);
  F(o, {k:0}, {k:1, duration:draw, ease:"power1.inOut", onUpdate:()=>{ const q = path.getPointAtLength(o.k*L); dot.setAttribute("cx", q.x); dot.setAttribute("cy", q.y); }}, c.t0+.2);
  for (let i=0;i<p.n;i++){
    const q = path.getPointAtLength(p.pos[i]*L), el = $(id+"-lb"+i);
    el.style.left = (q.x*1.0)+"px"; el.style.top = (q.y - 54)+"px";
    const t = Math.max(c.t0+.2+draw*p.pos[i], Math.min(p.cues[i], c.t1-.4));
    F(el, {opacity:0, y:16}, {opacity:1, y:0, duration:.35, ease:E}, t);
  }
  const tv = Math.max(c.t0+draw+.3, Math.min(p.cue, c.t1-.9));
  F(id+"-diprect", {attr:{width:0}}, {attr:{width:220}, duration:.6, ease:"power2.out"}, tv);
  F(id+"-valle", {opacity:0, y:12}, {opacity:1, y:0, duration:.4, ease:E}, tv+.1);
  if (p.mov >= 0){ const tm = Math.max(tv+.6, Math.min(p.mov, c.t1-.7));
    F(id+"-path2", {opacity:0, strokeDashoffset:1000}, {opacity:1, strokeDashoffset:0, duration:.9, ease:"power1.inOut"}, tm);
    F(id+"-mov", {opacity:0, x:20}, {opacity:1, x:0, duration:.35}, tm+.3); }
},
espectro(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .9, .5), W = 960, xs = [];
  for (let i=0;i<p.n;i++) xs.push((W/p.n)*(i+.5));
  const o = {v:0};
  for (let i=0;i<p.n;i++){
    const t = cues[i];
    F(id+"-knob", {left:(i ? xs[i-1] : xs[0])+"px"}, {left:xs[i]+"px", duration:i ? .5 : .01, ease:"power2.inOut"}, i ? t : c.t0);
    F(id+"-c"+i, {scale:1, opacity:.55}, {scale:1.04, opacity:1, duration:.4, ease:E}, t);
    if (i) F(id+"-c"+(i-1), {scale:1.04, opacity:1}, {scale:1, opacity:.55, duration:.4}, t);
    const prev = i ? p.vals[i-1] : 0, low = p.vals[i] < 35;
    F(id+"-fill", {scaleX:prev/100}, {scaleX:p.vals[i]/100, duration:.6, ease:"power3.out"}, t+.2);
    F(o, {v:prev}, {v:p.vals[i], duration:.6, ease:"power3.out", onUpdate:()=>{ $(id+"-num").textContent = Math.round(o.v)+"%"; }}, t+.2);
    F(id+"-num", {color:TXTC}, {color:low ? ACC : TXTC, duration:.3}, t+.3);
    F(id+"-fill", {backgroundColor:TXTC}, {backgroundColor:low ? ACC : TXTC, duration:.3}, t+.3);
    if (low) F("#"+c.id+" .stage", {x:0}, {x:5, duration:.05, yoyo:true, repeat:3, ease:"none"}, t+.5);
  }
  tl.set(id+"-c0", {opacity:1, scale:1.04}, c.t0);
  for (let i=1;i<p.n;i++) tl.set(id+"-c"+i, {opacity:.55}, c.t0);
},
diff(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .5, .4);
  for (let i=0;i<p.n;i++){
    F(id+"-a"+i, {opacity:0, x:-20}, {opacity:1, x:0, duration:.3, ease:E}, cues[i]);
    F(id+"-b"+i, {opacity:0, x:20}, {opacity:1, x:0, duration:.3, ease:E}, cues[i]+.15);
    $$(id+"-b"+i+" .df-bar").forEach((bar, j) => F(bar, {scaleX:0}, {scaleX:1, duration:.3, ease:"power3.out"}, cues[i]+.5+j*.12));
  }
},
cerebro(c, p){
  const id = "#"+c.id, rnd = seeded(3+SEED);
  show(id+"-a", c.t0+.1, .4, {y:20}); show(id+"-b", c.t0+.25, .4, {y:20});
  const ta = c.t0+.5, tb = Math.max(ta+1.2, Math.min(p.cue, c.t1-1.2));
  for (let n=0;n<p.na;n++){ if (rnd() <= p.da) F(id+"-ae"+n, {strokeDashoffset:100, opacity:.18}, {strokeDashoffset:0, opacity:.95, stroke:ACC, duration:.5, ease:"power2.out"}, ta+n*.06); }
  for (let n=0;n<p.nb;n++){ if (rnd() <= p.db) F(id+"-be"+n, {strokeDashoffset:100, opacity:.18}, {strokeDashoffset:0, opacity:.95, stroke:ACC, duration:.5, ease:"power2.out"}, tb+n*.06); }
  F(id+"-a svg", {scale:1}, {scale:1.03, duration:.6, yoyo:true, repeat:1, ease:"sine.inOut"}, ta+.3);
  if (p.val !== null){ const o = {v:0}, land = Math.max(tb+.8, Math.min(p.cv, c.t1-.5));
    F(o, {v:0}, {v:p.val, duration:Math.max(.6, land-tb), ease:"power3.out", onUpdate:()=>{ $(id+"-n").textContent = fmt(o.v, 0, true); }}, tb);
  }
  if ($(id+"-l")) show(id+"-l", tb+.4, .4, {y:14});
},
balanza(c, p){
  const id = "#"+c.id, cue = Math.max(c.t0+1.0, Math.min(p.cue, c.t1-1.0));
  show(id+"-beam", c.t0+.1, .5, {y:-30});
  F(id+"-beam", {rotation:0}, {rotation:p.ang, duration:.9, ease:"power2.inOut"}, cue);
  F(id+"-pl", {rotation:0}, {rotation:-p.ang, duration:.9, ease:"power2.inOut", transformOrigin:"50% 0"}, cue);
  F(id+"-pr", {rotation:0}, {rotation:-p.ang, duration:.9, ease:"power2.inOut", transformOrigin:"50% 0"}, cue);
  F(id+"-beam", {rotation:p.ang}, {rotation:p.ang*.85, duration:.5, yoyo:true, repeat:1, ease:"sine.inOut"}, cue+.9);
  pop(id+"-ar1", cue+.5); pop(id+"-ar2", cue+.7);
  if ($(id+"-nota")) show(id+"-nota", cue+1.2, .4, {y:10});
},
firma(c, p){
  const id = "#"+c.id, cue = Math.max(c.t0+.9, Math.min(p.cue, c.t1-1.4));
  for (let i=0;i<p.n;i++) show(id+"-l"+i, c.t0+.2+i*.18, .35, {x:-16});
  F(id+"-sig", {strokeDashoffset:1000}, {strokeDashoffset:0, duration:1.3, ease:"power1.inOut"}, cue);
  show(id+"-name", cue+1.2, .4, {y:10});
},
glitch(c, p){
  const id = "#"+c.id;
  if ($(id+"-tag")) show(id+"-tag", c.t0+.1, .3, {x:-20});
  p.cues.forEach((t, i) => {
    const tt = Math.max(t-.05, c.t0+.06+i*.04), w = id+"-w"+i;
    F(w, {opacity:0, x:-30, skewX:-12}, {opacity:1, x:0, skewX:0, duration:.16, ease:"power4.out"}, tt);
    F(w+" .r", {x:0, y:0, opacity:.9}, {x:-16, y:-6, opacity:.9, duration:.05, yoyo:true, repeat:5, ease:"none"}, tt);
    F(w+" .b", {x:0, y:0, opacity:.9}, {x:16, y:6, opacity:.9, duration:.05, yoyo:true, repeat:5, ease:"none"}, tt);
    tl.set(w+" .r", {opacity:0}, tt+.34); tl.set(w+" .b", {opacity:0}, tt+.34);
    tl.set(w+" .gl-m", {clipPath:"inset(0 0 55% 0)", x:12}, tt+.02);
    tl.set(w+" .gl-m", {clipPath:"inset(45% 0 0 0)", x:-12}, tt+.08);
    tl.set(w+" .gl-m", {clipPath:"inset(20% 0 50% 0)", x:8}, tt+.14);
    tl.set(w+" .gl-m", {clipPath:"none", x:0}, tt+.2);
    if (p.kw[i]) F(id+"-b"+i, {scaleX:0}, {scaleX:1, duration:.25, ease:"power3.out"}, tt+.1);
    F(id+"-tear", {opacity:1, y:-120}, {opacity:1, y:1010, duration:.32, ease:"none"}, tt);
    tl.set(id+"-tear", {opacity:0}, tt+.33);
    F("#"+c.id+" .stage", {x:0}, {x:(i%2?10:-10), duration:.04, yoyo:true, repeat:1, ease:"none"}, tt);
  });
  F(id+" .gl-box", {opacity:1}, {opacity:.7, duration:.04, yoyo:true, repeat:1}, c.t0+(c.t1-c.t0)*.55);
},
bandeja(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .28, .3);
  for (let i=0;i<p.n;i++) F(id+"-r"+i, {opacity:0, y:-26}, {opacity:1, y:0, duration:.32, ease:E}, cues[i]);
  if (p.mk >= 0 && p.mk < p.n){
    const t = Math.max(cues[p.mk]+.45, Math.min(p.cue, c.t1-.9)), r = id+"-r"+p.mk;
    F(id+"-sc"+p.mk, {opacity:1, y:0}, {opacity:1, y:150, duration:.5, ease:"none"}, t); tl.set(id+"-sc"+p.mk, {opacity:0}, t+.5);
    F(r, {backgroundColor:"rgba("+ACCRGB+",0)"}, {backgroundColor:"rgba("+ACCRGB+",.14)", duration:.3}, t+.2);
    F(r+" .bj-as", {color:TXTC}, {color:ACC, duration:.2}, t+.3);
    if (p.sello) F(id+"-st", {opacity:0, scale:2.2, rotation:-20}, {opacity:1, scale:1, rotation:-8, duration:.3, ease:"power4.out"}, t+.55);
  }
},
carta(c, p){
  const id = "#"+c.id, chs = $$(id+" .ch"), n = chs.length;
  const ts = c.t0+.4, dur = Math.min(n*.03, (c.t1-c.t0)*.66), dt = dur/Math.max(1,n);
  show(id+"-win", c.t0+.05, .4, {y:30});
  chs.forEach((ch,i) => { const t = ts+i*dt; tl.set(ch, {opacity:1, boxShadow:"3px 0 0 0 "+ACC}, t); if (i<n-1) tl.set(ch, {boxShadow:"0 0 0 0 rgba(0,0,0,0)"}, t+dt); });
  p.reds.forEach((k, j) => { const t = ts+(k+1)*dt+.05; F(id+"-rb"+j, {scaleX:0}, {scaleX:1, duration:.22, ease:"power3.out"}, t);
    F("#"+c.id+" .stage", {x:0}, {x:6, duration:.04, yoyo:true, repeat:1}, t); });
  const te = ts+dur;
  F(id+"-send", {scale:1}, {scale:.86, duration:.12, yoyo:true, repeat:1, ease:"power2.inOut"}, te+.25);
  show(id+"-st", te+.5, .35, {x:-20});
},
ranking(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .3, .35);
  if ($(id+"-tit")) show(id+"-tit", c.t0+.1, .35, {y:-16});
  for (let i=0;i<p.n;i++){
    const o = {v:0}, t = cues[i], land = Math.min(t+1.0, c.t1-.3);
    F(id+"-r"+i, {opacity:0, x:-40}, {opacity:1, x:0, duration:.3, ease:E}, t);
    F(id+"-f"+i, {scaleX:0}, {scaleX:Math.max(.02, p.vals[i]/p.max), duration:Math.max(.3, land-t), ease:"power3.out"}, t+.1);
    F(o, {v:0}, {v:p.vals[i], duration:Math.max(.3, land-t), ease:"power3.out", onUpdate:()=>{ $(id+"-v"+i).textContent = fmt(o.v, p.dec, true)+p.suf; }}, t+.1);
  }
  if (p.mk >= 0 && p.mk < p.n) F(id+"-r"+p.mk+" .rk-v", {scale:1}, {scale:1.18, duration:.18, yoyo:true, repeat:1, transformOrigin:"100% 50%"}, Math.min(cues[p.mk]+1.05, c.t1-.3));
  if ($(id+"-note")) show(id+"-note", Math.min(cues[p.n-1]+.9, c.t1-.5), .35, {y:10});
},
triturar(c, p){
  const id = "#"+c.id, cv = $(id+"-cv"), ctx = cv.getContext("2d"), rnd = seeded(11+SEED);
  const cue = Math.max(c.t0+1.1, Math.min(p.cue, c.t1-1.7));
  for (let i=0;i<p.n;i++) show(id+"-l"+i, c.t0+.25+i*.14, .3, {x:-20});
  show(id+"-lab", c.t0+.6, .4, {y:12});
  F(id+"-doc", {y:0}, {y:-14, duration:1.1, yoyo:true, repeat:Math.max(1, Math.floor((cue-c.t0)/1.1)), ease:"sine.inOut"}, c.t0);
  F(id+"-doc", {y:0, scaleX:1, scaleY:1, opacity:1}, {y:470, scaleX:.12, scaleY:.06, opacity:0, duration:.75, ease:"power2.in"}, cue);
  F(id+"-ring", {scale:1}, {scale:1.18, duration:.35, yoyo:true, repeat:1, ease:"power2.out"}, cue+.7);
  F(id+"-ring2", {scale:1, opacity:.6}, {scale:1.6, opacity:1, duration:.9, ease:"power2.out"}, cue+.6);
  const N = 320, P = [];
  for (let i=0;i<N;i++) P.push({x:270+rnd()*540, y:60+rnd()*300, d:rnd()*.55, w:10+rnd()*34, s:rnd(), a:(rnd()-.5)*1.4});
  const o = {k:0};
  F(o, {k:0}, {k:1, duration:1.7, ease:"none", onUpdate:()=>{
    ctx.clearRect(0,0,1080,1010); const k = o.k;
    P.forEach(q => { const u = (k - q.d)/(1-q.d); if (u<=0 || u>=1) return; const e = u*u*(3-2*u);
      const cx = 540 + Math.sin(u*6.28*q.s)*q.a*120*(1-u), cy = q.y + (700 - q.y)*e, x = q.x + (cx - q.x)*e;
      ctx.globalAlpha = (1-u)*.9+.1; ctx.fillStyle = q.s>.5 ? ACC : TXTC; ctx.fillRect(x, cy, q.w*(1-u*.6), 6); });
    ctx.globalAlpha = 1;
  }}, cue+.1);
  if (p.total > 0){ const cnt = {v:0};
    F(cnt, {v:0}, {v:p.total, duration:1.6, ease:"power2.out", onUpdate:()=>{ $(id+"-cnt").textContent = "+"+fmt(cnt.v,0,true)+" "+p.unidad; }}, cue+.5);
    show(id+"-cnt", cue+.5, .3, {y:10}); }
},
interruptor(c, p){
  const id = "#"+c.id, cue = Math.max(c.t0+1.3, Math.min(p.cue, c.t1-1.0)), on = p.on, dx = 184;
  show(id+"-ruta", c.t0+.1, .3, {x:-16}); show(id+"-tit", c.t0+.25, .4, {y:20}); show(id+"-sub", c.t0+.4, .4, {y:20}); show(id+"-row", c.t0+.55, .4, {y:24});
  tl.set(id+"-thumb", {x:on ? dx : 0}, c.t0);
  tl.set(id+"-on", {opacity:on ? 1 : 0}, c.t0); tl.set(id+"-off", {opacity:on ? 0 : 1}, c.t0);
  show(id+"-fg", cue-.6, .3, {scale:.6, x:40, y:40});
  F(id+"-fg", {scale:1}, {scale:.78, duration:.12, yoyo:true, repeat:1, ease:"power2.inOut"}, cue-.12);
  F(id+"-fg", {x:0}, {x:on ? -dx : dx, duration:.4, ease:"power3.inOut"}, cue);
  F(id+"-thumb", {x:on ? dx : 0}, {x:on ? 0 : dx, duration:.4, ease:"power3.inOut"}, cue);
  F(id+"-track", {backgroundColor:on ? ACC : MUTC}, {backgroundColor:on ? MUTC : ACC, duration:.4}, cue);
  F(id+"-on", {opacity:on ? 1 : 0}, {opacity:on ? 0 : 1, duration:.25}, cue+.1);
  F(id+"-off", {opacity:on ? 0 : 1}, {opacity:on ? 1 : 0, duration:.25}, cue+.1);
  F(id+"-fg", {opacity:1}, {opacity:0, duration:.3}, cue+.6);
  F("#"+c.id+" .stage", {scale:1}, {scale:1.03, duration:.1, yoyo:true, repeat:1, ease:"power2.out"}, cue+.35);
  show(id+"-ok", cue+.7, .35, {y:14});
},
censura(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .32, .35);
  if ($(id+"-h")) show(id+"-h", c.t0+.05, .3, {y:-10});
  for (let i=0;i<p.n;i++){
    F(id+"-l"+i, {opacity:0, x:-30}, {opacity:1, x:0, duration:.3, ease:E}, cues[i]);
    for (let j=0;j<p.reds[i];j++){ const t = cues[i]+.3+j*.12;
      F(id+"-b"+i+"_"+j, {scaleX:0}, {scaleX:1, duration:.26, ease:"power3.out"}, t);
      F("#"+c.id+" .stage", {y:0}, {y:4, duration:.04, yoyo:true, repeat:1}, t); }
  }
  if (p.sello){ const t = Math.max(cues[p.n-1]+.7, Math.min(p.cue, c.t1-.8));
    F(id+"-st", {opacity:0}, {opacity:1, duration:.05}, t);
    F(id+"-st span", {scale:2.4, rotation:-24}, {scale:1, rotation:-10, duration:.3, ease:"power4.out"}, t);
    F("#"+c.id+" .stage", {x:0}, {x:-8, duration:.05, yoyo:true, repeat:3}, t); }
},
visor(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, cues = stagger(c, p.cues, .4, .5);
  F(id+"-rec i", {opacity:1}, {opacity:.15, duration:.5, yoyo:true, repeat:Math.max(1, Math.floor(Dd/.5)), ease:"steps(1)"}, c.t0);
  F(id+"-scan", {y:-120}, {y:950, duration:2.2, repeat:Math.ceil(Dd/2.2), ease:"none"}, c.t0);
  F(id+"-mesh", {opacity:0}, {opacity:.6, duration:.6}, c.t0+.35);
  F(id+"-img", {scale:1}, {scale:1.06, duration:Dd, ease:"none"}, c.t0);
  const tc = {v:0};
  F(tc, {v:0}, {v:Dd, duration:Dd, ease:"none", onUpdate:()=>{ const s = tc.v, f = Math.floor((s%1)*30);
    $(id+"-tc").textContent = "00:00:"+String(Math.floor(s)).padStart(2,"0")+":"+String(f).padStart(2,"0"); }}, c.t0);
  for (let i=0;i<p.n;i++){ F(id+"-bx"+i, {opacity:0, scale:2.5}, {opacity:1, scale:1, duration:.3, ease:"power4.out"}, cues[i]); show(id+"-tg"+i, cues[i]+.15, .3, {x:-16}); }
  if (p.sello){ const t = Math.max(c.t0+1.2, Math.min(p.cue, c.t1-.8));
    F(id+"-st", {opacity:0}, {opacity:1, duration:.05}, t);
    F(id+"-st span", {scale:2.6, rotation:-18}, {scale:1, rotation:-7, duration:.3, ease:"power4.out"}, t);
    F("#"+c.id+" .stage", {x:0}, {x:-9, duration:.05, yoyo:true, repeat:3}, t); }
},
onda(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, cues = stagger(c, p.cues, .35, .5), rnd = seeded(5+SEED);
  for (let k=0;k<56;k++){ const b = $(id+"-b"+k); if (!b) continue; const h = parseFloat((b.style.transform.match(/scaleY\(([\d.]+)\)/)||[0,.5])[1]);
    const d = .22+rnd()*.4; F(b, {scaleY:h}, {scaleY:Math.max(.08, h*.35), duration:d, yoyo:true, repeat:Math.ceil(Dd/d), ease:"sine.inOut"}, c.t0+rnd()*.3); }
  F(id+"-ph", {left:"0%"}, {left:"100%", duration:Dd, ease:"none"}, c.t0);
  for (let i=0;i<p.n;i++) F(id+"-c"+i, {opacity:0, y:20, scale:.9}, {opacity:1, y:0, scale:1, duration:.3, ease:"back.out(1.6)"}, cues[i]);
  if (p.sello){ const t = Math.max(c.t0+1.2, Math.min(p.cue, c.t1-.8));
    F(id+"-st", {opacity:0}, {opacity:1, duration:.05}, t);
    F(id+"-st span", {scale:2.4, rotation:-16}, {scale:1, rotation:-6, duration:.3, ease:"power4.out"}, t);
    F("#"+c.id+" .stage", {x:0}, {x:-8, duration:.05, yoyo:true, repeat:3}, t); }
},
impacto(c, p){
  const id = "#"+c.id;
  if (p.logo) F(id+"-logo", {opacity:0, scale:.5, rotation:-12}, {opacity:1, scale:1, rotation:0, duration:.45, ease:"back.out(2)"}, c.t0+.05);
  p.cues.forEach((t, i) => {
    const tt = Math.max(t-.04, c.t0+.08+i*.05);
    F(id+"-w"+i, {opacity:0, scale:1.8, y:40, rotation:i%2?-4:4}, {opacity:1, scale:1, y:0, rotation:0, duration:.22, ease:"power4.out"}, tt);
    if (p.kw[i]){ F(id+"-b"+i, {scaleX:0}, {scaleX:1, duration:.25, ease:"power3.out"}, tt+.08);
      F(id+"-w"+i+" > span", {color:getComputedStyle(document.documentElement).getPropertyValue("--text").trim()}, {color:getComputedStyle(document.documentElement).getPropertyValue("--on-acc").trim(), duration:.12}, tt+.16); }
    F("#"+c.id+" .stage", {x:0, y:0}, {x:(i%2?7:-7), y:(i%2?-5:5), duration:.05, yoyo:true, repeat:1, ease:"none"}, tt+.02);
  });
},
presentador(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, cs = getComputedStyle(document.documentElement);
  tl.set("#hdr .h", {color:"#FFFFFF"}, c.t0); tl.set("#hdr .d", {color:"rgba(255,255,255,.8)"}, c.t0); tl.set("#hdr img", {filter:"none"}, c.t0);
  tl.set("#hdr .h", {color:cs.getPropertyValue("--text-soft").trim()}, c.t1); tl.set("#hdr .d", {color:cs.getPropertyValue("--text-muted").trim()}, c.t1);
  tl.set("#hdr img", {filter:cs.getPropertyValue("--mark-filter").trim() || "none"}, c.t1);
  F(id+"-wrap", {scale:1.0}, {scale:1.05, duration:Dd, ease:"none"}, c.t0);
  if ($(id+"-live")){ show(id+"-live", c.t0+.25, .35, {x:20}); F(id+"-live i", {opacity:1}, {opacity:.25, duration:.45, yoyo:true, repeat:Math.max(1, Math.floor(Dd/.9)), ease:"sine.inOut"}, c.t0+.3); }
  if ($(id+"-name")){ show(id+"-name", c.t0+.5, .45, {x:-40}); F(id+"-name", {opacity:1}, {opacity:0, duration:.3}, Math.max(c.t0+1.2, c.t1-.7)); }
},
imagen(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, k = (c.k+SEED) % 4;
  const mv = p.mov || ["acercar","alejar","derecha","izquierda"][k];
  const from = mv === "alejar" ? {scale:1.22, x:0, y:0} : (mv === "derecha" ? {scale:1.14, x:60, y:0} : (mv === "izquierda" ? {scale:1.14, x:-60, y:0} : {scale:1.04, x:0, y:10}));
  const to = mv === "alejar" ? {scale:1.04, x:0, y:0} : (mv === "derecha" ? {scale:1.14, x:-60, y:0} : (mv === "izquierda" ? {scale:1.14, x:60, y:0} : {scale:1.2, x:0, y:-10}));
  F(id+"-img", from, Object.assign({duration:Dd, ease:"none"}, to), c.t0);
  if (p.modo === "tarjeta"){
    F(id+"-card", {opacity:0, y:80, rotation:-4, scale:.92}, {opacity:1, y:0, rotation:-2, scale:1, duration:.7, ease:E}, c.t0+.05);
    F(id+"-card", {rotation:-2}, {rotation:1.5, duration:Dd, ease:"sine.inOut"}, c.t0+.7);
    show(id+"-cred", c.t0+1, .4, {y:10});
  } else {
    const t = Math.max(c.t0+.7, Math.min(p.cue, c.t0+(c.t1-c.t0)*.5));
    show(id+"-tit", t, .5, {y:40});
    show(id+"-cred", c.t0+.6, .4, {y:0});
  }
},
codigo(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .3);
  F(id+"-win", {rotationX:8, rotationY:-6}, {rotationX:0, rotationY:3, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  cues.forEach((t, i) => F(id+"-ln"+i, {opacity:0, x:-30}, {opacity:1, x:0, duration:.28, ease:E}, t-.05));
  p.mk.forEach(i => { const t = cues[i]; tl.set(id+"-ln"+i, {className:"cd-l mk"}, t+.25); F(id+"-ln"+i, {scale:1}, {scale:1.03, duration:.18, yoyo:true, repeat:1, transformOrigin:"0 50%"}, t+.3); });
},
pasos(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .5), n = p.n;
  for (let i=0;i<n;i++){
    F(id+"-k"+i, {opacity:0, x:-60}, {opacity:.4, x:0, duration:.45, ease:E}, c.t0+.2+i*.12);
    F(id+"-k"+i, {opacity:.4}, {opacity:1, duration:.25}, cues[i]-.05);
    tl.set(id+"-n"+i, {className:"ps-n on"}, cues[i]);
    F(id+"-n"+i, {scale:.7}, {scale:1, duration:.45, ease:"back.out(2.2)"}, cues[i]);
    if (i > 0) F(id+"-fill", {scaleY:(i-1)/(n-1)}, {scaleY:i/(n-1), duration:.5, ease:"power2.inOut"}, cues[i]-.4);
  }
},
anillo(c, p){
  const id = "#"+c.id, o = {v:p.desde}, land = Math.max(c.t0+1.2, Math.min(p.cue+.15, c.t1-.6)), dur = land-c.t0-.1;
  F(id+"-ring", {strokeDashoffset:100}, {strokeDashoffset:100-p.val, duration:dur, ease:"power3.out"}, c.t0+.1);
  F(o, {v:p.desde}, {v:p.val, duration:dur, ease:"power3.out", onUpdate:()=>{ $(id+"-n").textContent = fmt(o.v, p.dec); }}, c.t0+.1);
  F(id+"-n", {scale:1}, {scale:1.08, duration:.18, yoyo:true, repeat:1, ease:"power2.inOut"}, land-.1);
  show(id+"-l", c.t0+.5, .5, {y:30});
},
titular(c, p){
  const id = "#"+c.id;
  F(id+"-card", {opacity:0, y:50, rotationX:10}, {opacity:1, y:0, rotationX:0, duration:.55, ease:E}, c.t0+.05);
  F(id+"-tag", {opacity:0, scale:1.6}, {opacity:1, scale:1, duration:.3, ease:"back.out(2)"}, c.t0+.4);
  if ($(id+"-logo")){ F(id+"-logo", {opacity:0, scale:.4, rotation:-14}, {opacity:1, scale:1, rotation:0, duration:.5, ease:"back.out(2)"}, c.t0+.15);
    F(id+"-logo", {y:0}, {y:-10, duration:.9, yoyo:true, repeat:Math.max(1, Math.floor((c.t1-c.t0)/1.8)), ease:"sine.inOut"}, c.t0+.7); }
  const dt = Math.min(.14, (c.t1-c.t0-1.6)/Math.max(1,p.n));
  for (let i=0;i<p.n;i++) F(id+"-w"+i, {opacity:0, y:30, scale:1.3, filter:"blur(6px)"}, {opacity:1, y:0, scale:1, filter:"blur(0px)", duration:.3, ease:E}, c.t0+.55+i*dt);
  show(id+"-baj", c.t0+.6+p.n*dt+.15, .45, {y:20});
  F(id+"-rule", {scaleX:0}, {scaleX:1, duration:.7, ease:"power2.inOut"}, Math.max(c.t0+1.2, Math.min(p.cue, c.t1-.8)));
},
cita(c, p){
  const id = "#"+c.id;
  F(id+"-card", {opacity:0, y:40, scale:.96}, {opacity:1, y:0, scale:1, duration:.5, ease:E}, c.t0+.05);
  p.cues.forEach((t,i) => F(id+"-w"+i, {opacity:0, y:14}, {opacity:1, y:0, duration:.22, ease:"power2.out"}, Math.max(t-.04, c.t0+.4)));
  show(id+"-a", Math.max(c.t0+1.0, Math.min(p.autor, c.t0+(c.t1-c.t0)*.6)), .45, {y:20, x:-20});
},
tabla(c, p){
  const id = "#"+c.id, cue = Math.max(c.t0+1.0+p.n*.1, Math.min(p.cue, c.t1-.6));
  for (let i=0;i<p.n;i++) F(id+"-r"+i, {opacity:0, x:-40}, {opacity:1, x:0, duration:.35, ease:E}, c.t0+.3+i*.12);
  if (p.mk >= 0){
    tl.set(id+"-r"+p.mk, {className:"tb-r mk on"}, cue);
    F(id+"-r"+p.mk, {scale:1}, {scale:1.03, duration:.16, yoyo:true, repeat:1}, cue);
  }
},
calendario(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .4);
  for (let d=1; d<=p.n; d++) F(id+"-d"+d, {opacity:0, scale:.6}, {opacity:1, scale:1, duration:.3, ease:"back.out(1.5)"}, c.t0+.15+d*.018);
  p.dias.forEach((d, i) => {
    const t = Math.max(cues[i], c.t0+.9);
    tl.set(id+"-d"+d, {className:"ca-c mk on"}, t);
    F(id+"-d"+d, {scale:1}, {scale:1.12, duration:.2, yoyo:true, repeat:1, ease:"power2.inOut"}, t);
    F(id+"-b"+d, {opacity:0, y:10}, {opacity:1, y:0, duration:.3, ease:E}, t+.15);
  });
},
planes(c, p){
  const id = "#"+c.id, cues = stagger(c, p.cues, .35);
  for (let i=0;i<p.n;i++){
    F(id+"-c"+i, {opacity:0, y:80, scale:.94}, {opacity:1, y:0, scale:1, duration:.5, ease:E}, c.t0+.15+i*.14);
    F(id+"-c"+i, {scale:1}, {scale:1.04, duration:.2, yoyo:true, repeat:1, ease:"power2.inOut"}, Math.max(cues[i], c.t0+.8+i*.14));
  }
  p.hi.forEach(i => F(id+"-c"+i, {y:0}, {y:-18, duration:.5, ease:E}, Math.max(cues[i], c.t0+.9)));
},
sitio(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, duo = p.lay === "duo", cel = p.lay === "celular";
  if ($(id+"-br")){
    F(id+"-br", {opacity:0, y:110, rotationX:16, scale:.93}, {opacity:1, y:0, rotationX:0, scale:1, duration:.7, ease:E}, c.t0+.02);
    F(id+"-br", {rotationY:duo?-5:-4}, {rotationY:duo?3:4, duration:Dd, ease:"sine.inOut"}, c.t0);
  }
  if ($(id+"-ph")){
    F(id+"-ph", {opacity:0, x:cel?0:240, y:cel?160:80, rotation:cel?0:8}, {opacity:1, x:0, y:0, rotation:cel?0:3, duration:.75, ease:E}, c.t0+(duo?.28:.02));
    F(id+"-ph", {rotationY:cel?-12:0}, {rotationY:cel?10:-6, duration:Dd, ease:"sine.inOut"}, c.t0);
  }
  const stack = (pre, list) => {
    const n = list.length; if (!n) return;
    const cues = stagger(c, list.map(x => x.cue), .55, 0);
    list.forEach((x, i) => {
      const a = i ? cues[i] : c.t0, b = i < n-1 ? cues[i+1] : c.t1, el = id+"-"+pre+i;
      if (i) F(el, {opacity:0, scale:1.03}, {opacity:1, scale:1, duration:.26, ease:"power2.out"}, a-.06); else tl.set(el, {opacity:1}, c.t0);
      if (i < n-1) tl.set(el, {opacity:0}, b+.25);
      if (x.scroll > 0) F(el, {y:0}, {y:-x.scroll, duration:Math.max(.6, b-a-.55), ease:"power1.inOut"}, a+.4);
      if (x.tap){ const tt = Math.max(a+.45, b-.55);
        F(id+"-t"+i, {opacity:0, scale:.5}, {opacity:1, scale:1, duration:.14, ease:"power2.out"}, tt);
        F(id+"-t"+i+" i", {scale:.3, opacity:1}, {scale:1.9, opacity:0, duration:.55, ease:"power2.out"}, tt+.1);
        F(id+"-t"+i, {opacity:1}, {opacity:0, duration:.2}, tt+.5); }
    });
  };
  stack("d", p.desk); stack("c", p.cel);
  stagger(c, p.chips, .5, 1.1).forEach((t, i) => {
    const tt = Math.max(t, c.t0+.8);
    F(id+"-k"+i, {opacity:0, scale:.6, y:24, z:50}, {opacity:1, scale:1, y:0, z:50, duration:.42, ease:"back.out(2)"}, tt);
    F(id+"-k"+i+" .st-dot", {scale:1}, {scale:1.45, duration:.5, yoyo:true, repeat:Math.max(1, Math.floor((c.t1-tt)/1.0)), ease:"sine.inOut"}, tt+.4);
  });
  if ($(id+"-lab")) show(id+"-lab", c.t0+.55, .5, {y:30});
},
carrusel(c, p){
  const id = "#"+c.id, n = p.n, cues = stagger(c, p.cues, .42, 0);
  F(id+"-fr", {opacity:0, y:90, scale:.92}, {opacity:1, y:0, scale:1, duration:.55, ease:E}, c.t0+.02);
  F(id+"-fr", {rotationY:-6, rotationX:5}, {rotationY:6, rotationX:0, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  show(id+"-foot", c.t0+.25, .4, {y:20});
  for (let k=0;k<n;k++){
    const a = k ? cues[k] : c.t0, b = k < n-1 ? cues[k+1] : c.t1, dir = k%2 ? -1 : 1;
    if (k){ F(id+"-i"+k, {opacity:1, xPercent:100*dir}, {xPercent:0, duration:.3, ease:"power3.out"}, a-.08);
            F(id+"-i"+(k-1), {xPercent:0}, {xPercent:-40*dir, duration:.3, ease:"power3.out"}, a-.08);
            tl.set(id+"-i"+(k-1), {opacity:0}, a+.24); }
    else tl.set(id+"-i0", {opacity:1}, c.t0);
    F(id+"-i"+k, {scale:1}, {scale:1.06, duration:Math.max(.4, b-a+.3), ease:"none"}, a);
    const lab = [id+"-l"+k, id+"-n"+k, id+"-u"+k];
    F(lab, {opacity:0, y:22}, {opacity:1, y:0, duration:.24, ease:E}, a-.04);
    if (k < n-1) tl.set(lab, {opacity:0}, b-.05);
  }
},
muro(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0;
  [0,1,2].forEach(j => F(id+"-c"+j, {y:j===1?-700:0}, {y:j===1?0:-700, duration:Dd+.6, ease:"none"}, c.t0-.3));
  const TX = getComputedStyle(document.documentElement).getPropertyValue("--text").trim(), OA = getComputedStyle(document.documentElement).getPropertyValue("--on-acc").trim();
  p.cues.forEach((t, i) => {
    const tt = Math.max(t-.04, c.t0+.15+i*.05);
    F(id+"-w"+i, {opacity:0, scale:1.6, y:30}, {opacity:1, scale:1, y:0, duration:.24, ease:"power4.out"}, tt);
    if (p.kw[i]){ F(id+"-b"+i, {scaleX:0}, {scaleX:1, duration:.25, ease:"power3.out"}, tt+.08); F(id+"-w"+i+" > span:last-child", {color:TX}, {color:OA, duration:.12}, tt+.16); }
  });
},
notificaciones(c, p){
  const id = "#"+c.id;
  stagger(c, p.cues, .45, .5).forEach((t, i) => {
    F(id+"-k"+i, {opacity:0, y:-70, scale:.9}, {opacity:1, y:0, scale:1, duration:.5, ease:"back.out(1.6)"}, t-.05);
    F(id+"-k"+i, {x:0}, {x:i%2?-8:8, duration:.07, yoyo:true, repeat:1, ease:"none"}, t+.42);
  });
},
caos(c, p){
  const id = "#"+c.id;
  F(id+"-card", {opacity:0, y:70, scale:.9, rotation:-3}, {opacity:1, y:0, scale:1, rotation:0, duration:.6, ease:E}, c.t0+.02);
  F(id+"-card img", {scale:1.14}, {scale:1.0, duration:c.t1-c.t0, ease:"none"}, c.t0);
  if ($(id+"-cred")) show(id+"-cred", c.t0+.9, .4, {y:0});
  stagger(c, p.apps, .14, .3).forEach((t, i) => {
    F(id+"-a"+i, {opacity:0, scale:.3, rotation:i%2?-28:28}, {opacity:1, scale:1, rotation:i%2?-7:7, duration:.45, ease:"back.out(2.2)"}, t);
    F(id+"-a"+i, {y:0}, {y:i%2?-16:16, duration:1.1+i*.13, yoyo:true, repeat:Math.max(1, Math.floor((c.t1-t)/1.2)), ease:"sine.inOut"}, t+.45);
  });
  const nc = stagger(c, p.notis, .28, 1.0);
  nc.forEach((t, i) => {
    F(id+"-n"+i, {opacity:0, scale:.5, y:30}, {opacity:1, scale:1, y:0, duration:.34, ease:"back.out(2.4)"}, t);
    F("#"+c.id+" .stage", {x:0}, {x:i%2?7:-7, duration:.05, yoyo:true, repeat:1, ease:"none"}, t+.05);
  });
  if (nc.length){ const tt = nc[nc.length-1]+.25; if (tt < c.t1-.4) F(id+"-card", {rotation:-1.2}, {rotation:1.2, duration:.11, yoyo:true, repeat:Math.max(1, Math.floor((c.t1-tt)/.22)), ease:"sine.inOut"}, tt); }
},
planilla(c, p){
  const id = "#"+c.id, cue = Math.max(c.t0+1.0, Math.min(p.cue, c.t1-.8));
  F(id+"-win", {opacity:0, y:90, rotationX:12, scale:.94}, {opacity:1, y:0, rotationX:0, scale:1, duration:.6, ease:E}, c.t0+.02);
  F(id+"-win", {rotationY:-4}, {rotationY:4, duration:c.t1-c.t0, ease:"sine.inOut"}, c.t0);
  for (let r=1;r<=14;r++) F(id+"-r"+r, {opacity:0, x:-24}, {opacity:1, x:0, duration:.25, ease:E}, c.t0+.25+r*.035);
  F(id+"-dlg", {opacity:0, scale:.7, y:30}, {opacity:1, scale:1, y:0, duration:.35, ease:"back.out(2.2)"}, cue);
  F(id+"-win", {x:0}, {x:12, duration:.05, yoyo:true, repeat:5, ease:"none"}, cue+.05);
  F(id+"-win", {filter:"brightness(1)"}, {filter:"brightness(.82)", duration:.3}, cue);
},
logo(c, p){
  const id = "#"+c.id;
  F(id+"-bg", {clipPath:"circle(0% at 50% 55%)"}, {clipPath:"circle(140% at 50% 55%)", duration:.6, ease:"power3.inOut"}, c.t0);
  F(id+"-mark", {opacity:0, scale:.5, rotation:-14}, {opacity:1, scale:1, rotation:0, duration:.6, ease:"back.out(1.8)"}, c.t0+.3);
  show(id+"-wm", c.t0+.5, .5, {y:40});
  if ($(id+"-sub")) show(id+"-sub", c.t0+.85, .5, {y:24});
  if ($(id+"-lema")) F(id+"-lema", {opacity:0, letterSpacing:"0.8em"}, {opacity:.8, letterSpacing:"0.42em", duration:.8, ease:E}, c.t0+1.05);
  F(id+"-mark", {y:0}, {y:-12, duration:1.0, yoyo:true, repeat:Math.max(1, Math.floor((c.t1-c.t0)/2)), ease:"sine.inOut"}, c.t0+.9);
},
cuenta(c, p){
  const id = "#"+c.id, Dd = c.t1-c.t0, X0 = -110, X1 = 540, Y = 395;
  const fresh = c.first || c.tin !== "continuo";
  if (fresh){ F(id+"-card", {opacity:0, y:50, scale:.95}, {opacity:1, y:0, scale:1, duration:.6, ease:E}, c.t0+.02); }
  const xa = X0 + (X1-X0)*p.p0, xb = X0 + (X1-X0)*p.p1, tEnd = p.clic ? Math.max(c.t0+.4, Math.min(p.cue, c.t1-.8)) : c.t1;
  F(id+"-cur", {x:xa-12, y:Y-6}, {x:xb-12, y:Y-6, duration:Math.max(.1, tEnd-c.t0), ease:"none"}, c.t0);
  F(id+"-tr", {width:Math.max(0, xa)}, {width:Math.max(0, xb), duration:Math.max(.1, tEnd-c.t0), ease:"none"}, c.t0);
  const o = {v:p.desde}, num = $(id+"-num");
  const draw = () => { const v = Math.max(0, Math.round(o.v)); num.textContent = String(v).padStart(3, "0"); num.style.color = v <= p.rojo ? "#E5484D" : ""; };
  F(o, {v:p.desde}, {v:p.hasta, duration:Math.max(.1, tEnd-c.t0), ease:"none", onUpdate:draw}, c.t0);
  if (p.clic){
    F(id+"-cur", {scale:1}, {scale:.82, duration:.08, yoyo:true, repeat:1, ease:"power2.out", transformOrigin:"12px 6px"}, tEnd);
    F(id+"-btn", {scale:1}, {scale:.93, duration:.08, yoyo:true, repeat:1, ease:"power2.out"}, tEnd);
    F(id+"-rip", {opacity:.9, scale:.2}, {opacity:0, scale:3.2, duration:.7, ease:"power2.out"}, tEnd+.04);
    for (let k=0;k<12;k++) F(id+"-sp"+k, {opacity:1, y:0, scaleY:.4}, {opacity:0, y:-150, scaleY:1, duration:.5, ease:"power3.out"}, tEnd+.04);
    F("#flash", {opacity:0}, {opacity:.55, duration:.04, ease:"none"}, tEnd+.02); F("#flash", {opacity:.55}, {opacity:0, duration:.3, ease:"power2.out"}, tEnd+.06);
    F("#"+c.id+" .stage", {x:0, y:0}, {x:9, y:-6, duration:.05, yoyo:true, repeat:3, ease:"none"}, tEnd+.03);
    if ($(id+"-ok")){ F(id+"-bt", {opacity:1, y:0}, {opacity:0, y:-30, duration:.2}, tEnd+.25); F(id+"-ok", {opacity:0, y:30}, {opacity:1, y:0, duration:.25, ease:E}, tEnd+.3); }
    F(o, {v:p.hasta}, {v:0, duration:.01, onUpdate:draw}, tEnd);
  }
},
cierre(c, p){
  const id = "#"+c.id;
  F(id+"-mark", {scale:.8, opacity:0}, {scale:1, opacity:1, duration:.7, ease:E}, c.t0+.2);
  show(id+"-wm", c.t0+.45, .55, {y:26});
  if ($(id+"-lema")) F(id+"-lema", {opacity:0, letterSpacing:"0.8em"}, {opacity:1, letterSpacing:"0.42em", duration:.8, ease:E}, c.t0+.7);
  show(id+"-sub", c.t0+.8, .5, {y:20});
  F(id+"-cta", {opacity:0, scale:.85}, {opacity:1, scale:1, duration:.5, ease:E}, c.t0+1.2);
  show(id+"-src", c.t0+1.5, .5, {y:10});
}
};

const CALLS = __CALLS__;
const NOPUNCH = {presentador:1, impacto:1, cuenta:1, logo:1, muro:1, caos:1, glitch:1};
CALLS.forEach(c => { CAM(c); (SC[c.p.tipo] || (()=>{}))(c, c.p); if (!NOPUNCH[c.p.tipo]) PUNCH(c, c.kw); });

// subtítulos palabra por palabra: la palabra que suena entra con un pop; las ya dichas quedan en el tono suave del tema
const CAPS = __CAPS__;
const MARCA = __MARCA__;
const TXT = getComputedStyle(document.documentElement).getPropertyValue("--text").trim() || "#FFFFFF";
const DONE = MARCA ? TXT : (getComputedStyle(document.documentElement).getPropertyValue("--cap-done").trim() || "#C6CFE0");
const ONACC = getComputedStyle(document.documentElement).getPropertyValue("--on-acc").trim() || "#FFFFFF";
CAPS.forEach(g => {
  const el = "#g"+g.g;
  F(el, {opacity:0}, {opacity:1, duration:.01}, g.t0);
  F(el, {opacity:1}, {opacity:0, duration:.1}, g.t1-.1);
  const on = g.low ? "#FFFFFF" : TXT, done = g.low ? "rgba(255,255,255,.78)" : DONE;
  g.w.forEach(([w, t0, t1, kw]) => {
    if (MARCA && !g.low) F("#"+w, {opacity:0, y:22, filter:"blur(8px)", color:on}, {opacity:1, y:0, filter:"blur(0px)", duration:.26, ease:"power2.out"}, t0);
    else F("#"+w, {opacity:0, y:16, scale:1.08, color:on}, {opacity:1, y:0, scale:1, duration:.14, ease:"power2.out"}, t0);
    if (!kw && !MARCA) F("#"+w, {color:on}, {color:done, duration:.25}, t1+.05);
  });
  g.k.forEach(([k, t]) => {
    if (MARCA && !g.low){ F("#"+k+" .kb", {opacity:1, scaleX:0}, {opacity:1, scaleX:1, duration:.24, ease:"power3.out", transformOrigin:"0 50%"}, t+.04);
      F("#"+k+" .w", {color:TXT}, {color:ONACC, duration:.1}, t+.14); }
    else F("#"+k+" .kb", {opacity:0, scale:.7}, {opacity:1, scale:1, duration:.22, ease:"back.out(2)"}, t);
  });
});

window.__timelines = window.__timelines || {};
window.__timelines["main"] = tl;
})();
"""


# ---------------------------------------------------------------- audio
def mix_audio(work, voice, D, beats, groups, guion=None):
    import numpy as np, soundfile as sf
    guion = guion or {}
    vw = os.path.join(work, "voz.wav")
    sf.write(vw, voice[: int((D + 0.2) * SR)], SR)
    scenes = [b["t0"] for b in beats]
    cards, hits, ticks = [], [], []
    for b in beats:
        e = b["escena"]
        if e["tipo"] in ("impacto", "glitch"):
            hits += [round(w["t0"], 3) for w in b["words"]]
        if e["tipo"] in ("visor", "onda", "censura", "bandeja") and e.get("sello"):
            hits += scene_cues(b, [e.get("en", "")], b["t0"], b["t1"])
        if e["tipo"] == "llamada" and e.get("estado"):
            hits += scene_cues(b, [e.get("en", "")], b["t0"], b["t1"])
        if e["tipo"] == "marcas":
            hits += scene_cues(b, [x.get("en", "") for x in (e.get("logos") or [])][:4], b["t0"], b["t1"])
        if e["tipo"] == "cuenta":
            if e.get("clic"):
                hits += scene_cues(b, [e.get("en", "")], b["t0"], b["t1"])
            tk = b["t0"] + 0.25
            while tk < b["t1"] - 0.1:
                ticks.append(round(tk, 3)); tk += 0.5
        if e["tipo"] in ("notificaciones", "caos"):
            its = e.get("items") or e.get("notis") or []
            cards += scene_cues(b, [x.get("en", "") for x in its][:8], b["t0"], b["t1"])
        if e["tipo"] == "planilla":
            hits += scene_cues(b, [(e.get("error") or {}).get("en", "")], b["t0"], b["t1"])
        if e["tipo"] in ("chips", "lista", "flujo", "pasos", "planes", "calendario"):
            items = e.get("items") or e.get("entradas") or e.get("pasos") or e.get("planes") or e.get("marcas") or []
            cards += scene_cues(b, [x.get("en", x.get("texto", x.get("titulo", x.get("nombre", "")))) for x in items][:4], b["t0"], b["t1"])
    mus = guion.get("musica")
    estilo = (mus.get("estilo") if isinstance(mus, dict) else mus) or "tech"
    mw = os.path.join(work, "music.wav")
    subprocess.run([sys.executable, os.path.join(HERE, "music.py"), mw, str(round(D + 0.2, 3)),
                    json.dumps({"scenes": scenes, "cards": cards, "hits": hits, "ticks": ticks, "estilo": estilo, "semilla": seed_of(guion) if guion.get("beats") else 7})],
                   check=True, stdout=subprocess.DEVNULL)
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
            "alerta": "filas", "reloj": "despues", "prompt": "texto", "cursores": "despues", "capas": "items",
            "codigo": "lineas", "pasos": "pasos", "anillo": "valor", "titular": "titulo", "cita": "autor", "tabla": "filas",
            "calendario": "marcas", "planes": "planes", "presentador": "video", "carrusel": "items", "muro": "imagenes",
            "notificaciones": "items",
            "bandeja": "items", "carta": "texto", "ranking": "filas", "triturar": "lineas", "interruptor": "titulo",
            "censura": "lineas", "visor": "etiquetas", "onda": "etiquetas",
            "curva": "puntos", "espectro": "items", "diff": "lineas", "firma": "lineas"}
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
        for _cap, _pron in re.findall(r"\{([^|}]*)\|([^}]*)\}", txt):
            if re.search(r"(^|\s)i a(\s|$|[.,;:?!])", _pron):
                warn.append(f"beat {i}: '{{{_cap}|{_pron}}}': la voz junta 'i a' y suena 'i'; usá 'inteligencia artificial'")
        if txt.count("*") // 2 > 2:
            warn.append(f"beat {i}: más de 2 palabras clave; si todo está destacado, nada lo está")
        plano = re.sub(r"\{[^}]*\}", " ", txt)
        for w in re.findall(r"[@\w./+-]+", plano):
            wl = w.strip(".,;:!?¿¡").lower()
            if (re.search(r"[a-záéíóú][A-Z]", w) or (len(w) > 1 and w.isupper() and w.isalpha()) or "@" in w
                    or re.search(r"\w\.\w", w) or wl in ENGLISH):
                warn.append(f"beat {i}: '{w}' sin pronunciación; usá {{{w}|cómo se dice}}")
        refs = [e.get("logo")] + [x.get("marca") for x in e.get("logos") or []] + [x.get("logo") for x in e.get("items") or [] if isinstance(x, dict)] \
            + [(e.get(k) or {}).get("logo") for k in ("antes", "despues") if isinstance(e.get(k), dict)]
        for r in refs:
            if r and not logo_key(r):
                err.append(f"beat {i}: no hay logo para '{r}' (ver plantilla/logos/marcas.json o sumalo)")
        if t == "sitio" and not (e.get("escritorio") or e.get("celular")):
            err.append(f"beat {i}: la escena 'sitio' necesita 'escritorio' y/o 'celular' (capturas)")
        if t == "caos" and not e.get("apps"):
            warn.append(f"beat {i}: 'caos' sin 'apps': se ve vacío")
        if t == "marcas" and not e.get("logos"):
            err.append(f"beat {i}: la escena 'marcas' necesita 'logos'")
        if t == "presentador":
            if not guion.get("voz_archivo"):
                warn.append(f"beat {i}: 'presentador' sin voz_archivo: los labios no van a coincidir con la voz")
            if i != 1:
                warn.append(f"beat {i}: 'presentador' está probado como beat 1 (gancho)")
        if t in ("imagen", "retrato"):
            if not (e.get("archivo") or e.get("url")):
                err.append(f"beat {i}: la escena 'imagen' necesita 'archivo' (ruta local) o 'url' (https)")
            elif not e.get("credito"):
                warn.append(f"beat {i}: la imagen no tiene 'credito' (autor y licencia); ponelo salvo que sea propia o generada")
        if t == "cita" and e.get("texto") and len(e["texto"]) > 160:
            warn.append(f"beat {i}: la cita es larga ({len(e['texto'])} caracteres); hasta 160 se lee bien")
        if t == "titular" and len(re.sub(r"[*]", "", e.get("titulo", ""))) > 70:
            warn.append(f"beat {i}: el titular es largo (más de 70 caracteres)")
    if tipos and tipos[-1] != "cierre":
        err.append("el último beat tiene que ser 'cierre'")
    for i in range(1, len(tipos)):
        if tipos[i] == tipos[i - 1]:
            warn.append(f"beats {i} y {i + 1}: misma escena '{tipos[i]}' seguida")
    if len(set(t for t in tipos if t != "cierre")) < 5:
        warn.append("menos de 5 tipos de escena distintos")
    if not 8 <= len(beats) <= 12:
        warn.append(f"{len(beats)} beats (lo recomendado es 8 a 12)")
    tema = guion.get("tema")
    if tema is not None and tema not in THEMES:
        err.append(f"tema '{tema}' no existe; opciones: {', '.join(THEMES)}")
    tr = guion.get("transiciones")
    for t in ([tr] if isinstance(tr, str) else (tr or [])):
        if t not in TRANSITIONS:
            err.append(f"transición '{t}' no existe; opciones: {', '.join(TRANSITIONS)}")
    mus = (guion.get("musica") or {}).get("estilo") if isinstance(guion.get("musica"), dict) else guion.get("musica")
    if mus is not None and mus not in MUSIC_STYLES:
        err.append(f"estilo de música '{mus}' no existe; opciones: {', '.join(MUSIC_STYLES)}")
    if historial:
        prev = [x for x in historial.get("publicados", []) if x.get("escenas")]
        if prev:
            last = prev[-1]
            if last["escenas"][0] == tipos[0]:
                warn.append(f"arranca con '{tipos[0]}', igual que el reel anterior")
            if last.get("acento", "").lower() == str(guion.get("acento", "")).lower():
                warn.append("mismo color de acento que el reel anterior")
            recent = prev[-2:]
            if any((x.get("tema") or "noche") == (tema or "noche") for x in recent):
                warn.append(f"tema '{tema or 'noche'}' usado en uno de los últimos 2 reels; alterná ({', '.join(THEMES)})")
            if any((x.get("musica") or "tech") == (mus or "tech") for x in prev[-1:]):
                warn.append(f"misma música ('{mus or 'tech'}') que el reel anterior; alterná ({', '.join(MUSIC_STYLES)})")
            mine = set(t for t in tipos if t != "cierre")
            used3 = set(t for x in prev[-3:] for t in x.get("escenas", []) if t != "cierre")
            fresh = mine - used3
            if len(fresh) < 2:
                libres = sorted(SCENE_TYPES - used3 - {"cierre"})
                warn.append(f"solo {len(fresh)} tipo(s) de escena que no aparecieron en los últimos 3 reels; usá al menos 2 (libres: {', '.join(libres)})")
            same = mine & set(t for t in last.get("escenas", []) if t != "cierre")
            if mine and len(same) / len(mine) > 0.7:
                warn.append(f"{len(same)} de {len(mine)} escenas repiten las del reel anterior; cambiá algunas")
    return err, warn


def browser_env():
    env = dict(os.environ)
    br = find_browser()
    if br:
        env["HYPERFRAMES_BROWSER_PATH"] = br
    return env


def image_ext(path):
    head = open(path, "rb").read(12)
    for magic, ext in IMG_MAGIC.items():
        if head.startswith(magic):
            return ext
    return None


def concat_voz(parts, gap=0.3):
    """Varias tomas de voz (mp3/wav, o el audio de un mp4 como el clip del avatar) en una sola pista, con `gap` s entre medio.
    Así el gancho lo dice el clip del avatar (con su propio audio) y el resto sale de otra toma, todo alineado de una."""
    import hashlib
    h = hashlib.sha256(json.dumps([[x, os.path.getsize(x)] for x in parts]).encode()).hexdigest()[:10]
    out = os.path.join(tempfile.gettempdir(), f"voz-concat-{h}.wav")
    if os.path.exists(out):
        return out
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    for x in parts:
        cmd += ["-i", x]
    n = len(parts)
    for _ in range(n - 1):
        cmd += ["-f", "lavfi", "-t", str(gap), "-i", f"anullsrc=r={SR}:cl=mono"]
    fc, seq = [], []
    for i in range(n):
        fc.append(f"[{i}:a]aresample={SR},aformat=channel_layouts=mono[a{i}]")
        seq.append(f"[a{i}]")
        if i < n - 1:
            seq.append(f"[{n + i}:a]")
    fc.append("".join(seq) + f"concat=n={2 * n - 1}:v=0:a=1[o]")
    subprocess.run(cmd + ["-filter_complex", ";".join(fc), "-map", "[o]", out], check=True)
    return out


def prepare_presentador(guion, beats, work, guion_dir):
    """Copia el clip del avatar a assets, saca un fotograma de fondo y anota duración y recorte de la voz."""
    for i, b in enumerate(beats, 1):
        e = b["escena"]
        if e["tipo"] != "presentador":
            continue
        src = e["video"] if os.path.isabs(e["video"]) else os.path.join(guion_dir, e["video"])
        if not os.path.exists(src):
            print(f"ERROR beat {i}: no existe el video {src}")
            sys.exit(2)
        os.makedirs(os.path.join(work, "assets"), exist_ok=True)
        name = f"presentador{i}.mp4"
        shutil.copy(src, os.path.join(work, "assets", name))
        poster = os.path.join(work, "assets", f"presentador{i}.jpg")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-frames:v", "1", "-q:v", "3", poster], check=True)
        pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                            capture_output=True, text=True, check=True)
        e["_src"], e["_poster"] = "assets/" + name, f"assets/presentador{i}.jpg"
        e["_dur"] = float(pr.stdout.strip() or 0)
        e["_trim0"] = float(guion.get("_trim0", 0))


def media_refs(e):
    """Rutas de imágenes que usa una escena del estilo marca."""
    t = e.get("tipo")
    if t == "sitio":
        return [x["img"] for x in _imgs(e.get("escritorio")) + _imgs(e.get("celular"))]
    if t == "carrusel":
        return [x.get("img") for x in (e.get("items") or []) if x.get("img")]
    if t == "muro":
        return [x if isinstance(x, str) else x.get("img") for x in (e.get("imagenes") or [])]
    if t == "caos":
        return [e["foto"]] if e.get("foto") else []
    return []


def prepare_media(guion, beats, work, guion_dir):
    """Copia (o baja) las capturas y fotos de las escenas del estilo marca a assets/img; deja e['_m'] (ruta → src) y e['_dims'] (ancho, alto)."""
    import hashlib
    from PIL import Image
    dst_dir = os.path.join(work, "assets", "img")
    for i, b in enumerate(beats, 1):
        e = b["escena"]
        refs = media_refs(e)
        if not refs:
            continue
        os.makedirs(dst_dir, exist_ok=True)
        e["_m"], e["_dims"] = {}, {}
        for k, ref in enumerate(refs):
            if ref in e["_m"]:
                continue
            if str(ref).startswith("http"):
                h = hashlib.sha256(ref.encode()).hexdigest()[:16]
                src = os.path.join(EL_CACHE, "img-" + h)
                if not os.path.exists(src):
                    os.makedirs(EL_CACHE, exist_ok=True)
                    r = subprocess.run(["curl", "-sSL", "--max-time", "60", "-A", "tobdev-media/1.0 (reel)", "-o", src + ".part", ref], capture_output=True, text=True)
                    if r.returncode != 0 or not os.path.exists(src + ".part") or os.path.getsize(src + ".part") < 1000:
                        print(f"ERROR beat {i}: no se pudo bajar {ref}")
                        sys.exit(2)
                    os.replace(src + ".part", src)
            else:
                src = ref if os.path.isabs(ref) else os.path.join(guion_dir, ref)
            if not os.path.exists(src):
                print(f"ERROR beat {i}: no existe la imagen {src}")
                sys.exit(2)
            ext = image_ext(src)
            if not ext:
                print(f"ERROR beat {i}: {src} no es una imagen")
                sys.exit(2)
            name = f"m{i}-{k}.{ext}"
            shutil.copy(src, os.path.join(dst_dir, name))
            e["_m"][ref] = "assets/img/" + name
            with Image.open(src) as im:
                e["_dims"][ref] = im.size


def prepare_images(guion, beats, work, guion_dir):
    """Copia (o baja) las imágenes de las escenas `imagen` a assets/img y deja la ruta en escena['_src'].
    Falla con ERROR si no se pudo conseguir el archivo o no es una imagen: mejor cambiar la escena que publicar un cuadro vacío."""
    import hashlib
    dst_dir = os.path.join(work, "assets", "img")
    slots = []
    for i, b in enumerate(beats, 1):
        e = b["escena"]
        if e["tipo"] in ("imagen", "retrato"):
            slots.append((i, e, ""))
        elif e["tipo"] == "espectro":
            slots += [(i, x, f"-{k}") for k, x in enumerate((e.get("items") or [])[:3])]
    for i, e, suf in slots:
        os.makedirs(dst_dir, exist_ok=True)
        src = None
        if e.get("archivo"):
            src = e["archivo"] if os.path.isabs(e["archivo"]) else os.path.join(guion_dir, e["archivo"])
            if not os.path.exists(src):
                print(f"ERROR beat {i}: no existe la imagen {src}")
                sys.exit(2)
        elif e.get("url"):
            h = hashlib.sha256(e["url"].encode()).hexdigest()[:16]
            cache = os.path.join(EL_CACHE, "img-" + h)
            if not os.path.exists(cache):
                os.makedirs(EL_CACHE, exist_ok=True)
                r = subprocess.run(["curl", "-sSL", "--max-time", "60", "-A", "tobdev-media/1.0 (reel)", "-o", cache + ".part", e["url"]], capture_output=True, text=True)
                if r.returncode != 0 or not os.path.exists(cache + ".part") or os.path.getsize(cache + ".part") < 1000:
                    print(f"ERROR beat {i}: no se pudo bajar la imagen ({(r.stderr or '').strip()[-160:] or 'respuesta vacía'}). "
                          "Si el sitio está bloqueado en este entorno, pedí que la permitan en Ajustes → Capacidades, adjuntala como 'archivo' o cambiá la escena.")
                    sys.exit(2)
                os.replace(cache + ".part", cache)
            src = cache
        ext = image_ext(src)
        if not ext:
            print(f"ERROR beat {i}: {src} no es una imagen (jpg, png, webp o gif)")
            sys.exit(2)
        name = f"img{i}{suf}.{ext}"
        shutil.copy(src, os.path.join(dst_dir, name))
        e["_src"] = "assets/img/" + name


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
        va = guion["voz_archivo"]
        parts = va if isinstance(va, list) else [va]
        parts = [x if os.path.isabs(x) else os.path.join(os.path.dirname(os.path.abspath(args[0])), x) for x in parts]
        for x in parts:
            if not os.path.exists(x):
                print("ERROR no existe el audio de voz_archivo:", x)
                sys.exit(2)
            raw = raw + open(x, "rb").read()
        voz_path = parts[0] if len(parts) == 1 else concat_voz(parts)
    guion_dir = os.path.dirname(os.path.abspath(args[0]))
    for b in guion.get("beats", []):  # imágenes locales: si cambian, se vuelve a armar
        e = b.get("escena") or {}
        loc = e.get("archivo") if e.get("tipo") == "imagen" else (e.get("video") if e.get("tipo") == "presentador" else None)
        if loc:
            ip = loc if os.path.isabs(loc) else os.path.join(guion_dir, loc)
            if os.path.exists(ip):
                raw = raw + open(ip, "rb").read()
        for ref in media_refs(e):
            ip = ref if os.path.isabs(str(ref)) else os.path.join(guion_dir, str(ref))
            if os.path.exists(ip):
                raw = raw + f"{ip}:{os.path.getsize(ip)}:{os.path.getmtime(ip)}".encode()
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
        prepare_images(guion, beats, work, guion_dir)
        prepare_presentador(guion, beats, work, guion_dir)
        prepare_media(guion, beats, work, guion_dir)
        open(os.path.join(work, "index.html"), "w").write(build_html(guion, beats, groups, D))
        open(os.path.join(work, "meta.json"), "w").write('{"id":"reel","name":"reel"}')
        mix_audio(work, voice, D, beats, groups, guion)
        tema = guion.get("tema") if guion.get("tema") in THEMES else "noche"
        json.dump({"duracion": D, "tema": tema, "semilla": seed_of(guion), "escenas": [[b["escena"]["tipo"], b["t0"], b["t1"]] for b in beats]},
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
        sheets = [sh if os.path.isabs(sh) else os.path.join(work, sh) for sh in sheets]
        safe = safe_zone_sheets(os.path.dirname(sheets[0]))
        for sh in (safe or sheets):
            print("REVISAR", sh)
        if safe:
            print("ZONA SEGURA: nada de texto sobre las franjas rojas (Instagram las corta en celulares altos) ni en lo naranja "
                  "(botones y caption); lo importante adentro de las líneas amarillas")
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



# Zona segura del Reel (1080x1920). En celulares más altos que 9:16, Instagram agranda el video para llenar
# la pantalla y corta los costados (en un iPhone 15 se midieron ~44 px por lado; Meta pide dejar libre el 6%,
# ~65 px). Abajo a la derecha van los botones (me gusta, comentar, compartir) y abajo el caption.
SAFE_CUT, SAFE_MARGIN = 65, 100


def safe_zone_sheets(frames_dir):
    """Hojas de contacto propias con la zona segura dibujada encima. Devuelve las rutas o [] si no puede."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return []
    frames = sorted(f for f in os.listdir(frames_dir) if re.match(r"frame-\d+-at-[\d.]+s\.png$", f))
    if not frames:
        return []
    try:
        font = ImageFont.truetype(os.path.join(HERE, "fonts", "FreeSans-700.ttf"), 22)
    except OSError:
        font = ImageFont.load_default()
    tw, th, cols, per = 360, 640, 5, 15
    out = []
    for si in range(0, len(frames), per):
        chunk = frames[si:si + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw + (cols + 1) * 8, rows * (th + 34) + 8), (24, 24, 28))
        for j, f in enumerate(chunk):
            im = Image.open(os.path.join(frames_dir, f)).convert("RGBA").resize((1080, 1920))
            ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            d.rectangle([0, 0, SAFE_CUT, 1920], fill=(255, 40, 40, 120))
            d.rectangle([1080 - SAFE_CUT, 0, 1080, 1920], fill=(255, 40, 40, 120))
            d.rectangle([930, 1180, 1080 - SAFE_CUT, 1920], fill=(255, 150, 0, 70))
            d.rectangle([SAFE_CUT, 1640, 930, 1920], fill=(255, 150, 0, 70))
            for x in (SAFE_MARGIN, 1080 - SAFE_MARGIN):
                for y in range(0, 1920, 48):
                    d.line([x, y, x, y + 26], fill=(255, 220, 0, 230), width=4)
            tile = Image.alpha_composite(im, ov).convert("RGB").resize((tw, th))
            x0, y0 = 8 + (j % cols) * (tw + 8), 8 + (j // cols) * (th + 34)
            m = re.match(r"frame-(\d+)-at-([\d.]+)s", f)
            ImageDraw.Draw(sheet).text((x0, y0), f"{int(m.group(1)) + 1}. {m.group(2)} s", fill=(235, 235, 235), font=font)
            sheet.paste(tile, (x0, y0 + 28))
        path = os.path.join(frames_dir, f"zona-segura-{si // per + 1}.jpg")
        sheet.save(path, quality=88)
        out.append(path)
    return out

if __name__ == "__main__":
    main()

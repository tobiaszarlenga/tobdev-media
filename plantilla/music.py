#!/usr/bin/env python3
"""Música procedural + SFX para los reels de tobdev. Uso: python3 music.py salida.wav DURACION '{"cards":[..],"scenes":[..]}'"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import wave, sys, json

SR = 44100
DUR = float(sys.argv[2])
CUES = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
N = int(SR * DUR)
rng = np.random.default_rng(7)

L = np.zeros(N); R = np.zeros(N)            # dry
RL = np.zeros(N); RR = np.zeros(N)          # reverb send

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

def env_adsr(n, a, d, s, r, sustain_len):
    a_n, d_n, r_n = int(a*SR), int(d*SR), int(r*SR)
    s_n = max(0, int(sustain_len*SR) - a_n - d_n)
    e = np.concatenate([np.linspace(0, 1, max(a_n,1)), np.linspace(1, s, max(d_n,1)), np.full(s_n, s), np.linspace(s, 0, max(r_n,1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n-len(e)))

def place(sig, t, gain=1.0, pan=0.0, send=0.0):
    i = int(t*SR)
    if i >= N: return
    sig = sig[: N - i]
    lg = gain * np.cos((pan + 1) * np.pi / 4); rg = gain * np.sin((pan + 1) * np.pi / 4)
    L[i:i+len(sig)] += sig * lg; R[i:i+len(sig)] += sig * rg
    if send:
        RL[i:i+len(sig)] += sig * lg * send; RR[i:i+len(sig)] += sig * rg * send

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'band', fs=SR, output='sos'), x)

def tt(d): return np.arange(int(d*SR)) / SR

def saw(f, t):
    # band-limited-ish saw via a few harmonics
    y = np.zeros_like(t)
    for k in range(1, 14):
        if f*k > 9000: break
        y += np.sin(2*np.pi*f*k*t) / k
    return y * 0.6

# ---------- instruments ----------
def pad_chord(notes, t0, dur, gain=0.11, cutoff=3400):
    t = tt(dur + 0.8)
    y = np.zeros_like(t)
    for m in notes:
        f = mtof(m)
        for det in (-0.004, 0.004):
            y += saw(f * (1 + det), t + 0.013*m)
    y = lp(y, cutoff, 2)
    y *= env_adsr(len(t), 0.45, 0.4, 0.8, 0.8, dur) * gain / len(notes)
    place(y, t0, 1.0, -0.15, send=0.55)
    place(y, t0 + 0.012, 1.0, 0.15, send=0.0)

def pluck(m, t0, gain=0.09, pan=0.0, decay=0.28, bright=5200):
    t = tt(decay * 4)
    f = mtof(m)
    y = np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*2*f*t) + 0.12*np.sin(2*np.pi*3*f*t)
    y *= np.exp(-t/decay) * np.minimum(1, t/0.004)
    y = lp(y, bright, 2)
    place(y, t0, gain, pan, send=0.35)

def bass(m, t0, dur, gain=0.22):
    t = tt(dur)
    f = mtof(m)
    y = np.sin(2*np.pi*f*t) + 0.25*np.sin(2*np.pi*2*f*t)
    y *= env_adsr(len(t), 0.01, 0.15, 0.7, 0.12, dur)
    place(lp(y, 500), t0, gain, 0.0)

def kick(t0, gain=0.42):
    t = tt(0.45)
    f = 45 + 75*np.exp(-t/0.045)
    ph = 2*np.pi*np.cumsum(f)/SR
    y = np.sin(ph) * np.exp(-t/0.16)
    y += 0.25 * lp(rng.standard_normal(len(t)), 3000) * np.exp(-t/0.006)
    place(y, t0, gain, 0.0)

def hat(t0, gain=0.035, pan=0.2):
    t = tt(0.08)
    y = hp(rng.standard_normal(len(t)), 7000) * np.exp(-t/0.018)
    place(y, t0, gain, pan)

def clap(t0, gain=0.07):
    t = tt(0.3)
    y = bp(rng.standard_normal(len(t)), 900, 2600) * (np.exp(-t/0.06) + 0.5*np.exp(-np.maximum(t-0.012,0)/0.05)*(t>0.012))
    place(y, t0, gain, -0.1, send=0.6)

def tick(t0, f=1500, gain=0.16, pan=0.0):
    t = tt(0.06)
    y = np.sin(2*np.pi*f*t) * np.exp(-t/0.012) + 0.4*hp(rng.standard_normal(len(t)), 4000)*np.exp(-t/0.004)
    place(y, t0, gain, pan, send=0.2)

def thock(t0, gain=0.2):
    t = tt(0.25)
    f = 180 + 140*np.exp(-t/0.02)
    y = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t/0.07)
    place(y, t0, gain, 0.0, send=0.3)

def chime(notes, t0, gain=0.1, gap=0.09, pan=0.1):
    for k, m in enumerate(notes):
        t = tt(1.6)
        f = mtof(m)
        y = (np.sin(2*np.pi*f*t) + 0.3*np.sin(2*np.pi*2.01*f*t) + 0.12*np.sin(2*np.pi*3.98*f*t)) * np.exp(-t/0.45) * np.minimum(1, t/0.003)
        place(y, t0 + k*gap, gain, pan + 0.15*k, send=0.6)

def pop(t0, f=880, gain=0.12):
    t = tt(0.12)
    ff = f*(1 + 0.6*np.exp(-t/0.01))
    y = np.sin(2*np.pi*np.cumsum(ff)/SR) * np.exp(-t/0.03)
    place(y, t0, gain, 0.05, send=0.3)

def whoosh(t0, dur=0.45, gain=0.09, up=True):
    t = tt(dur)
    n = rng.standard_normal(len(t))
    e = np.sin(np.pi * t/dur) ** 2
    # sweeping bandpass approximated by mixing two filtered layers with crossfade
    lo_l = bp(n, 300, 1200); hi_l = bp(n, 1500, 6000)
    k = t/dur if up else 1 - t/dur
    y = (lo_l*(1-k) + hi_l*k) * e
    place(y, t0, gain, -0.3, send=0.4)
    place(y[::-1].copy(), t0, gain*0.5, 0.3, send=0.0)

def thump(t0, gain=0.5):
    t = tt(0.6)
    f = 42 + 60*np.exp(-t/0.05)
    y = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t/0.22)
    y += 0.5 * lp(rng.standard_normal(len(t)), 1800) * np.exp(-t/0.03)
    place(y, t0, gain, 0.0, send=0.5)

def beep(t0, f, gain=0.1, d=0.09):
    t = tt(d)
    y = np.sign(np.sin(2*np.pi*f*t)) * 0.4 + np.sin(2*np.pi*f*t)*0.6
    y = lp(y, 2500) * env_adsr(len(t), 0.004, 0.02, 0.8, 0.02, d)
    place(y, t0, gain, 0.0, send=0.2)

def riser(t0, dur, gain=0.08):
    t = tt(dur)
    n = rng.standard_normal(len(t))
    e = (t/dur) ** 2.2
    y = bp(n, 800, 5000) * e
    f = 220 * 2 ** (2 * t/dur)
    y += 0.25 * np.sin(2*np.pi*np.cumsum(f)/SR) * e
    place(y, t0, gain, 0.0, send=0.5)


# ---------- composición (reel de noticias) ----------
BAR = 2.4; BEAT = 0.6
scenes = CUES.get("scenes", [0.0])
PROG = [([48, 55, 62, 64], 36, [60, 64, 67, 74]), ([50, 55, 59, 62], 43, [59, 62, 67, 71]),
        ([52, 55, 60, 64], 45, [60, 64, 69, 72]), ([48, 52, 57, 64], 41, [57, 60, 64, 69])]
ARP = [0, 1, 2, 3, 2, 1, 2, 3]
END = DUR - 3.0
t = 0.0; bar = 0
while t < END - 1e-6:
    pad_notes, root, arp = PROG[bar % 4]
    pad_chord(pad_notes, t, min(BAR, END - t), gain=0.10)
    for k in range(8):
        tk = t + k * 0.3
        if tk >= END: break
        pluck(arp[ARP[k]], tk, gain=0.105, pan=-0.35 if k % 2 else 0.35)
    for b in range(4):
        tb = t + b * BEAT
        if tb >= END: break
        bass(root, tb, 0.5, gain=0.11)
        if tb >= 4.5:
            if b in (0, 2): kick(tb, gain=0.18)
            for h in (0.0, 0.3):
                if tb + h < END: hat(tb + h, gain=0.055 if h == 0 else 0.08)
    t += BAR; bar += 1
pad_chord([48, 55, 59, 62, 64], END, 3.0, gain=0.12, cutoff=2000)
bass(36, END, 2.5, gain=0.14)
for s in scenes[1:]: whoosh(s - 0.15, 0.45, gain=0.07)
chime([79, 84], 0.3, gain=0.07)
for c in CUES.get("cards", []): pop(c, f=880, gain=0.08)
if len(scenes) > 2: chime([84, 88], scenes[2] + 0.1, gain=0.06)
chime([72, 76, 79, 84], END + 0.2, gain=0.07, gap=0.11)
pop(END + 1.5, f=820, gain=0.09)

# ---------- reverb + master ----------
ir_t = tt(2.4)
ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t/0.55)
ir = lp(ir, 5000)
irL = ir; irR = np.roll(ir, 211)
wetL = fftconvolve(RL, irL)[:N]; wetR = fftconvolve(RR, irR)[:N]
norm = np.max(np.abs(np.concatenate([wetL, wetR]))) + 1e-9
wet_gain = 0.25 * (np.max(np.abs(L)) / norm)
outL = L + wetL * wet_gain; outR = R + wetR * wet_gain

# fade out tail
fade = np.ones(N); fs = int((DUR - 1.2)*SR); fade[fs:] = np.linspace(1, 0, N - fs) ** 1.5
fade[: int(0.02*SR)] = np.linspace(0, 1, int(0.02*SR))
outL *= fade; outR *= fade
# gentle glue + soft clip
peak = max(np.max(np.abs(outL)), np.max(np.abs(outR)))
outL = np.tanh(1.2 * outL / peak) / np.tanh(1.2); outR = np.tanh(1.2 * outR / peak) / np.tanh(1.2)
outL *= 0.84; outR *= 0.84

pcm = np.stack([outL, outR], axis=1)
pcm = np.clip(pcm * 32767, -32768, 32767).astype(np.int16)
out = sys.argv[1]
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("wrote", out, pcm.shape[0] / SR, "s")

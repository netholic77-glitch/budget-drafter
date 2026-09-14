# -*- coding: utf-8 -*-
"""나레이션(open_jtalk) + 저역 앰비언스 → 트랙. 컷 길이에 맞춰 낭독 속도만 조정."""
import os, sys, subprocess, wave, math, tempfile, importlib
import numpy as np

M = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "ep01")
OUT = sys.argv[2] if len(sys.argv) > 2 else "audio.wav"
CUTS, NAR = M.CUTS, M.NARRATION
SR = 48000
DUR = CUTS[-1][1]
DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
TMP = tempfile.mkdtemp()


def synth(text, rate):
    t, w = os.path.join(TMP, "t.txt"), os.path.join(TMP, "o.wav")
    open(t, "w", encoding="utf-8").write(text + "\n")
    subprocess.run(["open_jtalk", "-x", DIC, "-m", VOICE, "-r", f"{rate:.3f}",
                    "-jf", "0.55", "-ow", w, t], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(w) as f:
        return np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768


def trim(a, thr=0.004):
    i = np.where(np.abs(a) > thr)[0]
    return a[i[0]:i[-1] + 1] if len(i) else a


buf = np.zeros(int(SR * DUR), np.float32)
for (s, e, *_), text in zip(CUTS, NAR):
    avail = (e - s) - 0.42
    a = trim(synth(text, 1.0))
    rate = 1.0
    if len(a) / SR > avail:
        rate = min(1.45, (len(a) / SR) / avail)
        a = trim(synth(text, rate))
    if len(a) / SR > avail:
        n = int(avail * SR)
        a = a[:n] * np.concatenate([np.ones(max(n - 2400, 0)), np.linspace(1, 0, min(2400, n))])
    a[:480] *= np.linspace(0, 1, 480)
    st = int((s + 0.22) * SR)
    buf[st:st + len(a)] += a
    print(f"{s:5.1f}s len={len(a)/SR:4.2f}s rate={rate:4.2f}  {text[:34]}")

t = np.arange(len(buf)) / SR
pad = np.zeros_like(buf)                                    # 저역 앰비언스 (미니어처 방 공기)
for f, g in ((55.0, .60), (82.4, .34), (110.0, .26), (164.8, .13)):
    pad += (np.sin(2 * np.pi * f * t + np.sin(t * 0.3) * 0.4) * g).astype(np.float32)
pad *= (0.60 + 0.40 * np.sin(2 * np.pi * 0.07 * t)).astype(np.float32) * 0.034
rng = np.random.default_rng(9)
for s, *_ in CUTS[1:]:                                      # 컷 전환 — 낮고 둔한 임팩트
    n = int(0.30 * SR)
    st = max(int((s - 0.06) * SR), 0)
    tt = np.arange(n) / SR
    imp = (np.sin(2 * np.pi * 62 * tt) * np.exp(-tt * 16) * 0.09
           + rng.normal(0, 1, n) * np.exp(-tt * 40) * 0.016).astype(np.float32)
    pad[st:st + n] += imp[:len(pad) - st]
pad[:SR] *= np.linspace(0, 1, SR)
pad[-int(SR * 1.2):] *= np.linspace(1, 0, int(SR * 1.2))
buf += pad

buf = np.tanh(buf * 1.10) * 0.94
buf = buf / max(np.max(np.abs(buf)), 1e-6) * 0.92
with wave.open(OUT, "w") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((buf * 32767).astype(np.int16).tobytes())
print("→", OUT, round(DUR, 2), "s")

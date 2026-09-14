# -*- coding: utf-8 -*-
"""나레이션 — tohoku-f01(여성) happy. 컷 길이에 맞춰 낭독 속도만 조정."""
import os, sys, subprocess, wave, math, tempfile, importlib
import numpy as np

M = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "ep01")
OUT = sys.argv[2] if len(sys.argv) > 2 else "audio.wav"
CUTS, NAR = M.CUTS, M.NARRATION
SR, DUR = 48000, CUTS[-1][1]
DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(HERE, "voice", "tohoku-f01-happy.htsvoice")
TMP = tempfile.mkdtemp()


def synth(text, rate):
    t, w = os.path.join(TMP, "t.txt"), os.path.join(TMP, "o.wav")
    open(t, "w", encoding="utf-8").write(text + "\n")
    subprocess.run(["open_jtalk", "-x", DIC, "-m", VOICE, "-r", f"{rate:.3f}",
                    "-jf", "0.62", "-u", "0.0", "-ow", w, t], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(w) as f:
        sr = f.getframerate()
        a = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768
    if sr != SR:                                         # tohoku-f01은 48kHz가 아닐 수 있다
        n = int(len(a) * SR / sr)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    return a


def trim(a, thr=0.004):
    i = np.where(np.abs(a) > thr)[0]
    return a[i[0]:i[-1] + 1] if len(i) else a


buf = np.zeros(int(SR * DUR), np.float32)
for (s, e, *_), text in zip(CUTS, NAR):
    avail = (e - s) - 0.40
    a = trim(synth(text, 1.0))
    rate = 1.0
    if len(a) / SR > avail:
        rate = min(1.45, (len(a) / SR) / avail)
        a = trim(synth(text, rate))
    if len(a) / SR > avail:
        n = int(avail * SR)
        a = a[:n] * np.concatenate([np.ones(max(n - 2400, 0)), np.linspace(1, 0, min(2400, n))])
    a[:480] *= np.linspace(0, 1, 480)
    st = int((s + 0.20) * SR)
    buf[st:st + len(a)] += a
    print(f"{s:5.1f}s len={len(a)/SR:4.2f}s rate={rate:4.2f}  {text[:32]}")

t = np.arange(len(buf)) / SR
pad = np.zeros_like(buf)                                  # 아주 얕은 온기 있는 패드
for f, g in ((98.0, .50), (146.8, .30), (196.0, .20), (293.7, .11)):
    pad += (np.sin(2 * np.pi * f * t + np.sin(t * 0.21) * 0.5) * g).astype(np.float32)
pad *= (0.62 + 0.38 * np.sin(2 * np.pi * 0.06 * t)).astype(np.float32) * 0.021
for s, *_ in CUTS[1:]:                                    # 종이 넘기는 소리
    n = int(0.22 * SR)
    st = max(int((s - 0.05) * SR), 0)
    tt = np.arange(n) / SR
    rng = np.random.default_rng(int(s * 13))
    imp = (rng.normal(0, 1, n) * np.exp(-tt * 26) * 0.030).astype(np.float32)
    imp = np.convolve(imp, np.hanning(90) / 45, "same").astype(np.float32)
    pad[st:st + n] += imp[:len(pad) - st]
pad[:SR] *= np.linspace(0, 1, SR)
pad[-int(SR * 1.2):] *= np.linspace(1, 0, int(SR * 1.2))
buf += pad
buf = np.tanh(buf * 1.12) * 0.94
buf = buf / max(np.max(np.abs(buf)), 1e-6) * 0.93
with wave.open(OUT, "w") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((buf * 32767).astype(np.int16).tobytes())
print("→", OUT, round(DUR, 2), "s")

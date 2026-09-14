# -*- coding: utf-8 -*-
"""나레이션(오프라인 TTS) + 종이 넘김 효과음 + 저음 패드 → 60초 트랙."""
import os, sys, subprocess, wave, math, tempfile, importlib
import numpy as np
_m = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "ep01")
CUTS, NARRATION = _m.CUTS, _m.NARRATION

SR, DUR = 48000, 60.0
DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
TMP = tempfile.mkdtemp()


def synth(text, rate):
    t = os.path.join(TMP, "t.txt")
    w = os.path.join(TMP, "o.wav")
    open(t, "w", encoding="utf-8").write(text + "\n")
    subprocess.run(["open_jtalk", "-x", DIC, "-m", VOICE, "-r", f"{rate:.3f}",
                    "-jf", "0.6", "-ow", w, t], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(w) as f:
        a = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32768.0
    return a


def trim(a, thr=0.004):
    idx = np.where(np.abs(a) > thr)[0]
    return a[idx[0]:idx[-1] + 1] if len(idx) else a


buf = np.zeros(int(SR * DUR), np.float32)
report = []
for (s, e, *_), text in zip(CUTS, NARRATION):
    avail = (e - s) - 0.28
    a = trim(synth(text, 1.0))
    rate = 1.0
    if len(a) / SR > avail:                       # 컷 길이에 맞춰 낭독 속도만 조정
        rate = min(1.55, (len(a) / SR) / avail)
        a = trim(synth(text, rate))
    if len(a) / SR > avail:                       # 그래도 넘치면 끝을 페이드
        n = int(avail * SR)
        a = a[:n] * np.concatenate([np.ones(max(n - 2400, 0)), np.linspace(1, 0, min(2400, n))])
    st = int((s + 0.14) * SR)
    a = a * 1.0
    a[:480] *= np.linspace(0, 1, 480)
    buf[st:st + len(a)] += a
    report.append((s, round(len(a) / SR, 2), round(rate, 2), text))

# 종이 넘김 — 하드컷마다 (이 채널의 시그니처 사운드)
rng = np.random.default_rng(3)
for s, *_ in CUTS[1:]:
    n = int(0.16 * SR)
    noise = rng.normal(0, 1, n).astype(np.float32)
    k = np.exp(-np.linspace(0, 1, 240))          # 짧은 필터 → 사각거리는 질감
    noise = np.convolve(noise, k, "same")
    env = np.exp(-np.linspace(0, 11, n))
    st = int((s - 0.05) * SR)
    seg = (noise * env) * 0.085
    buf[max(st, 0):max(st, 0) + n] += seg[:len(buf) - max(st, 0)]

# 저음 패드 — 5음계 지속음, 아주 작게
t = np.arange(len(buf)) / SR
pad = np.zeros_like(buf)
for f, g in [(110.0, .5), (164.81, .32), (220.0, .22), (329.63, .12)]:
    pad += (np.sin(2 * np.pi * f * t) * g).astype(np.float32)
pad *= (0.55 + 0.45 * np.sin(2 * np.pi * 0.08 * t)).astype(np.float32)
pad *= 0.030
pad[:SR] *= np.linspace(0, 1, SR)
pad[-int(SR * 1.5):] *= np.linspace(1, 0, int(SR * 1.5))
buf += pad

buf = np.tanh(buf * 1.12) * 0.94
peak = np.max(np.abs(buf))
buf = buf / peak * 0.92
out = sys.argv[2] if len(sys.argv) > 2 else "audio.wav"
with wave.open(out, "w") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((buf * 32767).astype(np.int16).tobytes())

for s, d, r, tx in report:
    print(f"{s:5.1f}s  len={d:4.2f}s  rate={r:4.2f}  {tx}")
print("→", out)

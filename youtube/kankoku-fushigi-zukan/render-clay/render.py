# -*- coding: utf-8 -*-
"""韓国ふしぎ図鑑 — 1080×1920 / 30fps 렌더러. 레퍼런스(@weirdecon) 레이아웃 규격."""
import re, sys, time, subprocess, importlib
import numpy as np
from PIL import Image, ImageDraw
import clay, scenes, brand
from clay import W, H, BW, BH, font

M = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "ep01")
OUTMP4 = sys.argv[2] if len(sys.argv) > 2 else "out.mp4"
AUDIO = sys.argv[3] if len(sys.argv) > 3 else "audio.wav"
CUTS, EP = M.CUTS, M.EP
FPS = 30
DUR = CUTS[-1][1]
NF = int(FPS * DUR)

GOLD = (232, 196, 78)
SUBC = (252, 252, 250)
NOTEC = (152, 156, 152)
MARGIN = 64
EMPH_Y, SUB_MID, NOTE_Y = 86, 1548, 1862
LH = 76


def atoms(text):
    return re.findall(r"[0-9][0-9,.:→〜%]*(?:年|月|日|時|分|秒|ウォン|円|棟|世紀)?|.", text)


def wrap(text, f, maxw):
    """숫자·단위를 쪼개지 않는 픽셀 기준 줄바꿈. 구두점 경계를 우선한다."""
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    if d.textlength(text, font=f) <= maxw:
        return [text]
    cands = [i + 1 for i, c in enumerate(text) if c in "、。"]
    for h in sorted(cands, key=lambda i: abs(i - len(text) / 2)):
        a, b = text[:h], text[h:]
        if a and b and d.textlength(a, font=f) <= maxw and d.textlength(b, font=f) <= maxw:
            return [a, b]
    lines, cur = [], ""
    for at in atoms(text):
        if d.textlength(cur + at, font=f) > maxw and cur and at not in "、。）」":
            lines.append(cur); cur = ""
        cur += at
    if cur:
        lines.append(cur)
    return lines


def overlay(emph, sub, note):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if emph:
        d.text((W / 2, EMPH_Y), emph, font=font(50), fill=GOLD, anchor="mm",
               stroke_width=5, stroke_fill=(12, 18, 24))
    if sub:
        f = font(58)
        lines = wrap(sub, f, W - MARGIN * 2)
        y = SUB_MID - (len(lines) - 1) * LH / 2
        for ln in lines:
            d.text((W / 2, y), ln, font=f, fill=SUBC, anchor="mm",
                   stroke_width=8, stroke_fill=(8, 10, 14))
            y += LH
    if note:
        d.text((W / 2, NOTE_Y), note, font=font(26), fill=NOTEC, anchor="mm")
    return lay


def main():
    bgs, lays = {}, {}
    for i, (s, e, kind, emph, sub, note) in enumerate(CUTS):
        bgs[i] = (brand.endcard(W, H, EP["next"], EP["closing"]) if kind == "_endcard"
                  else scenes.SCENES[kind]().convert("RGB"))
        lays[i] = None if kind == "_endcard" else overlay(emph, sub, note)
    print("scenes ready", flush=True)

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUDIO,
           "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.1", "-g", "60",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
           "-movflags", "+faststart", OUTMP4]
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t0, ci = time.time(), 0
    for fr in range(NF):
        t = fr / FPS
        while ci + 1 < len(CUTS) and t >= CUTS[ci + 1][0]:
            ci += 1
        s, e, kind = CUTS[ci][0], CUTS[ci][1], CUTS[ci][2]
        p = (t - s) / (e - s)

        if kind == "_endcard":
            frame = bgs[ci]
        else:
            z = 1.0 + 0.055 * (p if ci % 2 == 0 else 1 - p)          # 켄번스 — 방향 교대
            cw, chh = BW / z, BH / z
            x0 = min(max((BW - cw) / 2 + (p - .5) * 30, 0), BW - cw)
            y0 = min(max((BH - chh) / 2, 0), BH - chh)
            frame = bgs[ci].resize((W, H), Image.BILINEAR,
                                   box=(x0, y0, x0 + cw, y0 + chh)).convert("RGBA")
            frame.alpha_composite(lays[ci])
            frame = frame.convert("RGB")
        pipe.stdin.write(frame.tobytes())
        if fr % 300 == 0:
            print(f"  {fr}/{NF}  {time.time()-t0:.0f}s", flush=True)

    pipe.stdin.close(); pipe.wait()
    print("done", round(time.time() - t0), "s")


main()

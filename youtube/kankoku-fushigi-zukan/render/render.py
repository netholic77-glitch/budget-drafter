# -*- coding: utf-8 -*-
"""EP.01 景福宮 — 1080×1920 / 30fps / 60초 애니매틱 렌더러."""
import re, sys, subprocess, math, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import importlib
import paperart as P
import scenes_ext
from paperart import W, H, BW, BH, font, INK, HANJI, RED, BLUE, GOLD, WHITE

EPMOD = importlib.import_module(sys.argv[1])
CUTS, EP, SRT = EPMOD.CUTS, EPMOD.EP, EPMOD.SRT
OUTFIT = getattr(EPMOD, "OUTFIT", "hanbok")
AUDIO = sys.argv[3] if len(sys.argv) > 3 else "audio.wav"

FPS, DUR = 30, 60.0
NFRAMES = int(FPS * DUR)


def get_scene(kind):
    if kind in scenes_ext.SCENES:
        return scenes_ext.SCENES[kind]()
    return P.scene(kind)

POSES = {
    "point":    [(-8, 105, 0, 0), (-10, 116, 0, -6), (-6, 96, 0, 3)],
    "surprise": [(-118, 118, 0, -10), (-104, 104, 0, 0), (-128, 128, 0, -16)],
    "idle":     [(-8, 8, 0, 0), (-12, 5, 0, -5), (-5, 11, 0, 3)],
    "bow":      [(-14, 14, 5, 10), (-17, 12, 8, 16), (-12, 17, 4, 7)],
    "sign":     [(-8, 58, 0, 0), (-10, 63, 0, -5), (-6, 53, 0, 3)],
    "wave":     [(-8, 124, 0, 0), (-8, 148, 0, -5), (-8, 108, 0, 3)],
}
COLORS = {"gold": GOLD, "red": (232, 74, 74), "white": WHITE}


def load_srt(path):
    out, blocks = [], re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip())
    for b in blocks:
        ln = [l for l in b.strip().split("\n") if l.strip()]
        out.append(" ".join(ln[2:]))
    return out


def wrap_ja(text, n=15):
    """숫자·단위를 쪼개지 않는 일본어 줄바꿈. 「1592年」이 18/67로 갈리지 않게."""
    atoms = re.findall(r"[0-9][0-9,.:→〜]*(?:年|月|日|時|分|秒|ウォン|円)?|.", text)
    # 읽는 호흡 우선: 、 경계에서 갈라 두 줄이 다 들어가면 그대로
    cands = [i + 1 for i, c in enumerate(text) if c in "、。"]
    if cands and len(text) <= n * 2 + 4:
        h = min(cands, key=lambda i: abs(i - len(text) / 2))
        a, b = text[:h], text[h:]
        if a and b and len(a) <= n + 3 and len(b) <= n + 3:
            return [a, b]
    lines, cur = [], ""
    for a in atoms:
        if len(cur) + len(a) > n and cur and a not in "、。）」":
            lines.append(cur); cur = ""
        cur += a
    if cur:
        lines.append(cur)
    return lines


def outlined(d, xy, text, f, fill, stroke=(0, 0, 0), sw=6, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=stroke)


def text_layer(i, sub):
    s, e, kind, big, bigc, pose, sign, shot = CUTS[i]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    top = Image.new("RGBA", (W, 620), (0, 0, 0, 0))          # 상단 가독성 그라데이션
    ta = np.zeros((620, W, 4), np.uint8)
    ta[:, :, 3] = (np.linspace(150, 0, 620)[:, None] * np.ones((1, W))).astype(np.uint8)
    lay.alpha_composite(Image.fromarray(ta), (0, 0))

    d.rounded_rectangle([56, 92, 452, 166], 37, fill=RED)     # 채널 배지
    d.text((254, 129), "韓国、1分旅", font=font(46), fill=WHITE, anchor="mm")
    d.text((476, 129), f"#{EP['no']}  {EP['place']}", font=font(40), fill=WHITE, anchor="lm")

    if i == 1:                                                # 타이틀 카드
        outlined(d, (W // 2, 470), EP["place"], font(210, serif=True), WHITE, INK, 9)
        outlined(d, (W // 2, 620), EP["kana"], font(62), GOLD, INK, 6)
    else:
        y = 268
        for ln in wrap_ja(sub):
            outlined(d, (W // 2, y), ln, font(64), WHITE, INK, 7)
            y += 86
        if big:
            outlined(d, (W // 2, y + 118), big, font(150 if len(big) < 8 else 104),
                     COLORS[bigc], INK, 9)

    bar = Image.new("RGBA", (W, 210), (0, 0, 0, 0))           # 하단 정보 스트립
    bd = ImageDraw.Draw(bar)
    bd.rectangle([0, 44, W, 210], fill=(18, 18, 18, 168))
    bd.text((56, 84), "背景＝紙切り絵（プレビュー）", font=font(30), fill=(226, 222, 214))
    bd.text((56, 128), f"本番実写：{shot}", font=font(30), fill=(176, 186, 196))
    lay.alpha_composite(bar, (0, H - 210))

    p0, p1 = s / DUR, e / DUR                                 # 진행 바
    d.rectangle([0, H - 10, W, H], fill=(255, 255, 255, 46))
    d.rectangle([0, H - 10, int(W * p1), H], fill=(*RED, 235))
    return lay


def main():
    subs = load_srt(SRT)
    print("SRT cues:", len(subs))
    bgs, texts, chars = {}, {}, {}
    for i, (s, e, kind, big, bigc, pose, sign, shot) in enumerate(CUTS):
        bgs[i] = get_scene(kind)
        texts[i] = text_layer(i, subs[i])
        variants = []
        for pz in POSES[pose]:
            c = P.with_shadow(P.hanchan(pz, outfit=OUTFIT, sign=sign))
            th = 640
            c = c.resize((int(c.width * th / c.height), th), Image.LANCZOS)
            variants.append(c)
        chars[i] = variants
    print("assets ready")

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", AUDIO,
           "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-level", "4.1", "-g", "60",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
           "-movflags", "+faststart", sys.argv[2] if len(sys.argv) > 2 else "out.mp4"]
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t0 = time.time()
    ci = 0
    for fr in range(NFRAMES):
        t = fr / FPS
        while ci + 1 < len(CUTS) and t >= CUTS[ci + 1][0]:
            ci += 1
        s, e = CUTS[ci][0], CUTS[ci][1]
        p = (t - s) / (e - s)

        z = 1.0 + 0.06 * p                                     # 켄번즈 미세 줌
        cw, chh = BW / z, BH / z
        dx = (p - 0.5) * 26
        x0 = min(max((BW - cw) / 2 + dx, 0), BW - cw)
        y0 = min(max((BH - chh) / 2, 0), BH - chh)
        frame = bgs[ci].resize((W, H), Image.BILINEAR,
                               box=(x0, y0, x0 + cw, y0 + chh)).convert("RGBA")

        v = chars[ci]
        ch = v[(fr // 3) % len(v)]                             # 2~3프레임 스냅
        slide = 0
        el = t - s
        if el < 0.22:                                          # 화면 밖에서 툭 진입
            slide = int((1 - el / 0.22) * 300)
        frame.alpha_composite(ch, (W - ch.width - 66 + slide, H - 74 - ch.height))
        frame.alpha_composite(texts[ci])

        if el < 0.07:                                          # 하드컷 플래시
            frame = Image.blend(frame, Image.new("RGBA", (W, H), (255, 255, 255, 255)),
                                0.30 * (1 - el / 0.07))
        pipe.stdin.write(frame.convert("RGB").tobytes())
        if fr % 300 == 0:
            print(f"  {fr}/{NFRAMES}  {time.time()-t0:.0f}s", flush=True)

    pipe.stdin.close()
    pipe.wait()
    print("done in", round(time.time() - t0), "s")


main()

# -*- coding: utf-8 -*-
"""클레이(점토) 질감 렌더링 툴킷.
마스크를 흐려 법선을 뽑고 램버트+스페큘러로 음영을 만든다 → 손으로 빚은 볼륨감."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
OS = 1.12
BW, BH = int(W * OS), int(H * OS)

NAVY_T = (8, 30, 42)        # 배경 상단
NAVY_B = (16, 52, 62)       # 배경 하단
FLOOR  = (104, 98, 84)
WARM   = (255, 198, 92)
GOLD   = (232, 194, 74)     # 상단 라벨
WHITE  = (250, 249, 246)

FSANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FSERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
_fc = {}
def font(size, serif=False):
    k = (size, serif)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FSERIF if serif else FSANS, size)
    return _fc[k]


def mask(size=None):
    return Image.new("L", size or (BW, BH), 0)


def shade(msk, color, blur=22, k=70.0, light=(0.60, -0.70, 0.38),
          amb=0.34, spec=0.42, rim=0.30, grain=5.0, seed=0):
    """마스크 → 점토 덩어리. alpha는 원본 마스크(살짝만 부드럽게)."""
    a = np.asarray(msk.filter(ImageFilter.GaussianBlur(blur)), np.float32) / 255.0
    gy, gx = np.gradient(a)
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(a)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    lx, ly, lz = light
    lln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / lln, ly / lln, lz / lln
    lam = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)

    hx, hy, hz = lx, ly, lz + 1.0                                # half-vector (V=0,0,1)
    hn = math.sqrt(hx * hx + hy * hy + hz * hz)
    sp = np.clip(nx * hx / hn + ny * hy / hn + nz * hz / hn, 0, 1) ** 26

    rimt = np.clip(1.0 - nz, 0, 1) ** 3                          # 가장자리 광
    base = np.array(color, np.float32) / 255.0
    warm = np.array(WARM, np.float32) / 255.0
    cool = np.array((72, 118, 140), np.float32) / 255.0

    out = base[None, None, :] * (amb * cool[None, None, :] * 1.6
                                 + (1 - amb) * lam[:, :, None] * warm[None, None, :])
    out += spec * sp[:, :, None] * warm[None, None, :]
    out += rim * rimt[:, :, None] * cool[None, None, :] * 0.9
    if grain:                                                    # 점토 지문 질감
        rng = np.random.default_rng(seed)
        out += rng.normal(0, grain / 255.0, out.shape[:2])[:, :, None]
    out = np.clip(out * 255, 0, 255).astype(np.uint8)

    rgba = np.dstack([out, np.asarray(msk.filter(ImageFilter.GaussianBlur(1.6)), np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def drop(msk, dx=-34, dy=30, blur=34, opacity=0.62):
    """바닥에 지는 그림자."""
    s = msk.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(s, np.float32) * opacity
    img = np.zeros((msk.height, msk.width, 4), np.uint8)
    img[:, :, 3] = np.clip(a, 0, 255).astype(np.uint8)
    out = Image.new("RGBA", (msk.width, msk.height), (0, 0, 0, 0))
    sh = Image.fromarray(img, "RGBA")
    off = Image.new("RGBA", (msk.width, msk.height), (0, 0, 0, 0))
    off.paste(sh, (dx, dy))
    return off


def stage(bulb=(0.62, 0.10), horizon=0.70, floor=FLOOR, wall_t=NAVY_T, wall_b=NAVY_B,
          bulb_power=1.0, seed=1):
    """디오라마 무대 — 네이비 벽 + 전구 + 콘크리트 바닥 + 비네트."""
    yy = np.linspace(0, 1, BH)[:, None]
    wall = np.zeros((BH, BW, 3), np.float32)
    for i in range(3):
        wall[:, :, i] = wall_t[i] + (wall_b[i] - wall_t[i]) * yy

    hy = int(BH * horizon)
    fy = np.linspace(0, 1, BH - hy)[:, None]
    for i in range(3):                                           # 바닥 (멀수록 밝음)
        wall[hy:, :, i] = floor[i] * (0.42 + 0.38 * (1 - fy[:, 0]))[:, None]

    bx, by = BW * bulb[0], BH * bulb[1]
    xs = np.arange(BW)[None, :]
    ys = np.arange(BH)[:, None]
    d = np.sqrt((xs - bx) ** 2 + ((ys - by) * 1.25) ** 2)
    glow = np.exp(-(d / (BW * 0.52)) ** 1.7) * bulb_power        # 넓은 빛무리
    core = np.exp(-(d / (BW * 0.055)) ** 2) * bulb_power
    warm = np.array(WARM, np.float32)
    wall += glow[:, :, None] * warm[None, None, :] * 0.62
    wall += core[:, :, None] * np.array((255, 245, 210), np.float32)[None, None, :]

    vx = (xs - BW / 2) / (BW / 2)
    vy = (ys - BH / 2) / (BH / 2)
    vig = np.clip(1.0 - 0.52 * (vx ** 2 + vy ** 2 * 0.72), 0.30, 1.0)
    wall *= vig[:, :, None]

    px = np.exp(-(((xs - BW * 0.52) / (BW * 0.46)) ** 2))        # 바닥 조명 웅덩이
    py = np.exp(-(((ys - BH * (horizon + 0.14)) / (BH * 0.17)) ** 2))
    wall += (px * py)[:, :, None] * warm[None, None, :] * 0.30

    rng = np.random.default_rng(seed)
    wall += rng.normal(0, 3.2, wall.shape[:2])[:, :, None]
    img = Image.fromarray(np.clip(wall, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(1.2))              # 얕은 심도 — 배경 흐림

    d2 = ImageDraw.Draw(img)                                     # 바닥 균열
    r2 = random.Random(seed + 3)
    for _ in range(5):
        x = r2.uniform(0, BW); y = r2.uniform(hy + 60, BH)
        pts = [(x, y)]
        for _ in range(7):
            x += r2.uniform(-120, 160); y += r2.uniform(-18, 26)
            pts.append((x, y))
        d2.line(pts, fill=(38, 34, 28), width=r2.randint(3, 7))
    return img


def place(base, msk, color, dx=-34, dy=30, sh=0.62, **kw):
    """그림자 → 점토 순으로 올린다."""
    base.alpha_composite(drop(msk, dx, dy, opacity=sh))
    base.alpha_composite(shade(msk, color, **kw))
    return base


def dof(img, amount=7, keep=(0.0, 0.42, 1.0, 1.0)):
    """상단(먼 곳)을 흐려 미니어처 심도를 만든다."""
    bl = img.filter(ImageFilter.GaussianBlur(amount))
    m = np.zeros((BH, BW), np.float32)
    y0, y1 = int(BH * keep[1]), int(BH * keep[3])
    m[:y0] = 1.0
    ramp = np.linspace(1, 0, max(y1 - y0, 1))
    m[y0:y1] = ramp[:, None] if False else ramp[:y1 - y0, None]
    return Image.composite(bl, img, Image.fromarray((m * 255).astype(np.uint8)))

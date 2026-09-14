# -*- coding: utf-8 -*-
"""종이 오려붙이기(paper-cut) 스타일 배경 · ハンちゃん 캐릭터 절차적 생성.
모든 그래픽은 이 코드가 직접 그린 원본이다. 외부 이미지 일절 사용 안 함."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
OS = 1.10                      # 켄번즈 여유분
BW, BH = int(W * OS), int(H * OS)

INK   = (26, 26, 26)
HANJI = (245, 241, 232)
RED   = (193, 39, 45)
BLUE  = (0, 91, 150)
GOLD  = (242, 169, 0)
SKIN  = (240, 214, 186)
WHITE = (252, 250, 245)

FONT_SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
_fc = {}
def font(size, serif=False):
    k = (size, serif)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT_SERIF if serif else FONT_SANS, size)
    return _fc[k]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, top, bottom):
    w, h = size
    col = np.linspace(0, 1, h)[:, None]
    arr = np.zeros((h, w, 3), np.float32)
    for i in range(3):
        arr[:, :, i] = top[i] + (bottom[i] - top[i]) * col
    return Image.fromarray(arr.astype(np.uint8))


def grain(img, amount=7):
    """한지 질감 — 종이 느낌의 핵심."""
    a = np.asarray(img).astype(np.int16)
    rng = np.random.default_rng(7)
    n = rng.normal(0, amount, a.shape[:2])[:, :, None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def ridge(d, y, amp, color, seed, w=BW, steps=9, base=BH):
    """산 능선 — 톱니 폴리곤."""
    rng = random.Random(seed)
    pts = [(0, base)]
    for i in range(steps + 1):
        x = w * i / steps
        yy = y + rng.uniform(-amp, amp) - abs(i - steps / 2) * amp * 0.25
        pts.append((x, yy))
    pts.append((w, base))
    d.polygon(pts, fill=color)


def roof(d, cx, cy, w, h, color):
    """한옥 기와지붕 — 처마 끝이 위로 들린 실루엣."""
    pts = []
    n = 40
    for i in range(n + 1):
        t = i / n
        x = cx - w / 2 + w * t
        sag = math.sin(math.pi * t) * h * 0.30
        flare = ((2 * t - 1) ** 6) * h * 0.55
        pts.append((x, cy - sag - flare))
    pts += [(cx + w / 2, cy + h * 0.30), (cx - w / 2, cy + h * 0.30)]
    d.polygon(pts, fill=color)


def hanok(d, cx, cy, w, h, body=INK, roofc=INK, tiers=1):
    """지붕 + 몸통(기단 포함)."""
    bw = w * 0.72
    d.rectangle([cx - bw / 2, cy, cx + bw / 2, cy + h], fill=body)
    d.rectangle([cx - w * 0.46, cy + h, cx + w * 0.46, cy + h + h * 0.16], fill=body)
    roof(d, cx, cy, w, h * 0.52, roofc)
    if tiers == 2:
        roof(d, cx, cy - h * 0.62, w * 0.80, h * 0.44, roofc)
        d.rectangle([cx - bw * 0.38, cy - h * 0.62, cx + bw * 0.38, cy], fill=body)


def building(d, x, y, w, h, color):
    d.rectangle([x, y, x + w, y + h], fill=color)


def person(d, x, y, s, color):
    """행렬용 인물 실루엣."""
    d.ellipse([x - 11 * s, y - 40 * s, x + 11 * s, y - 18 * s], fill=color)
    d.polygon([(x - 16 * s, y + 40 * s), (x - 13 * s, y - 16 * s),
               (x + 13 * s, y - 16 * s), (x + 16 * s, y + 40 * s)], fill=color)


def pine(d, x, y, s, color):
    d.rectangle([x - 4 * s, y - 40 * s, x + 4 * s, y], fill=color)
    for i, (dx, dy, r) in enumerate([(-26, -52, 26), (24, -60, 24), (0, -80, 30)]):
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s,
                   x + dx * s + r * s, y + dy * s + r * s], fill=color)


# ────────────────────────────────────────────────────────────── 장면 12종
def scene(kind):
    if kind == "city_palace":
        img = gradient((BW, BH), (226, 236, 244), HANJI)
        d = ImageDraw.Draw(img)
        d.ellipse([BW * .62, BH * .10, BW * .62 + 190, BH * .10 + 190], fill=(246, 226, 206))
        ridge(d, BH * .40, 90, (176, 190, 200), 3)
        ridge(d, BH * .47, 70, (140, 158, 172), 11)
        for i, (x, w, h) in enumerate([(40, 120, 420), (180, 95, 300), (860, 140, 480), (1020, 90, 350)]):
            building(d, x, BH * .58 - h, w, h, (108, 124, 138))
        hanok(d, BW / 2, BH * .58, 720, 210, INK, INK, tiers=2)
        d.rectangle([0, BH * .74, BW, BH], fill=(206, 198, 184))

    elif kind == "gate_plaque":
        img = gradient((BW, BH), (60, 48, 44), (32, 26, 24))
        d = ImageDraw.Draw(img)
        roof(d, BW / 2, BH * .30, BW * 1.25, 300, INK)
        for i in range(9):                                     # 서까래
            x = BW * .10 + i * BW * .10
            d.rectangle([x - 16, BH * .33, x + 16, BH * .47], fill=(64, 52, 46))
        d.rectangle([BW * .20, BH * .50, BW * .80, BH * .68], fill=INK)
        d.rectangle([BW * .21, BH * .51, BW * .79, BH * .67], outline=GOLD, width=9)
        f = font(150, serif=True)
        t = "光化門"
        bb = d.textbbox((0, 0), t, font=f)
        d.text(((BW - (bb[2] - bb[0])) / 2, BH * .585 - (bb[3] - bb[1]) / 2 - bb[1]), t, font=f, fill=GOLD)
        d.rectangle([0, BH * .78, BW, BH], fill=(46, 38, 34))

    elif kind == "hall":
        img = gradient((BW, BH), (216, 230, 240), HANJI)
        d = ImageDraw.Draw(img)
        ridge(d, BH * .38, 70, (186, 198, 206), 5)
        hanok(d, BW / 2, BH * .56, 860, 240, INK, RED, tiers=2)
        for i in range(3):                                      # 월대 계단
            y = BH * .745 + i * 34
            d.rectangle([BW * .22 - i * 26, y, BW * .78 + i * 26, y + 34], fill=(198, 190, 176))
        d.rectangle([0, BH * .86, BW, BH], fill=(210, 202, 188))

    elif kind == "fire":
        img = gradient((BW, BH), (126, 28, 26), (232, 148, 60))
        d = ImageDraw.Draw(img)
        rng = random.Random(2)
        for _ in range(90):                                     # 불티 종이조각
            x, y = rng.uniform(0, BW), rng.uniform(BH * .12, BH * .72)
            s = rng.uniform(6, 22)
            d.polygon([(x, y - s), (x + s * .6, y), (x, y + s), (x - s * .6, y)], fill=(250, 214, 140))
        hanok(d, BW / 2, BH * .60, 780, 220, (58, 26, 22), (58, 26, 22), tiers=2)
        d.rectangle([0, BH * .80, BW, BH], fill=(84, 32, 28))

    elif kind == "restore":
        img = gradient((BW, BH), (222, 228, 232), (198, 204, 208))
        d = ImageDraw.Draw(img)
        for x in range(0, BW, 96):                              # 공사 가림막
            d.line([(x, 0), (x, BH * .78)], fill=(176, 184, 190), width=6)
        for y in range(0, int(BH * .78), 96):
            d.line([(0, y), (BW, y)], fill=(176, 184, 190), width=6)
        d.rectangle([BW * .10, BH * .30, BW * .90, BH * .70], fill=(236, 238, 240))
        for k in range(-14, 34):                                # 공사 안전 사선
            x = BW * .10 + k * 62
            d.polygon([(x, BH * .70), (x + 30, BH * .70), (x + 30 + 300, BH * .30), (x + 300, BH * .30)],
                      fill=(246, 214, 120) if k % 2 == 0 else (236, 238, 240))
        d.rectangle([BW * .10, BH * .30, BW * .90, BH * .70], fill=None, outline=(150, 158, 164), width=10)
        d.line([(BW * .86, BH * .12), (BW * .86, BH * .70)], fill=INK, width=14)   # 크레인
        d.line([(BW * .40, BH * .14), (BW * .92, BH * .14)], fill=INK, width=14)
        d.rectangle([0, BH * .78, BW, BH], fill=(190, 186, 176))

    elif kind == "ceremony":
        img = gradient((BW, BH), (236, 226, 206), (212, 198, 176))
        d = ImageDraw.Draw(img)
        hanok(d, BW / 2, BH * .30, 900, 180, (120, 108, 96), (120, 108, 96))
        for i, x in enumerate(np.linspace(BW * .12, BW * .88, 6)):  # 깃발 행렬
            c = [RED, BLUE, GOLD][i % 3]
            d.line([(x, BH * .74), (x, BH * .50)], fill=INK, width=9)
            d.polygon([(x, BH * .50), (x + 86, BH * .545), (x, BH * .59)], fill=c)
            person(d, x - 52, BH * .77, 3.0, INK)
        d.rectangle([0, BH * .82, BW, BH], fill=(198, 184, 164))

    elif kind == "clock":
        img = gradient((BW, BH), (28, 62, 96), (12, 28, 48))
        d = ImageDraw.Draw(img)
        for cx, hh, mm in [(BW * .30, 10, 0), (BW * .70, 2, 0)]:
            cy, r = BH * .42, 170
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=HANJI)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=12)
            for t in range(12):
                a = math.radians(t * 30 - 90)
                d.line([(cx + math.cos(a) * r * .80, cy + math.sin(a) * r * .80),
                        (cx + math.cos(a) * r * .92, cy + math.sin(a) * r * .92)], fill=INK, width=6)
            a = math.radians(hh * 30 - 90)
            d.line([(cx, cy), (cx + math.cos(a) * r * .50, cy + math.sin(a) * r * .50)], fill=RED, width=16)
            d.line([(cx, cy), (cx, cy - r * .74)], fill=INK, width=10)
        roof(d, BW / 2, BH * .70, BW * 1.1, 240, INK)
        d.rectangle([0, BH * .84, BW, BH], fill=(10, 22, 38))

    elif kind == "closed":
        img = gradient((BW, BH), (150, 30, 34), (96, 18, 22))
        d = ImageDraw.Draw(img)
        d.rectangle([BW * .16, BH * .24, BW * .84, BH * .72], fill=(70, 14, 16))
        roof(d, BW / 2, BH * .24, BW * .96, 220, INK)
        d.line([(BW * .22, BH * .30), (BW * .78, BH * .66)], fill=HANJI, width=34)
        d.line([(BW * .78, BH * .30), (BW * .22, BH * .66)], fill=HANJI, width=34)
        d.rectangle([0, BH * .80, BW, BH], fill=(72, 14, 18))

    elif kind == "throne":                                    # 일월오봉도
        img = gradient((BW, BH), (24, 52, 92), (14, 32, 60))
        d = ImageDraw.Draw(img)
        d.ellipse([BW * .12, BH * .14, BW * .12 + 150, BH * .14 + 150], fill=RED)       # 해
        d.ellipse([BW * .72, BH * .14, BW * .72 + 150, BH * .14 + 150], fill=WHITE)     # 달
        peaks = [(.16, .42), (.32, .34), (.50, .27), (.68, .34), (.84, .42)]
        for px, py in peaks:                                                            # 다섯 봉우리
            d.polygon([(BW * px - 190, BH * .62), (BW * px, BH * py), (BW * px + 190, BH * .62)],
                      fill=(38, 84, 74))
        pine(d, BW * .14, BH * .70, 1.5, (22, 58, 48))
        pine(d, BW * .86, BH * .70, 1.5, (22, 58, 48))
        d.rectangle([0, BH * .70, BW, BH], fill=(16, 40, 68))
        for i in range(7):                                                              # 파도
            y = BH * .72 + i * 34
            pts = [(x, y + math.sin(x / 70 + i) * 13) for x in range(0, BW + 20, 20)]
            d.line(pts, fill=(86, 140, 178), width=7)

    elif kind == "pavilion":                                  # 경회루 + 수면 반영
        img = gradient((BW, BH), (206, 226, 238), (150, 186, 208))
        d = ImageDraw.Draw(img)
        ridge(d, BH * .30, 60, (176, 196, 208), 9)
        pav = Image.new("RGBA", (BW, 420), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pav)
        for i in range(8):
            x = BW * .18 + i * BW * .092
            pd.rectangle([x - 13, 200, x + 13, 400], fill=(64, 54, 48))
        pd.rectangle([BW * .12, 380, BW * .88, 412], fill=(78, 66, 58))     # 석축 기단
        roof(pd, BW / 2, 200, BW * .92, 180, INK)
        img.paste(pav, (0, int(BH * .24)), pav)
        water = BH * .62
        d.rectangle([0, water, BW, BH], fill=(120, 162, 190))
        ref = pav.transpose(Image.FLIP_TOP_BOTTOM)
        ref.putalpha(ref.split()[3].point(lambda v: int(v * 0.38)))
        img.paste(ref, (0, int(water - 30)), ref)
        for i in range(9):
            y = water + i * 46
            pts = [(x, y + math.sin(x / 60 + i * .8) * 9) for x in range(0, BW + 20, 20)]
            d.line(pts, fill=(168, 202, 222), width=6)

    elif kind == "hanbok":
        img = gradient((BW, BH), (238, 230, 214), (214, 202, 184))
        d = ImageDraw.Draw(img)
        d.rectangle([0, BH * .34, BW, BH * .62], fill=(190, 176, 156))     # 담장
        for x in range(0, BW, 120):
            roof(d, x + 60, BH * .34, 140, 46, (120, 108, 96))
        for cx, c1, c2 in [(BW * .34, RED, BLUE), (BW * .64, GOLD, RED)]:  # 한복 뒷모습
            d.polygon([(cx - 150, BH * .95), (cx - 66, BH * .735), (cx + 66, BH * .735), (cx + 150, BH * .95)], fill=c1)
            d.polygon([(cx - 68, BH * .745), (cx - 56, BH * .605), (cx + 56, BH * .605), (cx + 68, BH * .745)], fill=c2)
            d.ellipse([cx - 46, BH * .515, cx + 46, BH * .615], fill=INK)
            d.ellipse([cx - 18, BH * .585, cx + 18, BH * .625], fill=(58, 50, 46))
        d.rectangle([0, BH * .93, BW, BH], fill=(186, 174, 156))

    elif kind == "dabotap":
        img = gradient((BW, BH), (16, 20, 40), (52, 44, 72))
        d = ImageDraw.Draw(img)
        rng = random.Random(5)
        for _ in range(90):
            x, y = rng.uniform(0, BW), rng.uniform(0, BH * .58)
            r = rng.uniform(1.5, 4.2)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 226, 242))
        cx, stone, dark = BW / 2, (226, 222, 212), (170, 166, 158)
        d.rectangle([cx - 300, BH * .78, cx + 300, BH * .84], fill=stone)          # 지대석
        d.rectangle([cx - 250, BH * .70, cx + 250, BH * .78], fill=dark)
        for i in range(4):                                                          # 사방 계단
            d.rectangle([cx - 236 + i * 148, BH * .705, cx - 210 + i * 148, BH * .78], fill=(52, 46, 70))
        tiers = [(250, .66, .70), (206, .585, .625), (168, .515, .55), (130, .45, .482)]
        for w, y0, y1 in tiers:
            d.rectangle([cx - w, BH * y0, cx + w, BH * y1], fill=stone)             # 옥개석
            d.rectangle([cx - w * .52, BH * y1, cx + w * .52, BH * (y1 + .035)], fill=dark)  # 탑신
        d.ellipse([cx - 96, BH * .385, cx + 96, BH * .445], fill=stone)             # 앙화
        d.rectangle([cx - 58, BH * .345, cx + 58, BH * .392], fill=dark)
        d.ellipse([cx - 40, BH * .305, cx + 40, BH * .355], fill=stone)             # 보주
        d.rectangle([cx - 9, BH * .265, cx + 9, BH * .315], fill=stone)
        d.rectangle([0, BH * .84, BW, BH], fill=(28, 24, 46))

    else:
        img = Image.new("RGB", (BW, BH), HANJI)

    return grain(img, 6)


# ───────────────────────────────────────────────── ハンちゃん (6피스 컷아웃)
CW, CH = 680, 900
CX = CW // 2
PIV_L, PIV_R = (CX - 92, 372), (CX + 92, 372)     # 어깨 피벗
ARM, AP = 460, 230                                 # 팔 캔버스 / 피벗


def _arm(sleeve):
    """아래로 늘어뜨린 팔. 피벗(AP,AP) 기준 회전. +각도 = 화면 오른쪽으로."""
    a = Image.new("RGBA", (ARM, ARM), (0, 0, 0, 0))
    d = ImageDraw.Draw(a)
    d.rounded_rectangle([AP - 27, AP - 26, AP + 27, AP + 168], 27, fill=sleeve)   # 소매
    d.rounded_rectangle([AP - 23, AP + 146, AP + 23, AP + 218], 23, fill=SKIN)    # 손
    d.line([(AP - 27, AP + 124), (AP + 27, AP + 124)], fill=WHITE, width=6)       # 끝동
    return a


def _hand_xy(pivot, ang, r=196):
    """+각도(반시계)일 때 손끝이 화면 오른쪽으로 가도록."""
    t = math.radians(ang)
    return pivot[0] + r * math.sin(t), pivot[1] + r * math.cos(t)


def hanchan(pose, outfit="hanbok", sign=None):
    """pose = (왼팔각, 오른팔각, 몸기울기, y보정). 트위닝 없음 — 스냅 전용."""
    la, ra, tilt, dy = pose
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = CX
    ROBE = (236, 231, 218)
    sleeve = ROBE if outfit == "dopo" else BLUE

    d.rectangle([cx - 62, 752, cx - 18, 792], fill=WHITE)                                     # 버선
    d.rectangle([cx + 18, 752, cx + 62, 792], fill=WHITE)
    if outfit == "dopo":                                                                       # 도포 — 성곽 편
        d.polygon([(cx - 132, 758), (cx - 98, 356), (cx + 98, 356), (cx + 132, 758)], fill=ROBE, outline=(172, 166, 152), width=7)
        d.line([(cx - 126, 752), (cx + 126, 752)], fill=(196, 190, 176), width=7)
        d.polygon([(cx - 58, 360), (cx, 430), (cx + 58, 360)], fill=(214, 208, 194))           # 깃
        d.line([(cx, 430), (cx + 6, 520)], fill=(214, 208, 194), width=10)
        d.rectangle([cx - 104, 500, cx + 104, 534], fill=BLUE)                                 # 세조대
    else:
        d.polygon([(cx - 150, 760), (cx - 96, 470), (cx + 96, 470), (cx + 150, 760)], fill=RED)   # 치마
        d.line([(cx - 128, 700), (cx + 128, 700)], fill=(158, 30, 36), width=6)
        d.polygon([(cx - 104, 470), (cx - 92, 356), (cx + 92, 356), (cx + 104, 470)], fill=BLUE)  # 저고리
        d.polygon([(cx - 58, 360), (cx, 424), (cx + 58, 360)], fill=WHITE)                        # 동정
        d.line([(cx, 424), (cx + 8, 492)], fill=RED, width=13)                                    # 고름

    for ang, pivot in ((la, PIV_L), (ra, PIV_R)):
        a = _arm(sleeve).rotate(ang, resample=Image.BICUBIC, center=(AP, AP), expand=False)
        img.alpha_composite(a, (pivot[0] - AP, pivot[1] - AP))

    d.ellipse([cx - 86, 190, cx + 86, 372], fill=SKIN)                                         # 머리
    d.chord([cx - 92, 172, cx + 92, 322], 180, 360, fill=INK)                                  # 가르마
    for ox in (-28, 16):                                                                       # 눈
        d.ellipse([cx + ox, 300, cx + ox + 22, 326], fill=INK)
        d.ellipse([cx + ox + 12, 304, cx + ox + 19, 311], fill=WHITE)
    d.arc([cx - 18, 328, cx + 18, 354], 20, 160, fill=(176, 92, 84), width=7)                  # 입
    d.ellipse([cx - 78, 318, cx - 50, 342], fill=(240, 172, 164))                              # 볼
    d.ellipse([cx + 50, 318, cx + 78, 342], fill=(240, 172, 164))
    if outfit in ("gat", "dopo"):
        d.ellipse([cx - 124, 190, cx + 124, 234], fill=(34, 34, 38))
        d.rectangle([cx - 52, 138, cx + 52, 208], fill=(34, 34, 38))
    else:
        d.ellipse([cx - 30, 166, cx + 30, 208], fill=INK)                                      # 쪽머리
        d.ellipse([cx - 12, 175, cx + 12, 199], fill=RED)                                      # 댕기

    if sign:                                                    # 손에 든 안내 팻말
        hx, hy = _hand_xy(PIV_R, ra)
        f = font(56)
        tw = d.textlength(sign, font=f)
        sw = int(max(tw + 70, 180)); sh = 128
        s_img = Image.new("RGBA", (sw, sh + 46), (0, 0, 0, 0))
        sd = ImageDraw.Draw(s_img)
        sd.rectangle([sw // 2 - 10, sh - 20, sw // 2 + 10, sh + 46], fill=(150, 112, 74))
        sd.rounded_rectangle([0, 0, sw - 1, sh], 16, fill=HANJI, outline=INK, width=7)
        sd.text((sw / 2, sh / 2), sign, font=f, fill=RED, anchor="mm")
        sx = min(max(int(hx - sw / 2), 0), CW - sw)
        img.alpha_composite(s_img, (sx, int(hy - sh - 34)))

    if tilt:
        img = img.rotate(tilt, resample=Image.BICUBIC, center=(cx, 780), expand=False)
    if dy:
        o = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        o.alpha_composite(img, (0, int(dy)))
        img = o
    return img


def with_shadow(ch):
    """종이가 사진 위에 얹힌 느낌 — opacity 25% / blur 8 / y+12. 여백은 잘라낸다."""
    pad = 40
    out = Image.new("RGBA", (ch.width + pad * 2, ch.height + pad * 2), (0, 0, 0, 0))
    a = ch.split()[3].point(lambda v: int(v * 0.25))
    blk = Image.new("RGBA", ch.size, (0, 0, 0, 255))
    blk.putalpha(a)
    out.alpha_composite(blk, (pad, pad + 12))
    out = out.filter(ImageFilter.GaussianBlur(8))
    out.alpha_composite(ch, (pad, pad))
    bb = out.getbbox()
    return out.crop(bb) if bb else out

# -*- coding: utf-8 -*-
"""EP.02 仏国寺 · EP.03 水原華城 전용 종이 오려붙이기 장면."""
import math, random
from PIL import Image, ImageDraw
from paperart import (BW, BH, INK, HANJI, RED, BLUE, GOLD, WHITE, font,
                      gradient, grain, ridge, roof, hanok, pine, person)

STONE, STONE_D = (216, 212, 202), (176, 172, 162)


def _new(top, bot):
    img = gradient((BW, BH), top, bot)
    return img, ImageDraw.Draw(img)


def pagoda(d, cx, base_y, tiers, stone=STONE, dark=STONE_D, w0=210):
    """층탑 — 옥개석(넓은 판) + 탑신(좁은 몸). 위로 갈수록 좁아진다."""
    y = base_y
    w = w0
    for i in range(tiers):
        d.rectangle([cx - w, y - 18, cx + w, y], fill=stone)
        bh_ = 92 - i * 12
        d.rectangle([cx - w * .50, y - 18 - bh_, cx + w * .50, y - 18], fill=dark)
        y -= 18 + bh_ + 6
        w *= 0.84
    d.rectangle([cx - 11, y - 118, cx + 11, y], fill=stone)          # 찰주
    for k, r in enumerate((58, 46, 34)):
        yy = y - 34 - k * 30
        d.ellipse([cx - r, yy - 12, cx + r, yy + 12], fill=stone)    # 보륜
    d.ellipse([cx - 26, y - 150, cx + 26, y - 106], fill=stone)      # 보주
    return y


# ───────────────────────────────────────────── EP.02 仏国寺
def ilju_gate():
    img, d = _new((202, 220, 198), (238, 232, 214))
    for x, s in ((.05, 1.0), (.15, .78), (.95, 1.0), (.85, .78)):
        pine(d, BW * x, BH * .66, 2.8 * s, (44, 86, 58))
    d.rectangle([BW * .17, BH * .32, BW * .26, BH * .80], fill=(126, 54, 46))
    d.rectangle([BW * .74, BH * .32, BW * .83, BH * .80], fill=(126, 54, 46))
    roof(d, BW / 2, BH * .32, BW * .92, 200, INK)
    d.rectangle([BW * .34, BH * .355, BW * .66, BH * .455], fill=INK)
    d.rectangle([BW * .35, BH * .362, BW * .65, BH * .448], outline=GOLD, width=7)
    f = font(104, serif=True)
    d.text((BW / 2, BH * .405), "佛國寺", font=f, fill=GOLD, anchor="mm")
    d.rectangle([0, BH * .80, BW, BH], fill=(180, 168, 146))
    for i in range(9):
        y = BH * .82 + i * 46
        d.line([(BW * .30 - i * 42, y), (BW * .70 + i * 42, y)], fill=(168, 156, 134), width=5)
    return grain(img, 6)


def _bridge(sky_top, sky_bot, ground):
    img, d = _new(sky_top, sky_bot)
    ridge(d, BH * .30, 70, (168, 188, 176), 4)
    d.rectangle([0, BH * .54, BW, BH * .78], fill=(198, 192, 178))          # 석축
    for cx in (BW * .27, BW * .73):                                          # 홍예
        d.pieslice([cx - 92, BH * .60, cx + 92, BH * .84], 180, 360, fill=(104, 98, 88))
    d.polygon([(BW * .24, BH * .56), (BW * .50, BH * .26),
               (BW * .66, BH * .26), (BW * .42, BH * .56)], fill=(220, 214, 200))
    for i in range(14):                                                      # 계단 단
        t = i / 13
        x0 = BW * .24 + (BW * .26) * t
        y0 = BH * .56 - (BH * .30) * t
        d.line([(x0, y0), (x0 + BW * .18, y0)], fill=(178, 172, 158), width=7)
    hanok(d, BW * .60, BH * .22, 460, 150, INK, INK)                         # 자하문
    d.rectangle([0, BH * .78, BW, BH], fill=ground)
    return grain(img, 6)


def jahamun():
    return _bridge((212, 228, 238), (238, 232, 216), (184, 178, 162))


def bridge_dusk():
    return _bridge((84, 96, 142), (238, 186, 140), (96, 86, 92))


def stone_base():
    img, d = _new((228, 224, 212), (196, 190, 176))
    rng = random.Random(8)
    for ry in range(4):                                                      # 다듬은 돌 (위)
        for rx in range(7):
            x = rx * BW / 7 + (ry % 2) * BW / 14 - BW / 14
            y = BH * .16 + ry * 88
            d.rectangle([x + 7, y + 7, x + BW / 7 - 7, y + 80], fill=(210, 206, 196))
    d.rectangle([0, BH * .50, BW, BH * .535], fill=(150, 146, 138))
    for i in range(30):                                                      # 자연석 (아래)
        x = rng.uniform(-60, BW + 60)
        y = rng.uniform(BH * .58, BH * .92)
        r = rng.uniform(52, 118)
        c = (152, 148, 140) if i % 2 else (172, 168, 158)
        d.ellipse([x - r, y - r * .70, x + r, y + r * .70], fill=c)
    return grain(img, 7)


def seokgatap():
    img, d = _new((196, 216, 232), (234, 228, 212))
    ridge(d, BH * .32, 60, (176, 196, 186), 6)
    cx = BW / 2
    d.rectangle([cx - 250, BH * .82, cx + 250, BH * .90], fill=STONE)
    d.rectangle([cx - 200, BH * .76, cx + 200, BH * .82], fill=STONE_D)
    pagoda(d, cx, BH * .76, 3)
    d.rectangle([0, BH * .90, BW, BH], fill=(190, 184, 170))
    return grain(img, 6)


def finial():
    """석가탑 상부 클로즈업 — 옥개석 두 층 + 상륜부."""
    img, d = _new((188, 208, 226), (232, 226, 210))
    cx = BW / 2
    d.rectangle([cx - 330, BH * .74, cx + 330, BH * .80], fill=STONE)        # 3층 옥개석
    d.rectangle([cx - 168, BH * .80, cx + 168, BH], fill=STONE_D)
    d.rectangle([cx - 270, BH * .52, cx + 270, BH * .58], fill=STONE)        # 4층(상층) 옥개석
    d.rectangle([cx - 138, BH * .58, cx + 138, BH * .74], fill=STONE_D)
    d.rectangle([cx - 190, BH * .46, cx + 190, BH * .52], fill=STONE)        # 노반
    d.rectangle([cx - 19, BH * .16, cx + 19, BH * .46], fill=STONE_D)        # 찰주
    for k, r in enumerate((132, 108, 86)):                                   # 보륜
        yy = BH * .42 - k * BH * .075
        d.ellipse([cx - r, yy - 22, cx + r, yy + 22], fill=STONE)
        d.ellipse([cx - r, yy - 22, cx + r, yy + 22], outline=STONE_D, width=6)
    d.ellipse([cx - 64, BH * .11, cx + 64, BH * .175], fill=STONE)           # 보주
    return grain(img, 6)


def dabotap_day():
    img, d = _new((198, 218, 234), (236, 230, 214))
    ridge(d, BH * .30, 55, (178, 198, 188), 9)
    cx = BW / 2
    d.rectangle([cx - 280, BH * .82, cx + 280, BH * .90], fill=STONE)
    d.rectangle([cx - 232, BH * .74, cx + 232, BH * .82], fill=STONE_D)
    for i in range(4):
        d.rectangle([cx - 220 + i * 140, BH * .745, cx - 196 + i * 140, BH * .82], fill=(120, 116, 108))
    pagoda(d, cx, BH * .74, 4, w0=196)
    d.rectangle([0, BH * .90, BW, BH], fill=(188, 182, 168))
    return grain(img, 6)


def coin():
    img, d = _new((234, 228, 210), (202, 192, 168))
    cx, cy, r = BW / 2, BH * .45, BW * .37
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(190, 140, 76))
    d.ellipse([cx - r * .93, cy - r * .93, cx + r * .93, cy + r * .93], outline=(148, 102, 54), width=11)
    pagoda(d, cx, cy + r * .36, 3, stone=(160, 112, 60), dark=(134, 92, 46), w0=120)
    d.text((cx, cy + r * .62), "10", font=font(126), fill=(140, 96, 50), anchor="mm")
    return grain(img, 7)


def ticket():
    img, d = _new((226, 232, 236), (198, 204, 208))
    d.rectangle([BW * .12, BH * .32, BW * .88, BH * .76], fill=(238, 234, 224))
    roof(d, BW / 2, BH * .32, BW * .98, 190, INK)
    d.rectangle([BW * .22, BH * .44, BW * .78, BH * .58], fill=(66, 62, 58))
    d.rectangle([BW * .22, BH * .44, BW * .78, BH * .58], outline=(148, 142, 134), width=8)
    d.ellipse([BW * .06, BH * .60, BW * .44, BH * .82], outline=RED, width=15)
    d.text((BW * .25, BH * .71), "無料", font=font(108, serif=True), fill=RED, anchor="mm")
    d.rectangle([0, BH * .82, BW, BH], fill=(186, 190, 192))
    return grain(img, 6)


def dawn_gate():
    img, d = _new((52, 58, 108), (238, 178, 128))
    d.ellipse([BW * .40, BH * .40, BW * .60, BH * .52], fill=(252, 228, 182))
    ridge(d, BH * .50, 80, (98, 94, 124), 7)
    ridge(d, BH * .58, 60, (60, 58, 86), 12)
    roof(d, BW / 2, BH * .66, BW * .84, 200, (26, 24, 36))
    d.rectangle([BW * .28, BH * .66, BW * .72, BH * .88], fill=(26, 24, 36))
    d.pieslice([BW * .40, BH * .74, BW * .60, BH * .94], 180, 360, fill=(238, 184, 132))
    d.rectangle([0, BH * .88, BW, BH], fill=(38, 34, 50))
    return grain(img, 6)


# ───────────────────────────────────────────── EP.03 水原華城
def wallwalk():
    img, d = _new((198, 220, 238), (240, 234, 218))
    ridge(d, BH * .34, 60, (178, 196, 206), 2)
    d.polygon([(BW * .32, BH * .46), (BW * .68, BH * .46),
               (BW * 1.15, BH), (-BW * .15, BH)], fill=(210, 204, 190))
    for i in range(10):                                                    # 여장 (원근)
        t = i / 9
        w = 26 + t * 104
        y = BH * .46 + (BH * .56) * t
        xl = BW * .32 - (BW * .46) * t
        xr = BW * .68 + (BW * .46) * t
        d.rectangle([xl - w, y - w * 1.35, xl, y], fill=(178, 172, 158))
        d.rectangle([xr, y - w * 1.35, xr + w, y], fill=(190, 184, 170))
    for i in range(7):                                                     # 바닥 전돌
        t = (i + 1) / 8
        y = BH * .46 + (BH * .56) * t
        d.line([(BW * .32 - (BW * .46) * t, y), (BW * .68 + (BW * .46) * t, y)],
               fill=(192, 186, 172), width=6)
    return grain(img, 6)


def janganmun():
    img, d = _new((212, 228, 240), (236, 230, 214))
    d.rectangle([0, BH * .56, BW, BH * .80], fill=(200, 194, 180))
    for i in range(11):
        x = i * BW / 11
        d.rectangle([x + 10, BH * .515, x + BW / 11 - 10, BH * .56], fill=(186, 180, 166))
    d.pieslice([BW * .33, BH * .58, BW * .67, BH * .92], 180, 360, fill=(82, 74, 66))
    hanok(d, BW / 2, BH * .30, 780, 205, (120, 46, 44), INK, tiers=2)
    d.rectangle([0, BH * .80, BW, BH], fill=(182, 176, 160))
    return grain(img, 6)


def _wall_curve(sky_top, sky_bot, base, ground, hz=.62):
    img, d = _new(sky_top, sky_bot)
    ridge(d, BH * (hz - .22), 70, (176, 194, 204), 15)
    pts = [(x, BH * hz + math.sin(x / BW * 3.1) * BH * .055) for x in range(0, BW + 20, 20)]
    d.polygon(pts + [(BW, BH), (0, BH)], fill=base)
    for i in range(0, BW, 86):
        y = BH * hz + math.sin(i / BW * 3.1) * BH * .055
        d.rectangle([i + 8, y - 50, i + 72, y - 6], fill=(min(base[0] + 14, 255),
                                                          min(base[1] + 14, 255),
                                                          min(base[2] + 14, 255)))
    d.rectangle([0, BH * .88, BW, BH], fill=ground)
    return img, d


def wall_long():
    img, d = _wall_curve((206, 224, 238), (232, 226, 210), (200, 194, 180), (186, 180, 164))
    return grain(img, 6)


def drone_wall():
    img, d = _wall_curve((188, 212, 234), (228, 222, 206), (204, 198, 184), (170, 182, 158), hz=.74)
    for x, s in ((.10, 1.6), (.88, 1.4), (.24, 1.1)):
        pine(d, BW * x, BH * .92, s, (58, 96, 68))
    return grain(img, 6)


def night_wall():
    img, d = _wall_curve((14, 20, 46), (46, 52, 92), (40, 42, 68), (22, 24, 46), hz=.70)
    rng = random.Random(4)
    for _ in range(80):
        x, y = rng.uniform(0, BW), rng.uniform(0, BH * .44)
        r = rng.uniform(1.4, 4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(226, 224, 240))
    hanok(d, BW / 2, BH * .40, 620, 175, (58, 40, 40), (24, 22, 36), tiers=2)
    for x in (BW * .34, BW * .50, BW * .66):                                # 조명
        d.ellipse([x - 46, BH * .53, x + 46, BH * .60], fill=(248, 206, 128))
    return grain(img, 6)


def haenggung():
    img, d = _new((220, 230, 238), (238, 230, 212))
    for cx in (BW * .13, BW * .87):
        hanok(d, cx, BH * .48, 360, 145, (112, 52, 44), INK)
    hanok(d, BW / 2, BH * .36, 680, 205, (112, 52, 44), INK, tiers=2)
    d.rectangle([BW * .42, BH * .54, BW * .58, BH * .80], fill=(56, 46, 40))
    d.rectangle([0, BH * .80, BW, BH], fill=(202, 194, 178))
    return grain(img, 6)


def _page(bg, paper):
    img = Image.new("RGB", (BW, BH), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([BW * .05, BH * .07, BW * .95, BH * .93], fill=paper,
                outline=(118, 94, 64), width=9)
    for i in range(1, 8):
        x = BW * .05 + (BW * .90) * i / 8
        d.line([(x, BH * .07), (x, BH * .93)], fill=(200, 180, 146), width=4)
    return img, d


def uigwe_page():
    img, d = _page((226, 216, 192), (241, 233, 212))
    d.rectangle([BW * .16, BH * .22, BW * .84, BH * .64], fill=(234, 225, 202),
                outline=(118, 94, 64), width=7)
    cx = BW / 2
    d.rectangle([cx - 200, BH * .26, cx - 184, BH * .60], fill=(120, 88, 56))
    d.rectangle([cx + 184, BH * .26, cx + 200, BH * .60], fill=(120, 88, 56))
    d.rectangle([cx - 212, BH * .245, cx + 212, BH * .268], fill=(120, 88, 56))
    for x in (-110, 0, 110):
        d.ellipse([cx + x - 34, BH * .31, cx + x + 34, BH * .365], fill=(206, 190, 150),
                  outline=(120, 88, 56), width=6)
        d.line([(cx + x, BH * .365), (cx + x, BH * .52)], fill=(120, 88, 56), width=5)
    d.rectangle([cx - 130, BH * .52, cx + 130, BH * .60], fill=(168, 162, 150))
    d.text((BW * .30, BH * .78), "華城城役儀軌", font=font(62, serif=True),
           fill=(96, 74, 50), anchor="mm")
    return grain(img, 5)


def book_close():
    img, d = _page((216, 204, 178), (243, 236, 216))
    f = font(118, serif=True)
    for i, ch in enumerate("華城城役儀軌"):
        d.text((BW * .78, BH * .16 + i * BH * .125), ch, font=f, fill=(74, 58, 40), anchor="mm")
    rng = random.Random(6)
    for col in range(1, 6):                                  # 세로 글줄 (판독 불가 더미)
        x = BW * .78 - col * BW * .135
        for k in range(11):
            h = rng.uniform(26, 52)
            y = BH * .14 + k * BH * .07
            d.rectangle([x - 17, y, x + 17, y + h], fill=(126, 106, 78))
    d.rectangle([BW * .10, BH * .74, BW * .24, BH * .84], fill=RED)          # 인장
    return grain(img, 5)


def geojunggi():
    img = Image.new("RGB", (BW, BH), (238, 230, 208))
    d = ImageDraw.Draw(img)
    grid = (214, 200, 170)
    for x in range(0, BW, 90):
        d.line([(x, 0), (x, BH)], fill=grid, width=3)
    for y in range(0, BH, 90):
        d.line([(0, y), (BW, y)], fill=grid, width=3)
    cx = BW / 2
    wood, dark = (170, 126, 78), (118, 86, 52)
    d.rectangle([cx - 262, BH * .20, cx - 236, BH * .82], fill=wood)
    d.rectangle([cx + 236, BH * .20, cx + 262, BH * .82], fill=wood)
    d.rectangle([cx - 280, BH * .175, cx + 280, BH * .215], fill=dark)
    d.rectangle([cx - 280, BH * .80, cx + 280, BH * .835], fill=dark)
    for x, y in ((-150, .265), (0, .265), (150, .265), (-78, .435), (78, .435)):
        d.ellipse([cx + x - 46, BH * y - 46, cx + x + 46, BH * y + 46],
                  fill=(228, 214, 178), outline=dark, width=8)
        d.ellipse([cx + x - 12, BH * y - 12, cx + x + 12, BH * y + 12], fill=dark)
    for x in (-150, 0, 150):
        d.line([(cx + x, BH * .265), (cx + x, BH * .60)], fill=(96, 74, 52), width=6)
    d.rectangle([cx - 132, BH * .60, cx + 132, BH * .745], fill=(164, 160, 150))
    d.rectangle([cx - 132, BH * .60, cx + 132, BH * .745], outline=(120, 116, 108), width=7)
    return grain(img, 5)


def force_scale():
    """40근 → 2만 5천 근. 지렛대 도해."""
    img, d = _new((242, 234, 212), (210, 200, 174))
    fx, fy = BW * .46, BH * .62
    d.polygon([(fx - 96, fy), (fx + 96, fy), (fx, fy - 158)], fill=INK)      # 받침
    d.line([(BW * .06, fy - 236), (BW * .96, fy - 46)], fill=(120, 88, 56), width=26)
    d.ellipse([BW * .02, fy - 320, BW * .22, fy - 180], fill=BLUE)          # 작은 힘
    d.text((BW * .12, fy - 250), "40", font=font(86), fill=WHITE, anchor="mm")
    d.rectangle([BW * .70, fy - 44, BW * .99, fy + 172], fill=(158, 154, 144))
    d.rectangle([BW * .70, fy - 44, BW * .99, fy + 172], outline=(114, 110, 102), width=8)
    d.text((BW * .845, fy + 64), "25,000", font=font(60), fill=(72, 68, 62), anchor="mm")
    d.rectangle([0, BH * .84, BW, BH], fill=(194, 184, 160))
    return grain(img, 6)


def banghwa():
    img, d = _new((202, 222, 236), (150, 186, 208))
    ridge(d, BH * .28, 55, (176, 196, 208), 9)
    rock = Image.new("RGBA", (BW, 460), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rock)
    rd.polygon([(BW * .18, 460), (BW * .26, 300), (BW * .74, 300), (BW * .82, 460)],
               fill=(168, 162, 150))                                      # 암반
    for i in range(6):
        x = BW * .32 + i * BW * .072
        rd.rectangle([x - 12, 150, x + 12, 300], fill=(72, 60, 52))       # 기둥
    roof(rd, BW / 2, 150, BW * .66, 150, INK)
    img.paste(rock, (0, int(BH * .26)), rock)
    water = BH * .62
    d.rectangle([0, water, BW, BH], fill=(118, 160, 190))
    ref = rock.transpose(Image.FLIP_TOP_BOTTOM)
    ref.putalpha(ref.split()[3].point(lambda v: int(v * 0.34)))
    img.paste(ref, (0, int(water - 24)), ref)
    for i in range(8):
        y = water + i * 48
        pts = [(x, y + math.sin(x / 58 + i * .8) * 9) for x in range(0, BW + 20, 20)]
        d.line(pts, fill=(166, 200, 220), width=6)
    return grain(img, 6)


SCENES = {k: v for k, v in list(globals().items())
          if callable(v) and not k.startswith("_") and k not in
          ("gradient", "grain", "ridge", "roof", "hanok", "pine", "person", "font", "pagoda")}

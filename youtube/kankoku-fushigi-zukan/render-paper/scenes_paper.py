# -*- coding: utf-8 -*-
"""韓国ふしぎ図鑑 #01 景福宮 — 로우폴리 페이퍼크래프트 장면."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import lowpoly as L, figures as F
from lowpoly import (BW, BH, box, taper, gem, plate, wall, prism, Cam, render,
                     paper_grain, font, CREAM, IVORY, SAND, KRAFT, TERRA, SALMON,
                     CLAY, ROSE, NAVY, DEEPNAV, MUSTARD, WOOD, SKIN, INK)

CARD_BG = (23, 32, 45)
CORAL = (232, 135, 60)
CORAL2 = (240, 103, 78)
CARD_TXT = (216, 220, 224)


def _shot(ground, objs, people, cam, bg_col=CREAM, fog=0.0, moods=None):
    img = render(ground, objs, cam, Image.new("RGB", (BW, BH), bg_col))
    for i, p in enumerate(people):
        F.paint_face(img, cam, p[1], p[2], p[3],
                     (moods or {}).get(i, "smile"))
    if fog:
        v = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        vd = ImageDraw.Draw(v)
        for i in range(6):
            vd.ellipse([-BW * .3 + i * BW * .24, BH * (.46 + .02 * i),
                        BW * .6 + i * BW * .24, BH * (.74 + .02 * i)],
                       fill=(238, 232, 222, int(46 * fog)))
        img = img.convert("RGBA")
        img.alpha_composite(v.filter(ImageFilter.GaussianBlur(58)))
        img = img.convert("RGB")
    return paper_grain(img)


def _back(panels):
    return F.backdrop(panels)


PANELS_DAY = [(-20, 34, 44, SAND, 30), (7, 28, 38, CREAM, 28),
              (22, 24, 32, SALMON, 26), (-5, 18, 28, ROSE, 24)]
PANELS_WARM = [(-18, 32, 42, SALMON, 30), (9, 30, 38, SAND, 28),
               (24, 22, 30, ROSE, 26), (-6, 16, 26, CREAM, 24)]
PANELS_DUSK = [(-20, 34, 44, (150, 120, 132), 30), (8, 28, 38, (196, 150, 140), 28),
               (23, 24, 32, (120, 96, 118), 26), (-5, 18, 28, (172, 128, 128), 24)]


# ─────────────────────────────────────── 장면
def c01_hook():
    g = _back(PANELS_DAY) + F.floor_tiles(15, 9.0)
    o = F.hanok(0, 11, 17, 9, 7.0, tiers=2) + F.pillars(0, 11, 12, 9, 7.0, 6)
    p = [F.person(-3.4, -4.7, 0.24, 1.0, TERRA, NAVY, pose="look")]
    o += p[0][0]
    return _shot(g, o, p, Cam((1.7, 9.8, -28.0), (0, 5.1, 0), fov=50), moods={0: "flat"})


def c02_founding():
    g = _back(PANELS_WARM) + F.floor_tiles(15, 9.0)
    o = F.hanok(1, 12, 15, 8, 6.4, tiers=1)
    for i in range(3):                                              # 목재 더미
        for j in range(3 - i):
            o.append(box(5.4, 0.7, 0.9, WOOD, i * 4 + j)
                     .xf(t=(7.5, i * 0.72, -1.2 + j * 1.05 + i * 0.5)))
    p = [F.person(-3.6, -5.5, 0.30, 1.0, MUSTARD, CLAY, pose="raise"),
         F.person(-0.3, -7.7, -0.18, 0.98, TERRA, NAVY, pose="carry")]
    for q in p: o += q[0]
    return _shot(g, o, p, Cam((1.1, 8.8, -26.0), (0, 4.6, 0), fov=52))


def c03_fire():
    g = _back([(-20, 34, 44, (176, 86, 62), 30), (8, 28, 38, (204, 122, 74), 28),
               (23, 24, 32, (150, 66, 52), 26), (-5, 18, 28, (188, 100, 66), 24)])
    g += F.floor_tiles(15, 9.0, c1=(184, 150, 128), c2=(196, 164, 140))
    o = [F.roof(16, 9, 4.2, (78, 56, 52), 3).xf(L.rotz(0.22), (-2, 1.2, 9)),
         F.roof(11, 7, 3.2, (68, 48, 46), 4).xf(L.rotz(-0.30), (7, 0.8, 4)),
         box(18, 1.3, 9, (150, 118, 96), 5).xf(t=(0, 0, 9))]
    r = random.Random(7)
    for _ in range(34):                                             # 불티 종이조각
        s = r.uniform(0.22, 0.6)
        e = box(s, s, s * 0.2, (246, 196, 104), r.randint(0, 99))
        e.xf(L.roty(r.uniform(0, 3)), (r.uniform(-13, 13), r.uniform(3, 17), r.uniform(-6, 12)))
        e.noshadow = True
        o.append(e)
    p = [F.person(-0.8, -7.5, 0.10, 1.0, (120, 78, 66), (86, 62, 60), pose="raise")]
    o += p[0][0]
    return _shot(g, o, p, Cam((1.1, 8.8, -25.0), (0, 4.8, 0), fov=52),
                 bg_col=(196, 110, 74), moods={0: "sad"})


def c04_empty():
    g = _back(PANELS_DAY) + F.floor_tiles(15, 9.0, c1=SAND, c2=(232, 218, 198))
    o = []
    r = random.Random(11)
    for i in range(9):                                              # 주춧돌
        x, z = -9 + (i % 5) * 4.6, 2 + (i // 5) * 5.5
        o.append(gem(1.05, (196, 186, 168), i, n=7, squash=0.42).xf(t=(x, 0, z)))
    for i in range(14):                                             # 잡초
        x, z = r.uniform(-13, 13), r.uniform(-6, 12)
        o.append(taper(0.5, 0.1, r.uniform(1.1, 2.2), 0.5, 0.1, (126, 146, 96), i)
                 .xf(L.rotz(r.uniform(-.3, .3)), (x, 0, z)))
    p = [F.person(4.1, -6.5, -0.42, 0.98, TERRA, NAVY, pose="look")]
    o += p[0][0]
    return _shot(g, o, p, Cam((1.7, 7.8, -24.0), (0, 3.2, 0), fov=52), moods={0: "sad"})


def c05_move():
    g = _back(PANELS_DUSK) + F.floor_tiles(15, 9.0, c1=(226, 208, 192), c2=(238, 224, 208))
    o = F.hanok(13, 16, 13, 7, 5.6, tiers=1)
    o += [box(4.6, 2.6, 3.0, CLAY, 20).xf(t=(0, 3.4, 0)),            # 가마
          F.roof(5.6, 3.8, 1.8, INK, 21).xf(t=(0, 6.0, 0)),
          box(11.0, 0.34, 0.34, WOOD, 22).xf(t=(0, 4.3, 0))]
    p = [F.person(-3.4, -2.5, 0.06, 1.0, MUSTARD, NAVY, pose="carry"),
         F.person(3.4, -2.5, 0.06, 1.0, TERRA, NAVY, pose="carry")]
    for q in p: o += q[0]
    return _shot(g, o, p, Cam((1.1, 8.8, -24.0), (0, 4.0, 0), fov=52))


def c07_rebuild():
    g = _back(PANELS_WARM) + F.floor_tiles(15, 9.0)
    o = F.hanok(2, 13, 15, 8, 6.6, tiers=2)
    o += [box(0.5, 13.0, 0.5, WOOD, 30).xf(t=(-8.5, 0, 1)),          # 도르래 기둥
          box(9.0, 0.5, 0.5, WOOD, 31).xf(t=(-4.2, 12.6, 1)),
          gem(0.9, (168, 160, 148), 32, n=7, squash=0.5).xf(t=(0.2, 12.0, 1)),
          box(0.16, 6.4, 0.16, (150, 140, 126), 33).xf(t=(0.2, 5.6, 1)),
          box(3.4, 1.5, 2.0, WOOD, 34).xf(t=(0.2, 4.0, 1))]
    p = [F.person(-3.6, -6.7, 0.34, 1.0, TERRA, CLAY, pose="raise"),
         F.person(4.7, -5.5, -0.40, 0.96, MUSTARD, NAVY, pose="point")]
    for q in p: o += q[0]
    return _shot(g, o, p, Cam((1.1, 9.8, -26.0), (0, 5.0, 0), fov=52))


def c08_lost():
    g = _back([(-20, 34, 44, (196, 196, 192), 30), (8, 28, 38, (214, 212, 206), 28),
               (23, 24, 32, (178, 182, 182), 26), (-5, 18, 28, (204, 200, 194), 24)])
    g += F.floor_tiles(15, 9.0, c1=(224, 218, 208), c2=(234, 228, 218))
    o = [box(22, 1.5, 11, (198, 190, 174), 40).xf(t=(0, 0, 7)),
         box(17, 1.2, 8.5, (208, 200, 184), 41).xf(t=(0, 1.5, 7))]
    for i in range(6):
        o.append(gem(0.95, (188, 180, 164), 50 + i, n=7, squash=0.42)
                 .xf(t=(-7.5 + i * 3.0, 2.7, 7)))
    p = [F.person(2.8, -7.5, -0.30, 0.98, (150, 150, 148), (104, 110, 116), pose="look")]
    o += p[0][0]
    return _shot(g, o, p, Cam((1.1, 7.8, -25.0), (0, 3.8, 0), fov=52), fog=0.55, moods={0: "sad"})


def c09_restore():
    g = _back(PANELS_DAY) + F.floor_tiles(15, 9.0)
    o = F.hanok(0, 13, 15, 8, 6.6, tiers=2)
    for i in range(6):                                               # 비계
        o.append(box(0.34, 11.0, 0.34, WOOD, 60 + i).xf(t=(-9 + i * 3.6, 0, 6.2)))
    for j in range(4):
        o.append(box(19.0, 0.30, 0.30, WOOD, 70 + j).xf(t=(0, 2.4 + j * 2.7, 6.2)))
    p = [F.person(-4.4, -6.5, 0.34, 1.0, MUSTARD, NAVY, pose="raise"),
         F.person(4.2, -7.1, -0.34, 0.96, TERRA, CLAY, pose="point")]
    for q in p: o += q[0]
    return _shot(g, o, p, Cam((1.1, 9.8, -27.0), (0, 5.2, 0), fov=52))


def c11_today():
    g = _back(PANELS_DAY) + F.floor_tiles(15, 9.0)
    o = F.hanok(1, 12, 16, 8, 6.8, tiers=2) + F.pillars(1, 12, 11, 8, 6.8, 6)
    p = [F.person(-3.7, -5.9, 0.26, 1.02, CLAY, (206, 108, 96), pose="stand"),
         F.person(3.6, -6.7, -0.28, 0.98, NAVY, (92, 124, 168), pose="point")]
    for q in p: o += q[0]
    return _shot(g, o, p, Cam((1.1, 8.8, -26.0), (0, 4.6, 0), fov=52))


# ─────────────────────────────────────── 텍스트 카드
def card(title, items, accent=CORAL):
    img = Image.new("RGB", (BW, BH), CARD_BG)
    d = ImageDraw.Draw(img)
    d.text((BW / 2, BH * .235), title, font=font(96), fill=accent, anchor="mm")
    y = BH * .355
    for it in items:
        d.rectangle([BW * .115, y - 38, BW * .115 + 9, y + 38], fill=accent)
        d.text((BW * .165, y), it, font=font(64), fill=(250, 250, 250), anchor="lm")
        y += BH * .073
    return img


def c06_270():
    return card("270年、空き地", ["1592年 戦乱で全焼", "王は昌徳宮へ移る", "再建は1867年"])


def c10_quarter():
    return card("復元でもどったもの", ["一次復元 1990〜2010", "復元されたのは125棟", "高宗時代の約4分の1"])


SCENES = {"c01_hook": c01_hook, "c02_founding": c02_founding, "c03_fire": c03_fire,
          "c04_empty": c04_empty, "c05_move": c05_move, "c06_270": c06_270,
          "c07_rebuild": c07_rebuild, "c08_lost": c08_lost, "c09_restore": c09_restore,
          "c10_quarter": c10_quarter, "c11_today": c11_today}

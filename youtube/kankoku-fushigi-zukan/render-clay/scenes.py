# -*- coding: utf-8 -*-
"""EP.01 景福宮 — 장면 12컷. 전부 절차적 클레이 디오라마."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import clay, parts as P
from clay import BW, BH, mask, stage, shade, drop, place

# 점토 팔레트
TILE   = (92, 96, 104)        # 기와
WOOD   = (156, 74, 58)       # 단청 기둥·벽
STONE  = (172, 164, 146)     # 기단·주춧돌
EARTH  = (146, 136, 116)
LUMBER = (168, 116, 66)
LEAF   = (92, 116, 72)
SKIN   = (240, 184, 144)
CLOTH  = (150, 128, 92)
HANBOK_R = (178, 62, 58)
HANBOK_B = (56, 92, 130)
IRON   = (120, 122, 128)
CARD_BG = (13, 25, 49)
FACE   = (58, 42, 36)


def L(img, fn, color, far=0, **kw):
    m = mask(); d = ImageDraw.Draw(m); fn(d)
    if far:
        img.alpha_composite(drop(m, opacity=0.34).filter(ImageFilter.GaussianBlur(far)))
        img.alpha_composite(shade(m, color, **kw).filter(ImageFilter.GaussianBlur(far)))
    else:
        place(img, m, color, **kw)
    return img


def faces(img, spec_fn):
    L(img, spec_fn, FACE, blur=5, amb=.55, spec=.10, rim=.05, grain=0)
    return img


def card():
    """플랫 텍스트 카드 배경 — 레퍼런스의 네이비 카드와 동일 계열."""
    img = Image.new("RGB", (BW, BH), CARD_BG)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([-BW * .35, BH * .02, BW * .72, BH * .52], fill=(255, 255, 255, 9))
    d.ellipse([BW * .45, BH * .66, BW * 1.5, BH * 1.12], fill=(255, 255, 255, 7))
    return img.convert("RGBA")


# ─────────────────────────────────────────────── 12컷
def _fig(img, specs):
    """피규어는 옷 → 피부 순으로 두 레이어. 주역이므로 크고 선명하게."""
    L(img, lambda d: [P.figure(d, *a, part="cloth", **k) for a, k in specs],
      specs[0][1].pop("_cloth", None) or CLOTH, amb=.30, spec=.50)
    return img


def c01_hook():
    """밤. 광화문 앞에 선 여행자가 올려다본다."""
    img = stage(bulb=(0.68, 0.08), horizon=0.70).convert("RGBA")
    L(img, lambda d: [P.hall(d, BW * .18, BH * .66, 620, 210, 1),
                      P.hall(d, BW * .86, BH * .66, 620, 210, 1)], TILE, far=12)
    L(img, lambda d: P.hall(d, BW * .52, BH * .70, 1180, 400, 2), TILE, far=6)
    L(img, lambda d: P.pillars(d, BW * .52, BH * .70, 820, 300, 6), WOOD, far=6)
    L(img, lambda d: P.figure(d, BW * .44, BH * .90, 2.6, "look", part="cloth"),
      CLOTH, amb=.30, spec=.50)
    L(img, lambda d: P.figure(d, BW * .44, BH * .90, 2.6, "look", part="skin"),
      SKIN, amb=.30, spec=.52)
    L(img, lambda d: P.figure(d, BW * .44, BH * .90, 2.6, "look", part="face", mood="flat"), FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    return img


def c02_founding():
    """1395 — 짓는 사람들."""
    img = stage(bulb=(0.26, 0.10), horizon=0.72).convert("RGBA")
    L(img, lambda d: P.hall(d, BW * .62, BH * .70, 1240, 430, 2), TILE, far=9)
    L(img, lambda d: P.pillars(d, BW * .62, BH * .70, 880, 320, 6), WOOD, far=9)
    L(img, lambda d: P.timber(d, BW * .78, BH * .90, 1.5, 3), LUMBER, far=2)
    L(img, lambda d: [P.figure(d, BW * .30, BH * .88, 2.4, "carry", part="cloth"),
                      P.figure(d, BW * .62, BH * .91, 2.6, "raise", part="cloth")],
      CLOTH, amb=.30, spec=.50)
    L(img, lambda d: [P.figure(d, BW * .30, BH * .88, 2.4, "carry", part="skin"),
                      P.figure(d, BW * .62, BH * .91, 2.6, "raise", part="skin")],
      SKIN, amb=.30, spec=.52)
    L(img, lambda d: [P.figure(d, BW * .30, BH * .88, 2.4, "carry", part="face"),
                      P.figure(d, BW * .62, BH * .91, 2.6, "raise", part="face")], FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    return img


def c03_fire():
    """1592 — 전소."""
    img = stage(bulb=(0.52, 0.14), horizon=0.72, wall_t=(70, 22, 14), wall_b=(132, 52, 22),
                floor=(104, 62, 40), bulb_power=1.45).convert("RGBA")
    L(img, lambda d: [P.roof(d, BW * .36, BH * .60, 900, 300),
                      P.roof(d, BW * .72, BH * .70, 700, 240)], (58, 32, 26), far=6)
    L(img, lambda d: d.rectangle([BW * .08, BH * .74, BW * .92, BH * .81], fill=255),
      (76, 44, 32), far=2)
    L(img, lambda d: P.figure(d, BW * .50, BH * .90, 2.5, "raise", part="cloth"),
      (66, 40, 32), amb=.24, spec=.62)
    L(img, lambda d: P.figure(d, BW * .50, BH * .90, 2.5, "raise", part="skin"),
      (188, 116, 80), amb=.26, spec=.60)
    L(img, lambda d: P.figure(d, BW * .50, BH * .90, 2.5, "raise", part="face", mood="sad"), FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    em = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))                   # 불티 (발광체)
    ed = ImageDraw.Draw(em)
    r = random.Random(4)
    for _ in range(150):
        x, y = r.uniform(0, BW), r.uniform(BH * .04, BH * .78)
        s = r.uniform(4, 15)
        ed.ellipse([x - s, y - s, x + s, y + s], fill=(255, 206, 118, r.randint(120, 235)))
    img.alpha_composite(em.filter(ImageFilter.GaussianBlur(5)))
    return img


def c04_empty():
    """빈터 — 주춧돌과 잡초뿐."""
    img = stage(bulb=(0.60, 0.09), horizon=0.54).convert("RGBA")
    L(img, lambda d: [P.stump(d, BW * (.14 + .19 * i), BH * (.62 + .02 * (i % 3)), 74)
                      for i in range(5)], STONE, far=5)
    L(img, lambda d: [P.stump(d, BW * (.20 + .21 * i), BH * .80, 122) for i in range(4)], STONE)
    L(img, lambda d: [P.stump(d, BW * (.30 + .42 * i), BH * .97, 168) for i in range(2)],
      STONE, far=3)
    L(img, lambda d: [P.grass(d, BW * (.08 + .11 * i), BH * (.86 + .03 * (i % 2)), 2.2, i)
                      for i in range(8)], LEAF)
    L(img, lambda d: P.figure(d, BW * .74, BH * .84, 2.1, "look", part="cloth"),
      CLOTH, amb=.30, spec=.50, far=1)
    L(img, lambda d: P.figure(d, BW * .74, BH * .84, 2.1, "look", part="skin"),
      SKIN, amb=.30, spec=.52, far=1)
    L(img, lambda d: P.figure(d, BW * .74, BH * .84, 2.1, "look", part="face", mood="sad"),
      FACE, blur=4, amb=.58, spec=.08, rim=.04, grain=0, far=1)
    return img


def c05_move():
    """왕은 다른 궁으로 옮겨간다."""
    img = stage(bulb=(0.22, 0.11), horizon=0.71).convert("RGBA")
    L(img, lambda d: P.hall(d, BW * .82, BH * .68, 900, 320, 2), TILE, far=14)
    L(img, lambda d: P.palanquin(d, BW * .50, BH * .80, 2.1), WOOD, far=1)
    L(img, lambda d: [P.figure(d, BW * .13, BH * .90, 2.3, "carry", part="cloth"),
                      P.figure(d, BW * .87, BH * .90, 2.3, "carry", part="cloth")],
      CLOTH, amb=.30, spec=.50)
    L(img, lambda d: [P.figure(d, BW * .13, BH * .90, 2.3, "carry", part="skin"),
                      P.figure(d, BW * .87, BH * .90, 2.3, "carry", part="skin")],
      SKIN, amb=.30, spec=.52)
    L(img, lambda d: [P.figure(d, BW * .13, BH * .90, 2.3, "carry", part="face"),
                      P.figure(d, BW * .87, BH * .90, 2.3, "carry", part="face")], FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    return img


def c06_270():
    """카드 — 모래시계."""
    img = card()
    L(img, lambda d: P.hourglass(d, BW * .5, BH * .48, 2.0, part="sand"), (226, 176, 84),
      blur=12, amb=.52, spec=.34, rim=.12, grain=0)
    L(img, lambda d: P.hourglass(d, BW * .5, BH * .48, 2.0, part="glass"), (178, 190, 196),
      blur=12, amb=.44, spec=.55, rim=.28, grain=0)
    return img


def c07_rebuild():
    """1867 — 중건."""
    img = stage(bulb=(0.74, 0.09), horizon=0.73).convert("RGBA")
    L(img, lambda d: P.hall(d, BW * .56, BH * .71, 1260, 440, 2), TILE, far=8)
    L(img, lambda d: P.pillars(d, BW * .56, BH * .71, 880, 330, 6), WOOD, far=8)
    L(img, lambda d: [d.rectangle([BW * .13, BH * .14, BW * .165, BH * .56], fill=255),
                      d.rectangle([BW * .13, BH * .14, BW * .60, BH * .173], fill=255),
                      P.pulley(d, BW * .575, BH * .205, 62)], IRON, far=2)
    L(img, lambda d: d.line([(BW * .575, BH * .26), (BW * .575, BH * .62)], fill=255, width=14),
      (204, 184, 148), far=2)
    L(img, lambda d: P.timber(d, BW * .575, BH * .72, 1.5, 9), LUMBER, far=2)
    L(img, lambda d: P.figure(d, BW * .22, BH * .90, 2.5, "raise", part="cloth"),
      CLOTH, amb=.30, spec=.50)
    L(img, lambda d: P.figure(d, BW * .22, BH * .90, 2.5, "raise", part="skin"),
      SKIN, amb=.30, spec=.52)
    L(img, lambda d: P.figure(d, BW * .22, BH * .90, 2.5, "raise", part="face"), FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    return img


def c08_lost():
    """20세기 — 다시 사라진다."""
    img = stage(bulb=(0.46, 0.07), horizon=0.60, wall_t=(10, 26, 34), wall_b=(24, 48, 56),
                bulb_power=0.58).convert("RGBA")
    L(img, lambda d: [d.rectangle([BW * .02, BH * .70, BW * .68, BH * .82], fill=255),
                      d.rectangle([BW * .08, BH * .61, BW * .62, BH * .70], fill=255)],
      (150, 144, 128), far=3)
    L(img, lambda d: [P.stump(d, BW * (.13 + .12 * i), BH * .598, 54) for i in range(5)],
      STONE, far=2)
    L(img, lambda d: P.figure(d, BW * .74, BH * .93, 2.5, "look", part="cloth"),
      (78, 84, 86), amb=.26, spec=.34)
    L(img, lambda d: P.figure(d, BW * .74, BH * .93, 2.5, "look", part="skin"),
      (182, 150, 130), amb=.26, spec=.36)
    L(img, lambda d: P.figure(d, BW * .74, BH * .93, 2.5, "look", part="face", mood="sad"), FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    fog = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fog)
    for i in range(7):
        fd.ellipse([-BW * .2 + i * BW * .20, BH * (.54 + .014 * i), BW * .5 + i * BW * .20,
                    BH * (.78 + .014 * i)], fill=(150, 180, 194, 30))
    img.alpha_composite(fog.filter(ImageFilter.GaussianBlur(52)))
    return img


def c09_restore():
    """1990~ 복원."""
    img = stage(bulb=(0.64, 0.09), horizon=0.74).convert("RGBA")
    L(img, lambda d: P.hall(d, BW * .52, BH * .72, 1180, 410, 2), TILE, far=10)
    L(img, lambda d: P.scaffold(d, BW * .52, BH * .74, 1240, 700), LUMBER, far=3)
    L(img, lambda d: [P.figure(d, BW * .17, BH * .90, 2.3, "raise", part="cloth"),
                      P.figure(d, BW * .83, BH * .90, 2.2, "point", part="cloth")],
      CLOTH, amb=.30, spec=.50)
    L(img, lambda d: [P.figure(d, BW * .17, BH * .90, 2.3, "raise", part="skin"),
                      P.figure(d, BW * .83, BH * .90, 2.2, "point", part="skin")],
      SKIN, amb=.30, spec=.52)
    L(img, lambda d: [P.figure(d, BW * .17, BH * .90, 2.3, "raise", part="face"),
                      P.figure(d, BW * .83, BH * .90, 2.2, "point", part="face")], FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    return img


def c10_quarter():
    """카드 — 8×8 중 16칸(4분의 1)."""
    img = card()
    cols = rows = 8
    span = BW * .70
    cw = span / cols
    x0, y0 = (BW - span) / 2, BH * .30
    m1 = mask(); d1 = ImageDraw.Draw(m1)
    m2 = mask(); d2 = ImageDraw.Draw(m2)
    for r in range(rows):
        for c in range(cols):
            x, y = x0 + c * cw, y0 + r * cw
            box = [x + 8, y + 8, x + cw - 8, y + cw - 8]
            (d1 if (r >= rows // 2 and c < cols // 2) else d2).rounded_rectangle(box, 14, fill=255)
    img.alpha_composite(shade(m2, (44, 58, 92), blur=10, amb=.66, spec=.10, rim=.08, grain=0))
    img.alpha_composite(shade(m1, (236, 184, 58), blur=10, amb=.52, spec=.38, rim=.16, grain=0))
    return img


def c11_today():
    """오늘 — 한복 관람객."""
    img = stage(bulb=(0.34, 0.09), horizon=0.72).convert("RGBA")
    L(img, lambda d: P.hall(d, BW * .62, BH * .70, 1220, 420, 2), TILE, far=11)
    L(img, lambda d: P.pillars(d, BW * .62, BH * .70, 860, 310, 6), WOOD, far=11)
    L(img, lambda d: P.figure(d, BW * .30, BH * .90, 2.5, "stand", part="cloth"),
      HANBOK_R, amb=.30, spec=.50)
    L(img, lambda d: P.figure(d, BW * .70, BH * .90, 2.4, "point", part="cloth"),
      HANBOK_B, amb=.30, spec=.50)
    L(img, lambda d: [P.figure(d, BW * .30, BH * .90, 2.5, "stand", part="skin"),
                      P.figure(d, BW * .70, BH * .90, 2.4, "point", part="skin")],
      SKIN, amb=.30, spec=.52)
    L(img, lambda d: [P.figure(d, BW * .30, BH * .90, 2.5, "stand", part="face"),
                      P.figure(d, BW * .70, BH * .90, 2.4, "point", part="face")], FACE, blur=5, amb=.58, spec=.08, rim=.04, grain=0)
    return img


SCENES = {"c01_hook": c01_hook, "c02_founding": c02_founding, "c03_fire": c03_fire,
          "c04_empty": c04_empty, "c05_move": c05_move, "c06_270": c06_270,
          "c07_rebuild": c07_rebuild, "c08_lost": c08_lost, "c09_restore": c09_restore,
          "c10_quarter": c10_quarter, "c11_today": c11_today}

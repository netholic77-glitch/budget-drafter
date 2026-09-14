# -*- coding: utf-8 -*-
"""장면 부품 — 전부 마스크(L)에 그린다. 색과 음영은 clay.shade가 입힌다."""
import math, random
from PIL import ImageDraw
from clay import BW, BH


def roof(d, cx, cy, w, h, v=255):
    """한옥 기와지붕 — 처마 끝이 들린 실루엣."""
    pts, n = [], 44
    for i in range(n + 1):
        t = i / n
        x = cx - w / 2 + w * t
        sag = math.sin(math.pi * t) * h * 0.30
        flare = ((2 * t - 1) ** 6) * h * 0.60
        pts.append((x, cy - sag - flare))
    pts += [(cx + w / 2, cy + h * 0.26), (cx - w / 2, cy + h * 0.26)]
    d.polygon(pts, fill=v)


def hall(d, cx, base_y, w, h, tiers=1, v=255):
    """전각 — 기단 + 몸통 + 지붕."""
    bw = w * 0.70
    d.rectangle([cx - w * 0.50, base_y, cx + w * 0.50, base_y + h * 0.15], fill=v)   # 기단
    d.rectangle([cx - bw / 2, base_y - h, cx + bw / 2, base_y], fill=v)
    roof(d, cx, base_y - h, w, h * 0.50, v)
    if tiers == 2:
        d.rectangle([cx - bw * 0.36, base_y - h * 1.62, cx + bw * 0.36, base_y - h], fill=v)
        roof(d, cx, base_y - h * 1.62, w * 0.80, h * 0.42, v)


def pillars(d, cx, base_y, w, h, n=6, v=255):
    for i in range(n):
        x = cx - w / 2 + w * (i + 0.5) / n
        d.rectangle([x - w * 0.022, base_y - h, x + w * 0.022, base_y], fill=v)


def figure(d, cx, base_y, s=1.0, pose="stand", hat=None, v=255, part="all", mood="smile"):
    """클레이 인물. s=1 → 키 약 300px. part: cloth / skin / face."""
    hh = 300 * s
    hr = 50 * s
    hy = base_y - hh + hr
    sh_y = hy + hr * 0.86                                          # 어깨선
    hip_y = base_y - 118 * s
    skin = part in ("all", "skin")
    cloth = part in ("all", "cloth")
    face = part in ("all", "face")

    if face:                                                        # 눈·입 (어두운 점토)
        for sx in (-1, 1):
            d.ellipse([cx + sx * 21 * s - 8.5 * s, hy + 2 * s - 11 * s,
                       cx + sx * 21 * s + 8.5 * s, hy + 2 * s + 11 * s], fill=v)
        w = max(int(6 * s), 3)
        if mood == "smile":
            d.arc([cx - 19 * s, hy + 16 * s, cx + 19 * s, hy + 40 * s], 15, 165, fill=v, width=w)
        elif mood == "sad":
            d.arc([cx - 19 * s, hy + 24 * s, cx + 19 * s, hy + 48 * s], 195, 345, fill=v, width=w)
        else:
            d.line([(cx - 15 * s, hy + 30 * s), (cx + 15 * s, hy + 30 * s)], fill=v, width=w)
        return
    if skin:
        d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=v)     # 머리
    if cloth:
        d.polygon([(cx - 54 * s, hip_y), (cx - 44 * s, sh_y),
                   (cx + 44 * s, sh_y), (cx + 54 * s, hip_y)], fill=v)   # 몸통
        for sx in (-1, 1):                                          # 다리
            d.rounded_rectangle([cx + sx * 24 * s - 20 * s, hip_y - 8 * s,
                                 cx + sx * 24 * s + 20 * s, base_y], 18 * s, fill=v)
            d.ellipse([cx + sx * 24 * s - 26 * s, base_y - 22 * s,
                       cx + sx * 24 * s + 26 * s, base_y + 12 * s], fill=v)  # 신발

    ang = {"stand": (98, 84), "point": (100, 4), "look": (96, 78),
           "carry": (52, 128), "pull": (40, 140), "raise": (-14, 194)}[pose]
    for sx, a in ((-1, ang[0]), (1, ang[1])):
        px, py = cx + sx * 46 * s, sh_y + 16 * s
        t = math.radians(a if sx > 0 else 180 - a)
        ex, ey = px + math.cos(t) * 88 * s, py + math.sin(t) * 88 * s
        if cloth:
            d.line([(px, py), (ex, ey)], fill=v, width=int(34 * s))
            d.ellipse([px - 17 * s, py - 17 * s, px + 17 * s, py + 17 * s], fill=v)
        if skin:
            d.ellipse([ex - 19 * s, ey - 19 * s, ex + 19 * s, ey + 19 * s], fill=v)
    if not cloth:
        return
    if hat == "gat":
        d.ellipse([cx - hr * 1.9, hy - hr * 1.08, cx + hr * 1.9, hy - hr * 0.42], fill=v)
        d.rounded_rectangle([cx - hr * 0.74, hy - hr * 2.0, cx + hr * 0.74, hy - hr * 0.66],
                            12 * s, fill=v)
    elif hat == "crown":
        d.rectangle([cx - hr * 0.9, hy - hr * 1.72, cx + hr * 0.9, hy - hr * 0.86], fill=v)
        d.ellipse([cx - hr * 1.32, hy - hr * 1.02, cx + hr * 1.32, hy - hr * 0.5], fill=v)


def stump(d, x, y, r, v=255):
    """주춧돌."""
    d.ellipse([x - r, y - r * 0.42, x + r, y + r * 0.42], fill=v)
    d.rectangle([x - r * 0.92, y - r * 0.30, x + r * 0.92, y + r * 0.30], fill=v)


def grass(d, x, y, s, seed=0, v=255):
    r = random.Random(seed)
    for _ in range(7):
        h = r.uniform(40, 96) * s
        dx = r.uniform(-26, 26) * s
        d.line([(x + dx, y), (x + dx + r.uniform(-24, 24) * s, y - h)],
               fill=v, width=max(int(6 * s), 3))


def pine(d, x, y, s, v=255):
    d.rectangle([x - 7 * s, y - 62 * s, x + 7 * s, y], fill=v)
    for dx, dy, r in ((-34, -78, 34), (32, -90, 30), (0, -118, 40)):
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s,
                   x + dx * s + r * s, y + dy * s + r * s], fill=v)


def palanquin(d, cx, base_y, s=1.0, v=255):
    """가마 — 상자 + 지붕 + 멜대."""
    w, h = 300 * s, 190 * s
    d.rounded_rectangle([cx - w / 2, base_y - h, cx + w / 2, base_y], 18 * s, fill=v)
    roof(d, cx, base_y - h, w * 1.20, h * 0.52, v)
    d.rectangle([cx - w * 1.05, base_y - h * 0.72, cx + w * 1.05, base_y - h * 0.62], fill=v)


def timber(d, cx, base_y, s=1.0, seed=0, v=255):
    """목재 더미."""
    r = random.Random(seed)
    for row in range(3):
        for i in range(4 - row):
            x = cx - (3 - row) * 46 * s + i * 92 * s
            y = base_y - row * 50 * s
            d.rounded_rectangle([x - 44 * s, y - 46 * s, x + 44 * s, y], 14 * s, fill=v)


def scaffold(d, cx, base_y, w, h, v=255):
    """복원 공사 비계."""
    for i in range(5):
        x = cx - w / 2 + w * i / 4
        d.rectangle([x - 8, base_y - h, x + 8, base_y], fill=v)
    for j in range(4):
        y = base_y - h * (j + 1) / 4
        d.rectangle([cx - w / 2 - 8, y - 8, cx + w / 2 + 8, y + 8], fill=v)


def pulley(d, cx, cy, r, v=255):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=v)


def hourglass(d, cx, cy, s=1.0, v=255, part="glass"):
    """모래시계. part=glass(유리·틀) / sand(모래)."""
    w, h, t = 240 * s, 270 * s, 20 * s
    if part == "glass":
        d.rounded_rectangle([cx - w * .70, cy - h - t, cx + w * .70, cy - h + t], t, fill=v)
        d.rounded_rectangle([cx - w * .70, cy + h - t, cx + w * .70, cy + h + t], t, fill=v)
        for sx in (-1, 1):
            d.rounded_rectangle([cx + sx * w * .64 - t * .5, cy - h, cx + sx * w * .64 + t * .5,
                                 cy + h], t * .5, fill=v)
        for sy in (-1, 1):                                          # 유리 구
            d.polygon([(cx - w * .52, cy + sy * h * .92), (cx + w * .52, cy + sy * h * .92),
                       (cx + t * .5, cy), (cx - t * .5, cy)], fill=v)
    else:
        d.polygon([(cx - w * .40, cy + h * .34), (cx + w * .40, cy + h * .34),
                   (cx + t * .35, cy + t), (cx - t * .35, cy + t)], fill=v)
        d.polygon([(cx - w * .46, cy + h * .90), (cx + w * .46, cy + h * .90),
                   (cx + w * .30, cy + h * .34), (cx - w * .30, cy + h * .34)], fill=v)
        d.rectangle([cx - t * .18, cy, cx + t * .18, cy + h * .34], fill=v)

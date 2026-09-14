# -*- coding: utf-8 -*-
"""종이 인물 · 건축 부품. 전부 로우폴리 메시."""
import math
import numpy as np
from PIL import ImageDraw
import lowpoly as L
from lowpoly import Mesh, box, taper, gem, plate, wall, prism, roty, SKIN, INK


def _dim(c, k=0.86):
    return tuple(int(v * k) for v in c)


def person(x, z, rot=0.0, s=1.0, top=L.TERRA, bottom=L.NAVY, hair=L.INK,
           pose="stand", seed=0):
    """키 약 7*s. 반환: (메시들, 머리 월드좌표, 머리 반지름, 정면각)."""
    ms = []
    R = roty(rot)

    def add(m, t):
        m.xf(R, (0, 0, 0))
        m.v += np.asarray([x, 0, z]) + np.asarray(R) @ np.asarray(t, float)
        ms.append(m)

    leg_h = 2.9 * s if pose != "sit" else 1.15 * s
    for sx in (-1, 1):
        add(taper(0.86 * s, 0.76 * s, leg_h, 0.82 * s, 0.72 * s, bottom, seed + sx),
            (sx * 0.42 * s, 0, 0))
        add(box(0.80 * s, 0.30 * s, 1.15 * s, L.CLAY, seed + 2 + sx),
            (sx * 0.42 * s, 0, 0.30 * s))                                  # 신발
    ty = leg_h
    add(taper(1.50 * s, 1.78 * s, 2.30 * s, 0.88 * s, 0.98 * s, top, seed + 5), (0, ty, 0))
    hy = ty + 2.30 * s
    add(box(0.52 * s, 0.30 * s, 0.52 * s, SKIN, seed + 6), (0, hy, 0))     # 목
    arm = {"stand": (0.22, -0.22), "point": (0.10, -1.45), "look": (0.26, -0.14),
           "carry": (0.70, -0.70), "raise": (2.35, -2.35), "sit": (0.85, -0.85)}[pose]
    for i, sx in enumerate((-1, 1)):
        a = taper(0.52 * s, 0.44 * s, 1.95 * s, 0.52 * s, 0.44 * s, _dim(top), seed + 8 + i)
        a.v[:, 1] *= -1                                                    # 어깨에서 아래로
        a.xf(L.rotz(arm[i]))
        add(a, (sx * 1.08 * s, hy - 0.12 * s, -0.22 * s))
    hr = 0.74 * s
    head = gem(hr, SKIN, seed + 12, n=8, squash=1.06)
    add(head, (0, hy + 0.26 * s, 0))
    hcap = gem(hr * 1.10, hair, seed + 13, n=8, squash=0.92)
    hcap.v[:, 1] = np.where(hcap.v[:, 1] < hr * 1.05, hr * 1.05, hcap.v[:, 1])
    add(hcap, (0, hy + 0.40 * s, -0.05 * s))
    hw = np.asarray([x, 0, z]) + np.asarray(R) @ np.asarray([0, hy + 0.26 * s + hr, 0])
    return ms, hw, hr, rot


def paint_face(img, cam, hw, hr, rot=0.0, mood="smile", seed=0):
    """투영된 머리 위치에 2D로 이목구비를 찍는다."""
    pts, z = cam.project(np.array([hw, hw + np.array([hr, 0, 0])]))
    cx, cy = pts[0]
    px = abs(pts[1][0] - pts[0][0])
    if px < 6:
        return
    d = ImageDraw.Draw(img)
    ex, ey, er = px * 0.36, -px * 0.04, max(px * 0.062, 1.3)
    off = math.sin(rot) * px * 0.30
    for sx in (-1, 1):
        d.ellipse([cx + sx * ex + off - er, cy + ey - er * 1.25,
                   cx + sx * ex + off + er, cy + ey + er * 1.25], fill=INK)
    mw, my = px * 0.26, cy + px * 0.34
    if mood == "smile":
        d.arc([cx - mw + off, my - px * .16, cx + mw + off, my + px * .16], 10, 170,
              fill=(178, 96, 88), width=max(int(px * .07), 2))
    elif mood == "sad":
        d.arc([cx - mw + off, my, cx + mw + off, my + px * .30], 195, 345,
              fill=(178, 96, 88), width=max(int(px * .07), 2))
    else:
        d.line([(cx - mw * .7 + off, my), (cx + mw * .7 + off, my)],
               fill=(178, 96, 88), width=max(int(px * .07), 2))


def roof(w, d, h, color, seed=0, lift=0.34):
    """한옥 지붕 — 네 모서리를 들어 올린 팔작지붕 느낌."""
    x, z = w / 2, d / 2
    rx = w * 0.20
    e = h * lift
    v = [(-x, e, -z), (x, e, -z), (x, e, z), (-x, e, z),                  # 들린 처마 끝
         (-x * .78, 0, -z * .78), (x * .78, 0, -z * .78),
         (x * .78, 0, z * .78), (-x * .78, 0, z * .78),                   # 처마 안쪽
         (-rx, h, 0), (rx, h, 0)]                                          # 용마루
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),          # 처마 뒤집힘
         (4, 5, 9, 8), (6, 7, 8, 9), (5, 6, 9), (7, 4, 8),
         (0, 3, 2, 1)]
    return Mesh(v, f, color, seed)


def hanok(cx, cz, w, d, body_h, color_body=L.CLAY, color_roof=L.INK, seed=0,
          tiers=1, base=True, base_c=L.SAND):
    ms = []
    if base:
        ms.append(box(w * 1.14, body_h * 0.18, d * 1.14, base_c, seed).xf(t=(cx, 0, cz)))
        y0 = body_h * 0.18
    else:
        y0 = 0.0
    ms.append(box(w, body_h, d, color_body, seed + 1).xf(t=(cx, y0, cz)))
    ms.append(box(w * 1.02, body_h * 0.13, d * 1.02, L.NAVY, seed + 7)
              .xf(t=(cx, y0 + body_h * 0.87, cz)))                       # 창방
    ms.append(box(w * 0.26, body_h * 0.62, d * 0.10, L.INK, seed + 8)
              .xf(t=(cx, y0, cz - d * 0.52)))                            # 문
    ms.append(roof(w * 1.30, d * 1.30, body_h * 0.62, color_roof, seed + 2)
              .xf(t=(cx, y0 + body_h, cz)))
    if tiers == 2:
        h2 = body_h * 0.66
        ms.append(box(w * 0.72, h2, d * 0.72, color_body, seed + 3)
                  .xf(t=(cx, y0 + body_h + body_h * 0.62 * 0.16, cz)))
        ms.append(roof(w * 1.02, d * 1.02, h2 * 0.62, color_roof, seed + 4)
                  .xf(t=(cx, y0 + body_h + body_h * 0.62 * 0.16 + h2, cz)))
    return ms


def pillars(cx, cz, w, d, h, n=5, color=L.CLAY, seed=0):
    return [box(0.34, h, 0.34, color, seed + i).xf(t=(cx - w / 2 + w * i / (n - 1), 0, cz + d / 2))
            for i in range(n)]


def backdrop(panels):
    """뒤쪽 색면 벽 — 레퍼런스의 색지 배경."""
    ms = []
    for i, (x, w, h, c, zz) in enumerate(panels):
        ms.append(wall(w, h, c, 40 + i).xf(t=(x, 0, zz)))
    return ms


def floor_tiles(n=7, size=6.0, c1=L.CREAM, c2=L.IVORY, y=0.0):
    ms = []
    for i in range(n):
        for j in range(n):
            x = (i - n / 2 + .5) * size
            z = (j - n / 2 + .5) * size
            m = plate(size * .97, size * .97, c1 if (i + j) % 2 else c2, i * 9 + j, y)
            m.v += np.array([x, 0, z])
            m.noshadow = True
            ms.append(m)
    return ms

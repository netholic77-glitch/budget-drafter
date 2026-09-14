# -*- coding: utf-8 -*-
"""로우폴리 페이퍼크래프트 렌더러.
면마다 평면 음영 + 종이 결 + 미세한 톤 편차 → 「종이를 접어 만든 미니어처」."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
OS = 1.10
BW, BH = int(W * OS), int(H * OS)

FSANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FREG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
_fc = {}
def font(size, bold=True):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FSANS if bold else FREG, size)
    return _fc[k]

# ── 종이 팔레트 (레퍼런스 추출)
CREAM   = (240, 231, 216)
IVORY   = (247, 241, 230)
SAND    = (226, 209, 186)
KRAFT   = (198, 166, 128)
TERRA   = (201, 111, 74)
SALMON  = (226, 155, 121)
CLAY    = (184, 92, 74)
ROSE    = (214, 140, 128)
NAVY    = (46, 65, 102)
DEEPNAV = (30, 42, 68)
MUSTARD = (215, 154, 60)
WOOD    = (185, 138, 94)
SKIN    = (238, 205, 178)
INK     = (38, 44, 58)

LIGHT = np.array([-0.46, 0.80, -0.38])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


# ───────────────────────────── 메시
class Mesh:
    def __init__(self, verts, faces, color, seed=0):
        self.v = np.asarray(verts, np.float64)
        self.f = faces
        self.c = np.asarray(color, np.float64)
        self.seed = seed

    def xf(self, M=None, t=(0, 0, 0)):
        v = self.v if M is None else self.v @ np.asarray(M).T
        self.v = v + np.asarray(t, np.float64)
        return self


def roty(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def rotz(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def box(w, h, d, color, seed=0):
    x, y, z = w / 2, h, d / 2
    v = [(-x, 0, -z), (x, 0, -z), (x, 0, z), (-x, 0, z),
         (-x, y, -z), (x, y, -z), (x, y, z), (-x, y, z)]
    f = [(4, 5, 6, 7), (0, 3, 2, 1), (3, 7, 6, 2), (0, 1, 5, 4), (1, 2, 6, 5), (0, 4, 7, 3)]
    return Mesh(v, f, color, seed)


def taper(wb, wt, h, db, dt, color, seed=0):
    """아래가 넓고 위가 좁은 상자 — 몸통·지붕에 쓴다."""
    a, b, c, d_ = wb / 2, wt / 2, db / 2, dt / 2
    v = [(-a, 0, -c), (a, 0, -c), (a, 0, c), (-a, 0, c),
         (-b, h, -d_), (b, h, -d_), (b, h, d_), (-b, h, d_)]
    f = [(4, 5, 6, 7), (0, 3, 2, 1), (3, 7, 6, 2), (0, 1, 5, 4), (1, 2, 6, 5), (0, 4, 7, 3)]
    return Mesh(v, f, color, seed)


def gem(r, color, seed=0, n=8, squash=1.0):
    """저면수 구 — 머리·덩어리. 위/아래 캡 + 중간 띠 2줄."""
    v, f = [], []
    rings = [(0.92, 0.36), (0.62, 0.86), (0.20, 1.00), (-0.30, 0.94), (-0.74, 0.62)]
    for yy, rr in rings:
        for i in range(n):
            a = 2 * math.pi * i / n
            v.append((math.cos(a) * r * rr, yy * r * squash + r, math.sin(a) * r * rr))
    top = len(v); v.append((0, r * squash * 1.20 + r, 0))
    bot = len(v); v.append((0, -r * squash * 1.02 + r, 0))
    for i in range(n):
        j = (i + 1) % n
        f.append((top, i, j))
        for k in range(len(rings) - 1):
            f.append((k * n + i, (k + 1) * n + i, (k + 1) * n + j, k * n + j))
        f.append((bot, (len(rings) - 1) * n + j, (len(rings) - 1) * n + i))
    return Mesh(v, f, color, seed)


def plate(w, d, color, seed=0, y=0.0):
    """바닥/벽 평면."""
    x, z = w / 2, d / 2
    return Mesh([(-x, y, -z), (x, y, -z), (x, y, z), (-x, y, z)], [(0, 1, 2, 3)], color, seed)


def wall(w, h, color, seed=0):
    """세로 벽 (z=0 평면)."""
    x = w / 2
    return Mesh([(-x, 0, 0), (x, 0, 0), (x, h, 0), (-x, h, 0)], [(0, 1, 2, 3)], color, seed)


def prism(pts, h, color, seed=0):
    """다각형 밑면을 세로로 밀어 올린 기둥. pts = [(x,z), ...]"""
    n = len(pts)
    v = [(p[0], 0, p[1]) for p in pts] + [(p[0], h, p[1]) for p in pts]
    f = [tuple(range(n, 2 * n)), tuple(range(n - 1, -1, -1))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    return Mesh(v, f, color, seed)


# ───────────────────────────── 카메라 · 렌더
class Cam:
    def __init__(self, pos, tgt, fov=38.0, up=(0, 1, 0)):
        self.pos = np.asarray(pos, np.float64)
        f = np.asarray(tgt, np.float64) - self.pos
        f /= np.linalg.norm(f)
        r = np.cross(f, np.asarray(up, np.float64)); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.R = np.array([r, u, -f])
        self.fl = (BH / 2) / math.tan(math.radians(fov) / 2)

    def project(self, v):
        p = (v - self.pos) @ self.R.T
        z = -p[:, 2]
        z = np.where(z < 1e-3, 1e-3, z)
        x = p[:, 0] / z * self.fl + BW / 2
        y = -p[:, 1] / z * self.fl + BH / 2
        return np.stack([x, y], 1), z


def _shade(base, normal, jit):
    lam = max(float(np.dot(normal, LIGHT)), 0.0)
    up = max(normal[1], 0.0)
    k = 0.60 + 0.34 * lam + 0.10 * up                 # 매트 — 앰비언트 높게
    c = base * k * (1.0 + jit)
    return tuple(int(min(max(x, 0), 255)) for x in c)


def _draw(img, meshes, cam):
    tris = []
    for m in meshes:
        pts, z = cam.project(m.v)
        rng = np.random.default_rng(m.seed + 17)
        for face in m.f:
            a, b, c = m.v[face[0]], m.v[face[1]], m.v[face[2]]
            n = np.cross(b - a, c - a)
            ln = np.linalg.norm(n)
            if ln < 1e-9:
                continue
            n = n / ln
            if np.dot(n, a - cam.pos) > 0:
                n = -n
            col = _shade(m.c, n, float(rng.uniform(-0.035, 0.035)))
            tris.append((float(z[list(face)].mean()), [tuple(pts[i]) for i in face], col))
    tris.sort(key=lambda t: -t[0])
    d = ImageDraw.Draw(img)
    for _, poly, col in tris:
        d.polygon(poly, fill=col)
    return img


def render(ground, objects, cam, bg, floor_y=0.0, shadow=0.30):
    """바닥·배경 → 그림자 → 오브젝트 순. 그림자가 바닥 위에 남아야 종이가 떠 보인다."""
    img = bg.copy().convert("RGB")
    _draw(img, ground, cam)
    if shadow > 0 and objects:
        sh = Image.new("L", (BW, BH), 0)
        sd = ImageDraw.Draw(sh)
        for m in objects:
            if getattr(m, "noshadow", False):
                continue
            vs = m.v.copy()
            t = (vs[:, 1] - floor_y) / LIGHT[1]
            vs[:, 0] -= LIGHT[0] * t
            vs[:, 2] -= LIGHT[2] * t
            vs[:, 1] = floor_y + 0.02
            pts, _ = cam.project(vs)
            for face in m.f:
                sd.polygon([tuple(pts[i]) for i in face], fill=255)
        sh = sh.filter(ImageFilter.GaussianBlur(20))
        a = np.asarray(sh, np.float32) / 255.0 * shadow
        base = np.asarray(img, np.float32)
        dark = base * np.array([0.66, 0.62, 0.60])[None, None, :]
        img = Image.fromarray(np.clip(base * (1 - a[:, :, None]) + dark * a[:, :, None],
                                      0, 255).astype(np.uint8))
    _draw(img, objects, cam)
    return img


def paper_grain(img, amount=4.6, seed=3):
    a = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(seed)
    n = rng.normal(0, amount, a.shape[:2])
    fib = (np.sin(np.arange(a.shape[0])[:, None] * 1.7) * 1.1
           + np.sin(np.arange(a.shape[1])[None, :] * 2.3) * 0.9)
    a += (n + fib)[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

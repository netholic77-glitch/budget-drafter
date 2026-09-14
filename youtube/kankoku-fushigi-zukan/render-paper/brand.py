# -*- coding: utf-8 -*-
"""「韓国ふしぎ図鑑」 로고·엔드카드 (페이퍼 팔레트)."""
from PIL import Image, ImageDraw
from lowpoly import font

CH_NAME = "韓国ふしぎ図鑑"
CH_HANDLE = "@kankoku_fushigi"
CARD_BG = (23, 32, 45)
CORAL = (232, 135, 60)
PAPER = (240, 231, 216)
GAT = (32, 40, 56)
FACE = (228, 160, 96)


def logo(size=720):
    S = size
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = S / 720.0
    cx, cy = S / 2, S * 0.60
    d.ellipse([cx - 236 * u, cy - 176 * u, cx + 236 * u, cy + 176 * u], fill=FACE)
    d.ellipse([cx - 292 * u, cy - 52 * u, cx - 196 * u, cy + 52 * u], fill=FACE)
    d.ellipse([cx + 196 * u, cy - 52 * u, cx + 292 * u, cy + 52 * u], fill=FACE)
    d.ellipse([cx - 306 * u, cy - 306 * u, cx + 306 * u, cy - 190 * u],
              fill=GAT, outline=CORAL, width=int(7 * u))
    d.rounded_rectangle([cx - 116 * u, cy - 420 * u, cx + 116 * u, cy - 230 * u],
                        26 * u, fill=GAT, outline=CORAL, width=int(7 * u))
    d.ellipse([cx - 300 * u, cy - 292 * u, cx + 300 * u, cy - 204 * u], fill=GAT)
    for sx in (-1, 1):
        d.ellipse([cx + sx * 104 * u - 34 * u, cy - 62 * u,
                   cx + sx * 104 * u + 34 * u, cy + 8 * u], fill=GAT)
    d.arc([cx - 84 * u, cy + 30 * u, cx + 84 * u, cy + 136 * u], 15, 165,
          fill=GAT, width=int(20 * u))
    return img


def endcard(W, H, next_line, closing):
    img = Image.new("RGB", (W, H), CARD_BG)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([-W * .36, H * .03, W * .70, H * .50], fill=(255, 255, 255, 9))
    lg = logo(int(W * 0.62))
    img.paste(lg, (int((W - lg.width) / 2), int(H * .295)), lg)
    d.text((W / 2, H * .690), CH_NAME, font=font(100), fill=PAPER, anchor="mm")
    d.rectangle([W * .40, H * .725, W * .60, H * .728], fill=(232, 135, 60, 210))
    d.text((W / 2, H * .768), next_line, font=font(54), fill=CORAL, anchor="mm")
    d.text((W / 2, H * .832), closing, font=font(46), fill=(246, 246, 246), anchor="mm")
    d.text((W / 2, H * .945), CH_HANDLE, font=font(44), fill=(122, 134, 156), anchor="mm")
    return img

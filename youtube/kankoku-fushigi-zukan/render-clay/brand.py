# -*- coding: utf-8 -*-
"""「韓国ふしぎ図鑑」 브랜드 — 로고·엔드카드."""
from PIL import Image, ImageDraw
from clay import font

CH_NAME = "韓国ふしぎ図鑑"
CH_KANA = "かんこく ふしぎ ずかん"
CH_HANDLE = "@kankoku_fushigi"
NAVY = (13, 25, 49)
YELLOW = (255, 207, 41)
INK = (26, 30, 48)


def logo(size=720):
    """노란 얼굴 + 갓. @weirdecon 로고와 형제로 읽히되 한국 기표를 얹는다."""
    S = size
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = S / 720.0
    cx, cy = S / 2, S * 0.60
    d.ellipse([cx - 236 * u, cy - 176 * u, cx + 236 * u, cy + 176 * u], fill=YELLOW)  # 얼굴
    d.ellipse([cx - 292 * u, cy - 52 * u, cx - 196 * u, cy + 52 * u], fill=YELLOW)    # 귀
    d.ellipse([cx + 196 * u, cy - 52 * u, cx + 292 * u, cy + 52 * u], fill=YELLOW)
    d.ellipse([cx - 306 * u, cy - 306 * u, cx + 306 * u, cy - 190 * u],
              fill=INK, outline=(214, 176, 66), width=int(7 * u))                    # 갓 양태
    d.rounded_rectangle([cx - 116 * u, cy - 420 * u, cx + 116 * u, cy - 230 * u],
                        26 * u, fill=INK, outline=(214, 176, 66), width=int(7 * u))  # 갓 대우
    d.ellipse([cx - 300 * u, cy - 292 * u, cx + 300 * u, cy - 204 * u], fill=INK)
    for sx in (-1, 1):                                                               # 눈
        d.ellipse([cx + sx * 104 * u - 40 * u, cy - 66 * u,
                   cx + sx * 104 * u + 40 * u, cy + 14 * u], fill=INK)
    d.arc([cx - 84 * u, cy + 34 * u, cx + 84 * u, cy + 140 * u], 15, 165,
          fill=INK, width=int(22 * u))                                               # 입
    return img


def endcard(W, H, next_line, closing):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([-W * .38, H * .02, W * .70, H * .50], fill=(255, 255, 255, 10))
    d.ellipse([W * .42, H * .68, W * 1.5, H * 1.14], fill=(255, 255, 255, 8))
    lg = logo(int(W * 0.70))
    img.paste(lg, (int((W - lg.width) / 2), int(H * .30)), lg)
    d.text((W / 2, H * .705), CH_NAME, font=font(104), fill=(248, 248, 250), anchor="mm")
    d.text((W / 2, H * .762), next_line, font=font(56), fill=(238, 200, 74), anchor="mm")
    d.text((W / 2, H * .830), closing, font=font(50), fill=(252, 252, 252), anchor="mm",
           stroke_width=7, stroke_fill=(10, 14, 26))
    d.text((W / 2, H * .945), CH_HANDLE, font=font(46), fill=(126, 138, 166), anchor="mm")
    return img

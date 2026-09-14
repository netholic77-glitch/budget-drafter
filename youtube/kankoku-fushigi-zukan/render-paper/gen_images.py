# -*- coding: utf-8 -*-
"""Gemini 이미지 생성 → 1080×1920 PNG. 키는 GEMINI_API_KEY 환경변수에서만 읽는다."""
import os, sys, json, base64, time, urllib.request, urllib.error
from io import BytesIO
from PIL import Image
from prompts import SUFFIX, SCENES

KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not KEY:
    sys.exit("GEMINI_API_KEY 가 비어 있습니다.")
BASE = "https://generativelanguage.googleapis.com/v1beta"
OUT = sys.argv[1] if len(sys.argv) > 1 else "images"
os.makedirs(OUT, exist_ok=True)


def call(url, payload=None):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode() if payload else None,
        headers={"Content-Type": "application/json", "x-goog-api-key": KEY},
        method="POST" if payload else "GET")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def pick_model():
    ms = call(f"{BASE}/models")["models"]
    names = [m["name"].split("/")[-1] for m in ms]
    for want in ("gemini-3-pro-image", "gemini-3-pro-image-preview",
                 "gemini-2.5-flash-image", "gemini-2.5-flash-image-preview",
                 "gemini-2.0-flash-preview-image-generation"):
        for n in names:
            if n.startswith(want):
                return n
    cand = [n for n in names if "image" in n and "embedding" not in n]
    if not cand:
        print("사용 가능한 모델:", ", ".join(names[:40]))
        sys.exit("이미지 생성 모델을 찾지 못했습니다.")
    return cand[0]


def generate(model, prompt):
    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"responseModalities": ["IMAGE"],
                                    "imageConfig": {"aspectRatio": "9:16"}}}
    try:
        r = call(f"{BASE}/models/{model}:generateContent", payload)
    except urllib.error.HTTPError as e:                      # imageConfig 미지원 모델 대비
        body = e.read().decode()[:300]
        if e.code != 400:
            raise
        print("   imageConfig 미지원 → 재시도:", body[:110])
        payload["generationConfig"].pop("imageConfig")
        r = call(f"{BASE}/models/{model}:generateContent", payload)
    for c in r.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            d = p.get("inlineData") or p.get("inline_data")
            if d:
                return base64.b64decode(d["data"])
    raise RuntimeError(json.dumps(r)[:400])


def fit(raw, w=1080, h=1920):
    im = Image.open(BytesIO(raw)).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    return im.crop(((im.width - w) // 2, (im.height - h) // 2,
                    (im.width - w) // 2 + w, (im.height - h) // 2 + h))


model = pick_model()
print("모델:", model, flush=True)
for k, body in SCENES.items():
    p = os.path.join(OUT, f"{k}.png")
    if os.path.exists(p):
        print("skip", k); continue
    for attempt in range(3):
        try:
            fit(generate(model, body + " " + SUFFIX)).save(p)
            print("OK  ", k, flush=True)
            break
        except Exception as e:
            print("실패", k, attempt + 1, str(e)[:160], flush=True)
            time.sleep(4 * (attempt + 1))
print("→", OUT)

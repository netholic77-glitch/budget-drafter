# 로우폴리 페이퍼크래프트 렌더 파이프라인 (현행)

레퍼런스로 받은 완성본 3편(58.4·61.5·62.2초)의 비주얼·자막 규격을 따른다.
`ep01.py` 하나만 고치면 **1080×1920 / 30fps MP4**가 통째로 나온다. 1편 약 95초.

```bash
# 1회만
apt-get update && apt-get install -y ffmpeg fonts-noto-cjk \
    open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001
pip3 install pillow numpy
git clone --depth 1 https://github.com/icn-lab/htsvoice-tohoku-f01.git voice   # 여성 음성

python3 build_audio.py ep01 audio.wav
python3 render.py     ep01 out.mp4 audio.wav
```

## 왜 3D인가

레퍼런스의 종이 인형·종이 건물은 **평면 색면(facet)의 집합**이다. 생성형 이미지 없이도
작은 3D 엔진 하나로 그대로 재현된다 — 면마다 평면 음영을 주고 종이 결을 얹으면 끝이다.

`lowpoly.py` 가 그 엔진이다. 외부 이미지·생성형 이미지를 한 장도 쓰지 않는다.

- **투영** — 원근 카메라. `fov`는 세로 화각 기준(9:16이라 가로는 훨씬 좁다. 50~52°가 적정)
- **음영** — 면 법선 × 광원. `0.60 + 0.34·lambert + 0.10·up`. 앰비언트를 높게 잡아야 **매트한 종이**가 된다
- **면 편차** — 면마다 ±3.5% 톤 지터. 이게 「손으로 접은」 느낌의 정체다
- **그림자** — 광원 방향으로 바닥면에 투영 → 블러 → 바닥 위에 곱하기. **바닥을 먼저 그리고 그림자를 얹은 뒤 오브젝트를 그린다.** 순서가 바뀌면 그림자가 덮인다
- **정렬** — 화가 알고리즘(중심 깊이 내림차순). 씬당 면 수가 적어 충분하다

## 얼굴

이목구비는 3D로 만들지 않는다. 머리 중심을 투영한 2D 좌표에 눈·입을 찍는다
(`figures.paint_face`). 폴리곤으로 깎는 것보다 표정 제어가 쉽고 훨씬 빠르다.
`mood="smile"/"flat"/"sad"`.

## 자막 규격 (레퍼런스 실측)

| 요소 | 값 |
|---|---|
| 카드 배경 | `#17202D` |
| 코랄(제목·라벨) | `#E8873C` / 비교 카드의 韓国 은 `#F0674E` |
| 상단 라벨 | 44px Bold · y=84 · 중앙 |
| 자막 | 48px Bold · 흰색 · 검정 스트로크 7 · 최대 3줄 · 행간 64 · 중심 y=1512 |
| 해설(note) | 25px · `#969CA0` · y=1866 |
| 카드 제목 | 96px Bold 코랄 · y=0.235H |
| 카드 항목 | 64px Bold 흰색 + 코랄 세로바(9px) · 행간 0.073H |

## 나레이션

**tohoku-f01 (여성) / happy** — 도호쿠대 지능통신망연구실, **CC BY 4.0**.
상업 이용 가능하되 **출처 표기가 의무**다. 업로드 설명문에 아래 한 줄을 반드시 넣는다.

```
音声: HTS voice "tohoku-f01" © 2015 Tohoku University (CC BY 4.0)
```

컷 길이를 넘치면 낭독 속도만 자동으로 올린다(최대 1.45배). 숫자·고유명사는
`ep01.py`의 `NARRATION`에 가나로 풀어 적는다. 화면 자막은 한자 그대로다.

## 파일

| 파일 | 역할 |
|---|---|
| `lowpoly.py` | 3D 엔진 — 메시·카메라·평면 음영·그림자·종이 결 |
| `figures.py` | 인물(포즈 6종·표정 3종)·한옥·지붕·기둥·바닥 타일·배경 색면 |
| `scenes_paper.py` | 장면 9종 + 네이비 텍스트 카드 2종 |
| `brand.py` | 로고(갓 쓴 얼굴)·엔드카드 |
| `ep01.py` | 컷 타임라인 · 라벨 · 자막 · note · TTS 원고 |
| `build_audio.py` | 여성 TTS 합성 → 속도 조정 → 패드·전환음 믹스 |
| `render.py` | 켄번스 → 자막 합성 → ffmpeg 파이프 |

## 주의

- 완성본이 30MB를 넘으면 전송이 막힌다. 배포용은 `-crf 24` 로 다시 인코딩한다(약 18MB).
- 이전 포맷은 `render-clay/`(클레이 음영), `render/`(종이 오려붙이기)에 남아 있다. **현행은 이 폴더다.**

---

## 생성형 이미지로 교체하기 (Gemini)

이 컨테이너에서 `generativelanguage.googleapis.com` 은 **열려 있다**(구글이 직접 응답. 프록시 차단 없음).
필요한 것은 API 키뿐이다. 키가 있으면 3D 장면 대신 생성형 이미지를 쓴다.

```bash
export GEMINI_API_KEY=...            # aistudio.google.com/apikey
python3 gen_images.py images         # 9장 → images/*.png (1080×1920)
python3 render.py ep01 out.mp4 audio.wav
```

- `render.py` 는 `images/<장면키>.png` 가 있으면 **자동으로 그걸 쓰고**, 없으면 3D로 폴백한다.
  환경변수 `SCENE_IMAGES` 로 폴더를 바꿀 수 있다.
- `gen_images.py` 는 모델 목록을 조회해 이미지 생성 모델을 **자동 선택**한다(하드코딩 없음).
  `imageConfig.aspectRatio` 미지원 모델이면 그 필드를 빼고 재시도하고, 결과는 9:16으로 센터 크롭한다.
- **이미 있는 PNG는 건너뛴다.** 마음에 안 드는 컷만 지우고 다시 돌리면 그 컷만 새로 뽑힌다.
- 프롬프트는 `prompts.py`. `SUFFIX` 가 질감·팔레트·광원·구도를 고정한다 — **컷마다 이걸 빼면 톤이 어긋난다.**

### 주의

- 생성형 이미지는 컷마다 인물 얼굴·옷·소품이 달라진다. 9컷이 한 세계로 보이려면 보통 2~3회 돌려 고른다.
- 키는 **환경변수로만** 넘긴다. 코드·저장소·로그에 쓰지 않는다. `images/` 는 `.gitignore` 에 있다.

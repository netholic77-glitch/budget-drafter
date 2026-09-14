# 클레이 디오라마 렌더 파이프라인

`ep01.py`(컷 타임라인 + 내레이션)만 고치면 **1080×1920 / 30fps / 71.5초 MP4**가 통째로 나온다.
외부 이미지·생성형 이미지를 한 장도 쓰지 않는다. 장면은 전부 코드가 그린다.

```bash
# 1회만
apt-get update && apt-get install -y ffmpeg fonts-noto-cjk \
    open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001
pip3 install pillow numpy

python3 build_audio.py ep01 audio.wav      # 내레이션 + 앰비언스
python3 render.py     ep01 out.mp4 audio.wav
```

1편 약 70초 소요(장면 생성 25초 + 인코딩 45초).

## 파일

| 파일 | 역할 |
|---|---|
| `clay.py` | **핵심.** 마스크 → 법선 → 램버트/스페큘러/림 음영. 디오라마 무대(벽·전구·바닥·비네트) |
| `parts.py` | 부품 마스크 — 기와지붕·전각·피규어·주춧돌·가마·비계·모래시계 |
| `scenes.py` | 11개 장면 조립 + 플랫 카드 2종 |
| `brand.py` | 로고(노란 얼굴 + 갓)·엔드카드 |
| `ep01.py` | 컷 타임라인 · emph · 자막 · note · TTS 원고. **대본 수정은 여기서만** |
| `build_audio.py` | open_jtalk 합성 → 컷 길이에 맞춰 낭독 속도 조정 → 저역 앰비언스·전환 임팩트 믹스 |
| `render.py` | 켄번스(방향 교대) → 자막 합성 → ffmpeg 파이프 → H.264 + AAC |

## clay.shade — 이 파이프라인의 전부

마스크를 가우시안으로 흐리면 그 기울기가 곧 표면 법선이 된다.
거기에 우상단 광원으로 램버트 + 스페큘러 + 림라이트를 입히면 **평면 도형이 점토 덩어리가 된다.**

```python
m  = mask.filter(GaussianBlur(22))
gy, gx = np.gradient(m)                 # 법선
lam = clip(N·L, 0, 1)                   # 램버트
out = base*(amb*cool + (1-amb)*lam*warm) + spec*(N·H)**26 + rim*(1-Nz)**3
```

`blur`를 키우면 더 둥글고, 줄이면 더 각진 점토가 된다.

## 생성형 이미지로 교체하려면

`scenes.SCENES[kind]()` 자리에 1080×1920 PNG를 읽어 반환하면 끝이다.
`render.py`의 장면 로딩 한 줄만 바꾸면 타임라인·자막·오디오는 그대로 재사용된다.
이미지 프롬프트는 `../01_gyeongbokgung/image-prompts.md` 참조.

## 한계

- 내레이션은 Open JTalk 오프라인 합성. 남성 1종뿐이고 억양이 기계적이다. **업로드 전 교체 권장.**
- 클레이 "사진"이 아니라 **코드가 그린 클레이 "일러스트"**다. 조명·팔레트·구도·타이포는 레퍼런스와 같지만 질감은 다르다.
- 완성 MP4·WAV는 재생성 가능하므로 커밋하지 않는다.

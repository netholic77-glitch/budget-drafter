# EP.01 景福宮 — 생성형 이미지 프롬프트 (클레이 사진풍 교체용)

현재 영상의 장면은 코드가 그린 클레이 일러스트입니다.
**실제 클레이 사진풍으로 올리려면** 아래 프롬프트로 1080×1920 PNG를 만들어
`render-clay/scenes.py` 의 장면 반환부만 교체하면 됩니다. 타임라인·자막·오디오는 그대로 씁니다.

## 고정 접미사 (모든 컷에 붙일 것)

```
Claymation stop-motion still photograph, handmade plasticine miniature diorama on a tabletop,
visible fingerprint texture in the clay, slightly rough handmade edges,
lit by a single warm yellow desk lamp from the upper right, soft long shadows falling to the lower left,
deep teal-navy background #0F1B33, dark and moody, cracked concrete floor,
shallow depth of field, macro tabletop photography, cinematic.
No text, no letters, no watermark.
```

## 컷별 주제

| 컷 | 시간 | 주제 |
|---|---|---|
| 01 | 0–6 | 미니어처 한국 궁궐 문(단청 기와지붕) 앞에 홀로 선 여행자 클레이 피규어. 올려다보는 표정 |
| 02 | 6–12 | 목재를 나르고 들어올리는 인부 클레이 피규어 둘. 뒤에 짓다 만 전각 |
| 03 | 12–17.5 | 무너진 기와지붕 잔해. 붉은 조명. 공중에 떠다니는 불티. 실루엣이 된 피규어 |
| 04 | 17.5–23.5 | 주춧돌만 남은 빈터. 잡초. 멀리 홀로 선 피규어 한 명 |
| 05 | 23.5–30 | 가마를 멘 인부 둘이 오른쪽 궁궐로 이동 |
| 06 | 30–36.5 | **플랫 네이비 카드** — 모래시계 (이미지 생성 불필요, `make_card` 계열) |
| 07 | 36.5–42.5 | 도르래로 목재를 끌어올리는 중건 현장 |
| 08 | 42.5–48.5 | 텅 빈 석조 기단과 안개. 등 돌린 피규어 |
| 09 | 48.5–54 | 전각을 감싼 목재 비계. 복원 인부 둘 |
| 10 | 54–60.5 | **플랫 네이비 카드** — 8×8 블록 중 좌하단 4×4만 금색 |
| 11 | 60.5–67 | 한복(적·청)을 입은 관람객 피규어 둘. 뒤에 복원된 전각 |
| 12 | 67–71.5 | **엔드카드** — `brand.endcard()` 출력 |

## 도구 주의

레퍼런스(@weirdecon 1·2화)와 질감을 맞추려면 **같은 이미지 도구**를 쓰십시오.
도구를 바꾸면 점토 표면·조명 감쇠가 어긋나 한 채널 안에서 튑니다.
우하단에 도구 워터마크가 박히면 렌더 단계에서 크롭하십시오.

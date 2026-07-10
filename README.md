# budget-drafter

예산분석지원 시스템 — 엑셀·PDF 예산 자료를 업로드하면 전년 대비 증감을 분석하고, 워드 보고서를 자동으로 생성합니다.

## 기능

- 엑셀(.xlsx, .xls, .csv) 예산 자료 업로드 → 항목/부서/금년도·전년도 예산액 자동 인식
- 항목별 증감액·증감률 계산, 정렬 및 시각화
- 총예산/총증감/최대 증가·감소 항목 요약 카드
- PDF 예산 자료 텍스트 추출(표 형식이 아닌 문서 미리보기용)
- 워드(.docx) 분석 보고서 자동 생성
- 전체 데이터(JSON/CSV) + 보고서를 zip으로 일괄 다운로드
- 샘플 데이터로 바로 체험 가능

모든 처리는 브라우저에서 이루어지며, 업로드한 파일이 서버로 전송되지 않습니다.

## 개발

```bash
npm install
npm run dev
```

[http://localhost:3000](http://localhost:3000) 에서 확인할 수 있습니다.

## 배포

`main` 브랜치에 푸시되면 GitHub Actions가 정적 빌드(`next build`, `output: export`) 후
GitHub Pages로 자동 배포합니다.

import * as XLSX from "xlsx";

const ITEM_HEADERS = ["항목", "과목", "세부사업", "사업명", "세부사업명", "과목명", "구분"];
const DEPT_HEADERS = ["부서", "부서명", "소관", "소관부서", "실국"];
const CURRENT_HEADERS = [
  "예산액",
  "금액",
  "당해년도",
  "본예산",
  "올해예산",
  "편성액",
  "계상액",
  "2026년",
  "2026",
];
const PREVIOUS_HEADERS = [
  "전년도",
  "전년도예산",
  "전년",
  "작년",
  "전년도예산액",
  "2025년",
  "2025",
];

function normalizeHeader(header) {
  return String(header ?? "").replace(/\s+/g, "").trim();
}

function findColumn(headers, candidates) {
  const normalized = headers.map(normalizeHeader);
  for (const candidate of candidates) {
    const idx = normalized.findIndex((h) => h.includes(candidate));
    if (idx !== -1) return headers[idx];
  }
  return null;
}

function toNumber(value) {
  if (typeof value === "number") return value;
  if (value == null) return 0;
  const cleaned = String(value).replace(/[,원₩\s]/g, "");
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function parseWorkbook(arrayBuffer) {
  const workbook = XLSX.read(arrayBuffer, { type: "array" });
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: "" });

  if (rows.length === 0) {
    throw new Error("시트에서 데이터를 찾을 수 없습니다.");
  }

  const headers = Object.keys(rows[0]);
  const itemCol = findColumn(headers, ITEM_HEADERS) ?? headers[0];
  const deptCol = findColumn(headers, DEPT_HEADERS);
  const currentCol = findColumn(headers, CURRENT_HEADERS);
  const previousCol = findColumn(headers, PREVIOUS_HEADERS);

  if (!currentCol) {
    throw new Error(
      "예산액 열을 찾지 못했습니다. '예산액', '금액', '본예산' 등의 열 이름이 있는지 확인해 주세요."
    );
  }

  const items = rows
    .map((row) => {
      const name = String(row[itemCol] ?? "").trim();
      if (!name) return null;
      const current = toNumber(row[currentCol]);
      const previous = previousCol ? toNumber(row[previousCol]) : null;
      const diff = previous != null ? current - previous : null;
      const rate = previous ? (diff / previous) * 100 : null;
      return {
        name,
        department: deptCol ? String(row[deptCol] ?? "").trim() : "",
        current,
        previous,
        diff,
        rate,
      };
    })
    .filter(Boolean);

  return {
    sheetName,
    columns: { itemCol, deptCol, currentCol, previousCol },
    items,
  };
}

export function summarize(items) {
  const totalCurrent = items.reduce((sum, i) => sum + i.current, 0);
  const hasPrevious = items.some((i) => i.previous != null);
  const totalPrevious = hasPrevious
    ? items.reduce((sum, i) => sum + (i.previous ?? 0), 0)
    : null;
  const totalDiff = hasPrevious ? totalCurrent - totalPrevious : null;
  const totalRate = hasPrevious && totalPrevious ? (totalDiff / totalPrevious) * 100 : null;

  const ranked = hasPrevious
    ? [...items].filter((i) => i.diff != null).sort((a, b) => b.diff - a.diff)
    : [];

  return {
    itemCount: items.length,
    totalCurrent,
    totalPrevious,
    totalDiff,
    totalRate,
    hasPrevious,
    topIncrease: ranked[0] ?? null,
    topDecrease: ranked[ranked.length - 1] ?? null,
  };
}

export function buildSampleWorkbookRows() {
  return [
    { 항목: "도로 유지보수", 부서: "건설과", 전년도예산: 320000000, 예산액: 410000000 },
    { 항목: "노인 복지 지원", 부서: "복지과", 전년도예산: 550000000, 예산액: 620000000 },
    { 항목: "청년 창업 지원", 부서: "일자리과", 전년도예산: 180000000, 예산액: 150000000 },
    { 항목: "공원 조성", 부서: "녹지과", 전년도예산: 90000000, 예산액: 260000000 },
    { 항목: "재난 안전관리", 부서: "안전과", 전년도예산: 210000000, 예산액: 205000000 },
    { 항목: "문화행사 지원", 부서: "문화과", 전년도예산: 75000000, 예산액: 60000000 },
    { 항목: "상하수도 정비", 부서: "환경과", 전년도예산: 430000000, 예산액: 470000000 },
    { 항목: "교육 지원사업", 부서: "교육과", 전년도예산: 260000000, 예산액: 300000000 },
  ];
}

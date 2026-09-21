import * as XLSX from "xlsx";

const ITEM_HEADERS = [
  "세부사업명",
  "세부사업",
  "사업명",
  "단위사업",
  "정책사업",
  "과목명",
  "항목",
  "과목",
  "구분",
];
const DEPT_HEADERS = ["소관부서", "실국", "부서명", "부서", "소관", "기관"];

// 비교 기준(전년도/당초/기정) 열을 가리키는 표지.
// 추경 자료에서는 "기정예산"·"당초예산"이 비교 기준이 된다.
const BASE_MARKERS = ["전년도", "전년", "작년", "기정", "당초", "종전", "전회"];

// 금년도(분석 대상) 예산액 열 후보. 연도 숫자는 하드코딩하지 않는다.
const CURRENT_HEADERS = [
  "예산액",
  "편성액",
  "계상액",
  "요구액",
  "본예산",
  "추경예산",
  "올해예산",
  "금액",
];

// 금액 열로 오인되기 쉬운 파생·메타 열. 후보에서 먼저 제외한다.
const EXCLUDED_MARKERS = [
  "증감",
  "증액",
  "감액",
  "대비",
  "비율",
  "비중",
  "비고",
  "순위",
  "연번",
  "번호",
  "코드",
  "산출근거",
  "내역",
];

const YEAR_PATTERN = /(19|20)\d{2}/;

function normalizeHeader(header) {
  return String(header ?? "").replace(/\s+/g, "").trim();
}

/**
 * candidates 를 순서대로 훑되, 완전일치를 부분일치보다 우선한다.
 * "예산액" 을 찾을 때 "전년도예산액" 이 먼저 걸리는 것을 막기 위함이다.
 */
function findColumn(headers, candidates, exclude = []) {
  const pool = headers.filter((h) => !exclude.includes(h));
  const normalized = pool.map(normalizeHeader);

  for (const candidate of candidates) {
    const idx = normalized.indexOf(candidate);
    if (idx !== -1) return pool[idx];
  }
  for (const candidate of candidates) {
    const idx = normalized.findIndex((h) => h.includes(candidate));
    if (idx !== -1) return pool[idx];
  }
  return null;
}

function hasExcludedMarker(header) {
  const h = normalizeHeader(header);
  return EXCLUDED_MARKERS.some((marker) => h.includes(marker));
}

/** 헤더에서 연도(19xx/20xx)를 뽑는다. 없으면 null. */
function headerYear(header) {
  const match = normalizeHeader(header).match(YEAR_PATTERN);
  return match ? Number(match[0]) : null;
}

/** 해당 열의 값이 금액처럼 보이는지(숫자로 읽히는 비어있지 않은 값이 있는지) 확인한다. */
function looksNumeric(rows, column) {
  let seen = 0;
  for (const row of rows) {
    const raw = row[column];
    if (raw === "" || raw == null) continue;
    seen += 1;
    if (parseAmount(raw).ok) return true;
    if (seen >= 20) break;
  }
  return false;
}

const FULLWIDTH_DIGITS = /[０-９]/g;
// 한국 정부 재정 문서는 음수를 △ 로 표기한다(증가는 표지 없이 적는 것이 관례).
// 아래를 향한 ▽·▼ 도 감소로 읽고, 회계 괄호 표기 (1,234) 도 음수로 본다.
const NEGATIVE_MARKERS = /^[△▽▼−–—‐-]+/;
// ▲ 는 관례가 갈린다(증가 표지로 쓰는 자료가 많다). 부호를 뒤집지 않고 표지만 떼어낸다.
const POSITIVE_MARKERS = /^▲+/;

/**
 * 셀 값을 금액으로 읽는다. 읽지 못하면 ok:false 를 돌려주어
 * 호출부가 "조용히 0으로 처리된 칸"을 셀 수 있게 한다.
 */
export function parseAmount(value) {
  if (typeof value === "number") {
    return Number.isFinite(value) ? { ok: true, value } : { ok: false, value: 0 };
  }
  if (value == null) return { ok: false, value: 0 };

  let text = String(value).trim();
  if (!text) return { ok: false, value: 0 };

  let negative = false;

  // 회계 괄호 표기: (1,234) / （1,234）
  if (/^[(（].*[)）]$/.test(text)) {
    negative = true;
    text = text.slice(1, -1).trim();
  }

  // 선행 표지: △1,234 (음수) / ▲1,234 (부호 그대로)
  if (POSITIVE_MARKERS.test(text)) {
    text = text.replace(POSITIVE_MARKERS, "").trim();
  } else if (NEGATIVE_MARKERS.test(text)) {
    negative = !negative;
    text = text.replace(NEGATIVE_MARKERS, "").trim();
  }

  text = text
    .replace(FULLWIDTH_DIGITS, (d) => String.fromCharCode(d.charCodeAt(0) - 0xfee0))
    .replace(/[,\s원₩￦]/g, "");

  if (!/^\d+(\.\d+)?$/.test(text)) return { ok: false, value: 0 };

  const parsed = Number(text);
  if (!Number.isFinite(parsed)) return { ok: false, value: 0 };

  return { ok: true, value: negative ? -parsed : parsed };
}

function toNumber(value) {
  return parseAmount(value).value;
}

/**
 * 금년도·비교기준 열을 고른다.
 *  1) 헤더에 연도가 둘 이상 있으면 큰 연도 = 금년도, 그 다음 = 비교기준
 *  2) 없으면 비교기준 표지(전년도/기정/당초…)로 비교기준을 먼저 확정하고,
 *     남은 열에서 금년도를 고른다 (순서가 반대면 "전년도예산액"이 금년도로 잡힌다)
 */
function detectAmountColumns(headers, rows, exclude) {
  const candidates = headers.filter(
    (h) => !exclude.includes(h) && !hasExcludedMarker(h)
  );

  const dated = candidates
    .map((column) => ({ column, year: headerYear(column) }))
    .filter((entry) => entry.year != null);

  const years = [...new Set(dated.map((d) => d.year))].sort((a, b) => b - a);
  if (years.length >= 2) {
    return {
      currentCol: dated.find((d) => d.year === years[0]).column,
      previousCol: dated.find((d) => d.year === years[1]).column,
      basis: "year",
    };
  }

  const previousCol = findColumn(candidates, BASE_MARKERS);
  const currentCol =
    findColumn(candidates, CURRENT_HEADERS, previousCol ? [previousCol] : []) ??
    candidates.find((h) => h !== previousCol && looksNumeric(rows, h)) ??
    null;

  return { currentCol, previousCol, basis: previousCol ? "marker" : "none" };
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
  const deptCol = findColumn(headers, DEPT_HEADERS, [itemCol]);
  const { currentCol, previousCol } = detectAmountColumns(
    headers,
    rows,
    [itemCol, deptCol].filter(Boolean)
  );

  if (!currentCol) {
    throw new Error(
      "예산액 열을 찾지 못했습니다. '예산액', '편성액', '2027년' 등 금액 열 이름이 있는지 확인해 주세요."
    );
  }

  let unreadableCells = 0;
  const items = rows
    .map((row, index) => {
      const name = String(row[itemCol] ?? "").trim();
      if (!name) return null;

      const currentRaw = parseAmount(row[currentCol]);
      if (!currentRaw.ok && String(row[currentCol] ?? "").trim()) unreadableCells += 1;
      const current = currentRaw.value;

      let previous = null;
      if (previousCol) {
        const previousRaw = parseAmount(row[previousCol]);
        if (!previousRaw.ok && String(row[previousCol] ?? "").trim()) unreadableCells += 1;
        previous = previousRaw.value;
      }

      const diff = previous != null ? current - previous : null;
      const rate = previous ? (diff / previous) * 100 : null;

      return {
        id: `row-${index}`,
        name,
        department: deptCol ? String(row[deptCol] ?? "").trim() : "",
        current,
        previous,
        diff,
        rate,
      };
    })
    .filter(Boolean);

  const warnings = [];
  if (!previousCol) {
    warnings.push("비교 기준(전년도) 열을 찾지 못해 증감 분석을 생략했습니다.");
  }
  if (unreadableCells > 0) {
    warnings.push(
      `금액으로 읽지 못한 칸 ${unreadableCells}개를 0으로 처리했습니다. 원본을 확인해 주세요.`
    );
  }

  return {
    sheetName,
    columns: { itemCol, deptCol, currentCol, previousCol },
    warnings,
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

  // 전부 증가한 자료에서 "가장 작은 증가"가 감소 최대 항목으로 보고되지 않도록 부호를 확인한다.
  const first = ranked[0] ?? null;
  const last = ranked[ranked.length - 1] ?? null;

  return {
    itemCount: items.length,
    totalCurrent,
    totalPrevious,
    totalDiff,
    totalRate,
    hasPrevious,
    topIncrease: first && first.diff > 0 ? first : null,
    topDecrease: last && last.diff < 0 ? last : null,
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

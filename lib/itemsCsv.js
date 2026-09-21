// 브라우저 API 에 의존하지 않는 CSV 직렬화. exportZip 과 테스트가 함께 쓴다.

// 엑셀은 =, +, -, @ 로 시작하는 텍스트 칸을 수식으로 해석한다.
// 숫자 칸에는 적용하지 않으므로 음수 금액은 영향을 받지 않는다.
const FORMULA_START = /^[=+\-@\t\r]/;

function quote(text) {
  if (/[",\n\r]/.test(text) || text !== text.trim()) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function csvText(value) {
  let text = value == null ? "" : String(value);
  if (FORMULA_START.test(text)) text = `'${text}`;
  return quote(text);
}

function csvNumber(value) {
  if (value == null || value === "") return "";
  return String(value);
}

export const CSV_HEADER = ["항목", "부서", "금년도", "전년도", "증감액", "증감률(%)"];

export function buildItemsCsv(items) {
  const body = items.map((i) =>
    [
      csvText(i.name),
      csvText(i.department),
      csvNumber(i.current),
      csvNumber(i.previous),
      csvNumber(i.diff),
      csvNumber(i.rate == null ? null : Number(i.rate.toFixed(2))),
    ].join(",")
  );
  // 엑셀이 UTF-8 한글을 깨뜨리지 않도록 BOM 을 붙인다.
  return `﻿${[CSV_HEADER.join(","), ...body].join("\r\n")}\r\n`;
}

import test from "node:test";
import assert from "node:assert/strict";

import { buildItemsCsv } from "../lib/itemsCsv.js";

function rowsOf(csv) {
  return csv.replace(/^﻿/, "").trimEnd().split("\r\n");
}

test("엑셀이 한글을 읽도록 BOM 과 CRLF 를 쓴다", () => {
  const csv = buildItemsCsv([{ name: "가", department: "나", current: 1 }]);

  assert.ok(csv.startsWith("﻿"));
  assert.ok(csv.includes("\r\n"));
});

// 회귀: 항목명에 쉼표가 있으면 열이 밀려 CSV 가 통째로 어긋나던 문제.
test("쉼표가 든 항목명은 따옴표로 감싼다", () => {
  const csv = buildItemsCsv([
    { name: "도로, 교량 유지보수", department: "건설과", current: 100, previous: 80, diff: 20, rate: 25 },
  ]);

  const [, row] = rowsOf(csv);
  assert.equal(row, '"도로, 교량 유지보수",건설과,100,80,20,25');
});

test("따옴표는 두 번 겹쳐 이스케이프한다", () => {
  const csv = buildItemsCsv([{ name: '"특별" 사업', department: "", current: 1 }]);

  const [, row] = rowsOf(csv);
  assert.ok(row.startsWith('"""특별"" 사업"'));
});

test("줄바꿈이 든 항목명도 한 칸에 담긴다", () => {
  const csv = buildItemsCsv([{ name: "가\n나", department: "", current: 1 }]);

  assert.ok(csv.includes('"가\n나"'));
});

// 엑셀에서 열었을 때 셀 내용이 수식으로 실행되지 않도록 한다.
test("수식으로 시작하는 텍스트는 무력화한다", () => {
  const csv = buildItemsCsv([
    { name: "=1+1", department: "@SUM(A1)", current: 1 },
  ]);

  const [, row] = rowsOf(csv);
  assert.ok(row.startsWith("'=1+1,'@SUM(A1)"));
});

test("음수 금액은 수식 방어의 영향을 받지 않는다", () => {
  const csv = buildItemsCsv([
    { name: "감액", department: "", current: -500, previous: 100, diff: -600, rate: -600 },
  ]);

  const [, row] = rowsOf(csv);
  assert.equal(row, "감액,,-500,100,-600,-600");
});

test("전년도 자료가 없으면 해당 칸을 비운다", () => {
  const csv = buildItemsCsv([
    { name: "가", department: "", current: 100, previous: null, diff: null, rate: null },
  ]);

  const [, row] = rowsOf(csv);
  assert.equal(row, "가,,100,,,");
});

test("증감률은 소수 둘째 자리까지만 쓴다", () => {
  const csv = buildItemsCsv([
    { name: "가", department: "", current: 100, previous: 3, diff: 97, rate: (97 / 3) * 100 },
  ]);

  const [, row] = rowsOf(csv);
  assert.ok(row.endsWith(",3233.33"));
});

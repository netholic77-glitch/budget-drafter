import test from "node:test";
import assert from "node:assert/strict";
import * as XLSX from "xlsx";

import {
  parseAmount,
  parseWorkbook,
  summarize,
  buildSampleWorkbookRows,
} from "../lib/budgetAnalysis.js";

/** 행 배열을 xlsx 버퍼로 만든다 (앱이 업로드 파일을 다루는 경로와 동일). */
function workbookOf(rows) {
  return XLSX.write(
    { SheetNames: ["Sheet1"], Sheets: { Sheet1: XLSX.utils.json_to_sheet(rows) } },
    { type: "array", bookType: "xlsx" }
  );
}

test("parseAmount: 쉼표·원·공백을 제거한다", () => {
  assert.deepEqual(parseAmount("1,234,000원"), { ok: true, value: 1234000 });
  assert.deepEqual(parseAmount(" 5 000 "), { ok: true, value: 5000 });
  assert.deepEqual(parseAmount(42), { ok: true, value: 42 });
});

test("parseAmount: △ 는 정부 재정문서의 음수 표기다", () => {
  assert.deepEqual(parseAmount("△1,000"), { ok: true, value: -1000 });
  assert.deepEqual(parseAmount("▽500"), { ok: true, value: -500 });
  assert.deepEqual(parseAmount("▼500"), { ok: true, value: -500 });
  assert.deepEqual(parseAmount("-1,000"), { ok: true, value: -1000 });
});

// ▲ 는 자료마다 증가 표지로도 쓰여 관례가 갈린다.
// 부호를 임의로 뒤집으면 조용히 틀린 값이 되므로 표지만 떼어낸다.
test("parseAmount: ▲ 는 부호를 뒤집지 않는다", () => {
  assert.deepEqual(parseAmount("▲1,000"), { ok: true, value: 1000 });
});

test("parseAmount: 회계 괄호 표기는 음수다", () => {
  assert.deepEqual(parseAmount("(2,000)"), { ok: true, value: -2000 });
  assert.deepEqual(parseAmount("（2,000）"), { ok: true, value: -2000 });
});

test("parseAmount: 읽지 못한 값은 ok:false 로 알린다", () => {
  assert.deepEqual(parseAmount("해당없음"), { ok: false, value: 0 });
  assert.deepEqual(parseAmount(""), { ok: false, value: 0 });
  assert.deepEqual(parseAmount(null), { ok: false, value: 0 });
});

test("parseAmount: 전각 숫자를 읽는다", () => {
  assert.deepEqual(parseAmount("１２３"), { ok: true, value: 123 });
});

// 회귀: '전년도예산액' 이 '예산액' 을 포함해 금년도 열로도 잡히면서
// 전년도와 금년도가 같은 열이 되어 모든 증감이 0 으로 나오던 문제.
test("금년도/전년도 열 이름이 서로를 포함해도 구분한다", () => {
  const parsed = parseWorkbook(
    workbookOf([
      { 항목: "도로 유지보수", 부서: "건설과", 전년도예산액: 320000000, 예산액: 410000000 },
    ])
  );

  assert.equal(parsed.columns.previousCol, "전년도예산액");
  assert.equal(parsed.columns.currentCol, "예산액");
  assert.notEqual(parsed.columns.currentCol, parsed.columns.previousCol);
  assert.equal(parsed.items[0].current, 410000000);
  assert.equal(parsed.items[0].previous, 320000000);
  assert.equal(parsed.items[0].diff, 90000000);
});

// 회귀: 연도가 2025/2026 으로 하드코딩되어 있어 회계연도가 바뀌면
// 전년도 열을 찾지 못하고 증감 분석이 통째로 사라지던 문제.
test("연도 헤더는 하드코딩이 아니라 큰 연도를 금년도로 읽는다", () => {
  const parsed = parseWorkbook(
    workbookOf([{ 사업명: "청년지원", "2026년예산": 100, "2027년예산": 150 }])
  );

  assert.equal(parsed.columns.currentCol, "2027년예산");
  assert.equal(parsed.columns.previousCol, "2026년예산");
  assert.equal(parsed.items[0].diff, 50);
});

test("연도 열 순서가 뒤바뀌어 있어도 큰 연도가 금년도다", () => {
  const parsed = parseWorkbook(
    workbookOf([{ 사업명: "청년지원", "2030년": 150, "2029년": 100 }])
  );

  assert.equal(parsed.columns.currentCol, "2030년");
  assert.equal(parsed.columns.previousCol, "2029년");
});

test("증감·비율 열은 금액 열 후보에서 제외한다", () => {
  const parsed = parseWorkbook(
    workbookOf([{ 사업명: "가", 전년도예산: 100, 예산액: 150, 증감액: 50, 증감률: 50 }])
  );

  assert.equal(parsed.columns.currentCol, "예산액");
  assert.equal(parsed.columns.previousCol, "전년도예산");
});

test("추경 자료의 기정예산을 비교 기준으로 읽는다", () => {
  const parsed = parseWorkbook(
    workbookOf([{ 세부사업명: "가", 소관부서: "기획조정실", 기정예산: 1000, 추경예산: 1200 }])
  );

  assert.equal(parsed.columns.deptCol, "소관부서");
  assert.equal(parsed.columns.previousCol, "기정예산");
  assert.equal(parsed.columns.currentCol, "추경예산");
  assert.equal(parsed.items[0].diff, 200);
});

test("△ 로 적힌 감액이 0 이 아니라 음수로 반영된다", () => {
  const parsed = parseWorkbook(
    workbookOf([{ 항목: "감액사업", 전년도: 5000, 예산액: "△1,000" }])
  );

  assert.equal(parsed.items[0].current, -1000);
  assert.equal(parsed.items[0].diff, -6000);
});

test("읽지 못한 금액 칸이 있으면 경고를 남긴다", () => {
  const parsed = parseWorkbook(
    workbookOf([
      { 항목: "가", 전년도: 100, 예산액: 200 },
      { 항목: "나", 전년도: 100, 예산액: "비예산" },
    ])
  );

  assert.equal(parsed.items[1].current, 0);
  assert.equal(parsed.warnings.length, 1);
  assert.match(parsed.warnings[0], /읽지 못한/);
});

test("비교 기준 열이 없으면 경고하고 증감을 생략한다", () => {
  const parsed = parseWorkbook(workbookOf([{ 항목: "가", 예산액: 200 }]));

  assert.equal(parsed.columns.previousCol, null);
  assert.equal(parsed.items[0].previous, null);
  assert.equal(parsed.items[0].diff, null);
  assert.match(parsed.warnings[0], /비교 기준/);
});

test("항목명이 같아도 항목마다 고유 id 를 갖는다", () => {
  const parsed = parseWorkbook(
    workbookOf([
      { 항목: "사무관리비", 부서: "건설과", 예산액: 100 },
      { 항목: "사무관리비", 부서: "복지과", 예산액: 200 },
    ])
  );

  const ids = parsed.items.map((i) => i.id);
  assert.equal(new Set(ids).size, ids.length);
});

test("빈 시트는 오류를 던진다", () => {
  assert.throws(() => parseWorkbook(workbookOf([])), /데이터를 찾을 수 없습니다/);
});

test("금액 열이 없으면 안내와 함께 오류를 던진다", () => {
  assert.throws(
    () => parseWorkbook(workbookOf([{ 항목: "가", 비고: "메모" }])),
    /예산액 열을 찾지 못했습니다/
  );
});

test("summarize: 총계와 증감을 계산한다", () => {
  const parsed = parseWorkbook(workbookOf(buildSampleWorkbookRows()));
  const summary = summarize(parsed.items);

  assert.equal(summary.itemCount, 8);
  assert.equal(summary.hasPrevious, true);
  assert.equal(summary.totalCurrent, 2475000000);
  assert.equal(summary.totalPrevious, 2115000000);
  assert.equal(summary.totalDiff, 360000000);
  assert.equal(summary.topIncrease.name, "공원 조성");
  assert.equal(summary.topDecrease.name, "청년 창업 지원");
});

// 회귀: 모든 항목이 증가한 자료에서 '가장 작게 증가한 항목' 이
// 감소 최대 항목으로 보고되던 문제.
test("summarize: 전부 증가하면 감소 최대 항목은 없다", () => {
  const parsed = parseWorkbook(
    workbookOf([
      { 항목: "가", 전년도: 100, 예산액: 200 },
      { 항목: "나", 전년도: 100, 예산액: 110 },
    ])
  );
  const summary = summarize(parsed.items);

  assert.equal(summary.topIncrease.name, "가");
  assert.equal(summary.topDecrease, null);
});

test("summarize: 전년도 자료가 없으면 증감을 비운다", () => {
  const parsed = parseWorkbook(workbookOf([{ 항목: "가", 예산액: 200 }]));
  const summary = summarize(parsed.items);

  assert.equal(summary.hasPrevious, false);
  assert.equal(summary.totalDiff, null);
  assert.equal(summary.totalRate, null);
  assert.equal(summary.topIncrease, null);
});

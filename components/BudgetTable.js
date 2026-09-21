"use client";

import { useMemo, useState } from "react";

function formatWon(value) {
  if (value == null) return "-";
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

function formatRate(value) {
  if (value == null) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function toneOf(diff) {
  if (diff == null || diff === 0) return "flat";
  return diff > 0 ? "up" : "down";
}

const SORTERS = {
  name: (a, b) => a.name.localeCompare(b.name, "ko"),
  current: (a, b) => b.current - a.current,
  diff: (a, b) => (b.diff ?? 0) - (a.diff ?? 0),
  rate: (a, b) => (b.rate ?? 0) - (a.rate ?? 0),
};

export default function BudgetTable({ items, hasPrevious }) {
  const [sortKey, setSortKey] = useState("current");

  const sorted = useMemo(() => {
    const sorter = SORTERS[sortKey] ?? SORTERS.current;
    return [...items].sort(sorter);
  }, [items, sortKey]);

  // 세부사업이 수천 건인 예산서에서 Math.max(...arr) 는 스택을 넘기므로 reduce 를 쓴다.
  const maxAbsDiff = useMemo(
    () => items.reduce((max, i) => Math.max(max, Math.abs(i.diff ?? 0)), 1),
    [items]
  );

  return (
    <div className="table-wrap">
      <div className="table-controls">
        <label htmlFor="sort-select">정렬</label>
        <select id="sort-select" value={sortKey} onChange={(e) => setSortKey(e.target.value)}>
          <option value="current">금년도 예산 많은 순</option>
          <option value="name">이름순</option>
          {hasPrevious && <option value="diff">증감액 큰 순</option>}
          {hasPrevious && <option value="rate">증감률 큰 순</option>}
        </select>
      </div>
      <table className="budget-table">
        <thead>
          <tr>
            <th>항목</th>
            <th>부서</th>
            <th>금년도</th>
            {hasPrevious && <th>전년도</th>}
            {hasPrevious && <th>증감</th>}
          </tr>
        </thead>
        <tbody>
          {sorted.map((item) => (
            <tr key={item.id ?? `${item.name}-${item.department}`}>
              <td>{item.name}</td>
              <td>{item.department || "-"}</td>
              <td className="num">{formatWon(item.current)}</td>
              {hasPrevious && <td className="num">{formatWon(item.previous)}</td>}
              {hasPrevious && (
                <td className="num diff-cell">
                  <div className="diff-bar-track">
                    <div
                      className={`diff-bar ${toneOf(item.diff)}`}
                      style={{ width: `${(Math.abs(item.diff ?? 0) / maxAbsDiff) * 100}%` }}
                    />
                  </div>
                  <span className={`${toneOf(item.diff)}-text`}>
                    {formatWon(item.diff)} ({formatRate(item.rate)})
                  </span>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

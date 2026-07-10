function formatWon(value) {
  if (value == null) return "-";
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

function formatRate(value) {
  if (value == null) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export default function SummaryCards({ summary }) {
  const cards = [
    { label: "항목 수", value: `${summary.itemCount}개` },
    { label: "금년도 총예산", value: formatWon(summary.totalCurrent) },
    {
      label: "전년도 총예산",
      value: summary.hasPrevious ? formatWon(summary.totalPrevious) : "데이터 없음",
    },
    {
      label: "총 증감",
      value: summary.hasPrevious
        ? `${formatWon(summary.totalDiff)} (${formatRate(summary.totalRate)})`
        : "-",
      tone: summary.hasPrevious
        ? summary.totalDiff >= 0
          ? "up"
          : "down"
        : "neutral",
    },
  ];

  return (
    <div className="summary-grid">
      {cards.map((card) => (
        <div className={`summary-card tone-${card.tone ?? "neutral"}`} key={card.label}>
          <span className="summary-label">{card.label}</span>
          <span className="summary-value">{card.value}</span>
        </div>
      ))}
    </div>
  );
}

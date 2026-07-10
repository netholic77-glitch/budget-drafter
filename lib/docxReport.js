import {
  Document,
  Packer,
  Paragraph,
  Table,
  TableRow,
  TableCell,
  TextRun,
  HeadingLevel,
  WidthType,
  AlignmentType,
} from "docx";

function formatWon(value) {
  if (value == null) return "-";
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

function formatRate(value) {
  if (value == null) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function headerCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })] })],
    shading: { fill: "EEEEEE" },
  });
}

function cell(text) {
  return new TableCell({ children: [new Paragraph(text)] });
}

export async function buildBudgetReport({ sourceName, summary, items }) {
  const rows = [
    new TableRow({
      children: [
        headerCell("항목"),
        headerCell("부서"),
        headerCell("금년도"),
        headerCell("전년도"),
        headerCell("증감액"),
        headerCell("증감률"),
      ],
    }),
    ...items.map(
      (item) =>
        new TableRow({
          children: [
            cell(item.name),
            cell(item.department || "-"),
            cell(formatWon(item.current)),
            cell(formatWon(item.previous)),
            cell(formatWon(item.diff)),
            cell(formatRate(item.rate)),
          ],
        })
    ),
  ];

  const doc = new Document({
    sections: [
      {
        children: [
          new Paragraph({
            text: "예산분석 보고서",
            heading: HeadingLevel.TITLE,
            alignment: AlignmentType.CENTER,
          }),
          new Paragraph({
            text: `분석 대상 파일: ${sourceName}`,
            spacing: { after: 100 },
          }),
          new Paragraph({
            text: `생성일: ${new Date().toLocaleDateString("ko-KR")}`,
            spacing: { after: 300 },
          }),
          new Paragraph({ text: "요약", heading: HeadingLevel.HEADING_1 }),
          new Paragraph(`총 항목 수: ${summary.itemCount}개`),
          new Paragraph(`금년도 총예산: ${formatWon(summary.totalCurrent)}`),
          summary.hasPrevious
            ? new Paragraph(`전년도 총예산: ${formatWon(summary.totalPrevious)}`)
            : new Paragraph("전년도 예산 데이터 없음"),
          summary.hasPrevious
            ? new Paragraph(
                `총 증감액: ${formatWon(summary.totalDiff)} (${formatRate(summary.totalRate)})`
              )
            : new Paragraph(""),
          summary.topIncrease
            ? new Paragraph(
                `증가 최대 항목: ${summary.topIncrease.name} (${formatWon(
                  summary.topIncrease.diff
                )})`
              )
            : new Paragraph(""),
          summary.topDecrease
            ? new Paragraph(
                `감소 최대 항목: ${summary.topDecrease.name} (${formatWon(
                  summary.topDecrease.diff
                )})`
              )
            : new Paragraph(""),
          new Paragraph({
            text: "항목별 내역",
            heading: HeadingLevel.HEADING_1,
            spacing: { before: 300 },
          }),
          new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows }),
        ],
      },
    ],
  });

  return Packer.toBlob(doc);
}

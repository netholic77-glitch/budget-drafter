import JSZip from "jszip";
import { saveAs } from "file-saver";
import { buildBudgetReport } from "./docxReport";

export async function exportAnalysisZip({ sourceName, summary, items }) {
  const zip = new JSZip();

  zip.file("summary.json", JSON.stringify(summary, null, 2));
  zip.file("items.json", JSON.stringify(items, null, 2));

  const csvHeader = "항목,부서,금년도,전년도,증감액,증감률\n";
  const csvBody = items
    .map((i) =>
      [i.name, i.department, i.current, i.previous ?? "", i.diff ?? "", i.rate ?? ""].join(",")
    )
    .join("\n");
  zip.file("items.csv", csvHeader + csvBody);

  const reportBlob = await buildBudgetReport({ sourceName, summary, items });
  zip.file("예산분석_보고서.docx", reportBlob);

  const blob = await zip.generateAsync({ type: "blob" });
  saveAs(blob, `예산분석_${sourceName.replace(/\.[^.]+$/, "")}.zip`);
}

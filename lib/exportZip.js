import JSZip from "jszip";
import { saveAs } from "file-saver";
import { buildBudgetReport } from "./docxReport";
import { buildItemsCsv } from "./itemsCsv";

export async function exportAnalysisZip({ sourceName, summary, items }) {
  const zip = new JSZip();

  zip.file("summary.json", JSON.stringify(summary, null, 2));
  zip.file("items.json", JSON.stringify(items, null, 2));
  zip.file("items.csv", buildItemsCsv(items));

  const reportBlob = await buildBudgetReport({ sourceName, summary, items });
  zip.file("예산분석_보고서.docx", reportBlob);

  const blob = await zip.generateAsync({ type: "blob" });
  saveAs(blob, `예산분석_${sourceName.replace(/\.[^.]+$/, "")}.zip`);
}

"use client";

import { useCallback, useRef, useState } from "react";
import {
  parseWorkbook,
  summarize,
  buildSampleWorkbookRows,
} from "@/lib/budgetAnalysis";
import { extractPdfText } from "@/lib/pdfText";
import { buildBudgetReport } from "@/lib/docxReport";
import { exportAnalysisZip } from "@/lib/exportZip";
import { saveAs } from "file-saver";
import * as XLSX from "xlsx";
import SummaryCards from "@/components/SummaryCards";
import BudgetTable from "@/components/BudgetTable";

export default function Home() {
  const [sourceName, setSourceName] = useState("");
  const [items, setItems] = useState(null);
  const [summary, setSummary] = useState(null);
  const [pdfText, setPdfText] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [generating, setGenerating] = useState(false);
  const inputRef = useRef(null);

  const reset = () => {
    setItems(null);
    setSummary(null);
    setPdfText(null);
    setError("");
  };

  const handleWorkbookRows = useCallback((rows, name) => {
    const buffer = XLSX.write(
      { SheetNames: ["Sheet1"], Sheets: { Sheet1: XLSX.utils.json_to_sheet(rows) } },
      { type: "array", bookType: "xlsx" }
    );
    const parsed = parseWorkbook(buffer);
    setItems(parsed.items);
    setSummary(summarize(parsed.items));
    setSourceName(name);
    setStatus("done");
  }, []);

  const handleFile = useCallback(async (file) => {
    reset();
    setStatus("loading");
    setSourceName(file.name);
    try {
      const buffer = await file.arrayBuffer();
      const ext = file.name.split(".").pop().toLowerCase();

      if (ext === "xlsx" || ext === "xls" || ext === "csv") {
        const parsed = parseWorkbook(buffer);
        setItems(parsed.items);
        setSummary(summarize(parsed.items));
        setStatus("done");
      } else if (ext === "pdf") {
        const result = await extractPdfText(buffer);
        setPdfText(result);
        setStatus("done");
      } else {
        throw new Error("엑셀(.xlsx, .xls, .csv) 또는 PDF 파일만 지원합니다.");
      }
    } catch (err) {
      setError(err.message || "파일을 처리하는 중 오류가 발생했습니다.");
      setStatus("error");
    }
  }, []);

  const onInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const loadSample = () => {
    reset();
    handleWorkbookRows(buildSampleWorkbookRows(), "샘플_예산자료.xlsx");
  };

  const downloadReport = async () => {
    if (!items || !summary) return;
    setGenerating(true);
    try {
      const blob = await buildBudgetReport({ sourceName, summary, items });
      saveAs(blob, `예산분석_보고서_${sourceName.replace(/\.[^.]+$/, "")}.docx`);
    } finally {
      setGenerating(false);
    }
  };

  const downloadZip = async () => {
    if (!items || !summary) return;
    setGenerating(true);
    try {
      await exportAnalysisZip({ sourceName, summary, items });
    } finally {
      setGenerating(false);
    }
  };

  return (
    <main className="page">
      <header className="hero">
        <h1>예산분석지원 시스템</h1>
        <p>엑셀·PDF 예산 자료를 업로드하면 전년 대비 증감을 분석하고, 보고서를 자동으로 만들어 드립니다.</p>
      </header>

      <section
        className="dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv,.pdf"
          onChange={onInputChange}
          hidden
        />
        <p className="dropzone-title">파일을 여기에 끌어다 놓거나 클릭해서 선택하세요</p>
        <p className="dropzone-sub">엑셀(.xlsx, .xls, .csv) — 항목/예산액/전년도 열 포함 · PDF도 지원</p>
        <button
          type="button"
          className="btn-secondary"
          onClick={(e) => {
            e.stopPropagation();
            loadSample();
          }}
        >
          샘플 데이터로 체험하기
        </button>
      </section>

      {status === "loading" && <p className="status-line">"{sourceName}" 분석 중…</p>}
      {status === "error" && <p className="status-line status-error">{error}</p>}

      {summary && items && (
        <section className="results">
          <h2>{sourceName}</h2>
          <SummaryCards summary={summary} />
          <BudgetTable items={items} hasPrevious={summary.hasPrevious} />
          <div className="actions">
            <button type="button" className="btn-primary" onClick={downloadReport} disabled={generating}>
              워드 보고서 다운로드 (.docx)
            </button>
            <button type="button" className="btn-secondary" onClick={downloadZip} disabled={generating}>
              전체 데이터 zip 다운로드
            </button>
          </div>
        </section>
      )}

      {pdfText && (
        <section className="results">
          <h2>{sourceName} — 텍스트 추출 결과 ({pdfText.numPages}페이지)</h2>
          <p className="hint">
            PDF는 표 구조가 자동 인식되지 않아 텍스트만 추출합니다. 정밀 분석이 필요하면 엑셀 형식을 이용해 주세요.
          </p>
          <pre className="pdf-preview">{pdfText.fullText.slice(0, 5000)}</pre>
        </section>
      )}
    </main>
  );
}

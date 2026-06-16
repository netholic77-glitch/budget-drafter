"""PDF 파일에서 텍스트를 추출."""
from __future__ import annotations

import io

import pdfplumber


def extract_text_from_pdf(file_obj: io.BytesIO | bytes) -> str:
    """PDF 바이트/파일객체에서 페이지별 텍스트를 합쳐 반환한다.

    pdfplumber가 한글 PDF의 텍스트 레이어를 가장 안정적으로 추출한다.
    스캔본(이미지 PDF)일 경우 빈 문자열이 나올 수 있어 호출 측에서 검증 필요.
    """
    if isinstance(file_obj, bytes):
        file_obj = io.BytesIO(file_obj)

    pages_text: list[str] = []
    with pdfplumber.open(file_obj) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages_text.append(f"--- [Page {i}] ---\n{text}")

    return "\n\n".join(pages_text).strip()

"""HWPX 파일에서 텍스트를 추출.

HWPX는 ZIP 컨테이너 안에 XML 파일들이 든 구조다.
본문은 Contents/section*.xml 에 들어 있고, 텍스트 노드는
한컴 네임스페이스의 <hp:t> 요소에 있다.

여기서는 네임스페이스에 의존하지 않고, 모든 element의 text를 모은다.
주석/숨김 단락도 잡힐 수 있지만 분석용 발췌로는 충분하다.

HWP(.hwp, 한글 5.x 바이너리) 형식은 지원하지 않는다.
사용자는 한컴에서 '다른 이름으로 저장 → HWPX'로 변환하거나,
본문을 텍스트로 복사·붙여넣기 해야 한다.
"""
from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile


def extract_text_from_hwpx(file_obj: io.BytesIO | bytes) -> str:
    if isinstance(file_obj, bytes):
        file_obj = io.BytesIO(file_obj)

    sections_text: list[str] = []
    with zipfile.ZipFile(file_obj, "r") as zf:
        # Contents/sectionN.xml 들을 순서대로 처리
        section_names = sorted(
            n for n in zf.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        )
        if not section_names:
            raise ValueError("HWPX 본문(Contents/section*.xml)을 찾을 수 없습니다. 올바른 HWPX 파일인지 확인하세요.")

        for name in section_names:
            xml_bytes = zf.read(name)
            try:
                root = ET.fromstring(xml_bytes)
            except ET.ParseError as e:
                sections_text.append(f"[{name} 파싱 실패: {e}]")
                continue

            chunks: list[str] = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    chunks.append(elem.text)
                if elem.tail and elem.tail.strip():
                    chunks.append(elem.tail)

            sections_text.append("\n".join(chunks))

    return "\n\n".join(sections_text).strip()

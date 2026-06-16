"""규칙기반 예산분석 초안 생성기 (오프라인 · API 불필요).

집행률·실집행률 등 구조화된 입력과 사업설명서 본문의 키워드를 분석하여
표준양식 3개 섹션(사업개요·현황 / 문제점 / 분석의견)의 초안을 생성한다.
LLM을 쓰지 않으므로 인터넷·API 키 없이 동작하며, 결과는 분석가가 편집한다.

문제점과 분석의견은 같은 번호로 1:1 대응되도록 생성하여,
"무엇이 문제이고 → 어떻게 대응할지"가 한눈에 매칭되게 한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


@dataclass
class DraftResult:
    overview: str = ""
    issues: str = ""
    analysis: str = ""
    findings_count: int = 0


def _circled(n: int) -> str:
    return _CIRCLED[n - 1] if 1 <= n <= len(_CIRCLED) else f"{n})"


# ────────────────── 숫자/비율 파싱 ──────────────────
def _to_float(value) -> float | None:
    """정수·실수·'1,500'·'64%'·'1500백만원' 등에서 숫자를 추출."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        f = float(value)
        return f if f == f else None  # NaN 제외
    s = str(value).strip()
    if not s:
        return None
    s = s.replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def _as_rate(value) -> float | None:
    """집행률 값을 0~100 범위로 정규화 (0.64 → 64)."""
    f = _to_float(value)
    if f is None:
        return None
    if 0 < f <= 1:
        f *= 100
    return f


def _get(info: dict | None, *keys: str):
    if not info:
        return None
    for k in keys:
        if k in info and info[k] not in (None, ""):
            return info[k]
    return None


def _fmt(f: float | None) -> str:
    if f is None:
        return "-"
    if abs(f - round(f)) < 1e-9:
        return f"{int(round(f)):,}"
    return f"{f:,.1f}"


def _find_line(text: str | None, keywords: list[str]) -> str | None:
    """본문에서 keyword가 포함된 첫 줄을 머리기호를 떼고 반환."""
    if not text:
        return None
    for raw in re.split(r"[\n\r]+", text):
        line = raw.strip(" \t-·∙•○□▪◦*[]")
        if not line:
            continue
        if any(kw in line for kw in keywords):
            return line
    return None


def _evidence(line: str, limit: int = 120) -> str:
    return line if len(line) <= limit else line[:limit] + "…"


# ────────────────── 섹션 1: 사업개요 및 현황 ──────────────────
def _build_overview(
    project_name: str,
    department: str,
    fiscal_year: str,
    info: dict | None,
    source_text: str,
) -> str:
    budget = _to_float(_get(info, "예산현액", "예산", "예산액", "현액", "본예산"))
    executed = _to_float(_get(info, "집행액", "집행", "지출액", "지출"))
    rate = _as_rate(_get(info, "집행률", "집행율"))
    real = _as_rate(_get(info, "실집행률", "실집행율"))

    lines: list[str] = [
        f"□ 사업명: {project_name or '(미입력)'}",
        f"□ 소관부서: {department or '(미입력)'}",
        f"□ 회계연도: {fiscal_year or '(미입력)'}",
    ]

    seg: list[str] = []
    if budget is not None:
        seg.append(f"예산현액 {_fmt(budget)}백만원")
    if executed is not None:
        seg.append(f"집행액 {_fmt(executed)}백만원")
    if rate is not None:
        seg.append(f"집행률 {_fmt(rate)}%")
    if real is not None:
        seg.append(f"실집행률 {_fmt(real)}%")
    if seg:
        lines.append("□ 예산·집행: " + ", ".join(seg))

    lines.append("")

    purpose = _find_line(source_text, ["사업목적", "목적"])
    period = _find_line(source_text, ["사업기간", "기간"])
    basis = _find_line(source_text, ["근거", "법적근거", "추진근거", "관련근거"])
    if purpose:
        lines.append(f"○ {purpose}")
    if period:
        lines.append(f"○ {period}")
    if basis:
        lines.append(f"○ {basis}")

    if budget is not None and executed is not None:
        unexec = budget - executed
        narr = (
            f"○ 집행현황: 예산현액 {_fmt(budget)}백만원 중 {_fmt(executed)}백만원을 집행"
            f"(집행률 {_fmt(rate)}%)하여 미집행액 {_fmt(unexec)}백만원이 발생함."
        )
        if real is not None:
            narr += f" 실집행률은 {_fmt(real)}%로 확인됨."
        lines.append(narr)
    elif rate is not None:
        lines.append(f"○ 집행현황: 당해연도 집행률은 {_fmt(rate)}%로 확인됨.")

    if not (purpose or period or basis) and not (source_text or "").strip():
        lines.append(
            "○ (사업 목적·기간·근거 등은 '② 자료 입력'에 사업설명서를 넣으면 자동 추출됩니다. 직접 보완하세요.)"
        )

    return "\n".join(lines).strip()


# ────────────────── 섹션 2·3: 문제점/분석의견 탐지 ──────────────────
def _detect_findings(info: dict | None, source_text: str) -> list[dict]:
    """각 항목을 (issue, opinion) 쌍으로 반환. 문제점↔의견 번호가 1:1 대응됨."""
    findings: list[dict] = []
    text = source_text or ""

    budget = _to_float(_get(info, "예산현액", "예산", "예산액", "현액", "본예산"))
    executed = _to_float(_get(info, "집행액", "집행", "지출액", "지출"))
    rate = _as_rate(_get(info, "집행률", "집행율"))
    real = _as_rate(_get(info, "실집행률", "실집행율"))

    # 1) 집행률 구간별 부진
    if rate is not None:
        unexec_txt = ""
        if budget is not None and executed is not None:
            unexec_txt = f" 미집행액 {_fmt(budget - executed)}백만원이 발생함."
        if rate < 50:
            findings.append({
                "issue": f"집행 실적 매우 저조 — 당해연도 집행률이 {_fmt(rate)}%에 그쳐 "
                         f"예산 집행이 정상적으로 이루어지지 않고 있음.{unexec_txt}",
                "opinion": "집행 부진의 구조적 원인을 규명하고 잔여기간 집행계획을 전면 재수립할 필요가 있음. "
                           "집행 가능성이 낮은 예산은 감액조정 또는 사업 재설계를 검토할 필요가 있음.",
            })
        elif rate < 70:
            findings.append({
                "issue": f"집행 실적 저조 — 당해연도 집행률이 {_fmt(rate)}%로 목표 대비 부진함.{unexec_txt}",
                "opinion": "집행 지연 사유를 분석하고 잔여 예산의 집행계획 보완을 요구할 필요가 있음. "
                           "불용 예상액에 대한 대책 마련이 요구됨.",
            })
        elif rate < 85:
            findings.append({
                "issue": f"집행 실적 다소 부진 — 집행률이 {_fmt(rate)}%로 연내 전액 집행 여부에 대한 "
                         f"점검이 필요함.{unexec_txt}",
                "opinion": "연말 집행 집중(이월·불용) 가능성을 점검하고 균형 있는 집행 관리를 요구할 필요가 있음.",
            })

    # 2) 집행률-실집행률 격차(이월·불용 우려)
    if rate is not None and real is not None and (rate - real) >= 5:
        gap = rate - real
        findings.append({
            "issue": f"교부 후 실집행 지연 — 집행률 {_fmt(rate)}% 대비 실집행률이 {_fmt(real)}%로 "
                     f"{_fmt(gap)}%p 낮아, 교부 후 실제 집행이 지연되어 이월·불용 발생이 우려됨.",
            "opinion": "교부·정산 시기를 점검하고 실집행 기준의 성과관리를 강화할 필요가 있음. "
                       "이월·불용 최소화 방안 마련을 요구할 필요가 있음.",
        })
    elif real is not None and real < 50 and (rate is None or (rate - real) < 5):
        findings.append({
            "issue": f"실집행률 저조 — 실집행률이 {_fmt(real)}%로 낮아 실제 사업 효과 발생이 지연되고 있음.",
            "opinion": "실집행 부진 사유를 확인하고 집행 독려 및 정산 점검을 강화할 필요가 있음.",
        })

    # 3) 본문 키워드 기반 (근거 문장 인용)
    keyword_rules = [
        (["중도포기", "중도탈락", "이탈", "탈락", "포기"],
         "중도이탈 발생",
         "사업 대상자의 중도이탈이 확인되어 사업 효과 저하가 우려됨",
         "중도이탈 사유를 분석하고 사후관리·환류체계를 보완할 필요가 있음."),
        (["미실시", "미시행", "미개최", "실시하지", "시행하지"],
         "계획 대비 미실시 항목",
         "사업계획 대비 일부 항목이 미실시된 것으로 확인됨",
         "미실시 사유를 확인하고 잔여 계획의 이행 담보 방안을 요구할 필요가 있음."),
        (["미달", "미이수", "이수율", "달성률"],
         "목표 대비 실적 미달",
         "당초 목표 대비 실적이 미달된 정황이 확인됨",
         "실적 미달 원인을 분석하고 성과지표의 현실화를 검토할 필요가 있음."),
        (["중복", "유사사업", "유사 사업"],
         "유사·중복 가능성",
         "유사하거나 중복되는 사업이 존재할 가능성이 제기됨",
         "유사·중복 사업과의 관계를 점검하여 통폐합 또는 역할 재정립을 검토할 필요가 있음."),
    ]
    for keys, title, basis, opinion in keyword_rules:
        line = _find_line(text, keys)
        if line:
            findings.append({
                "issue": f"{title} — {basis}. (근거: \"{_evidence(line)}\")",
                "opinion": opinion,
            })

    # 성과 점검·환류 미비 (만족도/성과측정 + 부정맥락일 때만)
    sat_line = _find_line(text, ["만족도", "성과측정", "성과평가", "환류"])
    if sat_line and any(neg in sat_line for neg in ["미실시", "미조사", "안 함", "없", "부재", "미흡", "미시행"]):
        findings.append({
            "issue": f"성과 점검·환류 체계 미비 — 성과 측정·만족도 조사 등 환류 절차가 작동하지 않는 것으로 "
                     f"보임. (근거: \"{_evidence(sat_line)}\")",
            "opinion": "성과지표를 설정하고 정기적인 점검·환류 체계를 구축할 필요가 있음.",
        })

    return findings


# ────────────────── 진입점 ──────────────────
def generate_draft(
    project_name: str,
    department: str,
    fiscal_year: str,
    source_text: str,
    execution_info: dict | None = None,
) -> DraftResult:
    """구조화 입력+본문 키워드로 3개 섹션 초안을 생성. (LLM·API 불필요)"""
    overview = _build_overview(project_name, department, fiscal_year, execution_info, source_text)
    findings = _detect_findings(execution_info, source_text)

    if findings:
        issues = "\n".join(f"{_circled(i)} {f['issue']}" for i, f in enumerate(findings, 1))
        analysis = "\n".join(f"{_circled(i)} {f['opinion']}" for i, f in enumerate(findings, 1))
    else:
        issues = (
            "자동 탐지된 문제점이 없습니다. 집행률·실집행률 수치와 사업설명서 내용을 확인하여 직접 작성하세요.\n"
            "(팁: '① 저조사업 스크리닝'에서 사업을 선택하면 집행률 기반 문제점이 자동 생성됩니다.)"
        )
        analysis = "문제점 확정 후 대응 개선방안을 작성하세요."

    analysis += (
        "\n\n※ 추가 검토: 집행부에 집행 부진 사유서·잔여 집행계획·성과 실적자료 등 추가 자료를 요구하여 "
        "2차 분석을 진행할 필요가 있음."
    )

    return DraftResult(
        overview=overview,
        issues=issues,
        analysis=analysis,
        findings_count=len(findings),
    )

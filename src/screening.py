"""저조사업 스크리닝 - 집행률 엑셀 파싱 및 임계치 필터링.

공공기관 집행률 엑셀은 양식이 표준화되어 있지 않으므로
컬럼명을 자동 추정한 뒤, 사용자가 매핑을 수정할 수 있도록 한다.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd


STANDARD_COLUMNS = ["사업명", "예산현액", "집행액", "집행률", "실집행률"]


COLUMN_ALIASES = {
    "사업명": ["사업명", "세부사업명", "단위사업명", "정책사업명", "사업"],
    "예산현액": ["예산현액", "예산액", "예산", "현액", "본예산"],
    "집행액": ["집행액", "집행", "지출액", "지출"],
    "집행률": ["집행률", "집행율", "집행 률", "집행률(%)", "집행률%"],
    "실집행률": ["실집행률", "실집행율", "실집행률(%)", "실 집행률", "실집행률%"],
}


@dataclass
class ColumnMapping:
    """엑셀 실제 컬럼명 → 표준 컬럼명 매핑."""

    project_name: str | None = None
    budget: str | None = None
    executed: str | None = None
    execution_rate: str | None = None
    real_execution_rate: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "사업명": self.project_name,
            "예산현액": self.budget,
            "집행액": self.executed,
            "집행률": self.execution_rate,
            "실집행률": self.real_execution_rate,
        }

    @property
    def is_complete_for_filtering(self) -> bool:
        """필터링에 필수인 컬럼이 모두 매핑됐는지."""
        return bool(self.project_name and self.execution_rate)


def read_budget_excel(file_bytes: bytes, sheet_name: str | int = 0, header_row: int = 0) -> pd.DataFrame:
    """엑셀 바이트를 DataFrame으로 변환.

    header_row: 0-indexed. 병합 헤더가 있는 경우 사용자가 조정.
    """
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=header_row)
    # 컬럼명 공백 제거
    df.columns = [str(c).strip() for c in df.columns]
    # 빈 행 제거
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def _first(seq):
    return seq[0] if seq else None


def detect_and_read_execution_status(file_bytes: bytes) -> pd.DataFrame | None:
    """'사업별예산집행현황' 형식이면 세부사업 단위 집행률을 계산해 정규화 후 반환.

    이 형식 특징:
      - 머리글이 여러 행에 병합돼 있고(맨 위는 제목행), 데이터는 컬럼명 행 다음부터.
      - 집행률 컬럼이 없음 → '지출액(C) / 예산현액'으로 직접 계산해야 함.
      - 총계/회계/부서/정책/단위/세부 소계 행이 섞여 있어 세부사업 leaf만 추려야 함.

    형식이 아니면 None을 반환하여 호출측이 일반 엑셀 경로로 폴백하게 한다.
    반환 컬럼: 회계연도·부서명·정책사업명·단위사업명·세부사업명·예산현액·집행액·집행률
    (금액 단위: 백만원, 집행률: %)
    """
    try:
        full = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, header=None)
    except Exception:
        return None
    if full.empty:
        return None

    # 컬럼명 행 탐색: '세부사업명'과 '부서명'이 같은 행에 존재
    hdr_row = None
    for r in range(min(12, len(full))):
        row = [str(v) for v in full.iloc[r].tolist()]
        if any("세부사업명" in v for v in row) and any("부서명" in v for v in row):
            hdr_row = r
            break
    if hdr_row is None:
        return None

    # 헤더행 위의 그룹 머리글(병합)을 ffill 해서 합성 컬럼명 구성 (제목행=단일셀은 제외)
    group_rows = [full.iloc[r].ffill() for r in range(hdr_row) if full.iloc[r].notna().sum() >= 2]
    names: list[str] = []
    for j in range(full.shape[1]):
        parts: list[str] = []
        for gr in group_rows:
            v = gr.iloc[j]
            if pd.notna(v) and str(v).strip():
                parts.append(str(v).strip())
        h = full.iloc[hdr_row, j]
        if pd.notna(h) and str(h).strip():
            parts.append(str(h).strip())
        names.append(" / ".join(dict.fromkeys(parts)))

    def ends(suffix: str):
        return _first([n for n in names if n.split(" / ")[-1] == suffix])

    col_year = ends("회계연도")
    col_dept = ends("부서명")
    col_pol = ends("정책사업명")
    col_unit = ends("단위사업명")
    col_sub = ends("세부사업명")
    col_stat = ends("통계목")
    col_budget = _first([n for n in names if "예산현액" in n and n.split(" / ")[-1] == "계"])
    col_spent = _first([n for n in names if "지출액(C)" in n and n.split(" / ")[-1] == "계"])
    if col_spent is None:  # 일부 양식은 그룹명만 '지출'
        col_spent = _first([n for n in names if "지출" in n and n.split(" / ")[-1] == "계"])

    if not (col_sub and col_budget and col_spent):
        return None

    data = full.iloc[hdr_row + 1:].reset_index(drop=True)
    data.columns = names

    # 세부사업 leaf 행: 세부사업명 있고 통계목 비어있음(통계목 분해행 제외)
    sub_s = data[col_sub].astype(str).str.strip()
    mask = data[col_sub].notna() & sub_s.ne("") & sub_s.ne("nan")
    if col_stat:
        stat_s = data[col_stat].astype(str).str.strip()
        mask &= data[col_stat].isna() | stat_s.eq("") | stat_s.eq("nan")
    leaf = data[mask].copy()
    if leaf.empty:
        return None

    leaf["_예산"] = pd.to_numeric(leaf[col_budget], errors="coerce")
    leaf["_지출"] = pd.to_numeric(leaf[col_spent], errors="coerce")

    # 같은 세부사업이 재원별로 여러 행이면 합산(세부사업 단위 집행률)
    keys = [c for c in (col_year, col_dept, col_pol, col_unit, col_sub) if c]
    agg = leaf.groupby(keys, dropna=False, as_index=False).agg(
        _예산=("_예산", "sum"), _지출=("_지출", "sum")
    )
    agg = agg[agg["_예산"] > 0].reset_index(drop=True)
    if agg.empty:
        return None

    rename = {col_sub: "세부사업명"}
    if col_year:
        rename[col_year] = "회계연도"
    if col_dept:
        rename[col_dept] = "부서명"
    if col_pol:
        rename[col_pol] = "정책사업명"
    if col_unit:
        rename[col_unit] = "단위사업명"
    agg = agg.rename(columns=rename)

    if "회계연도" in agg.columns:
        agg["회계연도"] = agg["회계연도"].apply(
            lambda v: str(int(float(v))) if pd.notna(v) and str(v).strip() not in ("", "nan") else ""
        )

    agg["집행률"] = (agg["_지출"] / agg["_예산"] * 100).round(1)
    agg["예산현액"] = (agg["_예산"] / 1_000_000).round(1)  # 원 → 백만원
    agg["집행액"] = (agg["_지출"] / 1_000_000).round(1)    # 원 → 백만원

    ordered = [c for c in ("회계연도", "부서명", "정책사업명", "단위사업명", "세부사업명",
                           "예산현액", "집행액", "집행률") if c in agg.columns]
    return agg[ordered]


def auto_detect_columns(df: pd.DataFrame) -> ColumnMapping:
    """컬럼명을 보고 표준 컬럼을 자동 매핑한다."""
    mapping = ColumnMapping()
    actual_cols = [str(c) for c in df.columns]

    def find(standard_key: str) -> str | None:
        aliases = COLUMN_ALIASES[standard_key]
        for col in actual_cols:
            col_norm = col.replace(" ", "").replace("(", "").replace(")", "")
            for alias in aliases:
                alias_norm = alias.replace(" ", "").replace("(", "").replace(")", "")
                if alias_norm in col_norm or col_norm in alias_norm:
                    return col
        return None

    mapping.project_name = find("사업명")
    mapping.budget = find("예산현액")
    mapping.executed = find("집행액")
    mapping.execution_rate = find("집행률")
    mapping.real_execution_rate = find("실집행률")
    return mapping


def _coerce_rate(value) -> float | None:
    """집행률 셀을 0~100 범위의 float로 변환.

    엑셀에서 집행률이 '64%' 문자열, 0.64 소수, 64 정수 등 다양하게 들어옴.
    """
    if pd.isna(value):
        return None
    if isinstance(value, str):
        v = value.strip().rstrip("%").replace(",", "")
        try:
            v = float(v)
        except ValueError:
            return None
    else:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return None
    # 0~1 범위면 비율로 보고 100배
    if 0 < v <= 1:
        v *= 100
    return v


def filter_low_performing(
    df: pd.DataFrame,
    mapping: ColumnMapping,
    execution_threshold: float = 70.0,
    real_execution_threshold: float | None = None,
) -> pd.DataFrame:
    """집행률 임계치 미만인 사업을 추출.

    real_execution_threshold가 주어지고 실집행률 컬럼이 매핑되어 있으면
    두 조건 모두 충족(둘 중 하나라도 미달)하는 사업을 반환한다(OR).
    """
    if not mapping.is_complete_for_filtering:
        raise ValueError("사업명과 집행률 컬럼 매핑이 필요합니다.")

    work = df.copy()
    exec_col = mapping.execution_rate
    work["_집행률_norm"] = work[exec_col].apply(_coerce_rate)

    low_mask = work["_집행률_norm"] < execution_threshold

    if real_execution_threshold is not None and mapping.real_execution_rate:
        real_col = mapping.real_execution_rate
        work["_실집행률_norm"] = work[real_col].apply(_coerce_rate)
        low_mask = low_mask | (work["_실집행률_norm"] < real_execution_threshold)

    result = work[low_mask].drop(columns=[c for c in work.columns if c.startswith("_") and c.endswith("_norm")])
    return result.reset_index(drop=True)


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "저조사업") -> bytes:
    """DataFrame을 다운로드용 엑셀 바이트로 변환."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buffer.getvalue()

"""예산분석보고서 초안 작성기 - Streamlit 앱.

워크플로:
  ① 저조사업 스크리닝 : 집행률 엑셀 업로드 → 임계치 미만 사업 자동 추출
  ② 자료 입력         : PDF·HWPX·텍스트·가상데이터로 사업설명서 입력
  ③ 보고서 생성       : Gemini 무료 AI 분석 또는 규칙기반 자동초안 → 편집 → docx

보고서 본문은 Gemini(무료 모델)로 생성하며, 키가 없거나 호출 실패 시
규칙기반 오프라인 엔진으로 자동 폴백한다. (외부 유료 API 미사용)
"""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.draft_generator import generate_draft
from src.gemini_client import GeminiError, generate_draft_via_gemini, get_api_key
from src.parsers.hwpx_parser import extract_text_from_hwpx
from src.parsers.pdf_parser import extract_text_from_pdf
from src.report_writer import ReportData, build_report
from src.sample_data import (
    SAMPLE_DEPARTMENT,
    SAMPLE_PROJECT_NAME,
    get_sample_budget_excel_bytes,
    get_sample_project_text,
)
from src.screening import (
    ColumnMapping,
    auto_detect_columns,
    detect_and_read_execution_status,
    filter_low_performing,
    read_budget_excel,
    to_excel_bytes,
)

# 실행 위치(cwd)와 무관하게 app.py 옆의 .env를 로드 (preview/외부 런처 대응)
load_dotenv(Path(__file__).resolve().with_name(".env"))
GEMINI_KEY = get_api_key()
# 배포 환경(Streamlit Cloud 등): 대시보드 Secrets(st.secrets) 지원 — .env 없이도 동작
if not GEMINI_KEY:
    try:
        GEMINI_KEY = (st.secrets.get("GEMINI_API_KEY") or "").strip() or None
    except Exception:
        GEMINI_KEY = None
AI_AVAILABLE = bool(GEMINI_KEY)


st.set_page_config(
    page_title="예산분석지원 시스템",
    page_icon="📊",
    layout="wide",
)


# ── 브라우저 자동번역 차단: <html lang=ko translate=no> + 동적노드 차단 ──
components.html(
    """
    <script>
      try {
        const doc = window.parent.document;
        doc.documentElement.lang = 'ko';
        doc.documentElement.setAttribute('translate', 'no');
        doc.documentElement.classList.add('notranslate');
        if (!doc.querySelector('meta[name="google"][content="notranslate"]')) {
          const meta = doc.createElement('meta');
          meta.name = 'google'; meta.content = 'notranslate';
          doc.head.appendChild(meta);
        }
        const stamp = (el) => {
          if (el && el.nodeType === 1) {
            el.setAttribute('translate', 'no');
            el.classList && el.classList.add('notranslate');
          }
        };
        if (doc.body) { stamp(doc.body); doc.querySelectorAll('*').forEach(stamp); }
        const obs = new MutationObserver((muts) => {
          muts.forEach((m) => m.addedNodes.forEach((n) => {
            stamp(n);
            if (n.querySelectorAll) n.querySelectorAll('*').forEach(stamp);
          }));
        });
        if (doc.body) obs.observe(doc.body, { childList: true, subtree: true });
      } catch (e) { console.warn('notranslate inject failed:', e); }
    </script>
    """,
    height=0,
)


def _extract_upload_text(f) -> str:
    """업로드 파일(PDF/HWPX)에서 텍스트를 추출. 실패 시 빈 문자열."""
    if f is None:
        return ""
    name = (f.name or "").lower()
    try:
        data = f.getvalue()  # 재실행/다중호출에도 안전(포인터 무관)
        if name.endswith(".pdf"):
            return extract_text_from_pdf(data)
        if name.endswith(".hwpx") or name.endswith(".zip"):
            return extract_text_from_hwpx(data)
        st.warning(f"'{f.name}': 지원하지 않는 형식입니다 (PDF/HWPX만 가능).")
    except Exception as e:
        st.error(f"'{f.name}' 추출 실패: {e}")
    return ""


# ────────────────────── 사이드바 ──────────────────────
st.sidebar.title("📊 예산분석지원 시스템")
st.sidebar.caption("Gemini 무료 AI 분석 · 규칙기반 폴백")
st.sidebar.divider()

if AI_AVAILABLE:
    st.sidebar.success(
        "🤖 **Gemini 무료 AI 분석 사용 가능**\n\n"
        "보고서 본문을 Gemini 무료 모델이 작성합니다. "
        "호출 실패(쿼터·과부하) 시 규칙기반 엔진으로 자동 전환됩니다."
    )
else:
    st.sidebar.info(
        "💡 **규칙기반 오프라인 모드**\n\n"
        "GEMINI_API_KEY가 없어 규칙기반 엔진으로 동작합니다. "
        "AI 분석을 쓰려면 `.env`에 무료 Gemini 키를 넣으세요."
    )
st.sidebar.divider()
st.sidebar.markdown(
    "**구성**\n"
    "- ① 저조사업 스크리닝\n"
    "- ② 자료 입력\n"
    "- ③ 보고서 생성 (AI 분석 / 규칙기반)"
)


# ────────────────────── 본문 ──────────────────────
if AI_AVAILABLE:
    _badge_bg, _badge_fg, _badge_txt = "#BBDEFB", "#0D47A1", "Gemini AI"
else:
    _badge_bg, _badge_fg, _badge_txt = "#C8E6C9", "#1B5E20", "오프라인"
st.markdown(
    f"""
    <div style="display:flex; align-items:baseline; gap:12px;">
        <h1 style="margin:0;">예산분석지원 시스템</h1>
        <span style="background:{_badge_bg}; color:{_badge_fg}; padding:3px 10px;
                     border-radius:12px; font-size:0.85rem; font-weight:600;">
            {_badge_txt}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("표준양식: 사업개요·현황 / 문제점 / 분석의견 · Gemini 무료 AI 분석(실패 시 규칙기반 자동 폴백)")

tab_screening, tab_input, tab_report = st.tabs(
    ["① 저조사업 스크리닝", "② 자료 입력", "③ 보고서 생성"]
)


# ─── ① 저조사업 스크리닝 ───
with tab_screening:
    st.subheader("집행률 기반 저조사업 스크리닝")
    st.caption(
        "전년도/당해연도 집행률 엑셀에서 임계치 미만 사업을 자동 추출합니다. "
        "추출된 사업 중 하나를 선택하면 '② 자료 입력' 탭에 자동 반영됩니다."
    )

    src_col, sample_col = st.columns([3, 1])
    with src_col:
        data_source = st.radio(
            "데이터 소스",
            ["샘플 데이터 사용", "엑셀 파일 업로드"],
            horizontal=True,
        )
    with sample_col:
        st.download_button(
            "📥 샘플 엑셀 양식",
            data=get_sample_budget_excel_bytes(),
            file_name="집행률_샘플양식.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="본인 데이터를 이 양식과 비슷하게 만들면 자동 인식이 잘 됩니다.",
        )

    df_raw: pd.DataFrame | None = None
    is_exec_format = False

    if data_source == "샘플 데이터 사용":
        df_raw = pd.read_excel(io.BytesIO(get_sample_budget_excel_bytes()))
        st.info("💡 샘플 데이터(농정 분야 7개 사업)를 로드했습니다.")
    else:
        col_up, col_hdr = st.columns([3, 1])
        with col_up:
            up = st.file_uploader(
                "집행률 엑셀 업로드",
                type=["xlsx", "xls"],
                help="① 일반 집행률 표, 또는 ② '사업별예산집행현황'(집행률 자동 계산) 모두 지원합니다.",
            )
        with col_hdr:
            header_row = st.number_input(
                "헤더 행(0부터)",
                min_value=0,
                max_value=10,
                value=0,
                help="일반 엑셀에서 병합 헤더가 있으면 실제 컬럼명이 있는 행 번호 입력 ('집행현황' 형식은 자동 인식)",
            )
        if up is not None:
            raw_bytes = up.read()
            # '사업별예산집행현황' 형식이면 세부사업 단위로 집행률을 자동 계산
            exec_df = detect_and_read_execution_status(raw_bytes)
            if exec_df is not None:
                df_raw = exec_df
                is_exec_format = True
                st.success(
                    f"✅ '사업별예산집행현황' 형식 자동 인식 — 세부사업 **{len(df_raw):,}건**, "
                    "집행률을 **지출액 ÷ 예산현액**으로 자동 계산했습니다. (금액 단위: 백만원)"
                )
            else:
                try:
                    df_raw = read_budget_excel(raw_bytes, header_row=header_row)
                    st.success(f"✅ {len(df_raw):,}건 로드 완료")
                except Exception as e:
                    st.error(f"엑셀 파싱 실패: {e}")

    if df_raw is not None and len(df_raw) > 0:
        # 컬럼은 자동 인식(집행현황 형식은 세부사업명 단위로 고정). 매핑 UI는 생략.
        mapping = auto_detect_columns(df_raw)
        if is_exec_format:
            mapping = ColumnMapping(
                project_name="세부사업명",
                budget="예산현액",
                executed="집행액",
                execution_rate="집행률",
            )

        if not mapping.is_complete_for_filtering:
            st.divider()
            st.warning(
                "⚠️ 이 파일에서 **사업명·집행률** 컬럼을 자동 인식하지 못했습니다. "
                "'사업별예산집행현황' 형식이거나, 📥 샘플 엑셀 양식과 유사한 컬럼(사업명·집행률)을 갖춘 파일을 올려주세요."
            )
        else:
            st.divider()
            _detected = [f"사업명=**{mapping.project_name}**", f"집행률=**{mapping.execution_rate}**"]
            if mapping.budget:
                _detected.append(f"예산현액=**{mapping.budget}**")
            if mapping.executed:
                _detected.append(f"집행액=**{mapping.executed}**")
            st.caption("🔎 자동 인식 — " + " · ".join(_detected))

            st.markdown("##### 임계치 설정")
            has_real = bool(mapping.real_execution_rate)
            t1, t2 = st.columns(2)
            with t1:
                exec_threshold = st.slider("집행률 임계치 (% 미만이면 저조)", 0, 100, 70)
            with t2:
                use_real = st.checkbox(
                    "실집행률도 조건에 포함",
                    value=has_real,
                    disabled=not has_real,
                    help=None if has_real else "이 파일에는 실집행률 컬럼이 없습니다.",
                )
                real_threshold = st.slider(
                    "실집행률 임계치 (% 미만이면 저조)", 0, 100, 60, disabled=not (use_real and has_real)
                )

            try:
                low_df = filter_low_performing(
                    df_raw,
                    mapping,
                    execution_threshold=float(exec_threshold),
                    real_execution_threshold=float(real_threshold) if (use_real and has_real) else None,
                )
            except Exception as e:
                st.error(f"필터링 실패: {e}")
                low_df = pd.DataFrame()

            st.divider()
            st.markdown(f"##### 저조사업 추출 결과 — **{len(low_df)}건** / 전체 {len(df_raw)}건")

            if len(low_df) > 0:
                # 기본 정렬: 집행률 낮은 순(저조 우선). 이후 열 머리글 화살표로 자유롭게 재정렬.
                if "집행률" in low_df.columns:
                    low_df = low_df.sort_values("집행률", ascending=True, kind="stable").reset_index(drop=True)
                else:
                    low_df = low_df.reset_index(drop=True)

                st.caption("👇 **열 머리글의 화살표(↑↓)를 클릭하면 정렬**됩니다(예산현액·집행액·집행률 등). **행을 클릭**하면 그 사업이 분석대상으로 지정됩니다.")
                event = st.dataframe(
                    low_df,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="screening_table",
                )

                sel_rows = list(event.selection.rows) if (event and event.selection) else []
                if sel_rows:
                    picked_row_s = low_df.iloc[sel_rows[0]]
                    picked = str(picked_row_s[mapping.project_name])
                    st.session_state["picked_project_name"] = picked
                    st.session_state["picked_project_row"] = picked_row_s.to_dict()
                    info = []
                    if "집행률" in low_df.columns:
                        info.append(f"집행률 {picked_row_s['집행률']}%")
                    if "예산현액" in low_df.columns:
                        info.append(f"예산현액 {picked_row_s['예산현액']:,}백만원")
                    detail = (" · " + " / ".join(info)) if info else ""
                    st.success(
                        f"✅ 분석대상 지정: **{picked}**{detail}\n\n"
                        "→ **② 자료 입력**·**③ 보고서 생성** 탭에서 이어가세요."
                    )
                else:
                    st.info("표에서 분석할 사업의 행을 클릭하세요.")

                st.download_button(
                    "📥 저조사업 목록 다운로드 (xlsx)",
                    data=to_excel_bytes(low_df),
                    file_name=f"저조사업_{datetime.now():%Y%m%d_%H%M}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.info("저조사업이 없습니다. 임계치를 조정해보세요.")


# ─── ② 자료 입력 ───
with tab_input:
    st.subheader("사업 정보")

    picked_name = st.session_state.get("picked_project_name", "")
    picked_row = st.session_state.get("picked_project_row", {})

    use_sample = st.checkbox(
        "🧪 데모용 샘플 데이터로 채우기",
        value=False,
        help="실제 자료 없이 기능을 시험해볼 때 사용 (샘플 사업·사업설명서 자동 포함)",
    )

    if picked_name:
        st.success(f"📌 스크리닝에서 선택된 사업: **{picked_name}**")
        default_name = picked_name
    elif use_sample:
        default_name = SAMPLE_PROJECT_NAME
    else:
        default_name = ""

    default_dept = (str(picked_row.get("부서명") or "") if picked_row else "") or (
        SAMPLE_DEPARTMENT if use_sample else ""
    )
    default_year = str(picked_row.get("회계연도") or datetime.now().year) if picked_row else str(datetime.now().year)

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("사업명", value=default_name)
    with col2:
        department = st.text_input("소관부서", value=default_dept)

    fiscal_year = st.text_input("회계연도", value=default_year)

    st.divider()

    # ── 사업설명서 (핵심 자료) ──
    st.subheader("📄 사업설명서")
    st.caption("분석 대상 사업의 사업설명서를 업로드하거나 본문을 붙여넣으세요. (PDF / HWPX · HWP는 HWPX로 변환)")

    sample_desc = get_sample_project_text() if use_sample else ""
    if sample_desc:
        with st.expander("🧪 포함될 샘플 사업설명서 내용 (데모)"):
            st.text(sample_desc)

    desc_file = st.file_uploader(
        "사업설명서 파일 업로드 (PDF / HWPX)",
        type=["pdf", "hwpx", "zip"],
        key="desc_file",
        help="HWP(.hwp)는 한컴오피스에서 [다른 이름으로 저장] → HWPX로 변환 후 올리거나, 본문을 아래에 붙여넣으세요.",
    )
    desc_extracted = _extract_upload_text(desc_file)
    if desc_extracted:
        st.success(f"✅ 사업설명서에서 {len(desc_extracted):,}자 추출")
        with st.expander("추출된 사업설명서 텍스트 미리보기"):
            st.text(desc_extracted[:3000] + ("\n…(이하 생략)" if len(desc_extracted) > 3000 else ""))

    desc_paste = st.text_area(
        "또는 사업설명서 본문 직접 입력 / 붙여넣기",
        height=240,
        placeholder="예: 사업개요, 사업목적, 사업내용, 지원실적, 추진현황 등...",
    )

    st.divider()

    # ── 추가자료 (분석관이 수집한 보조자료) ──
    st.subheader("📎 추가자료 (선택)")
    st.caption("집행부 회신, 성과·정산자료, 관련 보도 등 분석에 필요한 자료를 자유롭게 모아 올리세요. (여러 개 가능)")

    extra_files = st.file_uploader(
        "추가자료 파일 업로드 (여러 개 선택 가능, PDF / HWPX)",
        type=["pdf", "hwpx", "zip"],
        accept_multiple_files=True,
        key="extra_files",
    )
    extra_parts: list[str] = []
    for f in (extra_files or []):
        t = _extract_upload_text(f)
        if t:
            extra_parts.append(f"[추가자료: {f.name}]\n{t}")
    if extra_parts:
        st.success(f"✅ 추가자료 {len(extra_parts)}개 파일에서 텍스트 추출 완료")

    extra_paste = st.text_area(
        "추가 메모·본문 붙여넣기 (선택)",
        height=150,
        placeholder="파일 외에 참고할 메모나 본문을 붙여넣으세요.",
    )

    # ── 수집한 자료 통합 → source_text ──
    parts: list[str] = []
    desc_combined = "\n".join(x.strip() for x in (sample_desc, desc_extracted, desc_paste) if x and x.strip())
    if desc_combined.strip():
        parts.append("[사업설명서]\n" + desc_combined.strip())
    parts.extend(extra_parts)
    if extra_paste.strip():
        parts.append("[추가 메모]\n" + extra_paste.strip())
    source_text = "\n\n".join(parts)

    if source_text.strip():
        st.info(
            f"📚 수집된 자료 총 **{len(source_text):,}자** — "
            f"사업설명서 {'있음' if desc_combined.strip() else '없음'} · 추가자료 {len(extra_parts)}개 파일"
        )
    else:
        st.warning("⚠️ 아직 수집된 자료가 없습니다. 사업설명서를 업로드하거나 본문을 붙여넣으세요.")

    st.session_state["source_text"] = source_text
    st.session_state["project_name"] = project_name
    st.session_state["department"] = department
    st.session_state["fiscal_year"] = fiscal_year


# ─── ③ 보고서 생성 ───
with tab_report:
    st.subheader("표준양식 보고서 생성")

    source_text = st.session_state.get("source_text", "")
    project_name = st.session_state.get("project_name", "")
    department = st.session_state.get("department", "")
    fiscal_year = st.session_state.get("fiscal_year", "")
    picked_row = st.session_state.get("picked_project_row", {})

    if not project_name:
        st.warning("⚠️ '② 자료 입력' 탭에서 사업명을 먼저 입력해주세요.")

    st.markdown(
        "집행률·실집행률 수치와 사업설명서 내용을 분석하여 **문제점**과 1:1 대응되는 **분석의견** "
        "초안을 자동 작성합니다. **Gemini 무료 AI 분석**은 문장이 풍부하고, **규칙기반**은 인터넷 없이 "
        "즉시 동작합니다. 생성된 초안은 아래 편집창에서 자유롭게 수정하세요."
    )

    # ── 분석 엔진 선택 ──
    if AI_AVAILABLE:
        engine_choice = st.radio(
            "분석 엔진",
            ["🤖 Gemini AI 분석 (무료 모델)", "⚙️ 규칙기반 (오프라인)"],
            horizontal=True,
            help="Gemini 호출이 실패(쿼터 초과·과부하)하면 규칙기반으로 자동 전환됩니다.",
        )
        use_ai = engine_choice.startswith("🤖")
    else:
        st.caption("⚙️ 규칙기반 엔진 (오프라인) — AI 분석을 쓰려면 `.env`에 GEMINI_API_KEY를 넣으세요.")
        use_ai = False

    gen_col1, gen_col2 = st.columns([1, 2])
    with gen_col1:
        gen_clicked = st.button(
            "⚙️ 자동초안 생성",
            disabled=not project_name,
            type="secondary",
            use_container_width=True,
        )
    with gen_col2:
        st.caption("Gemini 무료 AI · 실패 시 규칙기반 자동 폴백" if use_ai else "규칙기반 엔진 · 완전 오프라인")

    if gen_clicked:
        overview = issues = analysis = None
        findings = 0
        engine_label = ""

        if use_ai:
            with st.spinner("🤖 Gemini 무료 AI가 분석 중입니다... (최대 30초)"):
                try:
                    g = generate_draft_via_gemini(
                        project_name=project_name,
                        department=department,
                        fiscal_year=fiscal_year,
                        source_text=source_text,
                        execution_info=picked_row or None,
                        api_key=GEMINI_KEY,
                    )
                    overview, issues, analysis = g.overview, g.issues, g.analysis
                    findings = g.findings_count
                    engine_label = f"Gemini AI · {g.model}"
                except GeminiError as e:
                    st.warning(f"⚠️ Gemini 호출 실패 → 규칙기반 엔진으로 자동 전환합니다.\n\n사유: {e}")

        if overview is None:  # AI 미사용 또는 실패 → 규칙기반 폴백
            result = generate_draft(
                project_name=project_name,
                department=department,
                fiscal_year=fiscal_year,
                source_text=source_text,
                execution_info=picked_row or None,
            )
            overview, issues, analysis = result.overview, result.issues, result.analysis
            findings = result.findings_count
            engine_label = "규칙기반 오프라인"

        # 위젯 key에 직접 기록해야 편집창에 즉시 반영됨
        # (key가 있는 위젯은 한번 초기화되면 value= 인자를 무시하고 session_state 값을 따름)
        st.session_state["edit_overview"] = overview
        st.session_state["edit_issues"] = issues
        st.session_state["edit_analysis"] = analysis
        if findings:
            st.success(f"✅ 초안 생성 완료 [{engine_label}] — 문제점 {findings}건 탐지")
        else:
            st.info(f"ℹ️ 초안을 생성했습니다 [{engine_label}]. 자동 탐지된 문제점이 없어 직접 보완이 필요합니다.")

    with st.expander("✏️ 본문 편집", expanded=True):
        overview = st.text_area("1. 사업개요 및 현황", height=240, key="edit_overview")
        issues = st.text_area("2. 문제점", height=220, key="edit_issues")
        analysis = st.text_area("3. 분석의견", height=220, key="edit_analysis")

    if st.button("📄 보고서 초안 생성 (docx)", type="primary", disabled=not project_name):
        data = ReportData(
            project_name=project_name,
            department=department,
            fiscal_year=fiscal_year,
            overview=overview,
            issues=issues,
            analysis=analysis,
            raw_source_excerpt=source_text,
        )
        docx_bytes = build_report(data)

        filename = f"예산분석보고서_초안_{project_name}_{datetime.now():%Y%m%d_%H%M}.docx"
        st.download_button(
            label="⬇️ docx 다운로드",
            data=docx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        st.success(f"✅ 보고서가 생성되었습니다: **{filename}**")

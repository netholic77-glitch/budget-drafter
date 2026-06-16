"""Gemini 무료 모델 클라이언트 (REST · 표준 라이브러리만 사용).

google-generativeai SDK 없이 stdlib urllib만으로 Gemini API를 호출한다.
무료 티어 특성상 429(쿼터 초과)·503(과부하)가 잦으므로,
다중 모델 폴백 + 503 재시도를 수행하고, 모두 실패하면 GeminiError를 던져
호출측(app.py)이 규칙기반 엔진(draft_generator)으로 자동 폴백하게 한다.

출력 형식은 draft_generator.DraftResult와 호환되도록 3개 섹션
(사업개요 및 현황 / 문제점 / 분석의견)을 === 마커로 구분해 받는다.
"""
from __future__ import annotations

import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# 무료 티어에서 사용 가능한 모델. 앞에서부터 시도하며 429/503이면 다음으로 폴백.
# gemini-2.5-flash-lite가 실측상 무료 티어 안정성이 가장 좋았음(쿼터 여유·과부하 적음).
DEFAULT_MODELS = (
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",
)

SYSTEM_PROMPT = """당신은 대한민국 지방의회(예: 경기도의회)의 예산분석 전문위원입니다.
집행부가 제출한 사업설명서·집행 실적을 검토하여 의원 심사를 보조하는
'예산분석보고서' 초안을 표준양식으로 작성합니다.

[작성 원칙]
1. 사실 기반: 주어진 자료에 근거해서만 서술하고, 자료에 없는 수치·사실을 지어내지 마십시오.
   불명확하면 "추가 확인 필요"로 표기합니다.
2. 공공기관 문체: 간결한 개조식, '~함/~음/~필요가 있음' 등 보고서 종결어미를 사용합니다.
3. 비판적·중립적 관점: 집행 부진·이월·불용·중복·성과관리 미비 등 쟁점을 적극적으로 포착하되,
   단정 대신 점검·보완·자료요구 등 건설적 후속조치를 제안합니다.
4. 1:1 대응: '문제점'과 '분석의견'은 각각 ①②③… 번호를 매겨 같은 번호끼리 1:1로 대응시킵니다.
   (문제점 ②에 대한 대응은 분석의견 ②)
5. 근거 인용: 가능하면 문제점에 사업설명서의 근거 문구를 짧게 인용합니다. (근거: "…")

[출력 형식] — 아래 세 개의 마커를 반드시 그대로 출력하고, 각 마커 아래에 내용을 작성하십시오.
다른 머리말·맺음말·코드블록 없이 이 형식만 출력합니다.

=== 사업개요 및 현황 ===
(□/○ 개조식으로 사업명·소관부서·회계연도·예산/집행 현황·사업목적·근거 등을 정리)

=== 문제점 ===
① (문제점 1)
② (문제점 2)
…

=== 분석의견 ===
① (문제점 ①에 대한 분석의견·후속조치)
② (문제점 ②에 대한 분석의견·후속조치)
…
"""


class GeminiError(RuntimeError):
    """모든 모델 시도가 실패했음을 알리는 예외(호출측은 규칙기반으로 폴백)."""


@dataclass
class GeminiResult:
    overview: str = ""
    issues: str = ""
    analysis: str = ""
    findings_count: int = 0
    model: str = ""
    raw_text: str = ""


# ────────────────── 키 ──────────────────
def get_api_key(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit.strip()
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GENAI_API_KEY"):
        v = os.environ.get(var)
        if v and v.strip():
            return v.strip()
    return None


# ────────────────── 응답 파싱 ──────────────────
def _extract_text(payload: dict) -> str:
    """generateContent 응답에서 본문 텍스트를 추출."""
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    chunks = [p.get("text", "") for p in parts if isinstance(p, dict)]
    return "".join(chunks).strip()


def _parse_sections(text: str) -> tuple[str, str, str]:
    """=== 라벨 === 형식에서 3개 섹션을 추출. 마커가 없으면 전체를 개요로 둔다."""
    def extract(label: str) -> str:
        pattern = rf"===\s*{re.escape(label)}\s*===\s*\n?(.*?)(?=\n===\s|\Z)"
        m = re.search(pattern, text, re.DOTALL)
        return m.group(1).strip() if m else ""

    overview = extract("사업개요 및 현황") or extract("사업개요") or extract("사업 개요 및 현황")
    issues = extract("문제점")
    analysis = extract("분석의견") or extract("분석 의견")
    return overview, issues, analysis


def _count_findings(issues: str) -> int:
    return len(re.findall(r"[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]", issues))


# ────────────────── 프롬프트 빌더 ──────────────────
def _fmt_info(info: dict | None) -> str:
    if not info:
        return "(구조화된 집행 정보 없음)"
    keep = []
    for k, v in info.items():
        if str(k).startswith("_"):
            continue
        if v in (None, ""):
            continue
        keep.append(f"- {k}: {v}")
    return "\n".join(keep) if keep else "(구조화된 집행 정보 없음)"


def _build_user_prompt(
    project_name: str,
    department: str,
    fiscal_year: str,
    source_text: str,
    execution_info: dict | None,
    max_source_chars: int = 12000,
) -> str:
    src = (source_text or "").strip()
    if len(src) > max_source_chars:
        src = src[:max_source_chars] + "\n…(이하 생략)"
    return (
        f"[사업 기본정보]\n"
        f"- 사업명: {project_name or '(미입력)'}\n"
        f"- 소관부서: {department or '(미입력)'}\n"
        f"- 회계연도: {fiscal_year or '(미입력)'}\n\n"
        f"[집행 실적(스크리닝에서 추출)]\n{_fmt_info(execution_info)}\n\n"
        f"[사업설명서 / 원본자료]\n{src or '(원본자료 없음 — 기본정보·집행실적 위주로 작성)'}\n\n"
        f"위 자료를 바탕으로 지정된 출력 형식(=== 마커)에 맞춰 예산분석보고서 초안을 작성하십시오."
    )


# ────────────────── REST 호출 ──────────────────
def _post(url: str, body: dict, timeout: int = 60) -> tuple[int, dict | str]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
        # 인터넷 단절·DNS 실패·타임아웃 등 → 음수 상태로 표시(폴백 대상)
        reason = getattr(e, "reason", None) or e
        return -1, f"network error: {reason}"


def _call_model(
    model: str,
    api_key: str,
    user_prompt: str,
    *,
    temperature: float = 0.4,
    max_output_tokens: int = 4096,
    retries_503: int = 2,
) -> str:
    """단일 모델 호출. 503이면 백오프 재시도. 본문 텍스트를 반환.

    실패 시 예외를 던진다:
      - urllib.error.HTTPError 코드를 가진 GeminiError(분류용 .status 속성 포함)
    """
    url = f"{_API_BASE}/models/{model}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        },
    }

    last_err = "unknown"
    for attempt in range(retries_503 + 1):
        status, payload = _post(url, body)
        if status == 200 and isinstance(payload, dict):
            text = _extract_text(payload)
            if text:
                return text
            # 빈 응답(MAX_TOKENS로 thinking에 다 소모 등) → 폴백 대상
            last_err = "empty response"
            break
        # 오류 분류
        msg = ""
        if isinstance(payload, dict):
            msg = (payload.get("error") or {}).get("message", "") or str(payload)[:200]
        else:
            msg = str(payload)[:200]
        last_err = f"HTTP {status}: {msg}"
        if status == 503 and attempt < retries_503:
            time.sleep(1.5 * (attempt + 1))  # 1.5s, 3.0s 백오프
            continue
        err = GeminiError(last_err)
        err.status = status  # type: ignore[attr-defined]
        raise err
    err = GeminiError(last_err)
    err.status = 200  # type: ignore[attr-defined]
    raise err


# ────────────────── 진입점 ──────────────────
def generate_draft_via_gemini(
    project_name: str,
    department: str,
    fiscal_year: str,
    source_text: str,
    execution_info: dict | None = None,
    *,
    api_key: str | None = None,
    models: tuple[str, ...] = DEFAULT_MODELS,
) -> GeminiResult:
    """Gemini로 3개 섹션 초안을 생성. 모든 모델 실패 시 GeminiError 발생."""
    key = get_api_key(api_key)
    if not key:
        raise GeminiError("GEMINI_API_KEY가 설정되지 않았습니다.")

    user_prompt = _build_user_prompt(
        project_name, department, fiscal_year, source_text, execution_info
    )

    errors: list[str] = []
    for model in models:
        try:
            text = _call_model(model, key, user_prompt)
        except GeminiError as e:
            status = getattr(e, "status", None)
            errors.append(f"{model}: {e}")
            # 키/요청 오류(400·403)는 모델 폴백으로 해결되지 않음 → 즉시 중단
            if status in (400, 401, 403):
                raise GeminiError(
                    f"요청/인증 오류로 중단했습니다 ({model}). {e}"
                ) from e
            continue  # 404·429·503·빈응답 → 다음 모델

        overview, issues, analysis = _parse_sections(text)
        if not (overview or issues or analysis):
            # 마커 없이 평문만 온 경우: 전체를 분석의견에 넣어 사용자가 편집하게 함
            errors.append(f"{model}: 형식 마커 없음")
            overview, issues, analysis = "", "", text

        return GeminiResult(
            overview=overview,
            issues=issues,
            analysis=analysis,
            findings_count=_count_findings(issues),
            model=model,
            raw_text=text,
        )

    raise GeminiError("모든 모델 시도 실패: " + " | ".join(errors))

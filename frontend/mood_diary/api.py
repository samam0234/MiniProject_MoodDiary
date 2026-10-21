"""Django 백엔드 REST API 클라이언트.

모든 함수는 예외를 던지지 않고 :class:`ApiResult` 를 반환한다.
Reflex 이벤트 핸들러(서버 측 Python)에서 호출되므로 브라우저 CORS 와는 무관하다.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("mood_diary.frontend")

API_BASE_URL = os.getenv("MOOD_DIARY_API_URL", "http://localhost:8000").rstrip("/")
# AI 분석이 느릴 수 있으므로 백엔드의 AI timeout(기본 5초)보다 넉넉하게 잡는다.
REQUEST_TIMEOUT = float(os.getenv("MOOD_DIARY_API_TIMEOUT", "20"))

CONNECTION_ERROR = "서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."


@dataclass
class ApiResult:
    ok: bool
    status: int = 0
    data: Any = None
    error: str = ""
    details: Any = None


def _flatten_details(details: Any) -> str:
    """필드별 검증 오류(dict)를 사람이 읽을 한 줄 문장으로 만든다."""
    if not isinstance(details, dict):
        return ""
    parts: list[str] = []
    for field, messages in details.items():
        text = " ".join(str(m) for m in messages) if isinstance(messages, (list, tuple)) else str(messages)
        parts.append(f"{field}: {text}")
    return " / ".join(parts)


async def request(
    method: str,
    path: str,
    *,
    token: str = "",
    json: Any = None,
    params: dict[str, Any] | None = None,
) -> ApiResult:
    """백엔드에 요청을 보내고 ``{"success", "data", "error"}`` 응답을 ApiResult 로 변환한다."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=REQUEST_TIMEOUT) as client:
            response = await client.request(method, path, json=json, params=params, headers=headers)
    except httpx.HTTPError as exc:
        logger.warning("api_request_failed method=%s path=%s error=%s", method, path, type(exc).__name__)
        return ApiResult(ok=False, error=CONNECTION_ERROR)

    if response.status_code == 204:
        return ApiResult(ok=True, status=204)

    try:
        body = response.json()
    except ValueError:
        return ApiResult(ok=False, status=response.status_code, error="서버 응답을 해석할 수 없습니다.")

    if response.is_success and body.get("success"):
        return ApiResult(ok=True, status=response.status_code, data=body.get("data"))

    error = body.get("error") or {}
    message = error.get("message", "요청에 실패했습니다.") if isinstance(error, dict) else str(error)
    details = error.get("details") if isinstance(error, dict) else None
    detail_text = _flatten_details(details)
    return ApiResult(
        ok=False,
        status=response.status_code,
        error=f"{message} ({detail_text})" if detail_text else message,
        details=details,
    )

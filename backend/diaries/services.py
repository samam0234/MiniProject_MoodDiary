"""AI 서버 연동과 감정 트렌드 집계."""
from __future__ import annotations

import json
import logging
import time
from collections import Counter
from datetime import date, timedelta
from typing import Any

import requests
from django.conf import settings
from django.db.models import QuerySet

logger = logging.getLogger("mood_diary.backend")

EMOTIONS = ("joy", "sadness", "anger", "anxiety", "calm")
LABELS = ("positive", "negative", "neutral")

# AI 서버 장애 시 사용하는 기본값 (neutral, 0.5)
FALLBACK_ANALYSIS: dict[str, Any] = {
    "label": "neutral",
    "score": 0.5,
    "detailed_emotions": {emotion: 0.2 for emotion in EMOTIONS},
    "message": "",
    "source": "fallback",
}


def _log(event: str, **fields: Any) -> None:
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))


def _fallback(reason: str, duration_ms: float) -> dict[str, Any]:
    _log("ai_analysis_fallback", reason=reason, duration_ms=duration_ms)
    return {**FALLBACK_ANALYSIS, "detailed_emotions": dict(FALLBACK_ANALYSIS["detailed_emotions"])}


def _is_valid(result: Any) -> bool:
    """AI 서버 응답이 약속된 구조인지 검증한다. (결과 구조 일관성 보장)"""
    if not isinstance(result, dict):
        return False
    score = result.get("score")
    detailed = result.get("detailed_emotions")
    return (
        result.get("label") in LABELS
        and isinstance(score, (int, float))
        and not isinstance(score, bool)
        and 0.0 <= score <= 1.0
        and isinstance(detailed, dict)
        and set(detailed) == set(EMOTIONS)
    )


def analyze_text(text: str) -> dict[str, Any]:
    """AI 서버에 감정 분석을 요청한다. 실패하면 예외 대신 fallback 결과를 반환한다."""
    started = time.perf_counter()
    try:
        response = requests.post(
            f"{settings.AI_SERVER_URL}/analyze",
            json={"text": text},
            timeout=settings.AI_SERVER_TIMEOUT,
        )
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        response.raise_for_status()
        body = response.json()
    except requests.Timeout:
        return _fallback("timeout", round((time.perf_counter() - started) * 1000, 1))
    except (requests.RequestException, ValueError) as exc:
        return _fallback(type(exc).__name__, round((time.perf_counter() - started) * 1000, 1))

    result = body.get("data") if isinstance(body, dict) and body.get("success") else None
    if not _is_valid(result):
        return _fallback("invalid_response", elapsed)

    _log("ai_analysis_done", label=result["label"], score=result["score"], duration_ms=elapsed)
    return {
        "label": result["label"],
        "score": float(result["score"]),
        "detailed_emotions": {key: float(result["detailed_emotions"][key]) for key in EMOTIONS},
        "message": str(result.get("message") or ""),
        "source": str(result.get("source") or "unknown"),
    }


def _signed_sentiment(label: str, score: float) -> float:
    """label/score 를 -1.0(부정) ~ +1.0(긍정) 단일 지표로 변환한다."""
    if label == "positive":
        return score
    if label == "negative":
        return -score
    return 0.0


def build_trend(diaries: QuerySet, days: int, today: date) -> dict[str, Any]:
    """최근 ``days`` 일(오늘 포함)의 일자별 감정 추이를 집계한다. 일기가 있는 날짜만 포함한다."""
    start = today - timedelta(days=days - 1)
    rows = list(diaries.filter(entry_date__gte=start, entry_date__lte=today).order_by("entry_date"))

    by_date: dict[date, list] = {}
    for diary in rows:
        by_date.setdefault(diary.entry_date, []).append(diary)

    points = []
    for entry_date, items in by_date.items():
        labels = Counter(item.emotion_label for item in items)
        point: dict[str, Any] = {
            "date": entry_date.isoformat(),
            "entries": len(items),
            "sentiment": round(
                sum(_signed_sentiment(i.emotion_label, i.emotion_score) for i in items) / len(items), 3
            ),
            **{label: labels.get(label, 0) for label in LABELS},
        }
        for emotion in EMOTIONS:
            point[emotion] = round(
                sum(float((i.detailed_emotions or {}).get(emotion, 0.0)) for i in items) / len(items), 3
            )
        points.append(point)

    total_labels = Counter(item.emotion_label for item in rows)
    summary = {
        "entries": len(rows),
        "average_sentiment": (
            round(sum(_signed_sentiment(i.emotion_label, i.emotion_score) for i in rows) / len(rows), 3)
            if rows
            else None
        ),
        "label_counts": {label: total_labels.get(label, 0) for label in LABELS},
    }
    return {"days": days, "start": start.isoformat(), "end": today.isoformat(), "points": points, "summary": summary}

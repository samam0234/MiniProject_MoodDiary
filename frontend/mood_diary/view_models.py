"""백엔드 응답을 UI 에서 바로 쓸 수 있는 평평한 구조로 바꾼다. (Reflex 비의존, 단독 테스트 가능)"""
from __future__ import annotations

from typing import Any, TypedDict

EMOTION_LABELS = {"joy": "기쁨", "sadness": "슬픔", "anger": "분노", "anxiety": "불안", "calm": "평온"}
EMOTION_COLORS = {
    "joy": "amber",
    "sadness": "blue",
    "anger": "red",
    "anxiety": "purple",
    "calm": "green",
}
SENTIMENT_TEXT = {"positive": "긍정", "negative": "부정", "neutral": "중립"}
SENTIMENT_COLORS = {"positive": "green", "negative": "red", "neutral": "gray"}


class EmotionBar(TypedDict):
    key: str
    label: str
    color: str
    pct: int


class DiaryItem(TypedDict):
    id: int
    title: str
    content: str
    preview: str
    entry_date: str
    label_text: str
    label_color: str
    score_pct: int
    ai_message: str
    is_fallback: bool
    emotions: list[EmotionBar]


class TrendPoint(TypedDict):
    date: str
    day: str
    entries: int
    sentiment: float
    joy: float
    sadness: float
    anger: float
    anxiety: float
    calm: float


EMPTY_DIARY: DiaryItem = {
    "id": 0,
    "title": "",
    "content": "",
    "preview": "",
    "entry_date": "",
    "label_text": "",
    "label_color": "gray",
    "score_pct": 0,
    "ai_message": "",
    "is_fallback": False,
    "emotions": [],
}

PREVIEW_LENGTH = 80


def to_diary_item(raw: dict[str, Any]) -> DiaryItem:
    detailed = raw.get("detailed_emotions") or {}
    emotions: list[EmotionBar] = [
        {
            "key": key,
            "label": label,
            "color": EMOTION_COLORS[key],
            "pct": round(float(detailed.get(key, 0.0)) * 100),
        }
        for key, label in EMOTION_LABELS.items()
    ]
    content = raw.get("content", "")
    flat = " ".join(content.split())
    label = raw.get("emotion_label", "neutral")
    return {
        "id": raw["id"],
        "title": raw.get("title", ""),
        "content": content,
        "preview": flat if len(flat) <= PREVIEW_LENGTH else flat[:PREVIEW_LENGTH] + "…",
        "entry_date": raw.get("entry_date", ""),
        "label_text": SENTIMENT_TEXT.get(label, label),
        "label_color": SENTIMENT_COLORS.get(label, "gray"),
        "score_pct": round(float(raw.get("emotion_score", 0.0)) * 100),
        "ai_message": raw.get("ai_message", ""),
        "is_fallback": raw.get("analysis_source") == "fallback",
        "emotions": emotions,
    }


def to_trend_points(raw_points: list[dict[str, Any]]) -> list[TrendPoint]:
    return [
        {
            "date": point["date"],
            "day": point["date"][5:],  # MM-DD
            "entries": point["entries"],
            "sentiment": point["sentiment"],
            **{key: point[key] for key in EMOTION_LABELS},
        }
        for point in raw_points
    ]


def describe_average(value: float | None) -> str:
    """평균 감정 지수(-1~1)를 한 줄 문장으로 설명한다."""
    if value is None:
        return "기록 없음"
    if value >= 0.25:
        return f"긍정적 ({value:+.2f})"
    if value <= -0.25:
        return f"부정적 ({value:+.2f})"
    return f"평온/중립 ({value:+.2f})"

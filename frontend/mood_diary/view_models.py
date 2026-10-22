"""백엔드 응답을 UI 에서 바로 쓸 수 있는 평평한 구조로 바꾼다. (Reflex 비의존, 단독 테스트 가능)"""
from __future__ import annotations

from datetime import date
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
# 컨셉: "마음 날씨" - 감정 방향을 날씨로 표현한다.
SENTIMENT_EMOJI = {"positive": "☀️", "negative": "🌧️", "neutral": "☁️"}
SENTIMENT_WEATHER = {"positive": "맑음", "negative": "비", "neutral": "구름"}
EMOTION_EMOJI = {"joy": "😊", "sadness": "😢", "anger": "😠", "anxiety": "😰", "calm": "😌"}
WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")


class EmotionBar(TypedDict):
    key: str
    emoji: str
    label: str
    color: str
    pct: int


class DiaryItem(TypedDict):
    id: int
    title: str
    content: str
    preview: str
    entry_date: str
    long_date: str
    day: str
    month: str
    weekday: str
    label: str
    emoji: str
    weather: str
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
    "long_date": "",
    "day": "",
    "month": "",
    "weekday": "",
    "label": "neutral",
    "emoji": "",
    "weather": "",
    "label_text": "",
    "label_color": "gray",
    "score_pct": 0,
    "ai_message": "",
    "is_fallback": False,
    "emotions": [],
}

PREVIEW_LENGTH = 80


def split_date(value: str) -> dict[str, str]:
    """YYYY-MM-DD 를 달력 카드/긴 날짜 표기용 조각으로 나눈다. 해석할 수 없으면 원문을 유지한다."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return {"long_date": value, "day": "", "month": "", "weekday": ""}
    weekday = WEEKDAYS[parsed.weekday()]
    return {
        "long_date": f"{parsed.year}년 {parsed.month}월 {parsed.day}일 {weekday}요일",
        "day": str(parsed.day),
        "month": f"{parsed.month}월",
        "weekday": weekday,
    }


def to_diary_item(raw: dict[str, Any]) -> DiaryItem:
    detailed = raw.get("detailed_emotions") or {}
    emotions: list[EmotionBar] = [
        {
            "key": key,
            "emoji": EMOTION_EMOJI[key],
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
        **split_date(raw.get("entry_date", "")),
        "label": label,
        "emoji": SENTIMENT_EMOJI.get(label, "☁️"),
        "weather": SENTIMENT_WEATHER.get(label, ""),
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


def describe_trend(label_counts: dict[str, int], days: int) -> str:
    """기간 동안 가장 많았던 마음 날씨를 한 문장으로 요약한다. (동률이면 긍정 > 부정 > 중립 순)"""
    if sum(label_counts.values()) == 0:
        return ""
    top = max(("positive", "negative", "neutral"), key=lambda key: label_counts.get(key, 0))
    phrases = {
        "positive": "맑은 날이 많았어요 ☀️",
        "negative": "흐리고 비 오는 날이 많았어요 🌧️",
        "neutral": "잔잔한 구름 같은 날들이었어요 ☁️",
    }
    return f"최근 {days}일은 {phrases[top]}"


def describe_average(value: float | None) -> str:
    """평균 감정 지수(-1~1)를 한 줄 문장으로 설명한다."""
    if value is None:
        return "기록 없음"
    if value >= 0.25:
        return f"긍정적 ({value:+.2f})"
    if value <= -0.25:
        return f"부정적 ({value:+.2f})"
    return f"평온/중립 ({value:+.2f})"

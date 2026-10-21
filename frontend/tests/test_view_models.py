from mood_diary.view_models import describe_average, to_diary_item, to_trend_points

RAW = {
    "id": 7,
    "title": "오늘",
    "content": "줄바꿈이\n있는   긴 내용 " + "가" * 100,
    "entry_date": "2026-10-22",
    "emotion_label": "positive",
    "emotion_score": 0.756,
    "detailed_emotions": {"joy": 0.7, "sadness": 0.0, "anger": 0.0, "anxiety": 0.1, "calm": 0.2},
    "ai_message": "좋은 하루!",
    "analysis_source": "lexicon",
}


def test_to_diary_item():
    item = to_diary_item(RAW)
    assert item["label_text"] == "긍정"
    assert item["label_color"] == "green"
    assert item["score_pct"] == 76
    assert item["is_fallback"] is False
    assert [bar["key"] for bar in item["emotions"]] == ["joy", "sadness", "anger", "anxiety", "calm"]
    assert item["emotions"][0]["pct"] == 70
    assert "\n" not in item["preview"] and item["preview"].endswith("…")


def test_fallback_flag():
    assert to_diary_item({**RAW, "analysis_source": "fallback"})["is_fallback"] is True


def test_missing_optional_fields():
    item = to_diary_item({"id": 1})
    assert item["label_text"] == "중립"
    assert item["emotions"][0]["pct"] == 0


def test_trend_points():
    point = {"date": "2026-10-22", "entries": 2, "sentiment": 0.2, "positive": 1, "negative": 1, "neutral": 0,
             "joy": 0.5, "sadness": 0.1, "anger": 0.0, "anxiety": 0.2, "calm": 0.2}
    (out,) = to_trend_points([point])
    assert out["day"] == "10-22"
    assert out["joy"] == 0.5
    assert "positive" not in out


def test_describe_average():
    assert describe_average(None) == "기록 없음"
    assert describe_average(0.5).startswith("긍정적")
    assert describe_average(-0.5).startswith("부정적")
    assert describe_average(0.0).startswith("평온")

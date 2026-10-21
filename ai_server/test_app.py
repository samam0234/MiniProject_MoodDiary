import pytest

import analyzer
from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["success"] is True


def test_positive_text(client):
    res = client.post("/analyze", json={"text": "오늘은 정말 행복하고 즐거운 하루였다. 최고였다!"})
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert data["label"] == "positive"
    assert 0.0 <= data["score"] <= 1.0
    assert set(data["detailed_emotions"]) == set(analyzer.EMOTIONS)
    assert data["message"]


def test_negative_text(client):
    res = client.post("/analyze", json={"text": "너무 우울하고 외롭다. 눈물이 났고 걱정도 된다."})
    assert res.get_json()["data"]["label"] == "negative"


def test_neutral_when_no_keywords():
    result = analyzer.analyze("오늘 점심으로 김치찌개를 먹고 도서관에 갔다.")
    assert result["label"] == "neutral"
    assert 0.5 < result["score"] < 1.0  # 근거가 없으므로 100% 확신은 아니다


def test_single_keyword_is_weakly_polar():
    result = analyzer.analyze("오늘은 행복했다")
    assert result["label"] == "positive"
    assert result["score"] == pytest.approx(0.5, abs=0.01)


def test_more_evidence_raises_confidence():
    weak = analyzer.analyze("행복했다")["score"]
    strong = analyzer.analyze("행복했다 즐거웠다 최고였다 감사하다")["score"]
    assert strong > weak


def test_detailed_emotions_sum_to_one():
    result = analyzer.analyze("기쁘지만 조금 불안하고 걱정된다")
    assert sum(result["detailed_emotions"].values()) == pytest.approx(1.0, abs=0.01)


@pytest.mark.parametrize("body", [None, {}, {"text": ""}, {"text": "   "}, {"text": 123}])
def test_invalid_input(client, body):
    res = client.post("/analyze", json=body) if body is not None else client.post("/analyze")
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_too_long(client):
    res = client.post("/analyze", json={"text": "가" * 5001})
    assert res.status_code == 413

import json
from unittest import mock

import pytest
import requests

import analyzer
from app import create_app


def ollama_response(payload, status=200):
    res = mock.Mock()
    res.status_code = status
    res.json.return_value = {"message": {"role": "assistant", "content": json.dumps(payload, ensure_ascii=False)}}
    res.raise_for_status.side_effect = None if status < 400 else requests.HTTPError("boom")
    return res


MIXED = {"joy": 0.8, "sadness": 0.1, "anger": 0.0, "anxiety": 0.6, "calm": 0.2, "neutral": 0.3, "message": "잘 해낼 거예요."}


@pytest.fixture(autouse=True)
def use_ollama(monkeypatch):
    monkeypatch.setenv("EMOTION_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma4:12b")


def test_request_shape():
    with mock.patch("requests.post", return_value=ollama_response(MIXED)) as post:
        analyzer.analyze("합격했다")
    (url,), kwargs = post.call_args
    body = kwargs["json"]
    assert url.endswith("/api/chat")
    assert body["model"] == "gemma4:12b"
    assert body["stream"] is False and body["think"] is False
    assert body["format"]["required"] == ["joy", "sadness", "anger", "anxiety", "calm", "neutral", "message"]
    assert "<diary>" in body["messages"][1]["content"] and "합격했다" in body["messages"][1]["content"]
    assert kwargs["timeout"] > 0


def test_result_structure_matches_other_backends():
    with mock.patch("requests.post", return_value=ollama_response(MIXED)):
        result = analyzer.analyze("합격했지만 걱정된다")
    assert result["source"] == "ollama"
    assert result["label"] in {"positive", "negative", "neutral"}
    assert 0.0 <= result["score"] <= 1.0
    assert set(result["detailed_emotions"]) == set(analyzer.EMOTIONS)
    assert sum(result["detailed_emotions"].values()) == pytest.approx(1.0, abs=0.01)
    assert sum(result["sentiment_scores"].values()) == pytest.approx(1.0, abs=0.01)
    assert result["message"] == "잘 해낼 거예요."


def test_label_follows_strongest_signal():
    positive = {**MIXED, "joy": 0.9, "anxiety": 0.1, "neutral": 0.0}
    negative = {**MIXED, "joy": 0.0, "sadness": 0.9, "anxiety": 0.2, "neutral": 0.0}
    flat = {"joy": 0.0, "sadness": 0.0, "anger": 0.0, "anxiety": 0.0, "calm": 0.1, "neutral": 0.9, "message": ""}
    for payload, expected in ((positive, "positive"), (negative, "negative"), (flat, "neutral")):
        with mock.patch("requests.post", return_value=ollama_response(payload)):
            assert analyzer.analyze("x")["label"] == expected


def test_out_of_range_values_are_clamped():
    payload = {**MIXED, "joy": 7, "sadness": -3}
    with mock.patch("requests.post", return_value=ollama_response(payload)):
        result = analyzer.analyze("x")
    assert all(0.0 <= v <= 1.0 for v in result["detailed_emotions"].values())


def test_blank_message_uses_template():
    with mock.patch("requests.post", return_value=ollama_response({**MIXED, "message": "  "})):
        assert analyzer.analyze("x")["message"]  # 템플릿 문구


def test_long_message_is_truncated():
    with mock.patch("requests.post", return_value=ollama_response({**MIXED, "message": "가" * 1000})):
        assert len(analyzer.analyze("x")["message"]) == analyzer.MAX_MESSAGE_LENGTH


def test_all_zero_scores_raise():
    zeros = {name: 0.0 for name in (*analyzer.EMOTIONS, "neutral")} | {"message": "m"}
    with mock.patch("requests.post", return_value=ollama_response(zeros)):
        with pytest.raises(ValueError):
            analyzer.analyze("x")


@pytest.mark.parametrize("failure", [requests.ConnectionError, requests.Timeout])
def test_connection_failures_propagate(failure):
    with mock.patch("requests.post", side_effect=failure):
        with pytest.raises(requests.RequestException):
            analyzer.analyze("x")


def test_malformed_model_output_raises():
    bad = mock.Mock()
    bad.raise_for_status.side_effect = None
    bad.json.return_value = {"message": {"content": "not json"}}
    with mock.patch("requests.post", return_value=bad):
        with pytest.raises(ValueError):
            analyzer.analyze("x")


def test_endpoint_returns_500_when_ollama_down():
    client = create_app().test_client()
    with mock.patch("requests.post", side_effect=requests.ConnectionError):
        res = client.post("/analyze", json={"text": "오늘 하루"})
    assert res.status_code == 500
    assert res.get_json()["success"] is False  # Django 가 이 응답을 fallback(neutral, 0.5)으로 처리한다


def test_health_reports_model():
    data = create_app().test_client().get("/health").get_json()["data"]
    assert data["backend"] == "ollama" and data["model"] == "gemma4:12b"

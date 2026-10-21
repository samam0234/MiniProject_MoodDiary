from datetime import date, timedelta
from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Diary
from .services import FALLBACK_ANALYSIS, analyze_text

User = get_user_model()

AI_OK = {
    "success": True,
    "data": {
        "label": "positive",
        "score": 0.8,
        "sentiment_scores": {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
        "detailed_emotions": {"joy": 0.7, "sadness": 0.0, "anger": 0.0, "anxiety": 0.1, "calm": 0.2},
        "message": "좋은 하루!",
        "source": "lexicon",
    },
    "error": None,
}


def fake_response(payload, status=200):
    res = mock.Mock()
    res.status_code = status
    res.json.return_value = payload
    res.raise_for_status.side_effect = None if status < 400 else requests.HTTPError("boom")
    return res


class AnalyzeTextTests(TestCase):
    @mock.patch("diaries.services.requests.post", return_value=fake_response(AI_OK))
    def test_success(self, post):
        result = analyze_text("행복한 하루")
        self.assertEqual(result["label"], "positive")
        self.assertEqual(result["source"], "lexicon")
        self.assertIn("timeout", post.call_args.kwargs)

    @mock.patch("diaries.services.requests.post", side_effect=requests.Timeout)
    def test_timeout_falls_back(self, _post):
        self.assertEqual(analyze_text("x"), FALLBACK_ANALYSIS)

    @mock.patch("diaries.services.requests.post", side_effect=requests.ConnectionError)
    def test_connection_error_falls_back(self, _post):
        self.assertEqual(analyze_text("x")["source"], "fallback")

    @mock.patch("diaries.services.requests.post", return_value=fake_response({}, status=500))
    def test_http_error_falls_back(self, _post):
        self.assertEqual(analyze_text("x")["source"], "fallback")

    @mock.patch("diaries.services.requests.post")
    def test_malformed_response_falls_back(self, post):
        for bad in (
            {"success": True, "data": {"label": "happy", "score": 0.5, "detailed_emotions": {}}},
            {"success": True, "data": {"label": "positive", "score": 7, "detailed_emotions": AI_OK["data"]["detailed_emotions"]}},
            {"success": False, "data": None, "error": "x"},
            ["not", "a", "dict"],
        ):
            post.return_value = fake_response(bad)
            self.assertEqual(analyze_text("x")["source"], "fallback", bad)


class DiaryApiTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="Str0ng-pass!23")
        self.bob = User.objects.create_user("bob", password="Str0ng-pass!23")
        self.client = APIClient()
        self.client.force_authenticate(self.alice)

    def create(self, **overrides):
        payload = {"title": "오늘", "content": "행복했다", **overrides}
        return self.client.post("/api/diaries", payload, format="json")

    @mock.patch("diaries.services.requests.post", return_value=fake_response(AI_OK))
    def test_create_runs_analysis(self, _post):
        res = self.create()
        data = res.json()["data"]
        self.assertEqual(res.status_code, 201)
        self.assertEqual(data["emotion_label"], "positive")
        self.assertEqual(data["emotion_score"], 0.8)
        self.assertEqual(data["ai_message"], "좋은 하루!")
        self.assertEqual(Diary.objects.get().user, self.alice)

    @mock.patch("diaries.services.requests.post", side_effect=requests.ConnectionError)
    def test_create_survives_ai_outage(self, _post):
        res = self.create()
        data = res.json()["data"]
        self.assertEqual(res.status_code, 201)
        self.assertEqual((data["emotion_label"], data["emotion_score"]), ("neutral", 0.5))
        self.assertEqual(data["analysis_source"], "fallback")

    @mock.patch("diaries.services.requests.post", return_value=fake_response(AI_OK))
    def test_client_cannot_set_analysis_fields(self, _post):
        res = self.create(emotion_label="negative", emotion_score=0.01)
        self.assertEqual(res.json()["data"]["emotion_label"], "positive")

    def test_validation(self):
        for payload in ({"title": "", "content": "x"}, {"title": "t", "content": "   "}, {"content": "x"}):
            res = self.client.post("/api/diaries", payload, format="json")
            self.assertEqual(res.status_code, 400, payload)
            self.assertFalse(res.json()["success"])

    def test_requires_auth(self):
        self.assertEqual(APIClient().get("/api/diaries").status_code, 401)
        self.assertEqual(APIClient().get("/api/emotions/trend").status_code, 401)

    @mock.patch("diaries.services.requests.post", return_value=fake_response(AI_OK))
    def test_data_isolation(self, _post):
        diary_id = self.create().json()["data"]["id"]

        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get("/api/diaries").json()["data"]["count"], 0)
        self.assertEqual(self.client.get(f"/api/diaries/{diary_id}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/diaries/{diary_id}").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/diaries/{diary_id}", {"title": "hack"}, format="json").status_code, 404)
        self.assertEqual(self.client.get("/api/emotions/trend").json()["data"]["summary"]["entries"], 0)
        self.assertTrue(Diary.objects.filter(pk=diary_id).exists())

    @mock.patch("diaries.services.requests.post", return_value=fake_response(AI_OK))
    def test_list_and_detail(self, _post):
        diary_id = self.create().json()["data"]["id"]
        listing = self.client.get("/api/diaries").json()["data"]
        self.assertEqual(listing["count"], 1)
        detail = self.client.get(f"/api/diaries/{diary_id}")
        self.assertEqual(detail.json()["data"]["title"], "오늘")

    @mock.patch("diaries.services.requests.post", return_value=fake_response(AI_OK))
    def test_update_reanalyzes_only_when_text_changes(self, post):
        diary_id = self.create().json()["data"]["id"]
        calls_after_create = post.call_count

        self.client.patch(f"/api/diaries/{diary_id}", {"entry_date": "2026-01-02"}, format="json")
        self.assertEqual(post.call_count, calls_after_create)

        self.client.patch(f"/api/diaries/{diary_id}", {"content": "새 내용"}, format="json")
        self.assertEqual(post.call_count, calls_after_create + 1)

    @mock.patch("diaries.services.requests.post", return_value=fake_response(AI_OK))
    def test_delete(self, _post):
        diary_id = self.create().json()["data"]["id"]
        self.assertEqual(self.client.delete(f"/api/diaries/{diary_id}").status_code, 204)
        self.assertFalse(Diary.objects.exists())


class TrendApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="Str0ng-pass!23")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.today = timezone.localdate()

    def add(self, days_ago, label, score, **detailed):
        emotions = {"joy": 0.0, "sadness": 0.0, "anger": 0.0, "anxiety": 0.0, "calm": 0.0, **detailed}
        return Diary.objects.create(
            user=self.user, title="t", content="c", entry_date=self.today - timedelta(days=days_ago),
            emotion_label=label, emotion_score=score, detailed_emotions=emotions,
        )

    def test_aggregates_per_day_and_window(self):
        self.add(0, "positive", 0.8, joy=1.0)
        self.add(0, "negative", 0.4, sadness=1.0)
        self.add(2, "negative", 0.6, sadness=1.0)
        self.add(10, "positive", 0.9)  # 7일 범위 밖

        data = self.client.get("/api/emotions/trend?days=7").json()["data"]
        self.assertEqual(data["summary"]["entries"], 3)
        self.assertEqual([p["date"] for p in data["points"]], [
            (self.today - timedelta(days=2)).isoformat(), self.today.isoformat(),
        ])
        today_point = data["points"][-1]
        self.assertEqual(today_point["entries"], 2)
        self.assertAlmostEqual(today_point["sentiment"], (0.8 - 0.4) / 2)
        self.assertEqual((today_point["positive"], today_point["negative"]), (1, 1))
        self.assertAlmostEqual(today_point["joy"], 0.5)

        self.assertEqual(self.client.get("/api/emotions/trend?days=30").json()["data"]["summary"]["entries"], 4)

    def test_empty(self):
        data = self.client.get("/api/emotions/trend").json()["data"]
        self.assertEqual(data["points"], [])
        self.assertIsNone(data["summary"]["average_sentiment"])

    def test_invalid_days(self):
        for value in ("abc", "0", "999"):
            self.assertEqual(self.client.get(f"/api/emotions/trend?days={value}").status_code, 400, value)

    def test_neutral_counts_as_zero(self):
        self.add(0, "neutral", 0.9)
        self.assertEqual(self.client.get("/api/emotions/trend").json()["data"]["points"][0]["sentiment"], 0.0)

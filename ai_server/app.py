"""MoodDiary AI 서버 (Flask).

엔드포인트:
    GET  /health   서버 상태 확인
    POST /analyze  {"text": "..."} -> 감정 분석 결과
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

import analyzer

load_dotenv()

MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mood_diary.ai_server")


def log_event(event: str, **fields: Any) -> None:
    """구조화(JSON) 로그를 한 줄로 기록한다."""
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))


def ok(data: Any, status: int = 200):
    return jsonify({"success": True, "data": data, "error": None}), status


def fail(message: str, status: int):
    return jsonify({"success": False, "data": None, "error": message}), status


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False
    CORS(app, origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","))

    @app.get("/health")
    def health():
        return ok({"status": "ok", "backend": os.getenv("EMOTION_BACKEND", "lexicon")})

    @app.post("/analyze")
    def analyze():
        payload = request.get_json(silent=True)
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str) or not text.strip():
            return fail("text 필드는 비어 있지 않은 문자열이어야 합니다.", 400)
        if len(text) > MAX_TEXT_LENGTH:
            return fail(f"text 는 {MAX_TEXT_LENGTH}자 이하여야 합니다.", 413)

        started = time.perf_counter()
        try:
            result = analyzer.analyze(text)
        except Exception:  # 모델 로딩/추론 실패는 호출자(Django)가 fallback 처리한다.
            logger.exception("analyze_failed")
            log_event("analyze_failed", text_length=len(text))
            return fail("감정 분석 중 오류가 발생했습니다.", 500)

        log_event(
            "analyze_done",
            label=result["label"],
            score=result["score"],
            source=result["source"],
            text_length=len(text),
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        return ok(result)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))

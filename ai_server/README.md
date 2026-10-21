# ai_server (Flask)

일기 텍스트를 받아 감정 분석 결과를 돌려주는 서버. 기본 포트 **5000**.

```powershell
# 프로젝트 루트의 .venv 활성화 후
python app.py                 # http://localhost:5000
python -m pytest              # 25개 (pip install pytest 필요, 실제 LLM 호출 없음)
```

| 파일 | 역할 |
|------|------|
| `app.py` | Flask 앱, `/health`, `POST /analyze`, 입력 검증, JSON 구조화 로그, CORS |
| `analyzer.py` | 분석 엔진 (`ollama` 사용 중 / `lexicon` 대체 / `transformers` 선택) |
| `test_app.py` | pytest |
| `conftest.py`, `test_ollama.py` | 테스트는 항상 lexicon/mock 으로 동작 (로컬 `.env` 가 ollama 여도 LLM 호출 안 함) |
| `.env.example` | `PORT`, `EMOTION_BACKEND`, `OLLAMA_URL/MODEL/TIMEOUT/KEEP_ALIVE/TEMPERATURE`, `MAX_TEXT_LENGTH`, `CORS_ALLOWED_ORIGINS` |

## `POST /analyze`

요청 `{"text": "..."}` (비어 있으면 400, 5000자 초과 시 413)

```json
{"success": true, "error": null, "data": {
  "label": "positive", "score": 0.7727,
  "sentiment_scores": {"positive": 0.7727, "negative": 0.0455, "neutral": 0.1818},
  "detailed_emotions": {"joy": 1.0, "sadness": 0.0, "anger": 0.0, "anxiety": 0.0, "calm": 0.0},
  "message": "기분 좋은 하루였네요! ...", "source": "ollama"
}}
```

- `score` 는 `label` 에 대한 확신도(0~1). 세부 감정 5종: joy, sadness, anger, anxiety, calm.
- 이 서버가 실패하거나 느려도 Django 가 timeout/fallback(neutral, 0.5)으로 처리한다.
- **Ollama 백엔드**: `ollama serve` 실행 + `ollama pull gemma4:12b` 필요. `POST {OLLAMA_URL}/api/chat` 에 JSON 스키마(`format`)와 `think:false` 를 보내 감정 5종 + neutral 강도(0~1)와 격려 문구를 받는다. 값은 0~1 로 clamp, 세부 감정은 합 1 로 정규화하며, 긍정 = max(joy, calm), 부정 = max(sadness, anger, anxiety), 중립 = neutral 을 정규화해 label/score 를 정한다. 일기 글은 `<diary>` 태그로 감싸 지시문으로 취급하지 않도록 한다.
- Ollama 연결 실패·timeout·잘못된 JSON 이면 이 서버는 500 을 반환하고, Django 가 neutral/0.5 로 fallback 한다.
- `EMOTION_BACKEND=transformers` 를 쓰려면 `requirements.txt` 의 주석(`transformers`, `torch`)을 풀어 설치한다. (실제 모델로는 미검증)
- 분석 방식과 한계: [Docs/Architecture/ARCHITECTURE.md](../Docs/Architecture/ARCHITECTURE.md) §7

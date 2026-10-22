# API 가이드

기본 주소 `http://localhost:8000` · 인증이 필요한 API 는 `Authorization: Bearer <access>` 헤더 사용.

모든 응답은 다음 형식이다.

```json
{"success": true,  "data": ..., "error": null}
{"success": false, "data": null, "error": {"message": "...", "details": ...}}
```

## 1. 인증 `/api/auth`

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/api/auth/register` | 불필요 | 가입 → 201, 사용자 + 토큰 |
| POST | `/api/auth/login` | 불필요 | 로그인 → 200, 사용자 + 토큰 |
| POST | `/api/auth/refresh` | 불필요 | `{"refresh": "..."}` → 새 `access` |
| GET | `/api/auth/me` | 필요 | 현재 사용자 |

```jsonc
// POST /api/auth/register   {"username": "alice", "password": "Str0ng-pass!23", "email": "(선택)"}
{"success": true, "data": {
  "user":   {"id": 1, "username": "alice", "email": ""},
  "tokens": {"access": "eyJ...", "refresh": "eyJ..."}
}, "error": null}
```

| 상태 | 상황 |
|------|------|
| 400 | 비밀번호 규칙 위반(`details.password` 에 메시지 목록), 중복 아이디 |
| 401 | 로그인 실패(아이디/비밀번호 불일치), 유효하지 않은 토큰 |

> register/login 은 인증 클래스를 비활성화해 두었다. 만료된 토큰이 헤더에 남아 있어도 로그인이 막히지 않는다.

## 2. 일기 `/api/diaries`

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/diaries?page=1&page_size=20` | 내 일기 목록 (최신 날짜순, `page_size` 최대 100) |
| POST | `/api/diaries` | 작성 + 감정 분석 → 201 |
| GET | `/api/diaries/{id}` | 상세 |
| PATCH / PUT | `/api/diaries/{id}` | 수정 (title/content 가 바뀌면 재분석) |
| DELETE | `/api/diaries/{id}` | 삭제 → 204 (본문 없음) |
| POST | `/api/diaries/{id}/reanalyze` | 저장된 일기를 현재 AI 모델로 다시 분석 (아래 §2-1) |

요청 본문 (POST): `title`(필수, ≤200자), `content`(필수, ≤5000자), `entry_date`(선택, `YYYY-MM-DD`, 기본 오늘).
`emotion_*`, `detailed_emotions`, `ai_message`, `analysis_source` 는 서버가 채우며 요청에 넣어도 무시된다.

```jsonc
// 201 data
{
  "id": 3, "title": "좋은 날", "content": "오늘은 정말 행복했다.",
  "entry_date": "2026-10-22", "created_at": "...", "updated_at": "...",
  "emotion_label": "positive",          // positive | negative | neutral
  "emotion_score": 0.77,                // label 에 대한 확신도 0~1
  "detailed_emotions": {"joy": 1.0, "sadness": 0.0, "anger": 0.0, "anxiety": 0.0, "calm": 0.0},
  "ai_message": "기분 좋은 하루였네요! ...",
  "analysis_source": "ollama"           // ollama | lexicon | transformers | fallback
}
```

```jsonc
// 목록 data
{"count": 3, "next": null, "previous": null, "results": [ {일기}, ... ]}
```

| 상태 | 상황 |
|------|------|
| 400 | 제목/내용 비어 있음, 길이 초과 |
| 401 | 토큰 없음/무효 |
| 404 | 없는 일기 **또는 다른 사용자의 일기** |

AI 서버가 장애여도 저장은 성공하며 `emotion_label="neutral"`, `emotion_score=0.5`, `analysis_source="fallback"` 으로 기록된다.

### 2-1. 다시 분석 `POST /api/diaries/{id}/reanalyze`

저장된 제목·본문을 **현재 AI 모델**로 다시 분석해 `emotion_*`, `detailed_emotions`, `ai_message`, `analysis_source` 를 갱신한다. 요청 본문은 없다. AI 서버 장애로 기본값(fallback)이 나왔던 일기를 복구하거나, 모델/프롬프트를 바꾼 뒤 결과를 갱신할 때 쓴다.

```jsonc
// 200 data: 일기 전체 + 이전 분석 결과(비교용)
{
  "id": 3, "title": "...", "emotion_label": "positive", "emotion_score": 0.9, "analysis_source": "ollama", "...": "...",
  "previous": {"emotion_label": "neutral", "emotion_score": 0.5, "analysis_source": "fallback"}
}
```

| 상태 | 상황 |
|------|------|
| 200 | 재분석 성공 (결과가 같아도 200) |
| 503 | AI 서버 장애/시간 초과/잘못된 응답. **기존 분석 결과는 그대로 유지**되고 `error.message` 에 안내 문구가 담긴다 |
| 401 / 404 | 인증 없음 / 없는 일기 또는 다른 사용자의 일기 (이 경우 AI 도 호출하지 않는다) |
| 405 | POST 외 메서드 |

> 수정(PATCH)은 본문이 바뀔 때만 재분석하고 장애 시 fallback 값으로 저장하지만, 다시 분석은 장애 시 **저장하지 않고 오류를 돌려준다.** 좋은 결과가 기본값으로 덮이는 것을 막기 위함이다.

## 3. 감정 트렌드 `GET /api/emotions/trend?days=7`

`days` 는 1~90 정수(기본 7). 오늘 포함 최근 N일, **일기가 있는 날짜만** 반환한다.

```jsonc
{
  "days": 7, "start": "2026-10-16", "end": "2026-10-22",
  "points": [{
    "date": "2026-10-22", "entries": 3,
    "sentiment": 0.0,                         // −1(부정) ~ +1(긍정), 일별 평균
    "positive": 1, "negative": 1, "neutral": 1,
    "joy": 0.4, "sadness": 0.233, "anger": 0.067, "anxiety": 0.233, "calm": 0.067
  }],
  "summary": {"entries": 3, "average_sentiment": 0.0,
              "label_counts": {"positive": 1, "negative": 1, "neutral": 1}}
}
```

일기가 없으면 `points=[]`, `average_sentiment=null`. `days` 가 범위 밖이거나 정수가 아니면 400.

## 4. AI 서버 (내부용) `:5000`

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | `{"status": "ok", "backend": "ollama", "model": "gemma4:12b"}` |
| POST | `/analyze` | `{"text": "..."}` → 분석 결과 |

`/analyze` 응답 `data`: `label`, `score`, `sentiment_scores`(positive/negative/neutral), `detailed_emotions`, `message`, `source`.
오류: 400(text 가 비었거나 문자열 아님), 413(5000자 초과), 500(분석 실패 — Django 가 fallback 처리).

# 시스템 아키텍처

**작성일**: 2026-10-22 · 구현 기준 브랜치 `feature/mood-diary-mvp`

## 1. 구성

```
[Browser]
   │ HTTP / WebSocket
[Reflex :3000 ── Reflex 백엔드 :8001]      ← 상태(State)와 이벤트 핸들러가 여기서 실행된다
   │ REST (httpx, 서버 측 호출)
[Django + DRF :8000] ──── [SQLite (기본) / PostgreSQL :5432]
   │ HTTP (requests, timeout 5s)
[Flask AI :5000] ──── [감정 분석 엔진: lexicon | transformers]
```

| 계층 | 위치 | 책임 |
|------|------|------|
| UI | `frontend/mood_diary/pages.py`, `components.py` | 화면 구성, 로딩/에러 표시 |
| 상태 | `frontend/mood_diary/state.py` | 로그인 토큰, 목록/상세/트렌드 상태, 이벤트 핸들러 |
| API 클라이언트 | `frontend/mood_diary/api.py` | Django 호출, 응답을 `ApiResult` 로 변환 (예외를 던지지 않음) |
| 뷰 모델 | `frontend/mood_diary/view_models.py` | 응답 → 화면용 평평한 구조 (Reflex 비의존, 단독 테스트 가능) |
| 인증 | `backend/accounts/` | 커스텀 User, 가입/로그인/refresh/me |
| 일기 | `backend/diaries/` | 일기 CRUD, AI 연동(`services.py`), 트렌드 집계 |
| 공통 | `backend/common/` | 응답 래퍼 렌더러, 예외 핸들러, 페이지네이션 |
| AI | `ai_server/analyzer.py`, `app.py` | 감정 분석, 입력 검증, 구조화 로그 |

> 브라우저는 Django 를 직접 호출하지 않는다. Reflex 이벤트 핸들러(서버 측 Python)가 호출하므로 브라우저 CORS 는 개입하지 않는다.
> 그래도 `django-cors-headers` 와 Flask CORS 는 규칙에 따라 명시적으로 설정해 두었다.

## 2. 일기 작성 데이터 흐름

```
사용자 제출
 → Reflex create_diary (is_saving=True, 로딩 표시)
 → POST /api/diaries                        (Bearer access 토큰)
 → DiaryViewSet.perform_create
 → services.analyze_text("제목\n내용")
 → POST ai_server/analyze                    (timeout AI_SERVER_TIMEOUT=5s)
     ├ 성공 + 응답 구조 검증 통과 → 분석 결과 사용
     └ 타임아웃 / 연결 실패 / HTTP 오류 / 잘못된 구조 → FALLBACK (neutral, 0.5)
 → Diary 저장 (analysis_source = lexicon | transformers | fallback)
 → 201 응답 → Reflex 가 상세 페이지로 이동
```

- **fallback 원칙**: AI 서버 장애가 일기 저장을 막지 않는다. 대신 `analysis_source="fallback"` 로 표시하고 화면에 안내 문구를 보여준다.
- **응답 구조 검증**: label 이 positive/negative/neutral 인지, score 가 0~1 인지, `detailed_emotions` 키가 정확히 5종인지 확인한다. 어긋나면 fallback 으로 처리해 DB 의 결과 구조를 항상 일관되게 유지한다.
- 본문(제목/내용)이 바뀐 수정 요청에서만 재분석한다.

## 3. 인증 흐름

1. 가입/로그인 → 서버가 JWT `access`(60분) + `refresh`(7일) 발급.
2. Reflex 가 `LocalStorage` 에 보관 (새로고침 후에도 유지).
3. 인증 필요 호출에서 401 → `refresh` 로 access 재발급을 **한 번** 시도 → 실패하면 세션을 지우고 `/login` 으로 이동.
4. 모든 일기 쿼리는 `Diary.objects.filter(user=request.user)` 로 시작한다. 타인의 일기는 404 로 취급한다.

## 4. 응답 형식 (전 API 공통)

```json
{"success": true,  "data": { ... }, "error": null}
{"success": false, "data": null,    "error": {"message": "...", "details": ...}}
```

- `common.renderers.EnvelopeJSONRenderer` 가 모든 응답을 감싼다. 204 는 본문이 없다.
- `common.exceptions.api_exception_handler` 가 오류를 `{message, details}` 로 통일한다. 검증 오류는 `details` 에 필드별 메시지를 담고, 인증/404 는 `details=null`.

## 5. 데이터 모델

**User** — `AbstractUser` 상속 (`accounts.User`). 처음부터 커스텀 모델로 시작해 이후 확장이 가능하다.

**Diary**

| 필드 | 타입 | 비고 |
|------|------|------|
| user | FK(User) | CASCADE, `related_name="diaries"` |
| title | Char(200) | 공백만 입력 불가 |
| content | Text | 최대 5000자 |
| entry_date | Date | 일기 날짜, 기본 오늘. **트렌드 집계 기준** |
| created_at / updated_at | DateTime | 자동 |
| emotion_label | Char | positive / negative / neutral |
| emotion_score | Float | 0.0~1.0, **label 에 대한 확신도** |
| detailed_emotions | JSON | joy, sadness, anger, anxiety, calm (합 ≈ 1.0) |
| ai_message | Text | 격려/조언 문구 (선택 기능) |
| analysis_source | Char(20) | lexicon / transformers / fallback |

- 정렬: `-entry_date, -created_at` · 인덱스: `(user, entry_date)`
- 분석 필드(`emotion_*`, `detailed_emotions`, `ai_message`, `analysis_source`)는 읽기 전용이라 클라이언트가 직접 쓸 수 없다.

## 6. 감정 지수 (트렌드)

`emotion_score` 는 확신도라 그대로 더하면 의미가 없다. 트렌드에서는 아래처럼 −1 ~ +1 로 환산한다.

| label | 값 |
|-------|----|
| positive | +score |
| negative | −score |
| neutral | 0 |

하루에 여러 편이면 평균을 낸다. 일기가 있는 날짜만 `points` 에 포함하고(빈 날은 생략), `summary` 에 전체 건수·평균·라벨별 개수를 담는다.

## 7. 감정 분석 엔진 (lexicon)

1. 감정 5종(기쁨·슬픔·분노·불안·평온)별 한국어 키워드(어간)의 등장 횟수를 센다.
2. `detailed_emotions` = 횟수 비율. 키워드가 없으면 균등(0.2).
3. 긍정 근거 P = 기쁨+평온, 부정 근거 N = 슬픔+분노+불안.
4. 분모 = P + N + 중립 prior(1.0) + 극성 prior(0.25×2).
   긍정 = (P+0.25)/분모, 부정 = (N+0.25)/분모, 중립 = 1.0/분모.
5. 최댓값이 label, 그 값이 score. (근거가 없으면 중립 ≈ 0.67, 키워드 1개면 극성 ≈ 0.5)

한계: 부정문("기쁘지 않았다")·반어는 구분하지 못한다. 학습·데모용 기본 엔진이며 정확도가 필요하면 `transformers` 백엔드로 교체한다(미검증).

## 8. 환경 변수 요약

| 서비스 | 변수 | 기본값 |
|--------|------|--------|
| backend | `DJANGO_DEBUG` / `DJANGO_SECRET_KEY` / `DJANGO_ALLOWED_HOSTS` | true / (개발용 키) / localhost |
| backend | `AI_SERVER_URL` / `AI_SERVER_TIMEOUT` | http://localhost:5000 / 5 |
| backend | `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS` | 60 / 7 |
| backend | `DB_ENGINE` (+ `POSTGRES_*`) | sqlite |
| ai_server | `EMOTION_BACKEND` / `EMOTION_MODEL` / `MAX_TEXT_LENGTH` | lexicon / – / 5000 |
| frontend | `MOOD_DIARY_API_URL` / `MOOD_DIARY_API_TIMEOUT` | http://localhost:8000 / 20 |

`DJANGO_DEBUG=false` 인데 `DJANGO_SECRET_KEY` 가 없으면 서버가 기동 시 오류로 중단된다.

# MoodDiary

일기를 쓰면 AI가 감정을 분석하고, 감정 변화를 차트로 보여주는 미니 프로젝트.
설계는 [Docs/plan/mood-diary-plan.md](Docs/plan/mood-diary-plan.md), 작업 규칙은 [MoodDiary_인수인계.md](MoodDiary_인수인계.md)(규칙의 단일 출처)를 따른다.

```
[Reflex :3000 (+ Reflex 백엔드 :8001)] → [Django :8000] → [Flask AI :5000]
                                              ↓
                                  SQLite (기본) / PostgreSQL
```

| 폴더 | 역할 | 포트 |
|------|------|------|
| `frontend/` | Reflex UI (로그인, 일기 목록/작성/상세, 감정 트렌드 차트) | 3000 (Reflex 내부 백엔드 8001) |
| `backend/` | Django + DRF + JWT (인증, 일기 CRUD, 트렌드 집계) | 8000 |
| `ai_server/` | Flask 감정 분석 (`POST /analyze`) | 5000 |

> Reflex의 기본 백엔드 포트는 8000이라 Django와 충돌한다. 그래서 [frontend/rxconfig.py](frontend/rxconfig.py)에서 8001로 분리했다.

## 실행

Python 3.10+ 필요. 프로젝트 루트에서:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ai_server/requirements.txt -r backend/requirements.txt -r frontend/requirements.txt

# 각 폴더의 .env.example 을 .env 로 복사 (기본값 그대로 로컬 실행 가능)
```

터미널 3개에서 각각 실행한다.

```powershell
# 1) AI 서버
cd ai_server; python app.py

# 2) Django (최초 1회 migrate)
cd backend; python manage.py migrate; python manage.py runserver 8000

# 3) 프론트엔드 → http://localhost:3000
cd frontend; reflex run
```

AI 서버가 꺼져 있어도 일기는 저장된다. 이때 분석 결과는 `neutral / 0.5`(fallback)로 기록되고 상세 화면에 안내가 표시된다.

## PostgreSQL (선택)

기본은 SQLite다. PostgreSQL을 쓰려면 루트의 `.env.example`을 `.env`로 복사한 뒤 `docker compose up -d db`를 실행하고,
`backend/.env`에 `DB_ENGINE=postgres`와 같은 `POSTGRES_*` 값을 넣고 `python manage.py migrate`를 다시 실행한다.

## 루트 구조

```
frontend/ backend/ ai_server/   # 각 서버 (requirements.txt, .env.example 포함)
Docs/                           # plan, Architecture, branchs, find_debug, guidance, trainings, repeater, vaildates, web_management
docker-compose.yml              # PostgreSQL (프로젝트명 mood-diary)
MoodDiary_인수인계.md           # 작업 규칙 SSOT (CLAUDE.md 는 이 문서를 가리키기만 한다)
```

## 테스트

```powershell
cd ai_server; python -m pytest        # pip install pytest 필요
cd backend;   python manage.py test
cd frontend;  python -m pytest tests
```

## API (모든 응답: `{"success": bool, "data": ..., "error": ...}`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auth/register` | 회원가입 → 사용자 + JWT |
| POST | `/api/auth/login` | 로그인 → 사용자 + JWT |
| POST | `/api/auth/refresh` | access 토큰 재발급 |
| GET | `/api/auth/me` | 내 정보 |
| GET / POST | `/api/diaries` | 목록(페이지네이션) / 작성 + 감정 분석 |
| GET / PATCH / DELETE | `/api/diaries/{id}` | 상세 / 수정(본문 변경 시 재분석) / 삭제 |
| GET | `/api/emotions/trend?days=7` | 최근 N일 일자별 감정 추이 (1~90) |

인증이 필요한 API는 `Authorization: Bearer <access>` 헤더를 사용한다. 일기는 항상 본인 것만 조회·수정된다.

## 감정 분석

기본 백엔드는 한국어 키워드 사전 방식(`EMOTION_BACKEND=lexicon`)이라 모델 다운로드 없이 바로 동작한다.
결과는 긍정/부정/중립 + 세부 감정 5종(기쁨·슬픔·분노·불안·평온)이며, 트렌드의 "감정 지수"는 긍정 `+score`, 부정 `-score`, 중립 `0`으로 환산한 값이다(−1 ~ +1).

Hugging Face 모델을 쓰려면 `ai_server/requirements.txt`의 `transformers`, `torch` 주석을 풀어 설치하고 `EMOTION_BACKEND=transformers`로 지정한다.
(이 경로는 코드만 작성되어 있고 실제 모델로는 아직 검증하지 않았다.)

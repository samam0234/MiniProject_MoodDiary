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
| [frontend/](frontend/README.md) | Reflex UI (로그인, 일기 목록/작성/상세, 감정 트렌드 차트) | 3000 (Reflex 내부 백엔드 8001) |
| [backend/](backend/README.md) | Django + DRF + JWT (인증, 일기 CRUD, 트렌드 집계) | 8000 |
| [ai_server/](ai_server/README.md) | Flask 감정 분석 (`POST /analyze`) | 5000 |

## 현재 상태

`feature/mood-diary-mvp` 에서 MVP 구현 완료 (병합 전). 자동 테스트 56개 통과(AI 25 · Django 26 · 프론트 5), 세 서버 연동 확인. 감정 분석은 Ollama `gemma4:12b` 사용.
**아직 확인하지 않은 것**: 브라우저에서의 화면 조작(차트 렌더링 포함), transformers 백엔드, PostgreSQL 연결, 화면에서 Ollama 분석 흐름 전체. 자세한 내용은 [검증 체크리스트](Docs/vaildates/VALIDATION_CHECKLIST.md).

> Reflex의 기본 백엔드 포트는 8000이라 Django와 충돌한다. 그래서 [frontend/rxconfig.py](frontend/rxconfig.py)에서 8001로 분리했다.

## 실행

Python 3.10+ 필요. 프로젝트 루트에서:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ai_server/requirements.txt -r backend/requirements.txt -r frontend/requirements.txt

# 각 폴더의 .env.example 을 .env 로 복사 (없어도 기본값으로 로컬 실행 가능)
```

> 패키지는 `.venv` 에만 설치된다. **새 터미널을 열 때마다** `.\.venv\Scripts\Activate.ps1` 을 먼저 실행해야 한다. (안 하면 `ModuleNotFoundError`)

터미널 3개에서 각각 실행한다.

```powershell
# 1) AI 서버
cd ai_server; python app.py

# 2) Django (최초 1회 migrate)
cd backend; python manage.py migrate; python manage.py runserver 8000

# 3) 프론트엔드 → http://localhost:3000
cd frontend; reflex run
```

문제가 생기면 [실행 가이드의 문제 해결](Docs/guidance/RUN_GUIDE.md#5-문제-해결)을 먼저 확인한다. (예: `reflex run` 종료 후 8001 포트가 계속 점유되는 경우)

AI 서버가 꺼져 있어도 일기는 저장된다. 이때 분석 결과는 `neutral / 0.5`(fallback)로 기록되고 상세 화면에 안내가 표시된다.

## PostgreSQL (선택)

기본은 SQLite다. PostgreSQL을 쓰려면 루트의 `.env.example`을 `.env`로 복사한 뒤 `docker compose up -d db`를 실행하고,
`backend/.env`에 `DB_ENGINE=postgres`와 같은 `POSTGRES_*` 값을 넣고 `python manage.py migrate`를 다시 실행한다.

## 루트 구조

```
frontend/ backend/ ai_server/   # 각 서버 (README.md, requirements.txt, .env.example 포함)
Docs/                           # 문서 모음 (인덱스: Docs/README.md)
docker-compose.yml, .env.example  # PostgreSQL (프로젝트명 mood-diary)
MoodDiary_인수인계.md           # 작업 규칙 SSOT
CLAUDE.md                       # 인수인계 문서를 가리키기만 한다
.Agents .Claude .Codex .Grok .Gemini .Antigravity .Cursor .Manus   # 에이전트별 HANDOVER.md (SSOT 안내)
```

| 문서 | 내용 |
|------|------|
| [Docs/Architecture/ARCHITECTURE.md](Docs/Architecture/ARCHITECTURE.md) | 구성, 데이터 흐름, 인증, 데이터 모델, 감정 지수 |
| [Docs/guidance/RUN_GUIDE.md](Docs/guidance/RUN_GUIDE.md) | 실행·포트·문제 해결 |
| [Docs/guidance/API_GUIDE.md](Docs/guidance/API_GUIDE.md) | API 요청/응답 예시 |
| [Docs/vaildates/VALIDATION_CHECKLIST.md](Docs/vaildates/VALIDATION_CHECKLIST.md) | 검증 현황과 미검증 항목 |
| [Docs/find_debug/](Docs/find_debug/261022_debug_log.md) · [Docs/repeater/](Docs/repeater/261022_port_conflict.md) | 디버깅·포트 이슈 기록 |
| [Docs/web_management/PRE_DEPLOY_CHECKLIST.md](Docs/web_management/PRE_DEPLOY_CHECKLIST.md) | 배포 전 점검 |

## 테스트

```powershell
cd ai_server; python -m pytest        # 25개 (pip install pytest 필요, 실제 LLM 호출 없음)
cd backend;   python manage.py test   # 26개
cd frontend;  python -m pytest tests  # 5개
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

인증이 필요한 API는 `Authorization: Bearer <access>` 헤더를 사용한다. 일기는 항상 본인 것만 조회·수정된다. 요청/응답 예시는 [API 가이드](Docs/guidance/API_GUIDE.md).

## 계정

회원가입·로그인(JWT access 60분 / refresh 7일), 사용자별 데이터 분리를 지원한다. 이메일 인증, 비밀번호 찾기, 로그아웃 시 서버 측 토큰 무효화, 로그인 시도 제한은 아직 없다.

## 감정 분석

**Ollama `gemma4:12b`** (로컬 LLM)를 사용한다. 먼저 Ollama 가 실행 중이고 모델이 받아져 있어야 한다.

```powershell
ollama list                  # gemma4:12b 가 보여야 한다
ollama pull gemma4:12b       # 없을 때만 (약 7.6GB)
```

설정은 `ai_server/.env` (`EMOTION_BACKEND=ollama`, `OLLAMA_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT` …)에 있고 예시는 `.env.example` 이다.
첫 호출은 모델을 메모리에 올리느라 15초 안팎 걸리고(이후 4~9초), 그래서 Django `AI_SERVER_TIMEOUT=90`, 프론트 `MOOD_DIARY_API_TIMEOUT=120` 으로 설정한다. Ollama 가 꺼져 있으면 일기는 저장되되 `neutral / 0.5`(fallback)로 기록된다.

Ollama 를 쓰지 않을 때는 `EMOTION_BACKEND=lexicon` (한국어 키워드 사전, 의존성·다운로드 없음)으로 바꾼다.
결과는 긍정/부정/중립 + 세부 감정 5종(기쁨·슬픔·분노·불안·평온)이며, 트렌드의 "감정 지수"는 긍정 `+score`, 부정 `-score`, 중립 `0`으로 환산한 값이다(−1 ~ +1).

Hugging Face 모델을 쓰려면 `ai_server/requirements.txt`의 `transformers`, `torch` 주석을 풀어 설치하고 `EMOTION_BACKEND=transformers`로 지정한다.
(이 경로는 코드만 작성되어 있고 실제 모델로는 아직 검증하지 않았다.)

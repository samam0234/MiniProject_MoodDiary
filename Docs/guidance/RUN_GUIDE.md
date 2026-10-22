# 실행 가이드

## 1. 준비 (최초 1회)

```powershell
cd D:\vscode\2026_my_WebSite_study\MiniProject\MoodDiary
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ai_server/requirements.txt -r backend/requirements.txt -r frontend/requirements.txt
```

- Python 3.10 이상. (Reflex 는 3.10 지원 중단 예고 경고를 출력하지만 동작한다. 가능하면 3.11+ 권장.)
- `.env` 는 없어도 기본값으로 실행된다. 값을 바꾸려면 각 폴더의 `.env.example` 을 `.env` 로 복사한다. (`.env` 는 커밋 금지)

## 2. Ollama 준비 (AI 분석용)

감정 분석은 로컬 **Ollama `gemma4:12b`** 를 사용한다 (`ai_server/.env` 의 `EMOTION_BACKEND=ollama`).

```powershell
ollama list                  # gemma4:12b 가 보여야 한다 (Ollama 는 보통 11434 포트로 자동 실행)
ollama pull gemma4:12b       # 없을 때만, 약 7.6GB
```

- 첫 분석은 모델 로딩 때문에 15초 안팎, 이후 4~9초 걸린다. 일기 저장 화면에서 로딩 문구가 나오는 것이 정상이다.
- Ollama 없이 쓰려면 `ai_server/.env` 를 `EMOTION_BACKEND=lexicon` 으로 바꾸고 AI 서버를 재시작한다.
- `.env` 를 바꾼 뒤에는 **해당 서버를 재시작**해야 적용된다.

## 3. 실행 — 터미널 3개

**터미널마다 먼저 `.venv` 를 활성화해야 한다.** 패키지가 `.venv` 에만 설치되어 있다.

| 순서 | 폴더 | 명령 | 확인 |
|------|------|------|------|
| 1 | `ai_server` | `python app.py` | http://localhost:5000/health |
| 2 | `backend` | `python manage.py migrate` (최초 1회)<br>`python manage.py runserver 8000` | 로그인 없이 `/api/auth/me` → 401 이면 정상 |
| 3 | `frontend` | `reflex run` | http://localhost:3000 |

실행 순서는 AI → Django → Reflex 를 권장하지만, AI 서버가 꺼져 있어도 일기는 저장된다(fallback).

## 4. 포트

| 포트 | 서비스 |
|------|--------|
| 3000 | Reflex 프론트엔드 |
| **8001** | **Reflex 내부 백엔드** (기본값 8000 은 Django 와 충돌해 `frontend/rxconfig.py` 에서 변경) |
| 8000 | Django |
| 5000 | Flask AI |
| 11434 | Ollama |
| 5432 | PostgreSQL (선택, `docker compose up -d db`) |

## 5. 테스트

```powershell
cd ai_server;  python -m pytest            # 25개 (pytest 설치 필요: pip install pytest, 실제 LLM 호출 없음)
cd backend;    python manage.py test       # 26개
cd frontend;   python -m pytest tests      # 8개
cd frontend;   python e2e/ui_flow.py        # 브라우저 클릭 흐름(선택): 세 서버 실행 중 + pip install playwright, Edge 사용
```

## 6. 문제 해결

| 증상 | 원인 / 해결 |
|------|-------------|
| `ModuleNotFoundError: flask / corsheaders / ...` | `.venv` 미활성화. `.\.venv\Scripts\Activate.ps1` 후 다시 실행 |
| `flask`, `reflex` 명령을 찾을 수 없음 | 위와 동일 (시스템 Python 에는 설치하지 않았다) |
| `reflex run` 이 포트 8001/3000 사용 중이라며 실패 | 이전 `reflex run` 의 자식 프로세스가 남은 것. 아래 명령으로 점유 프로세스 확인 후 종료 |
| `pip install -r` 중 `UnicodeDecodeError: 'cp949'` | requirements.txt 에 한글 주석을 넣지 말 것 (pip 가 시스템 인코딩으로 읽는다) |
| 일기가 항상 "중립 50%" + 안내 문구 | AI 서버 연결 실패(fallback). 5000 포트 서버, `AI_SERVER_URL`, **Ollama 실행 여부(`ollama list`)** 확인. 첫 호출이 timeout 보다 오래 걸리지 않는지도 확인 |
| `.env` 를 바꿨는데 반영이 안 됨 | 서버를 재시작해야 한다. 5000 포트의 AI 서버가 예전 코드/설정으로 떠 있는지 확인 |
| 임시로 서버를 띄웠는데 다른 응답(404 등)이 옴 | 그 포트를 다른 프로그램이 쓰는 중. `Get-NetTCPConnection -LocalPort <포트>` 로 확인 (예: 5055 는 innorixes 가 사용) |
| 화면이 `Application Error: Failed to fetch dynamically imported module` 로 깨지고 콘솔에 `504 (Outdated Optimize Dep)` | Vite 개발 서버의 의존성 최적화 문제. 페이지에서 `rx.icon`(lucide)을 쓰지 않는다. 이미 생겼다면 `reflex run` 재시작(필요하면 `frontend/.web/node_modules/.vite` 삭제) |
| CSS(`assets/mood.css`)를 고쳤는데 화면이 그대로 | 개발 서버는 `.py` 파일이 바뀔 때 assets 를 복사한다. 아무 `.py` 를 저장하거나 서버를 재시작 |
| 로그인이 자꾸 풀림 | access 60분 만료 후 refresh 도 실패(7일 경과 또는 DB 초기화). 다시 로그인 |
| DB 를 지운 뒤 오류 | `python manage.py migrate` 다시 실행 |

포트 점유 확인/종료 (PowerShell):

```powershell
Get-NetTCPConnection -LocalPort 3000,5000,8000,8001 -State Listen | Select LocalPort, OwningProcess
taskkill /PID <PID> /T /F      # /T 로 자식 프로세스까지 종료해야 한다
```

> `reflex run` 은 부모/자식 프로세스 구조라 부모만 종료하면 8001 을 잡은 자식이 남는다. 반드시 `/T` 를 사용한다. (2026-10-22 실제 발생, `Docs/repeater/` 참고)

## 7. PostgreSQL (선택)

```powershell
copy .env.example .env                 # 루트: POSTGRES_* 값 수정
docker compose up -d db
# backend/.env 에 DB_ENGINE=postgres 와 같은 POSTGRES_* 설정
cd backend; python manage.py migrate
```

> `docker compose config` 문법 검증만 했고 컨테이너 기동·연결은 아직 확인하지 않았다.

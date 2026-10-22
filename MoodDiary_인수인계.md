# MoodDiary 에이전트 인수인계 문서

**프로젝트명**: MoodDiary (AI Emotion Analysis Diary)  
**작성일**: 2026-10-22  
**용도**: 모든 에이전트(.Agents, .Claude, .Codex, .Grok, .Gemini, .Antigravity, .Cursor, .Manus 등) 공통 인수인계  
**에이전트 폴더**: 각 폴더의 `HANDOVER.md` 는 이 문서를 가리키는 안내만 담는다. 규칙은 여기에만 쓴다.  
**원칙**: 이 문서가 규칙의 단일 출처(SSOT) 역할을 합니다. 다른 곳에 규칙을 중복 작성하지 마세요.

---

## 1. 프로젝트 개요

사용자가 일기를 작성하면 AI가 감정을 분석하고, 감정 트렌드를 시각화하며 간단한 조언/격려를 제공하는 미니 웹 애플리케이션.

- **목적**: Reflex + Django + Flask 기술 스택을 활용한 실무형 미니프로젝트
- **핵심 가치**: 감정 기록의 재미와 AI를 통한 자기 이해 향상

### 기술 스택

| 구분 | 기술 | 역할 |
|------|------|------|
| Frontend | Reflex (Python) | UI, 상태 관리, 차트 시각화 |
| Backend | Django + DRF | 사용자 인증, 일기 CRUD, 데이터 저장 |
| AI Server | Flask | 감정 분석 모델 호출 및 결과 반환 |
| Database | PostgreSQL (또는 SQLite) | 일기 및 분석 결과 저장 |
| AI Model | **Ollama `gemma4:12b`** (로컬 LLM) — 대체: 키워드 사전(lexicon), Hugging Face | 감정 분류 (긍정/부정/중립 + 세부 감정) |

### 아키텍처

```
[User]
   ↓
[Reflex Frontend]
   ↓ REST API (JSON)
[Django Backend] ←→ [PostgreSQL]
   ↓ HTTP
[Flask AI Server] → [Emotion Model]
```

- Frontend ↔ Backend: REST API
- Backend ↔ AI Server: 내부 HTTP 호출
- 인증: JWT 또는 Session

---

## 2. 필수 규칙 (예외 없음)

아래 항목은 **필수·예외 없음**입니다. 에이전트가 사소하다고 판단해 생략하지 마세요.

### 2.1 커밋 메시지
- 형식: `type(scope): 요약`
- type/scope는 영어, 제목 요약과 본문은 한국어
- 예시: `feat(diaries): 일기 작성 API에 감정 분석 연동 추가`
- ❌ 금지 예시: `feat: add diary`, `일기 작성 기능 추가`, `Update model`

### 2.2 커밋 기록 문서화
- 모든 커밋마다 `Docs/branchs/YYMMDD_HHMM_[id]_[이름]_[브랜치].md` 파일을 생성
- 템플릿을 사용하고, 해당 브랜치에 함께 커밋·푸시
- 경로와 파일명 규칙을 반드시 준수

### 2.3 브랜치 전략
- 작업은 `feature/*` 브랜치에서만 수행
- `develop` / `main`은 병합 전용
- 병합은 반드시 `--no-ff` 사용

### 2.4 병합 시점
- 요청받은 작업을 전부 커밋한 뒤에만 한 번에 총 병합
- 사용자 명시적 지시 없이는 병합하지 않음
- 병합 기록 문서도 총 병합 시점에 한 번에 작성

### 2.5 되돌리기 어려운 작업
- `git push`, 병합, 삭제, 덮어쓰기는 **명시적 사용자 지시**가 있을 때만 수행
- 한 번 승인한 것을 다른 상황에 확장 적용하지 않음

---

## 3. 권장 Docs 폴더 구조

프로젝트 루트에 `Docs/` 폴더를 만들고 아래 하위 폴더를 사용하세요. (현재 문서 목록: `Docs/README.md`)
새 문서의 파일명은 영문으로 작성한다.

| 폴더 | 용도 |
|------|------|
| `plan/` | 초기 기획·로직·DB·배포 계획 |
| `Architecture/` | 시스템·계층·데이터 흐름 아키텍처 |
| `branchs/` | 브랜치·커밋 기록 (템플릿 필수) |
| `find_debug/` | 작업/실행 디버깅 일일 기록 |
| `guidance/` | 기능·실행 가이드 |
| `trainings/` | 학습·연구 정리 |
| `repeater/` | 서버 연결·인프라 장애와 해결 |
| `vaildates/` | 검증·체크리스트 |
| `web_management/` | 배포 전/배포 시 웹 관리 기록 |

---

## 4. 스택·실행 환경 요약

| 구분 | 기술 | 기본 포트 | 의존성 파일 | 실행 명령 예시 |
|------|------|-----------|-------------|----------------|
| Frontend | Reflex | 3000 (Reflex 내부 백엔드 **8001**) | `frontend/requirements.txt` | `reflex run` |
| Backend | Django + DRF | 8000 | `backend/requirements.txt` | `python manage.py runserver` |
| AI Server | Flask | 5000 | `ai_server/requirements.txt` | `flask run` |
| Database | PostgreSQL | 5432 | `docker-compose.yml` | - |
| Docker (선택) | - | - | `docker-compose.yml` | 프로젝트명: `mood-diary` |

- 환경 변수는 `.env`로 관리, 민감 정보는 절대 커밋하지 않음 (각 폴더의 `.env.example` 참고)
- Reflex 기본 백엔드 포트(8000)는 Django 와 충돌하므로 `frontend/rxconfig.py` 에서 8001 로 분리했다.
- 의존성은 프로젝트 루트 `.venv` 에 설치한다. 터미널마다 활성화 후 실행 (자세한 내용: `Docs/guidance/RUN_GUIDE.md`)
- `requirements.txt` 에는 한글 주석을 쓰지 않는다 (pip 가 cp949 로 읽다가 실패)
- `reflex run` 종료 시 프로세스 트리 전체를 종료한다 (`taskkill /T /F`). 자식 워커가 8001 을 계속 점유한다.
- 개발 시 SQLite 사용 가능

---

## 5. 프로젝트 특화 코딩 수칙

### 5.1 공통
- Python 3.10+ , PEP 8 준수
- 타입 힌트 적극 사용
- public 함수/클래스에 docstring 작성
- 감정 분석 지연, API 오류 등은 구조화된 로그로 기록

### 5.2 Django Backend
- 앱 분리 권장: `diaries`, `accounts`
- 인증: JWT 권장 (`djangorestframework-simplejwt`)
- Diary 필수 필드: `user`, `title`, `content`, `created_at`, `emotion_label`, `emotion_score`, `detailed_emotions` (JSONField)
- CORS: `django-cors-headers` 필수 설정

### 5.3 Reflex Frontend
- 상태 관리: Reflex State 클래스
- 차트: Reflex 내장 또는 Plotly
- AI 응답 지연 대비 로딩 상태 표시 필수
- 디자인: 스타일은 `frontend/assets/mood.css` 한 파일 + `class_name` 으로 관리한다 (`Docs/guidance/DESIGN_GUIDE.md`)
- 아이콘은 이모지/기호를 사용한다. `rx.icon`(lucide)을 다수 쓰면 Vite 개발 서버가 `504 Outdated Optimize Dep` 로 깨진다.
- UI 변경 후에는 `python frontend/e2e/ui_flow.py` 로 클릭 흐름을 확인한다 (세 서버 실행 필요)

### 5.4 Flask AI Server
- 주요 엔드포인트: `POST /analyze` (일기 텍스트 → 감정 결과)
- timeout 설정 및 실패 시 fallback 처리 (neutral, 0.5)
- CORS 활성화

### 5.5 API 설계
- RESTful 준수
- 권장 응답 형식: `{"success": true/false, "data": ..., "error": ...}`
- 주요 엔드포인트 예시:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/diaries`
  - `POST /api/diaries` (작성 + 분석)
  - `GET /api/diaries/{id}`
  - `GET /api/emotions/trend`

### 5.6 데이터 모델 (주요)

**Diary**
- id, user_id, title, content, created_at
- emotion_label (positive/negative/neutral)
- emotion_score (0.0 ~ 1.0)
- detailed_emotions (JSON)

**User**
- Django 기본 User 확장 또는 AbstractUser

---

## 6. 리스크 및 대응

- **AI 모델 응답 지연**: 비동기 처리, timeout, 캐싱, 로딩 UI
- **Reflex 학습 곡선**: 공식 문서 + 간단한 컴포넌트부터 시작
- **CORS / 통신 이슈**: Django + Flask 모두 CORS 명시적 설정

---

## 7. 커밋 기록 템플릿 (복사해서 사용)

파일명 예시: `Docs/branchs/261022_1430_001_WHILE496_feature-diaries.md`

```markdown
# 커밋 기록

- **커밋 해시**: 
- **브랜치**: 
- **작성자**: 
- **작성일시**: 
- **관련 작업**: 

## 변경 내용 요약
(한국어)

## 주요 변경 파일
- 

## 기술적 결정 / 참고 사항
- 

## 테스트 결과
- 

## 다음 작업
- 
```

---

## 8. 작업 시 확인 체크리스트

- [ ] 커밋 메시지 형식 준수
- [ ] 커밋 기록 md 파일 생성 및 포함
- [ ] feature 브랜치에서 작업
- [ ] CORS 설정 확인
- [ ] 사용자별 데이터 격리
- [ ] 감정 분석 결과 구조 일관성
- [ ] AI 서버 장애 시 fallback 처리

---

## 9. 진행 상황 / 다음 단계

**완료** (`feature/mood-diary-mvp`, 병합 전)
1. ✅ 프로젝트 스켈레톤 (`frontend/`, `backend/`, `ai_server/`, `Docs/`, `docker-compose.yml`)
2. ✅ Django Backend (인증 + Diary CRUD + 트렌드)
3. ✅ Flask AI Server
4. ✅ Reflex Frontend
5. ✅ 자동 테스트 (AI 25 · Django 26 · 프론트 8) + 서버 연동 확인
6. ✅ UI 디자인 "마음 날씨" 적용 (`feature/ui-design`) + 브라우저 클릭 흐름 11개 항목 확인

**남은 일**
1. ⬜ 사용자 직접 화면 확인, Ollama 분석 결과를 화면에서 확인 — `Docs/vaildates/VALIDATION_CHECKLIST.md`
2. ⬜ 확장 기능 (검색, 월간 리포트, 태그) — 선택
3. ⬜ 병합 (사용자 지시 시에만, `--no-ff`, 병합 기록 문서 일괄 작성)

---

**이 문서를 프로젝트 루트 또는 Docs/에 두고 모든 에이전트가 참조하도록 하세요.**  
규칙이 변경되면 이 문서를 먼저 수정한 뒤 작업하세요.

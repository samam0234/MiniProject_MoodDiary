# AI 감정 분석 일기 앱 미니프로젝트 계획서

**프로젝트명**: MoodDiary (AI Emotion Analysis Diary)  
**작성일**: 2026-10-22  
**수정일**: 2026-10-22 (구현 결과 반영)  
**버전**: v1.1  
> v1.0 은 `mood-diary-plan.docx` 로 보존되어 있으며, 이 문서(md)가 최신이다. 변경 사항은 §11 참고.  

---

## 1. 프로젝트 개요

사용자가 일기를 작성하면 AI가 감정을 분석하고, 감정 트렌드를 시각화하며 간단한 조언이나 격려를 제공하는 미니 웹 애플리케이션.

- **목적**: Reflex + Django + Flask 기술 스택을 활용한 실무형 미니프로젝트 완성
- **핵심 가치**: 감정 기록의 재미와 AI를 통한 자기 이해 향상

## 2. 기술 스택

| 구분 | 기술 | 역할 |
|------|------|------|
| Frontend | Reflex (Python) | UI, 상태 관리, 차트 시각화 |
| Backend | Django + Django REST Framework | 사용자 인증, 일기 CRUD, 데이터 저장 |
| AI Server | Flask | 감정 분석 모델 호출 및 결과 반환 |
| Database | PostgreSQL (또는 SQLite for mini) | 일기 및 분석 결과 저장 |
| AI Model | **Ollama `gemma4:12b`** (로컬 LLM, v1.1 에서 확정) / 대체: 키워드 사전, Hugging Face | 감정 분류 (긍정/부정/중립 + 세부 감정) |

## 3. 주요 기능

### 3.1 필수 기능 (MVP)
1. **회원가입 / 로그인** (Django)
2. **일기 작성**
   - 제목, 내용, 날짜 입력
   - 실시간 또는 제출 후 감정 분석 요청
3. **감정 분석**
   - 긍정 / 부정 / 중립 점수
   - 세부 감정 (기쁨, 슬픔, 분노, 불안, 평온 등)
4. **일기 목록 & 상세 조회**
5. **감정 트렌드 시각화**
   - 최근 7일 / 30일 감정 변화 차트 (Reflex 차트)

### 3.2 확장 기능 (선택)
- AI 격려 메시지 / 조언 생성 — **구현됨(간이)**: 지배 감정별 고정 문구를 `ai_message` 로 제공 (LLM 생성은 아님)
- 일기 검색 (키워드 + 감정 필터)
- 월간 감정 리포트 PDF 내보내기
- 태그 기능

## 4. 시스템 아키텍처

```
[User]
   ↓
[Reflex Frontend]
   ↓ REST API
[Django Backend] ←→ [PostgreSQL]
   ↓ HTTP
[Flask AI Server] → [Emotion Model]
```

- Frontend ↔ Backend: REST API (JSON)
- Backend ↔ AI Server: 내부 HTTP 호출 (일기 텍스트 → 감정 결과)
- 인증: JWT 또는 Session (Django)

## 5. 데이터 모델 (주요)

### Diary
- id, user_id, title, content, created_at
- emotion_label (positive/negative/neutral)
- emotion_score (0.0 ~ 1.0) — label 에 대한 확신도
- detailed_emotions (JSON: joy, sadness, anger, anxiety, calm)
- **추가**: entry_date(일기 날짜, 트렌드 집계 기준), updated_at, ai_message, analysis_source(ollama/lexicon/transformers/fallback)

### User
- `AbstractUser` 를 상속한 `accounts.User` 사용 (구현 완료)

## 6. API 설계 (예시)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/auth/register | 회원가입 |
| POST | /api/auth/login | 로그인 |
| GET | /api/diaries | 일기 목록 |
| POST | /api/diaries | 일기 작성 + 분석 |
| GET | /api/diaries/{id} | 일기 상세 |
| PATCH/PUT | /api/diaries/{id} | 일기 수정 (본문 변경 시 재분석) — 추가 |
| DELETE | /api/diaries/{id} | 일기 삭제 — 추가 |
| POST | /api/diaries/{id}/reanalyze | 저장된 일기 다시 분석 (AI 장애 시 기존 결과 유지) — 추가 |
| GET | /api/emotions/trend?days=7 | 감정 트렌드 데이터 |
| POST | /api/auth/refresh | access 토큰 재발급 — 추가 |
| GET | /api/auth/me | 현재 사용자 — 추가 |

응답은 `{"success": bool, "data": ..., "error": ...}` 로 통일. 상세는 `Docs/guidance/API_GUIDE.md`.
## 7. 개발 일정 (예상)

| 단계 | 내용 | 기간 |
|------|------|------|
| 1 | 프로젝트 구조 세팅 + DB 설계 | 1일 |
| 2 | Django Backend (인증 + CRUD) | 2일 |
| 3 | Flask AI Server (감정 분석) | 1일 |
| 4 | Reflex Frontend (UI + 연동) | 2~3일 |
| 5 | 통합 테스트 + 차트 시각화 | 1일 |
| **합계** | | **약 7~8일** |

## 8. 디렉토리 구조 (초안)

```
mood-diary/
├── frontend/          # Reflex
│   ├── mood_diary/
│   └── requirements.txt
├── backend/           # Django
│   ├── config/
│   ├── diaries/
│   └── requirements.txt
├── ai_server/         # Flask
│   ├── app.py
│   └── requirements.txt
├── Docs/              # plan, Architecture, branchs, find_debug, guidance, trainings, repeater, vaildates, web_management
├── docker-compose.yml # PostgreSQL (선택)
├── MoodDiary_인수인계.md  # 작업 규칙 SSOT
└── README.md
```

## 9. 리스크 및 대응

- **AI 모델 응답 지연**: 비동기 처리 또는 캐싱 고려
- **Reflex 학습 곡선**: 공식 문서 + 간단한 컴포넌트부터 시작
- **CORS / 통신 이슈**: Django CORS headers + Flask CORS 설정

## 10. 기대 효과

- Reflex, Django, Flask 3개 스택을 동시에 경험
- AI 모델 연동 실습
- 풀스택 미니프로젝트 포트폴리오 완성

---

## 11. 구현 현황 (v1.1)

브랜치 `feature/mood-diary-mvp` 에서 MVP 를 구현했다.

| 항목 | 상태 |
|------|------|
| 회원가입 / 로그인 (JWT) | ✅ 완료 |
| 일기 작성·목록·상세 (+수정·삭제) | ✅ 완료 |
| 감정 분석 (긍정/부정/중립 + 세부 5종) | ✅ 완료 — Ollama gemma4:12b 실제 호출 확인, 키워드 사전은 대체 엔진 |
| 감정 트렌드 7일/30일 (Reflex 차트) | ✅ 데이터 확인, 브라우저(Edge)에서 차트 렌더링·전환 확인 |
| 저장된 일기 "다시 분석하기" 버튼 | ✅ `feature/diary-reanalyze`: 상세 화면 버튼 + `POST /reanalyze`, 이전/이후 비교 안내, 장애 시 기존 결과 유지 |
| UI 디자인 (컨셉 "마음 날씨") | ✅ `feature/ui-design`: 종이 일기장 톤, ☀️☁️🌧️ 날씨 배지, 줄 노트 입력, 모바일 대응 |
| AI 서버 장애 fallback (neutral, 0.5) | ✅ 완료 |
| 격려 메시지 | ✅ 간이 구현 |
| 일기 검색, PDF 리포트, 태그 | ⬜ 미구현 |
| Hugging Face 모델 연동 | ⬜ 코드만 작성, 미검증 |
| docker-compose (PostgreSQL) | 파일 작성, 문법 검증만 |

### 계획 대비 변경점

1. **Reflex 내부 백엔드 포트 8001**: Reflex 기본 백엔드가 8000 이라 Django 와 충돌해 분리했다.
2. **감정 분석 방식**: 로컬 Ollama `gemma4:12b` 를 사용한다(JSON 스키마 출력, 외부 API 키 불필요). 모델 로딩 때문에 첫 호출이 약 15초 걸려 AI 서버 90초 / 프론트 120초 timeout 을 `.env` 로 둔다. Ollama 가 없을 때를 위해 의존성 없는 키워드 사전(`EMOTION_BACKEND=lexicon`)을 대체 엔진으로 유지한다.
3. **Diary 필드 추가**: `entry_date`, `updated_at`, `ai_message`, `analysis_source`.
4. **감정 지수 정의**: 트렌드는 positive `+score`, negative `-score`, neutral `0` 의 일별 평균(−1~+1).
5. **API 추가**: 수정·삭제, `auth/refresh`, `auth/me`, 목록 페이지네이션.
6. **Reflex ↔ Django 호출은 서버 측**: 브라우저 CORS 는 개입하지 않는다(설정은 규칙대로 유지).

### 일정 (실적)
계획 약 7~8일 대비 하루 세션에서 MVP 구현·테스트까지 진행. 남은 일: 브라우저 수동 검증, 확장 기능, 배포 준비.

**다음 단계**: 브라우저 수동 검증 → 확장 기능(검색·리포트) 선택 → 병합(사용자 지시 시)

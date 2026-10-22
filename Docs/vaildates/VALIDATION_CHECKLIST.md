# 검증 체크리스트

**기준일**: 2026-10-22 · 브랜치 `feature/mood-diary-mvp`
표기: ✅ 확인함 · ⬜ 아직 확인하지 않음 · ➖ 해당 없음

## 1. 자동 테스트

| 대상 | 명령 | 결과 |
|------|------|------|
| AI 서버 | `python -m pytest` | ✅ 25 passed (lexicon 13 + ollama mock 12) |
| Django | `python manage.py test` | ✅ 26 passed (AI 호출은 mock) |
| Reflex view_models | `python -m pytest tests` | ✅ 8 passed |
| **브라우저 클릭 흐름** | `python frontend/e2e/ui_flow.py` (Edge, 실서버) | ✅ 11/11 (아래 §2) |

## 2. 기능 (MVP, 계획서 §3.1)

| 항목 | 상태 | 근거 |
|------|------|------|
| 회원가입 / 로그인 (Django) | ✅ | 테스트 + 실서버 호출 |
| 일기 작성 (제목·내용·날짜) | ✅ | 테스트 + 실서버 호출 |
| 감정 분석 (긍정/부정/중립 + 세부 감정) | ✅ | lexicon 으로 실서버 연동 3건 작성 |
| **Ollama gemma4:12b 실제 호출** | ✅ | AI 서버 4건(긍정/부정/평범/인젝션 문장) + Django `analyze_text` 검증 통과, 첫 호출 ~14s · 이후 4~9s |
| Ollama 로 화면(Reflex)에서 일기 저장 | ⬜ | 브라우저 미확인 |
| Ollama 중단 시 fallback | ✅ | mock 테스트 (실제 중단 상태 재현은 미확인) |
| 일기 목록 / 상세 | ✅ | 테스트 + 실서버 호출 |
| 감정 트렌드 7일/30일 데이터 | ✅ | 테스트 + 실서버 호출 |
| 트렌드 **차트 렌더링** (Reflex) | ✅ | Edge 에서 SVG 차트 2개 렌더링, 7일/30일 전환, 스크린샷 육안 확인 |
| 화면에서 로그인 실패/성공·작성·삭제·로그아웃 | ✅ | Playwright 로 실제 클릭 (콘솔 오류 0) |
| 로그아웃 후 보호 페이지 접근 차단 | ✅ | `/diaries` 직접 접근 → `/login` |
| 디자인(데스크톱 1280 / 모바일 390) | ✅ | 로그인·가입·목록·작성·상세(긍정/부정)·트렌드 스크린샷 확인 후 수정 2회 |
| 화면 흐름 중 사용한 AI 엔진 | ➖ | 점검 시 AI 서버(5000)가 lexicon 모드 — Ollama 결과의 화면 표시는 별도 확인 필요 |

## 3. 작업 시 확인 체크리스트 (인수인계 §8)

| 항목 | 상태 | 비고 |
|------|------|------|
| 커밋 메시지 형식 | ✅ | `type(scope): 한국어 요약` |
| 커밋 기록 md 생성·포함 | ✅ | `Docs/branchs/` 커밋마다 1개 |
| feature 브랜치에서 작업 | ✅ | `feature/mood-diary-mvp` |
| CORS 설정 | ✅ | Django `django-cors-headers`, Flask `flask-cors` (코드로 설정, 브라우저 간 직접 호출은 없음) |
| 사용자별 데이터 격리 | ✅ | 타인 일기 조회/수정/삭제 404, 트렌드 분리 — 테스트 |
| 감정 분석 결과 구조 일관성 | ✅ | 응답 구조 검증 후 불일치 시 fallback — 테스트 4종 |
| AI 서버 장애 시 fallback | ✅ | 타임아웃/연결/HTTP/구조 오류 테스트 + AI 서버를 내린 실서버 확인 |

## 4. 규칙 준수 (인수인계 §2)

| 항목 | 상태 |
|------|------|
| 병합은 사용자 지시 시에만, `--no-ff` | ✅ 아직 병합하지 않음 |
| push 는 사용자 지시 시에만 | ✅ push 하지 않음 |
| 민감 정보 미커밋 (`.env`, DB, 토큰) | ✅ `git ls-files` 로 `.venv`, `db.sqlite3`, `.env`, `.web`, `.states` 미추적 확인 |

## 5. 미검증 항목

- ⬜ Edge 외 브라우저(Chrome·Firefox·Safari)와 실제 모바일 기기
- ⬜ 토큰 만료(60분) 후 자동 refresh / 재로그인 이동
- ⬜ 접근성: 색 대비, 키보드 이동, 스크린리더 (정량 점검 안 함)
- ⬜ 다크 모드 (라이트로 고정)
- ⬜ `EMOTION_BACKEND=transformers` (코드만 작성, 모델 미설치)
- ⬜ Ollama 로 일기 저장 → 상세 화면에 분석 결과가 표시되는지(AI 서버를 ollama 모드로 재시작 후), 동시 요청 시 응답 지연
- ⬜ PostgreSQL 연결 (`docker compose up -d db` + `DB_ENGINE=postgres`)
- ⬜ 모바일/좁은 화면 레이아웃
- ⬜ `DJANGO_DEBUG=false` 배포 설정 (`Docs/web_management/PRE_DEPLOY_CHECKLIST.md` 참고)

## 6. 알려진 한계

- LLM 점수는 보정된 확률이 아니라 모델이 매긴 강도이며 호출마다 소폭 달라질 수 있다. 첫 호출은 모델 로딩으로 느리다.
- (lexicon 대체 엔진) 키워드 사전 방식이라 부정문·반어를 구분하지 못한다.
- 로그아웃해도 서버에서 refresh 토큰을 무효화하지 않는다 (만료까지 유효).
- 로그인 시도 횟수 제한, 이메일 인증, 비밀번호 찾기 없음.
- 일기 목록은 프론트에서 최대 100건만 불러온다 (페이지 이동 UI 없음).

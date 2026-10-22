# frontend (Reflex)

UI 와 상태 관리. 프론트 **3000**, Reflex 내부 백엔드 **8001** (Django 8000 과 충돌 방지).

```powershell
# 프로젝트 루트의 .venv 활성화 후
reflex run                    # http://localhost:3000
python -m pytest tests        # 9개
python e2e/ui_flow.py          # 브라우저 클릭 흐름 점검 (세 서버 실행 + pip install playwright)
```

| 경로 | 역할 |
|------|------|
| `rxconfig.py` | 포트(3000/8001), 테마·사이트맵 플러그인 |
| `mood_diary/mood_diary.py` | 앱 진입점, 페이지/on_load 등록 |
| `mood_diary/pages.py` | 로그인, 회원가입, 목록, 작성, 상세, 트렌드 |
| `mood_diary/components.py` | 네비게이션, 에러 콜아웃, 로딩, 감정 막대, 배지 |
| `mood_diary/state.py` | `AppState`: 토큰(LocalStorage), 이벤트 핸들러, 401 시 refresh 재시도 |
| `mood_diary/api.py` | Django 호출(`httpx`), 응답을 `ApiResult` 로 변환 |
| `mood_diary/view_models.py` | 응답 → 화면용 구조 변환 (이모지·날짜 조각·날씨 라벨 포함, Reflex 비의존) |
| `assets/mood.css` | 디자인 시스템 "마음 날씨" (토큰, 카드, 줄 노트, 반응형) |
| `assets/favicon.svg` | 파비콘 |
| `e2e/ui_flow.py` | Playwright 로 로그인~삭제~로그아웃 흐름을 눌러 보는 스모크 테스트 |

| 페이지 | 경로 |
|--------|------|
| 로그인 / 회원가입 | `/login`, `/register` |
| 일기 목록 / 작성 / 상세 | `/diaries`, `/diaries/new`, `/diaries/[diary_id]` |
| 감정 트렌드 (7일/30일) | `/trend` |

- Django 는 서버 측에서 호출하므로 브라우저 CORS 와 무관하다. 주소는 `MOOD_DIARY_API_URL`(기본 http://localhost:8000).
- 일기 저장처럼 AI 분석이 걸리는 작업은 `is_saving` 로딩 상태와 안내 문구를 표시한다.
- 상세 화면의 "다시 분석하기" 버튼(`AppState.reanalyze_diary`)은 이전/이후 결과를 비교한 안내를 **버튼 바로 위**에 보여주고, 실패 시에도 기존 결과를 유지한다.
- 디자인 컨셉·토큰·작업 규칙: [Docs/guidance/DESIGN_GUIDE.md](../Docs/guidance/DESIGN_GUIDE.md). `rx.icon` 대신 이모지를 쓴다(Vite 개발 서버 504 이슈).
- 빌드 산출물(`.web/`, `.states/`)은 커밋하지 않는다. `e2e/ui_flow.py` 의 스크린샷은 기본으로 시스템 임시 폴더에 저장된다(`frontend/` 안에 저장하면 Reflex 개발 서버가 재시작된다).
- 학습 메모: [Docs/trainings/REFLEX_NOTES.md](../Docs/trainings/REFLEX_NOTES.md)

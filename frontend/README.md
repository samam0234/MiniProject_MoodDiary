# frontend (Reflex)

UI 와 상태 관리. 프론트 **3000**, Reflex 내부 백엔드 **8001** (Django 8000 과 충돌 방지).

```powershell
# 프로젝트 루트의 .venv 활성화 후
reflex run                    # http://localhost:3000
python -m pytest tests        # 5개
```

| 경로 | 역할 |
|------|------|
| `rxconfig.py` | 포트(3000/8001), 테마·사이트맵 플러그인 |
| `mood_diary/mood_diary.py` | 앱 진입점, 페이지/on_load 등록 |
| `mood_diary/pages.py` | 로그인, 회원가입, 목록, 작성, 상세, 트렌드 |
| `mood_diary/components.py` | 네비게이션, 에러 콜아웃, 로딩, 감정 막대, 배지 |
| `mood_diary/state.py` | `AppState`: 토큰(LocalStorage), 이벤트 핸들러, 401 시 refresh 재시도 |
| `mood_diary/api.py` | Django 호출(`httpx`), 응답을 `ApiResult` 로 변환 |
| `mood_diary/view_models.py` | 응답 → 화면용 구조 변환 (Reflex 비의존) |

| 페이지 | 경로 |
|--------|------|
| 로그인 / 회원가입 | `/login`, `/register` |
| 일기 목록 / 작성 / 상세 | `/diaries`, `/diaries/new`, `/diaries/[diary_id]` |
| 감정 트렌드 (7일/30일) | `/trend` |

- Django 는 서버 측에서 호출하므로 브라우저 CORS 와 무관하다. 주소는 `MOOD_DIARY_API_URL`(기본 http://localhost:8000).
- 일기 저장처럼 AI 분석이 걸리는 작업은 `is_saving` 로딩 상태와 안내 문구를 표시한다.
- 빌드 산출물(`.web/`, `.states/`)은 커밋하지 않는다.
- 학습 메모: [Docs/trainings/REFLEX_NOTES.md](../Docs/trainings/REFLEX_NOTES.md)

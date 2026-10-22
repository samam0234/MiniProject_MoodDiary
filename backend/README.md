# backend (Django + DRF)

인증, 일기 CRUD, AI 서버 연동, 감정 트렌드 집계. 기본 포트 **8000**.

```powershell
# 프로젝트 루트의 .venv 활성화 후
python manage.py migrate
python manage.py runserver 8000
python manage.py createsuperuser      # 선택: /admin 접속용
python manage.py test                 # 33개
```

| 경로 | 역할 |
|------|------|
| `config/` | settings(.env 로 제어), urls, wsgi |
| `common/` | 응답 래퍼 렌더러(`{success,data,error}`), 예외 핸들러, 페이지네이션 |
| `accounts/` | 커스텀 `User(AbstractUser)`, 가입/로그인/refresh/me (JWT) |
| `diaries/` | `Diary` 모델, `services.py`(AI 호출 + fallback, 트렌드 집계), 뷰, 테스트 |

- DB: 기본 SQLite(`db.sqlite3`, 커밋 금지). `DB_ENGINE=postgres` 로 PostgreSQL 전환.
- AI 서버: `AI_SERVER_URL`(기본 http://localhost:5000), `AI_SERVER_TIMEOUT`(코드 기본 5초, `.env.example` 은 Ollama 용 90초). 실패하면 neutral/0.5 로 저장하고 `analysis_source="fallback"`.
- 모든 일기 쿼리는 로그인 사용자 기준으로 필터링된다 (타인 일기는 404).
- `POST /api/diaries/{id}/reanalyze`: 저장된 제목·본문을 현재 AI 모델로 다시 분석한다. AI 서버 장애(fallback)면 기존 결과를 덮어쓰지 않고 503 을 반환하며, 성공 시 응답에 이전 결과(`previous`)가 함께 담긴다.
- `DJANGO_DEBUG=false` 에서는 `DJANGO_SECRET_KEY` 가 필수다.
- API 상세: [Docs/guidance/API_GUIDE.md](../Docs/guidance/API_GUIDE.md) · 환경 변수: `.env.example`

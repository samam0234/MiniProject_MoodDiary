# 배포 전 웹 관리 체크리스트

**상태**: 아직 배포한 적 없음 (로컬 개발 단계). 배포를 진행할 때 이 문서를 기준으로 점검하고, 실제 배포 기록은 날짜별 파일(`YYMMDD_deploy.md`)로 추가한다.

## 1. 반드시 바꿔야 하는 설정

| 항목 | 현재(개발) | 배포 시 |
|------|-----------|---------|
| `DJANGO_DEBUG` | true | **false** |
| `DJANGO_SECRET_KEY` | 개발용 고정 키 | 새로 생성한 비밀 값 (`DEBUG=false` 에서 비어 있으면 기동 중단) |
| `DJANGO_ALLOWED_HOSTS` | localhost, 127.0.0.1 | 실제 도메인 |
| `CORS_ALLOWED_ORIGINS` | localhost:3000 | 실제 프론트 도메인 (Flask `CORS_ALLOWED_ORIGINS` 도 `*` 에서 축소) |
| DB | SQLite | PostgreSQL (`DB_ENGINE=postgres`, 강한 비밀번호) |
| `POSTGRES_PASSWORD` | change-me | 비밀 값 (docker-compose 기본값 사용 금지) |
| `AI_SERVER_URL` | localhost:5000 | 내부 네트워크 주소, 외부 비공개 |
| `MOOD_DIARY_API_URL` | localhost:8000 | 프론트 서버에서 접근 가능한 백엔드 주소 |

## 2. 보안

- [ ] `.env`, `db.sqlite3`, 토큰이 저장소에 없다 (`git ls-files` 로 확인)
- [ ] HTTPS 적용 (JWT 가 평문으로 오가지 않도록)
- [ ] AI 서버(5000)는 외부에서 직접 접근할 수 없다 (인증이 없다)
- [ ] 정적 파일 서빙, `collectstatic`, 프로덕션 WSGI 서버(gunicorn 등) 구성 — 현재는 `runserver` 만 사용
- [ ] 로그인 시도 제한 / 비밀번호 변경·찾기 필요 여부 결정
- [ ] 토큰 저장 방식(현재 브라우저 localStorage) 의 XSS 위험 검토, 로그아웃 시 refresh 토큰 블랙리스트 필요 여부
- [ ] `/admin` 접근 제한

## 3. 운영

- [ ] 구조화 로그(JSON) 수집 위치 결정: `ai_analysis_done` / `ai_analysis_fallback` / `analyze_done` 이벤트 모니터링 (fallback 비율이 높으면 AI 서버 장애)
- [ ] DB 백업 정책
- [ ] AI 서버 timeout(5초)과 Reflex 요청 timeout(20초) 조정
- [ ] Reflex 프로덕션 실행 방식 결정 (`reflex export` 정적 + 백엔드 분리, 또는 `reflex run --env prod`)
- [ ] Python 3.11+ 로 상향 (Reflex 가 3.10 지원 중단 예고)

## 4. 배포 직전 검증

- [ ] 세 영역 테스트 통과 (`Docs/vaildates/VALIDATION_CHECKLIST.md` §1)
- [ ] 브라우저에서 가입 → 작성 → 상세 → 트렌드 → 삭제 → 로그아웃 수동 확인
- [ ] AI 서버를 내린 상태에서 일기 작성 시 fallback 안내가 표시되는지 확인

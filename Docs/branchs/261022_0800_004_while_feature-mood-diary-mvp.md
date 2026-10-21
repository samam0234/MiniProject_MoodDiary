# 커밋 기록

- **커밋 해시**: 이 커밋 자체 (`git log -- Docs/branchs/261022_0800_004_while_feature-mood-diary-mvp.md` 로 확인)
- **브랜치**: feature/mood-diary-mvp
- **작성자**: while
- **작성일시**: 2026-10-22 08:00
- **관련 작업**: Reflex 프론트엔드

## 변경 내용 요약
로그인, 회원가입, 일기 목록·작성·상세, 감정 트렌드 차트 페이지를 구현했다. AI 분석 중에는 로딩 상태를 표시한다.

## 주요 변경 파일
- frontend/rxconfig.py, mood_diary/(api, state, view_models, components, pages, mood_diary), tests/, requirements.txt, .env.example

## 기술적 결정 / 참고 사항
- Reflex 기본 백엔드 포트(8000)가 Django 와 충돌해 backend_port 를 8001 로 분리했다.
- JWT 는 LocalStorage 에 보관하고 401 시 refresh 로 한 번 재시도한다.
- 서버 측 httpx 로 Django 를 호출하므로 브라우저 CORS 와 무관하다.

## 테스트 결과
- 단위 테스트 5개 통과, reflex export 컴파일·빌드 성공, reflex run 기동 확인
- 브라우저에서의 화면 조작은 미확인

## 다음 작업
- 브라우저 수동 확인, 필요 시 확장 기능(검색, PDF 리포트 등)

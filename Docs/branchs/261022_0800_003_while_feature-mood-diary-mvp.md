# 커밋 기록

- **커밋 해시**: 이 커밋 자체 (`git log -- Docs/branchs/261022_0800_003_while_feature-mood-diary-mvp.md` 로 확인)
- **브랜치**: feature/mood-diary-mvp
- **작성자**: while
- **작성일시**: 2026-10-22 08:00
- **관련 작업**: Django 백엔드

## 변경 내용 요약
JWT 인증(가입/로그인/refresh/me), 일기 CRUD, AI 서버 연동, 감정 트렌드 API 를 구현했다. 모든 응답은 {success, data, error} 형식이다.

## 주요 변경 파일
- backend/config, common, accounts, diaries, manage.py, requirements.txt, .env.example, migrations

## 기술적 결정 / 참고 사항
- 커스텀 User(AbstractUser) 를 첫 마이그레이션부터 적용했다.
- AI 서버 timeout/장애/응답 구조 불일치 시 neutral 0.5 fallback 으로 저장한다 (analysis_source=fallback).
- 일기는 항상 본인 것만 조회·수정되며, 본문 변경 시에만 재분석한다.
- 로그인 실패는 인증 클래스를 비운 뷰에서 403 으로 바뀌는 문제를 피하려고 401 을 직접 반환한다.
- DB 는 SQLite 기본, DB_ENGINE=postgres 로 전환한다.

## 테스트 결과
- manage.py test 26개 통과 (AI 서버 호출은 mock)
- 실제 AI 서버와 연동한 E2E 및 AI 서버 중단 시 fallback 확인

## 다음 작업
- Reflex 프론트엔드 구현

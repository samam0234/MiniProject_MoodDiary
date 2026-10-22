# 커밋 기록

- **커밋 해시**: 이 커밋 자체 (`git log -- Docs/branchs/261022_1816_016_while_feature-diary-reanalyze.md` 로 확인)
- **브랜치**: feature/diary-reanalyze
- **작성자**: while
- **작성일시**: 2026-10-22 18:16
- **관련 작업**: 저장된 일기 다시 분석 API

## 변경 내용 요약
POST /api/diaries/{id}/reanalyze 를 추가했다. 저장된 제목·본문을 현재 AI 모델로 다시 분석해 분석 필드를 갱신하고, 응답에 이전 결과(previous)를 담는다. AI 서버 장애(fallback)면 기존 결과를 덮어쓰지 않고 503 을 반환한다.

## 주요 변경 파일
- backend/diaries/views.py (reanalyze 액션, AnalysisUnavailable 예외)
- backend/diaries/tests.py (ReanalyzeApiTests 7개)

## 기술적 결정 / 참고 사항
- 장애 시 fallback 값을 저장하지 않는다. 신규 저장·수정은 장애 시 fallback 을 저장하지만, 재분석은 사용자가 일부러 요청한 작업이라 기존의 좋은 결과를 기본값으로 덮어쓰면 안 된다.
- 남의 일기는 404 이며 AI 를 호출하지 않는다(테스트로 고정).

## 테스트 결과
- manage.py test 33개 통과 (기존 26 + 재분석 7)

## 다음 작업
- 프론트엔드 재분석 버튼과 비교 안내

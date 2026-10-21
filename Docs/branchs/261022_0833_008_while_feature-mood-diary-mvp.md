# 커밋 기록

- **커밋 해시**: 이 커밋 자체 (`git log -- Docs/branchs/261022_0833_008_while_feature-mood-diary-mvp.md` 로 확인)
- **브랜치**: feature/mood-diary-mvp
- **작성자**: while
- **작성일시**: 2026-10-22 08:33
- **관련 작업**: Ollama 전환 내용 문서 반영

## 변경 내용 요약
AI 모델이 Ollama gemma4:12b 로 바뀐 것을 README, 기획서(v1.1), 인수인계(기술 스택 표), 아키텍처, 실행·API 가이드, 검증 체크리스트, 배포 전 체크리스트, 디버깅 기록에 반영했다.

## 주요 변경 파일
- README.md, ai_server/README.md, backend/README.md
- MoodDiary_인수인계.md (AI Model 행만 변경, 필수 규칙은 변경 없음)
- Docs/plan/mood-diary-plan.md, Docs/Architecture/ARCHITECTURE.md
- Docs/guidance/RUN_GUIDE.md (Ollama 준비 절, 문제 해결 추가), API_GUIDE.md
- Docs/vaildates/VALIDATION_CHECKLIST.md, Docs/web_management/PRE_DEPLOY_CHECKLIST.md, Docs/find_debug/261022_debug_log.md

## 기술적 결정 / 참고 사항
- lexicon 은 삭제하지 않고 "Ollama 를 쓸 수 없을 때의 대체 엔진"으로 문서화했다.
- 테스트 개수를 AI 25 · Django 26 · 프론트 5 (총 56)로 갱신했다.
- 검증하지 않은 항목(브라우저에서 Ollama 분석 흐름)은 체크리스트에 ⬜ 로 남겼다.

## 테스트 결과
- 전체 테스트 56개 통과, 문서 상대 링크 깨짐 0개

## 다음 작업
- 브라우저 수동 검증 후 체크리스트 갱신

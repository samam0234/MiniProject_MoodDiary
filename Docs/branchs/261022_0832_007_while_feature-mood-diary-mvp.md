# 커밋 기록

- **커밋 해시**: 이 커밋 자체 (`git log -- Docs/branchs/261022_0832_007_while_feature-mood-diary-mvp.md` 로 확인)
- **브랜치**: feature/mood-diary-mvp
- **작성자**: while
- **작성일시**: 2026-10-22 08:32
- **관련 작업**: AI 모델을 Ollama gemma4:12b 로 전환

## 변경 내용 요약
AI 서버에 `EMOTION_BACKEND=ollama` 백엔드를 추가했다. 로컬 Ollama 의 `gemma4:12b` 에 JSON 스키마 출력으로 감정 5종 + neutral 강도와 격려 문구를 요청하고, 기존 응답 구조(label/score/detailed_emotions/message/source)로 변환한다. 설정은 `.env` 로 관리한다.

## 주요 변경 파일
- ai_server/analyzer.py (analyze_ollama 추가), app.py (/health 에 model 표시)
- ai_server/requirements.txt (requests), ai_server/conftest.py, ai_server/test_ollama.py
- ai_server/.env.example (EMOTION_BACKEND=ollama, OLLAMA_*), backend/.env.example (AI_SERVER_TIMEOUT=90), frontend/.env.example (MOOD_DIARY_API_TIMEOUT=120)

## 기술적 결정 / 참고 사항
- 실제 `.env` (ai_server, backend, frontend, 루트)는 로컬에 생성했으며 .gitignore 대상이라 커밋하지 않았다.
- 첫 호출이 모델 로딩 포함 약 14초라 timeout 을 OLLAMA 60 < Django 90 < 프론트 120 으로 계층화했다. 코드 기본값(5s/20s)은 lexicon 용으로 유지했다.
- think:false 로 추론 단계를 끄고, 일기는 <diary> 태그로 감싸 지시문으로 취급하지 않게 했다. 프롬프트 인젝션 문장을 섞은 일기도 슬픔으로 분류함을 확인했다.
- Ollama 실패(연결/timeout/잘못된 JSON/전부 0점)는 AI 서버 500 → Django fallback(neutral, 0.5) 규칙을 그대로 따른다.
- 로컬 .env 가 ollama 여도 테스트가 LLM 을 호출하지 않도록 conftest.py 가 lexicon 을 강제한다.

## 테스트 결과
- AI 서버 pytest 25개 통과 (기존 13 + ollama mock 12)
- 실제 gemma4:12b 로 별도 포트의 AI 서버에서 4건 분석 (첫 호출 ~14s, 이후 4~9s), Django analyze_text 가 응답을 정상 수용
- 기존에 떠 있는 5000/8000 서버는 건드리지 않았으므로 재시작 전까지는 이전 설정으로 동작한다

## 다음 작업
- AI 서버와 Django 재시작 후 브라우저에서 일기 저장 흐름 확인

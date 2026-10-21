# 커밋 기록

- **커밋 해시**: 이 커밋 자체 (`git log -- Docs/branchs/261022_0800_002_while_feature-mood-diary-mvp.md` 로 확인)
- **브랜치**: feature/mood-diary-mvp
- **작성자**: while
- **작성일시**: 2026-10-22 08:00
- **관련 작업**: Flask AI 서버

## 변경 내용 요약
POST /analyze 와 /health 를 제공하는 감정 분석 서버를 구현했다. 기본 백엔드는 한국어 키워드 사전, EMOTION_BACKEND=transformers 로 Hugging Face 파이프라인 선택이 가능하다.

## 주요 변경 파일
- ai_server/app.py, analyzer.py, test_app.py, requirements.txt, .env.example

## 기술적 결정 / 참고 사항
- 극성 쪽에도 가상 근거(POLAR_PRIOR)를 둬서 키워드가 없을 때 중립 확신도가 100% 가 되지 않게 했다.
- 입력 검증(400/413), CORS, JSON 구조화 로그를 적용했다.
- transformers 경로는 코드만 작성했고 실제 모델로는 검증하지 않았다.

## 테스트 결과
- pytest 13개 통과

## 다음 작업
- Django 백엔드 연동

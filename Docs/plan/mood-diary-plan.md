# AI 감정 분석 일기 앱 미니프로젝트 계획서

**프로젝트명**: MoodDiary (AI Emotion Analysis Diary)  
**작성일**: 2026-10-22  
**버전**: v1.0  

---

## 1. 프로젝트 개요

사용자가 일기를 작성하면 AI가 감정을 분석하고, 감정 트렌드를 시각화하며 간단한 조언이나 격려를 제공하는 미니 웹 애플리케이션.

- **목적**: Reflex + Django + Flask 기술 스택을 활용한 실무형 미니프로젝트 완성
- **핵심 가치**: 감정 기록의 재미와 AI를 통한 자기 이해 향상

## 2. 기술 스택

| 구분 | 기술 | 역할 |
|------|------|------|
| Frontend | Reflex (Python) | UI, 상태 관리, 차트 시각화 |
| Backend | Django + Django REST Framework | 사용자 인증, 일기 CRUD, 데이터 저장 |
| AI Server | Flask | 감정 분석 모델 호출 및 결과 반환 |
| Database | PostgreSQL (또는 SQLite for mini) | 일기 및 분석 결과 저장 |
| AI Model | Hugging Face Transformers (또는 OpenAI API) | 감정 분류 (긍정/부정/중립 + 세부 감정) |

## 3. 주요 기능

### 3.1 필수 기능 (MVP)
1. **회원가입 / 로그인** (Django)
2. **일기 작성**
   - 제목, 내용, 날짜 입력
   - 실시간 또는 제출 후 감정 분석 요청
3. **감정 분석**
   - 긍정 / 부정 / 중립 점수
   - 세부 감정 (기쁨, 슬픔, 분노, 불안, 평온 등)
4. **일기 목록 & 상세 조회**
5. **감정 트렌드 시각화**
   - 최근 7일 / 30일 감정 변화 차트 (Reflex 차트)

### 3.2 확장 기능 (선택)
- AI 격려 메시지 / 조언 생성
- 일기 검색 (키워드 + 감정 필터)
- 월간 감정 리포트 PDF 내보내기
- 태그 기능

## 4. 시스템 아키텍처

```
[User]
   ↓
[Reflex Frontend]
   ↓ REST API
[Django Backend] ←→ [PostgreSQL]
   ↓ HTTP
[Flask AI Server] → [Emotion Model]
```

- Frontend ↔ Backend: REST API (JSON)
- Backend ↔ AI Server: 내부 HTTP 호출 (일기 텍스트 → 감정 결과)
- 인증: JWT 또는 Session (Django)

## 5. 데이터 모델 (주요)

### Diary
- id, user_id, title, content, created_at
- emotion_label (positive/negative/neutral)
- emotion_score (0.0 ~ 1.0)
- detailed_emotions (JSON)

### User
- Django 기본 User 모델 확장 또는 AbstractUser

## 6. API 설계 (예시)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/auth/register | 회원가입 |
| POST | /api/auth/login | 로그인 |
| GET | /api/diaries | 일기 목록 |
| POST | /api/diaries | 일기 작성 + 분석 |
| GET | /api/diaries/{id} | 일기 상세 |
| GET | /api/emotions/trend | 감정 트렌드 데이터 |

## 7. 개발 일정 (예상)

| 단계 | 내용 | 기간 |
|------|------|------|
| 1 | 프로젝트 구조 세팅 + DB 설계 | 1일 |
| 2 | Django Backend (인증 + CRUD) | 2일 |
| 3 | Flask AI Server (감정 분석) | 1일 |
| 4 | Reflex Frontend (UI + 연동) | 2~3일 |
| 5 | 통합 테스트 + 차트 시각화 | 1일 |
| **합계** | | **약 7~8일** |

## 8. 디렉토리 구조 (초안)

```
mood-diary/
├── frontend/          # Reflex
│   ├── mood_diary/
│   └── requirements.txt
├── backend/           # Django
│   ├── config/
│   ├── diaries/
│   └── requirements.txt
├── ai_server/         # Flask
│   ├── app.py
│   └── requirements.txt
├── docker-compose.yml (선택)
└── README.md
```

## 9. 리스크 및 대응

- **AI 모델 응답 지연**: 비동기 처리 또는 캐싱 고려
- **Reflex 학습 곡선**: 공식 문서 + 간단한 컴포넌트부터 시작
- **CORS / 통신 이슈**: Django CORS headers + Flask CORS 설정

## 10. 기대 효과

- Reflex, Django, Flask 3개 스택을 동시에 경험
- AI 모델 연동 실습
- 풀스택 미니프로젝트 포트폴리오 완성

---

**다음 단계**: 이 계획서 기반으로 프로젝트 스켈레톤 생성 및 각 서버 코드 작성 시작

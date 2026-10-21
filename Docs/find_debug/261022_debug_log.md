# 디버깅 기록 — 2026-10-22

초기 구현(`feature/mood-diary-mvp`) 중 발견하고 해결한 문제들. 증상 → 원인 → 조치 순.

## 1. `pip install -r requirements.txt` 가 `UnicodeDecodeError: 'cp949'` 로 실패
- **원인**: requirements.txt 의 한글 주석을 pip 가 Windows 시스템 인코딩(cp949)으로 읽다가 실패.
- **조치**: requirements.txt 주석을 영어로 변경.
- **재발 방지**: requirements.txt 에는 한글을 쓰지 않는다.

## 2. Reflex 앱 import 시 `SyntaxError: 'return' with value in async generator`
- **원인**: `load_diaries` 등 이벤트 핸들러가 `yield`(로딩 표시용)와 `return rx.redirect(...)` 를 함께 사용. async 제너레이터에서는 값 있는 `return` 이 불가.
- **조치**: `yield rx.redirect(...)` 후 빈 `return`. 동기 핸들러(`prepare_new_diary`)는 그대로 `return` 사용.
- **재발 방지**: 중간에 `yield` 가 있는 핸들러에서는 이벤트를 모두 `yield` 로 내보낸다.

## 3. 로그인 실패가 401 이 아닌 403 으로 응답
- **원인**: login/register 뷰는 만료된 토큰이 로그인을 막지 않도록 `authentication_classes = []` 로 두었는데, DRF 는 인증 클래스가 없으면 `AuthenticationFailed` 를 403 으로 바꾼다.
- **조치**: 로그인 실패 시 `Response(..., status=401)` 을 직접 반환. 테스트(`test_login_wrong_password`) 로 고정.

## 4. 키워드가 없는 글이 "중립 100%" 로 분석됨
- **원인**: 중립 prior 만 있고 극성 prior 가 없어 근거가 0 이면 `1.0/1.0 = 1.0`.
- **조치**: 극성 쪽에도 `POLAR_PRIOR=0.25` 를 부여 → 근거 없음 ≈ 중립 67%, 키워드 1개 ≈ 극성 50%.
- **테스트**: `test_neutral_when_no_keywords`, `test_single_keyword_is_weakly_polar`, `test_more_evidence_raises_confidence`.

## 5. 잘못된 토큰의 에러 메시지에 내부 필드(`token_class`, `messages`) 노출
- **원인**: simplejwt 오류 응답이 `{detail, code, messages}` 인데 예외 핸들러가 `detail` 만 있는 경우만 단순화했다.
- **조치**: `detail` 키가 있으면 `message=detail`, `details=null` 로 통일. 테스트(`test_invalid_token_error_is_clean`) 추가.

## 6. Reflex 경고 정리
- `SitemapPlugin` 이 명시되지 않았다는 경고 → `rxconfig.py` 에 `rx.plugins.SitemapPlugin()` 추가.
- `App(theme=...)` deprecated → `rx.plugins.RadixThemesPlugin(theme=...)` 로 이동.
- 남은 경고: Python 3.10 지원 중단 예고 (동작에는 영향 없음).

## 7. Reflex 종료 후 포트 8001 이 계속 점유됨 → `Docs/repeater/261022_port_conflict.md` 참고

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

## 7. Ollama 연동 시 확인한 점
- `gemma4:12b` 는 thinking 기능이 있어 `think:false` 로 끄고, `format` 에 JSON 스키마를 줘서 구조화 출력을 받는다.
- 첫 호출 ~14초(모델 로딩 8.5초 포함)라 기존 AI timeout 5초로는 항상 fallback 이 된다 → `.env` 에서 OLLAMA 60 / Django 90 / 프론트 120 초로 상향.
- 로컬 `.env` 가 `EMOTION_BACKEND=ollama` 이면 테스트가 실제 LLM 을 부를 수 있어 `ai_server/conftest.py` 로 lexicon 을 강제한다.
- 임시 서버를 5055 에 띄웠더니 다른 프로그램(`innorixes`)이 쓰는 포트라 404 응답이 왔다 → 5077 로 변경. 포트를 쓰기 전 점유 여부 확인.
- PowerShell `Invoke-RestMethod` 는 charset 없는 JSON 응답의 한글을 깨뜨려 보여준다(서버 응답은 정상 UTF-8). 한글 확인은 Python 으로 한다.

## 8. UI 디자인 작업 중 문제 (2026-10-22)
- **`504 (Outdated Optimize Dep)` 로 화면 전체가 `Application Error`**: `rx.icon`(lucide) 여러 개를 쓰자 Vite 개발 서버가 아이콘 모듈 최적화를 계속 실패했다(요청마다 다른 아이콘, 재시도해도 동일, `curl` 로는 200). 사용자가 실행 중인 서버를 재시작하지 않고 **아이콘을 이모지/기호로 대체**해 해결. → 규칙: 아이콘은 이모지.
- **CSS 수정이 반영되지 않음**: `assets/mood.css` 만 고치면 `.web/public` 으로 복사되지 않았다(서빙본 확인). `.py` 파일을 갱신하면 복사된다.
- **배경이 흰색**: Radix 루트(`.radix-themes`)가 `--color-background` 로 body 배경을 덮었다 → 투명으로 덮어씀.
- **줄 노트 글자가 줄선과 겹침**: textarea 위 패딩(8px)과 줄 무늬(32px 주기) 위상이 달랐다 → 패딩 16px + 줄 무늬 `background-position-y: 16px`.
- **차트 y축 눈금 잘림/겹침**: `y_axis` 폭 34→44(세부 감정), 차트 `margin` 과 x축 `tick_margin` 추가.
- **모바일**: 히어로 이모지가 글자를 가림, 상단 로그아웃이 줄바꿈, 목록 제목이 배지 때문에 어색하게 줄바꿈 → 각각 숨김/아바타만/배지를 제목 아래로.
- 검증 도구: Playwright + 시스템 Edge(`channel="msedge"`, 브라우저 다운로드 불필요), 스크립트는 `frontend/e2e/ui_flow.py`.

## 9. 다시 분석하기 작업 중 문제 (2026-10-22)
- **e2e 가 로그인 직후 멈춤 (두 번 연속, 재현 어려움)**: 스크린샷을 `frontend/e2e/shots/` 에 저장하자 Reflex 개발 서버가 파일 변경을 감지해 재시작되었고, 그 사이 세션/상태가 끊겼다. 스크린샷을 프로젝트 밖(`<TEMP>/mood_diary_e2e`)으로 옮겨 해결. 같은 스크립트의 임시 복사본(저장 위치만 TEMP)은 통과해서 원인을 좁혔다.
- **안내가 안 보이는 UX 문제**: 버튼은 페이지 맨 아래, 결과/오류 안내는 맨 위에 뜨도록 만들어 길게 스크롤한 상태에서는 오류를 못 볼 수 있었다(스크린샷에서 상단 바에 가려짐) → 안내를 버튼 바로 위로 이동하고, 재분석 오류는 전역 오류 대신 전용 상태(`reanalyze_error`)로 표시.
- **설계 결정**: 재분석이 fallback 이면 저장하지 않고 503. (신규 저장/수정은 장애 시 fallback 값을 저장하지만, 재분석은 사용자가 일부러 요청한 작업이라 좋은 기존 결과를 덮어쓰면 안 된다.)
- **프로세스 정리 실수(내 잘못)**: 새 코드를 로드하려고 8000 포트 Django 를 종료했는데, 시작 시각을 확인하지 않고 내가 띄운 것이라고 가정했다. 실제로는 몇십 초 전에 시작된 다른 프로세스(사용자의 터미널일 가능성)였다. → 서버를 종료하기 전에는 `CreationDate`/`CommandLine`/부모 프로세스로 **누가 띄웠는지 먼저 확인**한다.
- 테스트 계정(`e2e_*`, `dbg_*`)이 실행할 때마다 쌓여 13개를 한꺼번에 정리했다. 사용자 계정은 건드리지 않았다.

## 10. Reflex 종료 후 포트 8001 이 계속 점유됨 → `Docs/repeater/261022_port_conflict.md` 참고

# 학습 정리 — Reflex 0.9 / DRF 패턴

구현하면서 확인한 내용. 버전: reflex 0.9.13, Django 5.2, DRF 3.x.

## Reflex 0.9

- **설정은 `rxconfig.py` 의 플러그인으로**: `rx.plugins.RadixThemesPlugin(theme=...)`, `rx.plugins.SitemapPlugin()`. `rx.App(theme=...)` 는 deprecated.
- **State 변수 타입**: 리스트/딕셔너리 항목은 `TypedDict` 로 선언하면 `rx.foreach` 안에서 `item["title"]` 처럼 접근할 수 있다. 중첩 TypedDict(`emotions: list[EmotionBar]`)도 가능.
- **LocalStorage**: `token: str = rx.LocalStorage("", name="...")` 로 새로고침 후에도 값을 유지.
- **동적 라우트**: 페이지 `route="/diaries/[diary_id]"`, 핸들러에서 `self.router.page.params.get("diary_id")`.
- **이벤트 핸들러에서 로딩 표시**: 값을 바꾸고 `yield` → 느린 호출 → 값 되돌리기. `yield` 가 있으면 `return 값` 을 쓸 수 없다(async 제너레이터). 이벤트는 `yield rx.redirect(...)`.
- **다른 핸들러 연결**: 핸들러 안에서 `return AppState.other_handler` 로 이벤트 체이닝. 다른 핸들러를 직접 순회하지 않는다.
- **자동 setter 없음**: `set_xxx` 가 자동 생성되지 않으므로 제어 입력(`value` + `on_change`)에는 핸들러를 직접 작성. 일반 입력은 `rx.form` + `form_data` 가 간단.
- **차트**: `rx.recharts.line_chart(rx.recharts.line(data_key=...), x_axis, y_axis(domain=[-1, 1]), ..., data=State.list)`. 데이터는 평평한 dict 리스트가 가장 안전.
- **포트**: 프론트 3000, 내부 백엔드 기본 8000. 다른 서버와 겹치면 `backend_port` 변경.
- **브라우저 CORS 와 무관한 구조**: 이벤트 핸들러는 서버 측 Python 이라 `httpx` 로 외부 API 를 호출하면 브라우저가 직접 요청하지 않는다.

## DRF

- **응답 래퍼는 Renderer 로**: `JSONRenderer` 를 상속해 `{success, data, error}` 로 감싸면 뷰를 건드리지 않고 전 API 에 적용된다. 204 는 본문을 비워야 한다.
- **예외 형식 통일**: `EXCEPTION_HANDLER` 에서 `response.data` 를 `{message, details}` 로 정규화. 처리되지 않은 예외도 JSON 500 으로 변환.
- **`authentication_classes = []` 주의**: 인증 헤더가 없을 때 401 대신 403 이 된다. 로그인 실패는 직접 401 반환.
- **사용자별 격리**: `get_queryset()` 에서 `filter(user=request.user)` 로 시작하면 조회·수정·삭제가 모두 자동으로 본인 것만 대상이 되고 타인 객체는 404.
- **서버가 채우는 필드**: Serializer 의 `read_only_fields` 로 지정하면 요청 본문에 넣어도 무시된다.
- **외부 서비스 호출**: `timeout` 필수, 예외·상태 코드·응답 구조를 모두 검증하고 실패 시 기본값으로 대체. 구조화 로그에는 사유(`timeout` 등)와 소요 시간을 남긴다.
- **커스텀 User 는 첫 마이그레이션 전에**: `AUTH_USER_MODEL` 을 나중에 바꾸기 어렵다.

## 감정 분석 설계 메모

- 확신도(score)와 감정 방향(−1~+1)은 다른 값이다. 시계열로 합치려면 부호를 붙여 환산해야 한다.
- 근거가 적을 때 확신도가 1.0 이 되지 않도록 prior(가상 근거)를 둔다.

## UI 스타일링 (2026-10-22, 디자인 작업에서 확인)

- **순수 CSS + `class_name`**: `rx.App(stylesheets=[폰트 URL, "/mood.css"])` 로 `assets/mood.css` 를 불러오고, 컴포넌트는 `rx.el.div(..., class_name="md-card")` 처럼 쓴다. 외부 UI 키트가 필요 없다.
- **State 값으로 클래스 조합**: `class_name=f"md-card entry entry-{item['label']}"` 처럼 Var 를 f-string 에 넣으면 JS 템플릿 문자열이 되어 foreach 안에서도 동작한다. 조건부 클래스는 `rx.cond(cond, "a active", "a")`.
- **인라인 스타일에 Var**: `style={"width": f"{bar['pct']}%"}` 로 막대 너비 같은 동적 값을 준다.
- **네이티브 요소와 `rx.form`**: `rx.el.input(name=...)`, `rx.el.textarea(name=...)` 도 `rx.form(on_submit=...)` 의 `form_data` 에 담긴다. (Radix 입력창 대신 직접 스타일링할 때 유용)
- **활성 메뉴 표시**: `self.router.page.path` 로 계산 변수(`nav_section`)를 만들어 링크 클래스에 사용한다.
- **head 설정**: `rx.App(head_components=[rx.el.link(rel="icon", href="/favicon.svg"), ...])`.
- **Radix 루트 배경**: `.radix-themes` 가 `--color-background` 로 배경을 덮으므로 사이트 배경을 쓰려면 투명으로 덮어쓴다.
- **개발 서버 주의**: `rx.icon`(lucide)을 여러 개 쓰면 Vite 가 `504 Outdated Optimize Dep` 로 화면이 깨졌다 → 이모지 사용. `assets/` 변경은 `.py` 갱신 때 복사된다.
- **브라우저 검증**: Playwright 는 `pip install playwright` 만 하고 `launch(channel="msedge")` 로 설치된 Edge 를 쓰면 브라우저 다운로드가 필요 없다. 전체 페이지 스크린샷(`full_page=True`)을 직접 보며 디자인을 다듬는 것이 가장 빨랐다.

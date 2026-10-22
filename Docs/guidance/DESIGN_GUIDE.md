# 디자인 가이드 — "마음 날씨"

**작성일**: 2026-10-22 · 브랜치 `feature/ui-design` · 스타일 파일 `frontend/assets/mood.css`

## 1. 컨셉

> 오늘의 마음을 일기장에 적으면, AI가 그날의 감정을 **날씨처럼** 읽어준다.

| 요소 | 표현 |
|------|------|
| 일기장 | 따뜻한 크림색 종이 배경, 줄 노트 입력창, 세리프 서체 |
| 감정 방향 | ☀️ 맑음(긍정) · ☁️ 구름(중립) · 🌧️ 비(부정) |
| 세부 감정 | 😊 기쁨 · 😢 슬픔 · 😠 분노 · 😰 불안 · 😌 평온 |
| AI | 🌙 "마음 한마디" 말풍선 |
| 브랜드 | 🌙 달 마크 + 보라색 포인트 |

미니 프로젝트답게 외부 UI 키트 없이 CSS 한 파일과 Reflex 기본 컴포넌트만으로 구성했다.

## 2. 디자인 토큰 (`:root` 변수)

| 구분 | 변수 | 값 |
|------|------|----|
| 종이/잉크 | `--paper` `--card` `--ink` `--ink-soft` `--line` | `#fbf6ee` `#fffdf9` `#342e3d` `#6f6779` `#e9e0d1` |
| 브랜드 | `--brand` `--brand-deep` `--brand-soft` | `#7b5fd0` `#5f45b0` `#eee8fb` |
| 마음 날씨 | `--pos` `--neu` `--neg` (+ `-soft`) | 민트 `#3fae86` · 라벤더그레이 `#8b85a0` · 코랄 `#e0675b` |
| 세부 감정 | `--joy` `--sadness` `--anger` `--anxiety` `--calm` | `#f2b33d` `#5c8deb` `#ef6b5b` `#9b7be0` `#4fbf9f` |
| 모양 | `--radius` `--shadow` `--shadow-lift` | 20px, 은은한 따뜻한 그림자 |

서체: 본문 **Noto Sans KR**, 제목·일기 본문 **Gowun Batang**(Google Fonts, 로딩 실패 시 시스템 서체로 대체).
기본 배경은 복숭아·라벤더 그라데이션 위에 종이색이며, Radix 테마는 `appearance="light"` 로 고정했다(다크 모드 미지원).

## 3. 구성 요소 (CSS 클래스 ↔ 코드)

| 클래스 | 용도 | 코드 위치 |
|--------|------|-----------|
| `md-nav`, `md-navlink(.active)` | 상단 고정바, 현재 메뉴 강조 | `components.navbar` (`AppState.nav_section`) |
| `md-card`, `.hoverable` | 종이 카드 | 전 페이지 |
| `entry`, `entry-positive/negative/neutral`, `date-chip` | 목록 카드: 날씨 색 띠 + 달력 칩 | `pages.diary_card` |
| `weather` | 날씨 배지(이모지·라벨·확신도) | `components.weather_badge` |
| `sky` | 상세 상단 "오늘의 마음 날씨" 카드 | `pages.diary_detail_page` |
| `bar-row`, `bar-fill`, `emo-*` | 세부 감정 막대 | `components.emotion_bar` |
| `bubble` | AI 한마디 말풍선 | `components.ai_bubble` |
| `paper-lined` | 줄 노트 입력창(빨간 여백선) | `pages.new_diary_page` |
| `stat`, `segmented` | 트렌드 요약 카드, 7일/30일 토글 | `pages.trend_page` |
| `hero` | 로그인/가입 2단 카드 | `pages._auth_page` |
| `btn btn-primary/ghost/danger` | 버튼 | 전 페이지 |
| `thinking`, `skeleton` | AI 분석 중 점 3개, 목록 로딩 스켈레톤 | `components.thinking`, `skeleton_list` |
| `notice error/warn` | 오류/AI 서버 fallback 안내 | `components.error_notice`, 상세 페이지 |

화면에 쓰는 값(이모지, 날짜 조각, 날씨 라벨)은 `frontend/mood_diary/view_models.py` 에서 만들고 단위 테스트가 있다.

## 4. 반응형·접근성

- 720px 이하: 히어로 1단, 통계 카드 세로 정렬, 상단 메뉴 두 줄(사용자 이름은 아바타만), 목록 배지는 제목 아래.
- `prefers-reduced-motion` 에서 애니메이션 제거. 입력창에는 포커스 링을 둔다. 오류는 `role="alert"`.
- **색 대비는 정량 측정하지 않았다.** 파스텔 배지의 글자색 대비는 접근성 점검이 필요하다.

## 5. 작업 규칙 (이번에 겪은 문제 기반)

1. **아이콘은 이모지/기호를 쓴다.** `rx.icon`(lucide)을 여러 개 쓰면 Vite 개발 서버가 `504 Outdated Optimize Dep` 로 페이지가 깨졌다. (`Docs/find_debug/261022_debug_log.md`)
2. **`assets/` 수정은 개발 서버에 바로 반영되지 않을 수 있다.** Reflex 는 Python 파일이 갱신될 때 assets 를 `.web/public` 으로 복사한다. CSS 만 고쳤다면 아무 `.py` 를 저장(touch)하거나 서버를 재시작한다.
3. 색·여백은 `:root` 변수를 쓴다. 감정 색을 바꿀 때는 CSS 변수, 차트 선 색(`pages.EMOTION_LINES`), 뷰 모델(`EMOTION_COLORS`) 세 곳이 함께 바뀌어야 한다.
4. Radix 루트가 배경을 덮으므로 `.radix-themes { --color-background: transparent }` 를 유지한다.

## 6. 검증 방법

실제 브라우저(Microsoft Edge, Playwright)로 데스크톱 1280px / 모바일 390px 스크린샷을 찍어 확인했고, 클릭 흐름은 스크립트로 점검한다.

```powershell
pip install playwright
cd frontend
python e2e/ui_flow.py            # 세 서버가 실행 중이어야 함, e2e_xxxxx 계정이 DB 에 남는다
```

결과: 11개 항목(로그인 오류 → 로그인 → 작성·분석 → 상세 → 차트 → 삭제 → 로그아웃 → 보호 페이지 차단, 콘솔 오류 없음) 통과.

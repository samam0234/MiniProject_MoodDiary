"""브라우저 UI 흐름 점검 (수동 실행용 스모크 테스트).

로그인 실패 → 로그인 → 일기 작성(AI 분석) → 상세 → 마음 날씨 차트 → 삭제 → 로그아웃 → 보호 페이지 차단을
실제 브라우저로 눌러 확인한다. 화면 스크린샷도 함께 저장한다.

사전 조건: AI 서버(5000), Django(8000), Reflex(3000)가 실행 중이어야 한다.
준비:      pip install playwright   (브라우저는 설치된 Microsoft Edge 를 사용한다. Chrome 은 --channel chrome)
실행:      python e2e/ui_flow.py [--channel msedge] [--shots <스크린샷 폴더>]

스크린샷은 기본적으로 시스템 임시 폴더(<TEMP>/mood_diary_e2e)에 저장한다. 프로젝트의 frontend/ 안에 저장하면
Reflex 개발 서버가 파일 변경을 감지해 재시작되면서 테스트 도중 세션이 끊긴다.

주의: 실행할 때마다 `e2e_xxxxx` 테스트 계정과 일기 3건이 개발 DB 에 남는다. (삭제 API 가 없다)
      `python manage.py shell` 에서 `User.objects.filter(username__startswith="e2e_").delete()` 로 지울 수 있다.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
import uuid
from datetime import date
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

API = "http://localhost:8000"
WEB = "http://localhost:3000"
PASSWORD = "Str0ng-pass!23"

SEED = [
    ("행복한 하루", "오늘은 정말 행복하고 즐거웠다. 감사한 하루!"),
    ("우울한 저녁", "혼자라서 외롭고 우울했다. 눈물이 났다."),
    ("평범한 하루", "점심에 김치찌개를 먹고 도서관에 갔다."),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="msedge")
    parser.add_argument("--shots", default=str(Path(tempfile.gettempdir()) / "mood_diary_e2e"))
    args = parser.parse_args()
    shots = Path(args.shots)
    shots.mkdir(parents=True, exist_ok=True)
    print(f"스크린샷 저장 위치: {shots}")

    username = f"e2e_{uuid.uuid4().hex[:6]}"
    tokens = requests.post(
        f"{API}/api/auth/register", json={"username": username, "password": PASSWORD}, timeout=20
    ).json()["data"]["tokens"]
    for title, content in SEED:
        requests.post(
            f"{API}/api/diaries", json={"title": title, "content": content},
            headers={"Authorization": f"Bearer {tokens['access']}"}, timeout=120,
        ).raise_for_status()

    results: list[tuple[str, bool]] = []

    def check(name: str, condition: bool, extra: str = "") -> None:
        results.append((name, bool(condition)))
        print(("PASS " if condition else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel)
        page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        # 1. 잘못된 로그인
        page.goto(f"{WEB}/login", wait_until="networkidle")
        page.fill("input[name=username]", username)
        page.fill("input[name=password]", "wrong-password")
        page.get_by_role("button", name="로그인", exact=True).click()
        page.wait_for_selector(".notice.error", timeout=15000)
        check("잘못된 로그인 → 에러 안내", "올바르지 않습니다" in page.inner_text(".notice.error"))
        page.screenshot(path=str(shots / "login_error.png"))

        # 2. 정상 로그인
        page.fill("input[name=password]", PASSWORD)
        page.get_by_role("button", name="로그인", exact=True).click()
        page.wait_for_url("**/diaries", timeout=20000)
        page.wait_for_selector(".entry", timeout=20000)
        check("로그인 → 일기 목록", page.locator(".entry").count() == len(SEED), f"{page.locator('.entry').count()}건")
        check("현재 메뉴 강조", "active" in (page.locator(".md-navlink", has_text="내 일기").get_attribute("class") or ""))
        page.screenshot(path=str(shots / "diaries.png"), full_page=True)

        # 3. 일기 작성
        page.get_by_role("link", name="새 일기").first.click()
        page.wait_for_url("**/diaries/new")
        page.wait_for_function("document.querySelector('input[type=date]').value !== ''", timeout=10000)
        check("날짜 기본값 = 오늘", page.input_value("input[type=date]") == date.today().isoformat())
        page.fill("input[name=title]", "UI 흐름 점검")
        page.fill("textarea[name=content]", "디자인 작업을 마치고 정말 뿌듯하고 행복했다. 감사한 하루!")
        page.get_by_role("button", name="저장하고 분석하기").click()
        page.wait_for_url(re.compile(r".*/diaries/\d+$"), timeout=90000)  # Ollama 첫 호출은 오래 걸릴 수 있다
        page.wait_for_selector(".sky", timeout=20000)
        check("상세: 마음 날씨 카드", "마음 날씨" in page.inner_text(".sky"), page.inner_text(".sky").replace("\n", " "))
        check("상세: 제목·본문", "UI 흐름 점검" in page.inner_text("h1") and "뿌듯" in page.inner_text(".reading-body"))
        page.screenshot(path=str(shots / "detail.png"), full_page=True)
        detail_url = page.url

        # 3-1. 다시 분석하기 (결과 비교 안내가 나오고, 날씨 카드가 유지되어야 한다)
        page.get_by_role("button", name="다시 분석하기").click()
        page.wait_for_selector(".notice.info", timeout=90000)
        notice = page.inner_text(".notice.info").replace("\n", " ")
        check("다시 분석하기 → 결과 비교 안내", "다시 분석" in notice or "분석이 완료" in notice, notice)
        check("다시 분석 후 날씨 카드 유지", "마음 날씨" in page.inner_text(".sky"))
        page.screenshot(path=str(shots / "detail_reanalyzed.png"), full_page=True)

        # 4. 트렌드
        page.get_by_role("link", name="마음 날씨").click()
        page.wait_for_url("**/trend")
        page.wait_for_selector(".stat-grid", timeout=20000)
        check("트렌드 차트 2개 렌더링", page.locator(".recharts-wrapper svg").count() >= 2)
        page.get_by_role("button", name="30일").click()
        page.wait_for_timeout(2000)
        check("30일 전환", "on" in (page.get_by_role("button", name="30일").get_attribute("class") or ""))
        page.screenshot(path=str(shots / "trend.png"), full_page=True)

        # 5. 삭제
        page.goto(detail_url, wait_until="networkidle")
        page.wait_for_selector(".sky", timeout=20000)
        page.get_by_role("button", name="삭제").first.click()
        page.get_by_role("button", name="삭제하기").click()
        page.wait_for_url("**/diaries", timeout=20000)
        page.wait_for_selector(".entry", timeout=20000)
        check("삭제 → 목록에서 사라짐", "UI 흐름 점검" not in page.inner_text("body"))

        # 6. 로그아웃
        page.get_by_role("button", name="로그아웃").click()
        page.wait_for_url("**/login", timeout=15000)
        page.goto(f"{WEB}/diaries", wait_until="networkidle")
        page.wait_for_timeout(1500)
        check("로그아웃 후 보호 페이지 차단", "/login" in page.url, page.url)

        check("브라우저 콘솔 오류 없음", not errors, str(errors[:3]))
        browser.close()

    failed = [name for name, passed in results if not passed]
    print(f"\n결과: {len(results) - len(failed)}/{len(results)} 통과" + (f" | 실패: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

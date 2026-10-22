"""앱 전역 상태와 이벤트 핸들러."""
from __future__ import annotations

from datetime import date
from typing import Any

import reflex as rx

from . import api
from .view_models import (
    EMPTY_DIARY,
    DiaryItem,
    TrendPoint,
    describe_average,
    describe_trend,
    to_diary_item,
    to_trend_points,
)

LOGIN_ROUTE = "/login"
DIARIES_ROUTE = "/diaries"


class AppState(rx.State):
    # JWT 는 브라우저 localStorage 에 보관해 새로고침 후에도 로그인이 유지된다.
    access_token: str = rx.LocalStorage("", name="mood_diary_access")
    refresh_token: str = rx.LocalStorage("", name="mood_diary_refresh")
    username: str = rx.LocalStorage("", name="mood_diary_username")

    error_message: str = ""
    is_loading: bool = False  # 목록/상세/트렌드 조회 중
    is_saving: bool = False  # 폼 제출(로그인/저장/AI 분석) 중

    diaries: list[DiaryItem] = []
    diary: DiaryItem = EMPTY_DIARY
    new_entry_date: str = ""

    trend_days: int = 7
    trend_points: list[TrendPoint] = []
    trend_entries: int = 0
    trend_average_text: str = ""
    trend_headline: str = ""
    trend_positive: int = 0
    trend_negative: int = 0
    trend_neutral: int = 0

    # --- 파생 값 -------------------------------------------------------------
    @rx.var
    def is_logged_in(self) -> bool:
        return bool(self.access_token)

    @rx.var
    def user_initial(self) -> str:
        return self.username[:1].upper() if self.username else ""

    @rx.var
    def nav_section(self) -> str:
        """현재 경로가 속한 네비게이션 항목 (활성 링크 표시용)."""
        path = self.router.page.path
        if path.startswith("/diaries/new"):
            return "new"
        if path.startswith("/diaries"):
            return "list"
        if path.startswith("/trend"):
            return "trend"
        return ""

    @rx.var
    def has_diaries(self) -> bool:
        return len(self.diaries) > 0

    @rx.var
    def has_trend(self) -> bool:
        return len(self.trend_points) > 0

    # --- 내부 유틸 -----------------------------------------------------------
    def _clear_session(self) -> None:
        self.access_token = ""
        self.refresh_token = ""
        self.username = ""

    def _store_session(self, data: dict[str, Any]) -> None:
        self.access_token = data["tokens"]["access"]
        self.refresh_token = data["tokens"]["refresh"]
        self.username = data["user"]["username"]

    async def _call(self, method: str, path: str, **kwargs: Any) -> api.ApiResult:
        """인증이 필요한 호출. access 토큰이 만료되면 refresh 로 한 번 재시도한다."""
        result = await api.request(method, path, token=self.access_token, **kwargs)
        if result.status != 401 or not self.refresh_token:
            return result

        refreshed = await api.request("POST", "/api/auth/refresh", json={"refresh": self.refresh_token})
        if not refreshed.ok:
            self._clear_session()
            return result
        self.access_token = refreshed.data["access"]
        return await api.request(method, path, token=self.access_token, **kwargs)

    def _session_expired(self):
        self._clear_session()
        self.error_message = ""
        return rx.redirect(LOGIN_ROUTE)

    # --- 인증 ----------------------------------------------------------------
    @rx.event
    def go_home(self):
        return rx.redirect(DIARIES_ROUTE if self.access_token else LOGIN_ROUTE)

    @rx.event
    def prepare_auth_page(self):
        """로그인/회원가입 페이지 진입: 이미 로그인 상태면 목록으로 보낸다."""
        self.error_message = ""
        if self.access_token:
            return rx.redirect(DIARIES_ROUTE)

    @rx.event
    async def register(self, form_data: dict):
        username = (form_data.get("username") or "").strip()
        password = form_data.get("password") or ""
        if not username or not password:
            self.error_message = "아이디와 비밀번호를 모두 입력해 주세요."
            return
        if password != form_data.get("password_confirm"):
            self.error_message = "비밀번호 확인이 일치하지 않습니다."
            return

        self.is_saving = True
        self.error_message = ""
        yield
        result = await api.request("POST", "/api/auth/register", json={"username": username, "password": password})
        self.is_saving = False
        if not result.ok:
            self.error_message = result.error
            return
        self._store_session(result.data)
        yield rx.redirect(DIARIES_ROUTE)

    @rx.event
    async def login(self, form_data: dict):
        username = (form_data.get("username") or "").strip()
        password = form_data.get("password") or ""
        if not username or not password:
            self.error_message = "아이디와 비밀번호를 모두 입력해 주세요."
            return

        self.is_saving = True
        self.error_message = ""
        yield
        result = await api.request("POST", "/api/auth/login", json={"username": username, "password": password})
        self.is_saving = False
        if not result.ok:
            self.error_message = result.error
            return
        self._store_session(result.data)
        yield rx.redirect(DIARIES_ROUTE)

    @rx.event
    def logout(self):
        self._clear_session()
        self.diaries = []
        self.diary = EMPTY_DIARY
        self.trend_points = []
        return rx.redirect(LOGIN_ROUTE)

    # --- 일기 ----------------------------------------------------------------
    @rx.event
    async def load_diaries(self):
        if not self.access_token:
            yield rx.redirect(LOGIN_ROUTE)
            return
        self.error_message = ""
        self.is_loading = True
        yield
        result = await self._call("GET", "/api/diaries", params={"page_size": 100})
        self.is_loading = False
        if result.status == 401:
            yield self._session_expired()
            return
        if not result.ok:
            self.error_message = result.error
            return
        self.diaries = [to_diary_item(row) for row in result.data["results"]]

    @rx.event
    def prepare_new_diary(self):
        if not self.access_token:
            return rx.redirect(LOGIN_ROUTE)
        self.error_message = ""
        self.new_entry_date = date.today().isoformat()

    @rx.event
    def set_new_entry_date(self, value: str):
        self.new_entry_date = value

    @rx.event
    async def create_diary(self, form_data: dict):
        title = (form_data.get("title") or "").strip()
        content = (form_data.get("content") or "").strip()
        if not title or not content:
            self.error_message = "제목과 내용을 모두 입력해 주세요."
            return

        payload: dict[str, Any] = {"title": title, "content": content}
        if self.new_entry_date:
            payload["entry_date"] = self.new_entry_date

        self.is_saving = True  # AI 분석 응답이 느릴 수 있어 로딩 상태를 표시한다.
        self.error_message = ""
        yield
        result = await self._call("POST", "/api/diaries", json=payload)
        self.is_saving = False
        if result.status == 401:
            yield self._session_expired()
            return
        if not result.ok:
            self.error_message = result.error
            return
        yield rx.redirect(f"{DIARIES_ROUTE}/{result.data['id']}")

    @rx.event
    async def load_diary(self):
        if not self.access_token:
            yield rx.redirect(LOGIN_ROUTE)
            return
        diary_id = self.router.page.params.get("diary_id", "")
        self.error_message = ""
        self.diary = EMPTY_DIARY
        self.is_loading = True
        yield
        result = await self._call("GET", f"/api/diaries/{diary_id}")
        self.is_loading = False
        if result.status == 401:
            yield self._session_expired()
            return
        if not result.ok:
            self.error_message = "일기를 찾을 수 없습니다." if result.status == 404 else result.error
            return
        self.diary = to_diary_item(result.data)

    @rx.event
    async def delete_diary(self):
        self.is_saving = True
        self.error_message = ""
        yield
        result = await self._call("DELETE", f"/api/diaries/{self.diary['id']}")
        self.is_saving = False
        if result.status == 401:
            yield self._session_expired()
            return
        if not result.ok:
            self.error_message = result.error
            return
        yield rx.redirect(DIARIES_ROUTE)

    # --- 감정 트렌드 -----------------------------------------------------------
    @rx.event
    async def load_trend(self):
        if not self.access_token:
            yield rx.redirect(LOGIN_ROUTE)
            return
        self.error_message = ""
        self.is_loading = True
        yield
        result = await self._call("GET", "/api/emotions/trend", params={"days": self.trend_days})
        self.is_loading = False
        if result.status == 401:
            yield self._session_expired()
            return
        if not result.ok:
            self.error_message = result.error
            return

        summary = result.data["summary"]
        self.trend_points = to_trend_points(result.data["points"])
        self.trend_entries = summary["entries"]
        self.trend_average_text = describe_average(summary["average_sentiment"])
        self.trend_positive = summary["label_counts"]["positive"]
        self.trend_negative = summary["label_counts"]["negative"]
        self.trend_neutral = summary["label_counts"]["neutral"]
        self.trend_headline = describe_trend(summary["label_counts"], self.trend_days)

    @rx.event
    def select_trend_days(self, value: str):
        self.trend_days = int(value)
        return AppState.load_trend

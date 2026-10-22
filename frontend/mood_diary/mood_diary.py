"""Reflex 앱 진입점: 페이지 등록."""
import reflex as rx

from .pages import (
    diaries_page,
    diary_detail_page,
    login_page,
    new_diary_page,
    register_page,
    trend_page,
)
from .state import AppState

FONTS = (
    "https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700"
    "&family=Noto+Sans+KR:wght@400;500;700&display=swap"
)

app = rx.App(
    stylesheets=[FONTS, "/mood.css"],
    head_components=[
        rx.el.link(rel="icon", href="/favicon.svg", type="image/svg+xml"),
        rx.el.meta(name="theme-color", content="#fbf6ee"),
    ],
)

app.add_page(lambda: rx.fragment(), route="/", on_load=AppState.go_home, title="MoodDiary")
app.add_page(login_page, route="/login", on_load=AppState.prepare_auth_page, title="로그인 · MoodDiary")
app.add_page(register_page, route="/register", on_load=AppState.prepare_auth_page, title="회원가입 · MoodDiary")
app.add_page(diaries_page, route="/diaries", on_load=AppState.load_diaries, title="내 일기 · MoodDiary")
app.add_page(new_diary_page, route="/diaries/new", on_load=AppState.prepare_new_diary, title="새 일기 · MoodDiary")
app.add_page(
    diary_detail_page, route="/diaries/[diary_id]", on_load=AppState.load_diary, title="일기 · MoodDiary"
)
app.add_page(trend_page, route="/trend", on_load=AppState.load_trend, title="마음 날씨 · MoodDiary")

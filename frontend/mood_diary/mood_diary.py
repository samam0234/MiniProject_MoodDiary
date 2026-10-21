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

app = rx.App()

app.add_page(lambda: rx.fragment(), route="/", on_load=AppState.go_home, title="MoodDiary")
app.add_page(login_page, route="/login", on_load=AppState.prepare_auth_page, title="로그인 · MoodDiary")
app.add_page(register_page, route="/register", on_load=AppState.prepare_auth_page, title="회원가입 · MoodDiary")
app.add_page(diaries_page, route="/diaries", on_load=AppState.load_diaries, title="내 일기 · MoodDiary")
app.add_page(new_diary_page, route="/diaries/new", on_load=AppState.prepare_new_diary, title="새 일기 · MoodDiary")
app.add_page(
    diary_detail_page, route="/diaries/[diary_id]", on_load=AppState.load_diary, title="일기 · MoodDiary"
)
app.add_page(trend_page, route="/trend", on_load=AppState.load_trend, title="감정 트렌드 · MoodDiary")

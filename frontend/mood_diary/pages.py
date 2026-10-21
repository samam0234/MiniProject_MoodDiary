"""페이지 정의."""
from __future__ import annotations

import reflex as rx

from .components import (
    emotion_bar,
    loading_indicator,
    page_layout,
    sentiment_badge,
)
from .state import AppState
from .view_models import DiaryItem


# --- 인증 ---------------------------------------------------------------------
def _auth_form(title: str, submit_label: str, on_submit, confirm: bool = False) -> rx.Component:
    return page_layout(
        rx.card(
            rx.form(
                rx.vstack(
                    rx.heading(title, size="6"),
                    rx.input(name="username", placeholder="아이디", required=True, width="100%"),
                    rx.input(name="password", type="password", placeholder="비밀번호", required=True, width="100%"),
                    *(
                        [
                            rx.input(
                                name="password_confirm", type="password", placeholder="비밀번호 확인",
                                required=True, width="100%",
                            )
                        ]
                        if confirm
                        else []
                    ),
                    rx.button(submit_label, type="submit", loading=AppState.is_saving, width="100%"),
                    spacing="3",
                    width="100%",
                ),
                on_submit=on_submit,
                reset_on_submit=False,
            ),
            max_width="26rem",
            width="100%",
        ),
    )


def login_page() -> rx.Component:
    return _auth_form("로그인", "로그인", AppState.login)


def register_page() -> rx.Component:
    return _auth_form("회원가입", "가입하고 시작하기", AppState.register, confirm=True)


# --- 일기 목록 ---------------------------------------------------------------
def diary_card(item: rx.Var[DiaryItem]) -> rx.Component:
    return rx.link(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.heading(item["title"], size="4"),
                    rx.spacer(),
                    sentiment_badge(item["label_text"], item["label_color"], item["score_pct"]),
                    width="100%",
                    align="center",
                ),
                rx.text(item["entry_date"], size="1", color_scheme="gray"),
                rx.text(item["preview"], size="2"),
                spacing="2",
                align="start",
                width="100%",
            ),
            width="100%",
        ),
        href=f"/diaries/{item['id']}",
        underline="none",
        width="100%",
    )


def diaries_page() -> rx.Component:
    return page_layout(
        rx.hstack(
            rx.heading("내 일기", size="6"),
            rx.spacer(),
            rx.button("새 일기 쓰기", on_click=rx.redirect("/diaries/new")),
            width="100%",
            align="center",
        ),
        rx.cond(
            AppState.is_loading,
            loading_indicator("일기를 불러오는 중…"),
            rx.cond(
                AppState.has_diaries,
                rx.vstack(rx.foreach(AppState.diaries, diary_card), spacing="3", width="100%"),
                rx.text("아직 작성한 일기가 없어요. 오늘의 감정을 기록해 보세요.", color_scheme="gray"),
            ),
        ),
    )


# --- 일기 작성 ---------------------------------------------------------------
def new_diary_page() -> rx.Component:
    return page_layout(
        rx.heading("새 일기", size="6"),
        rx.form(
            rx.vstack(
                rx.input(name="title", placeholder="제목", required=True, max_length=200, width="100%"),
                rx.input(
                    type="date",
                    value=AppState.new_entry_date,
                    on_change=AppState.set_new_entry_date,
                    width="100%",
                ),
                rx.text_area(
                    name="content", placeholder="오늘 하루는 어땠나요?", required=True,
                    rows="10", max_length=5000, width="100%",
                ),
                rx.hstack(
                    rx.button("저장하고 감정 분석", type="submit", loading=AppState.is_saving),
                    rx.cond(AppState.is_saving, loading_indicator("AI가 감정을 분석하고 있어요…")),
                    align="center",
                    spacing="4",
                ),
                spacing="3",
                width="100%",
            ),
            on_submit=AppState.create_diary,
            reset_on_submit=False,
            width="100%",
        ),
    )


# --- 일기 상세 ---------------------------------------------------------------
def diary_detail_page() -> rx.Component:
    diary = AppState.diary
    return page_layout(
        rx.link("← 목록으로", href="/diaries"),
        rx.cond(
            AppState.is_loading,
            loading_indicator("일기를 불러오는 중…"),
            rx.cond(
                diary["id"] != 0,
                rx.vstack(
                    rx.hstack(
                        rx.heading(diary["title"], size="6"),
                        rx.spacer(),
                        sentiment_badge(diary["label_text"], diary["label_color"], diary["score_pct"]),
                        width="100%",
                        align="center",
                    ),
                    rx.text(diary["entry_date"], size="2", color_scheme="gray"),
                    rx.card(rx.text(diary["content"], white_space="pre-wrap"), width="100%"),
                    rx.cond(
                        diary["is_fallback"],
                        rx.callout(
                            "AI 서버에 연결할 수 없어 기본값(중립 50%)으로 저장되었습니다.",
                            icon="info",
                            color_scheme="amber",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.heading("세부 감정", size="4"),
                            rx.foreach(diary["emotions"], emotion_bar),
                            rx.cond(
                                diary["ai_message"] != "",
                                rx.callout(diary["ai_message"], icon="heart", color_scheme="violet", width="100%"),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                    ),
                    rx.alert_dialog.root(
                        rx.alert_dialog.trigger(rx.button("삭제", color_scheme="red", variant="soft")),
                        rx.alert_dialog.content(
                            rx.alert_dialog.title("일기를 삭제할까요?"),
                            rx.alert_dialog.description("삭제한 일기는 되돌릴 수 없습니다."),
                            rx.hstack(
                                rx.alert_dialog.cancel(rx.button("취소", variant="soft", color_scheme="gray")),
                                rx.alert_dialog.action(
                                    rx.button("삭제", color_scheme="red", on_click=AppState.delete_diary),
                                ),
                                spacing="3",
                                justify="end",
                                margin_top="4",
                            ),
                        ),
                    ),
                    spacing="4",
                    width="100%",
                    align="start",
                ),
            ),
        ),
    )


# --- 감정 트렌드 -------------------------------------------------------------
def _range_button(label: str, days: int) -> rx.Component:
    return rx.button(
        label,
        variant=rx.cond(AppState.trend_days == days, "solid", "soft"),
        on_click=AppState.select_trend_days(str(days)),
    )


def _emotion_line(key: str, color: str) -> rx.Component:
    return rx.recharts.line(data_key=key, name=key, stroke=color, type_="monotone", dot=True)


def trend_page() -> rx.Component:
    return page_layout(
        rx.hstack(
            rx.heading("감정 트렌드", size="6"),
            rx.spacer(),
            _range_button("최근 7일", 7),
            _range_button("최근 30일", 30),
            width="100%",
            align="center",
        ),
        rx.cond(
            AppState.is_loading,
            loading_indicator("트렌드를 불러오는 중…"),
            rx.cond(
                AppState.has_trend,
                rx.vstack(
                    rx.hstack(
                        rx.card(rx.vstack(rx.text("기록한 일기", size="1"), rx.heading(AppState.trend_entries, size="5"))),
                        rx.card(rx.vstack(rx.text("평균 감정", size="1"), rx.heading(AppState.trend_average_text, size="5"))),
                        rx.card(
                            rx.vstack(
                                rx.text("긍정 / 부정 / 중립", size="1"),
                                rx.heading(
                                    f"{AppState.trend_positive} / {AppState.trend_negative} / {AppState.trend_neutral}",
                                    size="5",
                                ),
                            )
                        ),
                        spacing="3",
                        wrap="wrap",
                    ),
                    rx.heading("감정 지수 (−1 부정 ~ +1 긍정)", size="4"),
                    rx.recharts.line_chart(
                        _emotion_line("sentiment", "#7c3aed"),
                        rx.recharts.reference_line(y=0, stroke="#9ca3af", stroke_dasharray="4 4"),
                        rx.recharts.x_axis(data_key="day"),
                        rx.recharts.y_axis(domain=[-1, 1]),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.graphing_tooltip(),
                        data=AppState.trend_points,
                        width="100%",
                        height=280,
                    ),
                    rx.heading("세부 감정 변화", size="4"),
                    rx.recharts.line_chart(
                        _emotion_line("joy", "#f59e0b"),
                        _emotion_line("sadness", "#3b82f6"),
                        _emotion_line("anger", "#ef4444"),
                        _emotion_line("anxiety", "#8b5cf6"),
                        _emotion_line("calm", "#22c55e"),
                        rx.recharts.x_axis(data_key="day"),
                        rx.recharts.y_axis(domain=[0, 1]),
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
                        rx.recharts.graphing_tooltip(),
                        rx.recharts.legend(),
                        data=AppState.trend_points,
                        width="100%",
                        height=280,
                    ),
                    spacing="4",
                    width="100%",
                ),
                rx.text("이 기간에 작성한 일기가 없어요.", color_scheme="gray"),
            ),
        ),
    )

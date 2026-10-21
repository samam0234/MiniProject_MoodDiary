"""여러 페이지에서 공유하는 UI 조각."""
from __future__ import annotations

import reflex as rx

from .state import AppState
from .view_models import EmotionBar


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.link(rx.heading("MoodDiary", size="5"), href="/", underline="none"),
            rx.spacer(),
            rx.cond(
                AppState.is_logged_in,
                rx.hstack(
                    rx.link("일기 목록", href="/diaries"),
                    rx.link("새 일기", href="/diaries/new"),
                    rx.link("감정 트렌드", href="/trend"),
                    rx.text(AppState.username, color_scheme="gray", size="2"),
                    rx.button("로그아웃", variant="soft", size="2", on_click=AppState.logout),
                    align="center",
                    spacing="4",
                    wrap="wrap",
                ),
                rx.hstack(
                    rx.link("로그인", href="/login"),
                    rx.link("회원가입", href="/register"),
                    spacing="4",
                ),
            ),
            align="center",
            padding_x="6",
            padding_y="3",
        ),
        border_bottom="1px solid var(--gray-5)",
        width="100%",
    )


def error_callout() -> rx.Component:
    return rx.cond(
        AppState.error_message != "",
        rx.callout(AppState.error_message, icon="triangle_alert", color_scheme="red", width="100%"),
    )


def page_layout(*children: rx.Component) -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(error_callout(), *children, spacing="5", width="100%"),
            size="3",
            padding_y="6",
        ),
        min_height="100vh",
    )


def loading_indicator(text: str) -> rx.Component:
    return rx.hstack(rx.spinner(size="3"), rx.text(text, color_scheme="gray"), align="center", spacing="3")


def emotion_bar(bar: rx.Var[EmotionBar]) -> rx.Component:
    return rx.hstack(
        rx.text(bar["label"], size="2", width="3rem"),
        rx.progress(value=bar["pct"], color_scheme=bar["color"], width="100%"),
        rx.text(f"{bar['pct']}%", size="2", width="3rem", text_align="right"),
        align="center",
        width="100%",
    )


def sentiment_badge(label_text, label_color, score_pct) -> rx.Component:
    return rx.badge(rx.text(label_text, " ", score_pct, "%"), color_scheme=label_color, size="2")

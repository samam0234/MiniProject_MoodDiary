"""여러 페이지에서 공유하는 UI 조각. 스타일은 assets/mood.css 의 클래스를 사용한다."""
from __future__ import annotations

import reflex as rx

from .state import AppState
from .view_models import DiaryItem, EmotionBar

div, span = rx.el.div, rx.el.span


def _cls(base: str, active) -> rx.Var:
    return rx.cond(active, f"{base} active", base)


def nav_link(emoji: str, label: str, href: str, section: str) -> rx.Component:
    return rx.link(
        span(emoji),
        label,
        href=href,
        underline="none",
        class_name=_cls("md-navlink", AppState.nav_section == section),
    )


def navbar() -> rx.Component:
    return div(
        div(
            rx.link(
                span("🌙", class_name="md-brand-mark"),
                span("MoodDiary"),
                href="/",
                underline="none",
                class_name="md-brand",
            ),
            rx.cond(
                AppState.is_logged_in,
                div(
                    nav_link("📖", "내 일기", "/diaries", "list"),
                    nav_link("✍️", "새 일기", "/diaries/new", "new"),
                    nav_link("⛅", "마음 날씨", "/trend", "trend"),
                    class_name="md-navlinks",
                ),
            ),
            div(class_name="md-spacer"),
            rx.cond(
                AppState.is_logged_in,
                rx.fragment(
                    div(span(AppState.user_initial, class_name="md-avatar"), span(AppState.username), class_name="md-user"),
                    rx.el.button(
                        "로그아웃",
                        on_click=AppState.logout,
                        class_name="btn btn-ghost btn-sm",
                    ),
                ),
                rx.fragment(
                    rx.link("로그인", href="/login", underline="none", class_name="md-navlink"),
                    rx.link("시작하기", href="/register", underline="none", class_name="btn btn-primary btn-sm"),
                ),
            ),
            class_name="md-nav-inner",
        ),
        class_name="md-nav",
    )


def error_notice() -> rx.Component:
    return rx.cond(
        AppState.error_message != "",
        div(span("⚠️"), span(AppState.error_message), class_name="notice error", role="alert"),
    )


def page_layout(*children: rx.Component) -> rx.Component:
    return div(
        navbar(),
        div(
            div(error_notice(), *children, class_name="md-stack"),
            div("MoodDiary · 오늘의 마음을 날씨처럼 기록해요", class_name="md-foot"),
            class_name="md-container",
        ),
        class_name="md-shell",
    )


def page_head(eyebrow: str, title, subtitle=None, action: rx.Component | None = None) -> rx.Component:
    sub = rx.el.p(subtitle, class_name="md-sub") if subtitle is not None else rx.fragment()
    return div(
        div(
            div(eyebrow, class_name="md-eyebrow"),
            rx.el.h1(title, class_name="md-title"),
            sub,
        ),
        action if action is not None else rx.fragment(),
        class_name="md-page-head",
    )


def thinking(text: str) -> rx.Component:
    """AI 분석/로딩 중 표시."""
    return span(rx.el.i(), rx.el.i(), rx.el.i(), span(text), class_name="thinking")


def skeleton_list() -> rx.Component:
    return div(div(class_name="skeleton"), div(class_name="skeleton"), div(class_name="skeleton"), class_name="md-stack")


def weather_badge(emoji, label_text, score_pct) -> rx.Component:
    return span(
        span(emoji),
        span(label_text),
        span(f"{score_pct}%", class_name="pct"),
        class_name="weather",
    )


def date_chip(item: rx.Var[DiaryItem]) -> rx.Component:
    return div(
        span(item["month"], class_name="m"),
        span(item["day"], class_name="d"),
        span(item["weekday"], class_name="w"),
        class_name="date-chip",
    )


def emotion_bar(bar: rx.Var[EmotionBar]) -> rx.Component:
    return div(
        div(span(bar["emoji"]), span(bar["label"]), class_name="name"),
        div(div(class_name=f"bar-fill emo-{bar['key']}", style={"width": f"{bar['pct']}%"}), class_name="bar-track"),
        div(f"{bar['pct']}%", class_name="pct"),
        class_name="bar-row",
    )


def ai_bubble(message) -> rx.Component:
    return div(
        span("🌙", class_name="avatar"),
        div(div("마음 한마디", class_name="who"), div(message)),
        class_name="bubble",
    )


def empty_state(emoji: str, title: str, text: str, action: rx.Component | None = None) -> rx.Component:
    return div(
        div(emoji, class_name="emoji"),
        rx.el.h3(title),
        rx.el.p(text, class_name="md-sub"),
        action if action is not None else rx.fragment(),
        class_name="md-card empty",
    )

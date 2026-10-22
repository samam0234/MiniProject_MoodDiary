"""페이지 정의. 디자인 컨셉은 "마음 날씨" — 스타일은 assets/mood.css."""
from __future__ import annotations

import reflex as rx

from .components import (
    ai_bubble,
    date_chip,
    emotion_bar,
    empty_state,
    page_head,
    page_layout,
    skeleton_list,
    thinking,
    weather_badge,
)
from .state import AppState
from .view_models import DiaryItem

div, span, p = rx.el.div, rx.el.span, rx.el.p


def field(label: str, *inputs: rx.Component) -> rx.Component:
    return div(rx.el.label(label, class_name="md-label"), *inputs)


def submit_button(label: str, busy_text: str) -> rx.Component:
    return rx.el.button(
        rx.cond(AppState.is_saving, thinking(busy_text), span(label)),
        type="submit",
        disabled=AppState.is_saving,
        class_name="btn btn-primary btn-block",
    )


# --- 인증 ---------------------------------------------------------------------
def _hero_side(headline: str) -> rx.Component:
    return div(
        span("☀️", class_name="float-emoji", style={"top": "22px", "right": "34px"}),
        span("☁️", class_name="float-emoji", style={"bottom": "34px", "right": "70px", "animationDelay": "1.2s"}),
        span("🌧️", class_name="float-emoji", style={"bottom": "110px", "right": "10px", "fontSize": "34px", "animationDelay": "2.4s"}),
        div("MoodDiary", class_name="md-eyebrow"),
        rx.el.h2(headline),
        p("일기를 쓰면 AI가 오늘의 마음을 날씨처럼 읽어드려요.", class_name="md-sub"),
        rx.el.ul(
            rx.el.li(span("✍️"), span("제목과 이야기만 적으면 끝")),
            rx.el.li(span("🌤️"), span("감정 5가지를 한눈에 확인")),
            rx.el.li(span("📈"), span("일주일·한 달 마음 날씨 변화")),
            rx.el.li(span("🔒"), span("내 일기는 나만 볼 수 있어요")),
        ),
        class_name="hero-side",
    )


def _auth_page(
    headline: str,
    title: str,
    subtitle: str,
    submit_label: str,
    busy_text: str,
    on_submit,
    alt_text: str,
    alt_label: str,
    alt_href: str,
    confirm: bool = False,
) -> rx.Component:
    inputs = [
        field("아이디", rx.el.input(name="username", placeholder="아이디", required=True, auto_complete="username", class_name="md-input")),
        field(
            "비밀번호",
            rx.el.input(
                name="password", type="password", placeholder="8자 이상", required=True,
                auto_complete="new-password" if confirm else "current-password", class_name="md-input",
            ),
        ),
    ]
    if confirm:
        inputs.append(
            field(
                "비밀번호 확인",
                rx.el.input(
                    name="password_confirm", type="password", placeholder="한 번 더 입력", required=True,
                    auto_complete="new-password", class_name="md-input",
                ),
            )
        )
    return page_layout(
        div(
            _hero_side(headline),
            div(
                rx.el.h1(title),
                p(subtitle, class_name="md-sub", style={"marginBottom": "18px"}),
                rx.form(
                    div(*inputs, submit_button(submit_label, busy_text), class_name="md-stack", style={"gap": "14px"}),
                    on_submit=on_submit,
                    reset_on_submit=False,
                ),
                p(span(alt_text + " "), rx.link(alt_label, href=alt_href, underline="none"), class_name="alt-link", style={"marginTop": "16px"}),
                class_name="hero-form",
            ),
            class_name="md-card hero",
        ),
    )


def login_page() -> rx.Component:
    return _auth_page(
        "오늘의 마음은\n어떤 날씨인가요?",
        "다시 오셨네요",
        "로그인하고 일기를 이어서 써보세요.",
        "로그인",
        "로그인 중…",
        AppState.login,
        "처음이신가요?",
        "회원가입",
        "/register",
    )


def register_page() -> rx.Component:
    return _auth_page(
        "하루 한 줄,\n마음에 날씨를 달아요",
        "시작해볼까요?",
        "아이디와 비밀번호만 있으면 바로 시작할 수 있어요.",
        "가입하고 시작하기",
        "가입 중…",
        AppState.register,
        "이미 계정이 있나요?",
        "로그인",
        "/login",
        confirm=True,
    )


# --- 일기 목록 ---------------------------------------------------------------
def diary_card(item: rx.Var[DiaryItem]) -> rx.Component:
    return rx.link(
        div(
            date_chip(item),
            div(
                div(
                    rx.el.h3(item["title"], class_name="entry-title"),
                    weather_badge(item["emoji"], item["label_text"], item["score_pct"]),
                    class_name="entry-head",
                ),
                p(item["preview"], class_name="entry-preview"),
            ),
            class_name=f"md-card hoverable entry entry-{item['label']}",
        ),
        href=f"/diaries/{item['id']}",
        underline="none",
        class_name="md-link",
    )


def write_button() -> rx.Component:
    return rx.link(span("✍️ 새 일기 쓰기", class_name="btn btn-primary"), href="/diaries/new", underline="none")


def diaries_page() -> rx.Component:
    return page_layout(
        page_head(
            "MY DIARY",
            rx.fragment(AppState.username, "님의 일기장"),
            "오늘은 어떤 하루였나요? 가볍게 한 줄부터 적어보세요.",
            write_button(),
        ),
        rx.cond(
            AppState.is_loading,
            skeleton_list(),
            rx.cond(
                AppState.has_diaries,
                div(rx.foreach(AppState.diaries, diary_card), class_name="md-stack"),
                empty_state("📓", "아직 비어 있는 일기장이에요", "첫 일기를 쓰면 AI가 오늘의 마음 날씨를 알려드려요.", write_button()),
            ),
        ),
    )


# --- 일기 작성 ---------------------------------------------------------------
def new_diary_page() -> rx.Component:
    return page_layout(
        page_head("NEW ENTRY", "오늘의 이야기", "저장하면 AI가 감정을 분석해 마음 날씨를 만들어요."),
        div(
            rx.form(
                div(
                    div(
                        rx.el.input(name="title", placeholder="제목을 적어주세요", required=True, max_length=200, class_name="md-input md-input-title"),
                        style={"flex": "1"},
                    ),
                    rx.el.input(
                        type="date",
                        value=AppState.new_entry_date,
                        on_change=AppState.set_new_entry_date,
                        class_name="md-input",
                        style={"width": "170px", "flex": "none"},
                    ),
                    style={"display": "flex", "gap": "14px", "alignItems": "center", "flexWrap": "wrap"},
                ),
                rx.el.textarea(
                    name="content",
                    placeholder="오늘 있었던 일, 느낀 감정을 편하게 적어보세요…",
                    required=True,
                    max_length=5000,
                    class_name="paper-lined",
                    style={"marginTop": "16px"},
                ),
                div(
                    rx.cond(
                        AppState.is_saving,
                        thinking("AI가 마음 날씨를 읽고 있어요… (처음엔 조금 걸릴 수 있어요)"),
                        span("최대 5000자까지 적을 수 있어요", class_name="md-sub", style={"fontSize": "13px"}),
                    ),
                    div(class_name="md-spacer"),
                    rx.el.button(
                        rx.cond(AppState.is_saving, span("분석 중…"), span("저장하고 분석하기")),
                        type="submit",
                        disabled=AppState.is_saving,
                        class_name="btn btn-primary",
                    ),
                    style={"display": "flex", "alignItems": "center", "gap": "12px", "marginTop": "16px", "flexWrap": "wrap"},
                ),
                on_submit=AppState.create_diary,
                reset_on_submit=False,
            ),
            class_name="md-card",
        ),
    )


# --- 일기 상세 ---------------------------------------------------------------
def delete_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(rx.el.button("🗑 삭제", class_name="btn btn-danger btn-sm")),
        rx.alert_dialog.content(
            rx.alert_dialog.title("이 일기를 삭제할까요?"),
            rx.alert_dialog.description("삭제한 일기는 되돌릴 수 없어요."),
            div(
                rx.alert_dialog.cancel(rx.el.button("취소", class_name="btn btn-ghost btn-sm")),
                rx.alert_dialog.action(rx.el.button("삭제하기", on_click=AppState.delete_diary, class_name="btn btn-danger btn-sm")),
                style={"display": "flex", "gap": "10px", "justifyContent": "flex-end", "marginTop": "18px"},
            ),
        ),
    )


def reanalyze_button() -> rx.Component:
    return rx.el.button(
        rx.cond(AppState.is_reanalyzing, thinking("AI가 다시 읽고 있어요…"), span("🔄 다시 분석하기")),
        on_click=AppState.reanalyze_diary,
        disabled=AppState.is_reanalyzing,
        title="저장된 일기를 현재 AI 모델로 다시 분석해요",
        class_name="btn btn-ghost btn-sm",
    )


def diary_detail_page() -> rx.Component:
    d = AppState.diary
    return page_layout(
        rx.link(span("← 목록으로", class_name="btn btn-ghost btn-sm"), href="/diaries", underline="none"),
        rx.cond(
            AppState.is_loading,
            skeleton_list(),
            rx.cond(
                d["id"] != 0,
                div(
                    div(
                        div(d["long_date"], class_name="md-eyebrow"),
                        rx.el.h1(d["title"], class_name="md-title"),
                    ),
                    div(
                        span(d["emoji"], class_name="big"),
                        div(
                            div(rx.fragment("오늘의 마음 날씨 · ", d["weather"]), class_name="label"),
                            div(rx.fragment(d["label_text"], " ", d["score_pct"], "% 확신"), class_name="hint"),
                        ),
                        class_name=f"sky entry-{d['label']}",
                    ),
                    div(d["content"], class_name="md-card reading reading-body"),
                    rx.cond(
                        d["is_fallback"],
                        div(
                            span("🔌"),
                            span("AI 서버에 연결할 수 없어 기본값(중립 50%)으로 저장되었어요. 서버가 켜진 뒤 아래 \"다시 분석하기\"를 눌러 주세요."),
                            class_name="notice warn",
                        ),
                        div(
                            div(
                                rx.el.h3("세부 감정", class_name="chart-title"),
                                p("이 일기에서 느껴지는 감정의 비율이에요.", class_name="md-sub", style={"fontSize": "13px", "marginBottom": "14px"}),
                                div(rx.foreach(d["emotions"], emotion_bar), class_name="md-stack", style={"gap": "14px"}),
                                class_name="md-card",
                            ),
                            rx.cond(d["ai_message"] != "", ai_bubble(d["ai_message"])),
                            class_name="md-stack",
                        ),
                    ),
                    # 결과/오류 안내는 버튼 바로 위에 둔다 (긴 일기에서 아래로 스크롤해도 보이도록)
                    rx.cond(
                        AppState.reanalyze_notice != "",
                        div(span("🔄"), span(AppState.reanalyze_notice), class_name="notice info", role="status"),
                    ),
                    rx.cond(
                        AppState.reanalyze_error != "",
                        div(span("⚠️"), span(AppState.reanalyze_error), class_name="notice error", role="alert"),
                    ),
                    div(
                        reanalyze_button(),
                        delete_dialog(),
                        class_name="detail-actions",
                    ),
                    class_name="md-stack",
                ),
            ),
        ),
    )


# --- 감정 트렌드 -------------------------------------------------------------
def _range_button(label: str, days: int) -> rx.Component:
    return rx.el.button(
        label,
        on_click=AppState.select_trend_days(str(days)),
        class_name=rx.cond(AppState.trend_days == days, "seg on", "seg"),
    )


def _stat(key: str, value: rx.Component) -> rx.Component:
    return div(div(key, class_name="k"), div(value, class_name="v"), class_name="md-card stat")


EMOTION_LINES = (
    ("joy", "기쁨", "#f2b33d"),
    ("sadness", "슬픔", "#5c8deb"),
    ("anger", "분노", "#ef6b5b"),
    ("anxiety", "불안", "#9b7be0"),
    ("calm", "평온", "#4fbf9f"),
)


def trend_page() -> rx.Component:
    axis_style = {"tick_line": False, "axis_line": False, "stroke": "#a29aac"}
    chart_margin = {"top": 12, "right": 16, "left": 0, "bottom": 12}
    return page_layout(
        page_head(
            "MOOD WEATHER",
            "마음 날씨 변화",
            AppState.trend_headline,
            div(
                _range_button("7일", 7),
                _range_button("30일", 30),
                class_name="segmented",
            ),
        ),
        rx.cond(
            AppState.is_loading,
            skeleton_list(),
            rx.cond(
                AppState.has_trend,
                div(
                    div(
                        _stat("기록한 일기", rx.fragment(AppState.trend_entries, span(" 편", class_name="md-sub"))),
                        _stat("평균 마음", AppState.trend_average_text),
                        _stat(
                            "맑음 · 구름 · 비",
                            rx.fragment(
                                f"☀️ {AppState.trend_positive}  ☁️ {AppState.trend_neutral}  🌧️ {AppState.trend_negative}",
                            ),
                        ),
                        class_name="stat-grid",
                    ),
                    div(
                        rx.el.h3("감정 지수", class_name="chart-title"),
                        p("위로 갈수록 맑음(긍정), 아래로 갈수록 비(부정)예요.", class_name="md-sub", style={"fontSize": "13px", "marginBottom": "10px"}),
                        rx.recharts.area_chart(
                            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#ece3d2", vertical=False),
                            rx.recharts.reference_line(y=0, stroke="#c9bfd6", stroke_dasharray="5 5"),
                            rx.recharts.area(
                                data_key="sentiment", name="감정 지수", type_="monotone", stroke="#7b5fd0", stroke_width=3,
                                fill="#7b5fd0", fill_opacity=0.14, dot=True, active_dot=True,
                            ),
                            rx.recharts.x_axis(data_key="day", tick_margin=10, padding={"left": 12, "right": 12}, **axis_style),
                            rx.recharts.y_axis(domain=[-1, 1], width=34, **axis_style),
                            rx.recharts.graphing_tooltip(),
                            data=AppState.trend_points,
                            margin=chart_margin,
                            width="100%",
                            height=260,
                        ),
                        class_name="md-card",
                    ),
                    div(
                        rx.el.h3("세부 감정", class_name="chart-title"),
                        p("날짜별로 어떤 감정이 두드러졌는지 볼 수 있어요.", class_name="md-sub", style={"fontSize": "13px", "marginBottom": "10px"}),
                        rx.recharts.line_chart(
                            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#ece3d2", vertical=False),
                            *[
                                rx.recharts.line(data_key=key, name=name, type_="monotone", stroke=color, stroke_width=2.5, dot=True)
                                for key, name, color in EMOTION_LINES
                            ],
                            rx.recharts.x_axis(data_key="day", tick_margin=10, padding={"left": 12, "right": 12}, **axis_style),
                            rx.recharts.y_axis(domain=[0, 1], width=44, **axis_style),
                            rx.recharts.graphing_tooltip(),
                            rx.recharts.legend(),
                            data=AppState.trend_points,
                            margin=chart_margin,
                            width="100%",
                            height=280,
                        ),
                        class_name="md-card",
                    ),
                    class_name="md-stack",
                ),
                empty_state(
                    "🌥️",
                    "이 기간에는 일기가 없어요",
                    "일기를 쓰면 마음 날씨의 변화를 여기서 볼 수 있어요.",
                    rx.link(span("일기 쓰러 가기", class_name="btn btn-primary"), href="/diaries/new", underline="none"),
                ),
            ),
        ),
    )

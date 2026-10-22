import reflex as rx

# Reflex 의 기본 백엔드 포트(8000)는 Django 와 충돌하므로 8001 로 분리한다.
config = rx.Config(
    app_name="mood_diary",
    frontend_port=3000,
    backend_port=8001,
    plugins=[
        # 디자인 컨셉 "마음 날씨": 따뜻한 종이 톤은 assets/mood.css 에서 정의하고,
        # Radix 컴포넌트(알림창 등)는 라이트 + 보라 포인트로 맞춘다.
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="light", accent_color="violet", gray_color="sand", radius="large")
        ),
        rx.plugins.SitemapPlugin(),
    ],
)

import reflex as rx

# Reflex 의 기본 백엔드 포트(8000)는 Django 와 충돌하므로 8001 로 분리한다.
config = rx.Config(
    app_name="mood_diary",
    frontend_port=3000,
    backend_port=8001,
    plugins=[
        rx.plugins.RadixThemesPlugin(theme=rx.theme(accent_color="violet", radius="large")),
        rx.plugins.SitemapPlugin(),
    ],
)

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("mood_diary.backend")

VALIDATION_MESSAGE = "요청 값이 올바르지 않습니다."


def api_exception_handler(exc, context):
    """에러를 ``{"message": str, "details": ...}`` 구조로 통일한다."""
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("unhandled_api_error", exc_info=exc)
        return Response(
            {"message": "서버 내부 오류가 발생했습니다.", "details": None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    if isinstance(data, dict) and "detail" in data:  # 인증/권한/404 등 (simplejwt 의 code/messages 는 숨긴다)
        response.data = {"message": str(data["detail"]), "details": None}
    else:
        response.data = {"message": VALIDATION_MESSAGE, "details": data}
    return response

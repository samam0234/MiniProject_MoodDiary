from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer, issue_tokens


class RegisterView(APIView):
    """POST /api/auth/register"""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = {"user": UserSerializer(user).data, "tokens": issue_tokens(user)}
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login"""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            # 인증 클래스를 비운 뷰에서는 AuthenticationFailed 가 403 으로 바뀌므로 401 을 직접 반환한다.
            return Response(
                {"message": "아이디 또는 비밀번호가 올바르지 않습니다.", "details": None},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({"user": UserSerializer(user).data, "tokens": issue_tokens(user)})


class MeView(APIView):
    """GET /api/auth/me - 현재 로그인한 사용자 정보"""

    def get(self, request):
        return Response(UserSerializer(request.user).data)

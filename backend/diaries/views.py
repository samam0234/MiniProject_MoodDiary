from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Diary
from .serializers import DiarySerializer
from .services import analyze_text, build_trend

MAX_TREND_DAYS = 90


class AnalysisUnavailable(APIException):
    """AI 분석을 수행하지 못했을 때 (기존 분석 결과는 유지한다)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "AI 서버에 연결할 수 없어 다시 분석하지 못했어요. 기존 분석 결과는 그대로 유지돼요."
    default_code = "analysis_unavailable"


def apply_analysis(diary: Diary, analysis: dict) -> None:
    diary.emotion_label = analysis["label"]
    diary.emotion_score = analysis["score"]
    diary.detailed_emotions = analysis["detailed_emotions"]
    diary.ai_message = analysis["message"]
    diary.analysis_source = analysis["source"]


class DiaryViewSet(viewsets.ModelViewSet):
    """일기 CRUD. 항상 로그인한 사용자 본인의 일기만 조회/수정할 수 있다."""

    serializer_class = DiarySerializer

    def get_queryset(self):
        return Diary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        data = serializer.validated_data
        analysis = analyze_text(f"{data['title']}\n{data['content']}")
        diary = Diary(user=self.request.user, **data)
        apply_analysis(diary, analysis)
        diary.save()
        serializer.instance = diary

    def perform_update(self, serializer):
        diary = serializer.instance
        changed = {"title", "content"} & set(serializer.validated_data)
        for field, value in serializer.validated_data.items():
            setattr(diary, field, value)
        if changed:  # 본문이 바뀐 경우에만 재분석한다.
            apply_analysis(diary, analyze_text(f"{diary.title}\n{diary.content}"))
        diary.save()

    @action(detail=True, methods=["post"])
    def reanalyze(self, request, pk=None):
        """POST /api/diaries/{id}/reanalyze - 저장된 일기를 현재 AI 모델로 다시 분석한다.

        AI 서버 장애(fallback)로 분석하지 못하면 기존 결과를 덮어쓰지 않고 503 을 반환한다.
        응답에는 비교용으로 이전 분석 결과(previous)가 함께 담긴다.
        """
        diary = self.get_object()
        previous = {
            "emotion_label": diary.emotion_label,
            "emotion_score": diary.emotion_score,
            "analysis_source": diary.analysis_source,
        }
        analysis = analyze_text(f"{diary.title}\n{diary.content}")
        if analysis["source"] == "fallback":
            raise AnalysisUnavailable()
        apply_analysis(diary, analysis)
        diary.save()
        return Response({**self.get_serializer(diary).data, "previous": previous})


class EmotionTrendView(APIView):
    """GET /api/emotions/trend?days=7|30"""

    def get(self, request):
        raw = request.query_params.get("days", "7")
        try:
            days = int(raw)
        except ValueError:
            raise ValidationError({"days": "정수여야 합니다."})
        if not 1 <= days <= MAX_TREND_DAYS:
            raise ValidationError({"days": f"1 ~ {MAX_TREND_DAYS} 사이여야 합니다."})

        diaries = Diary.objects.filter(user=request.user)
        return Response(build_trend(diaries, days, timezone.localdate()))

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Diary
from .serializers import DiarySerializer
from .services import analyze_text, build_trend

MAX_TREND_DAYS = 90


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

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Diary(models.Model):
    """사용자 일기와 AI 감정 분석 결과."""

    class EmotionLabel(models.TextChoices):
        POSITIVE = "positive", "긍정"
        NEGATIVE = "negative", "부정"
        NEUTRAL = "neutral", "중립"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diaries")
    title = models.CharField(max_length=200)
    content = models.TextField()
    entry_date = models.DateField(default=timezone.localdate, help_text="일기를 쓴 날짜 (트렌드 집계 기준)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emotion_label = models.CharField(
        max_length=10, choices=EmotionLabel.choices, default=EmotionLabel.NEUTRAL
    )
    emotion_score = models.FloatField(
        default=0.5, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    detailed_emotions = models.JSONField(default=dict, blank=True)
    ai_message = models.TextField(blank=True, default="")
    # lexicon / transformers / fallback (AI 서버 장애 시)
    analysis_source = models.CharField(max_length=20, default="fallback")

    class Meta:
        ordering = ["-entry_date", "-created_at"]
        indexes = [models.Index(fields=["user", "entry_date"])]

    def __str__(self) -> str:
        return f"[{self.entry_date}] {self.title}"

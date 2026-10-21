from rest_framework import serializers

from .models import Diary


class DiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Diary
        fields = (
            "id",
            "title",
            "content",
            "entry_date",
            "created_at",
            "updated_at",
            "emotion_label",
            "emotion_score",
            "detailed_emotions",
            "ai_message",
            "analysis_source",
        )
        # 분석 결과는 서버가 채우며 클라이언트가 직접 쓸 수 없다.
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "emotion_label",
            "emotion_score",
            "detailed_emotions",
            "ai_message",
            "analysis_source",
        )

    def validate_title(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("제목을 입력해 주세요.")
        return value

    def validate_content(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("내용을 입력해 주세요.")
        if len(value) > 5000:
            raise serializers.ValidationError("내용은 5000자 이하여야 합니다.")
        return value

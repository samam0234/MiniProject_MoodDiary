from django.contrib import admin

from .models import Diary


@admin.register(Diary)
class DiaryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "entry_date", "emotion_label", "emotion_score", "analysis_source")
    list_filter = ("emotion_label", "analysis_source")
    search_fields = ("title", "content", "user__username")

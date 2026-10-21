from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import DiaryViewSet, EmotionTrendView

router = SimpleRouter(trailing_slash=False)
router.register("diaries", DiaryViewSet, basename="diary")

urlpatterns = [
    path("emotions/trend", EmotionTrendView.as_view(), name="emotion-trend"),
    path("", include(router.urls)),
]

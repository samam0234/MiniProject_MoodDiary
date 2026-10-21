from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """커스텀 사용자 모델. 이후 프로필 필드를 확장할 수 있도록 처음부터 분리해 둔다."""

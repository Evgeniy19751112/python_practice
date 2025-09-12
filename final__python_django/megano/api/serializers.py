import logging

from django.core.validators import FileExtensionValidator
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, ImageField
from rest_framework.serializers import Serializer

logger = logging.getLogger("api")


class BaseImageSerializer(Serializer):
    src = ImageField(
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["png", "jpg", "jpeg", "gif", "svg"]
            )
        ],
    )
    alt = CharField(max_length=128, required=False, allow_blank=True)

    def validate_image(self, value):
        max_size_value: float = 3.0
        max_size = 3 * 1024 * 1024  # 3MB
        if value.size > max_size:
            raise ValidationError(f"Максимальный размер файла {max_size_value:3.1f}MB")
        return value

    def get_src(self, obj):
        return obj.src.url if obj.src else None

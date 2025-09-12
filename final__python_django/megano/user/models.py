import os

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError


def image_directory_path(instance: "Profile", filename: str) -> str:
    """Формируем путь к изображениям для профиля пользователя."""
    pattern: str = "app/users/profile_{}/img_{}"

    # Формируем новое имя файла
    now = timezone.now()
    datetime_str = now.strftime("%Y%m%d%H%M%S%f")
    *name, ext = os.path.splitext(filename)
    new_filename = f"{datetime_str}{ext}"

    if instance is not None and hasattr(instance, "profile") and instance.profile:
        result_path = pattern.format(instance.profile.pk, new_filename)
    else:
        result_path = pattern.format("unknown", new_filename)

    return result_path


class ImagesAvatar(models.Model):
    """Модель для хранения аватара пользователя."""

    src = models.ImageField(
        verbose_name="Link to the avatar image",
        null=True,
        blank=True,
        upload_to=image_directory_path,
        default="app/default_avatar.png",
    )
    alt = models.CharField(
        max_length=128,
        verbose_name="Image avatar description",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Avatar"
        verbose_name_plural = "Avatars"

    @classmethod
    def get_allowed_extensions(cls):
        return ["png", "jpg", "jpeg"]

    def clean_src(self):
        file = self.src
        if file:
            file_extension = os.path.splitext(file.name)[1]
            if file_extension.lower() not in self.get_allowed_extensions():
                raise ValidationError("Unsupported file format")
        return file

    def is_custom_avatar(self):
        default_path = self._meta.get_field("src").default
        return self.src and str(self.src) != default_path

    def __str__(self):
        return f"Avatar #{self.id}; src '{self.src}'; alt '{self.alt}'"


class Profile(models.Model):
    """Модель профиля пользователя."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="User",
    )
    fullName = models.CharField(
        max_length=128,
        verbose_name="Full name",
        null=True,
        blank=True,
        unique=False,
    )
    phone = models.PositiveIntegerField(
        blank=True,
        null=True,
        unique=True,
        verbose_name="Phone number",
    )
    balance = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=0,
        verbose_name="Balance",
        null=False,
        blank=False,
    )
    avatar = models.OneToOneField(
        ImagesAvatar,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Avatar",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Profile #{self.id} for user {self.user}"

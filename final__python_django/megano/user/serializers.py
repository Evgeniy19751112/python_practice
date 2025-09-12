import logging
import re

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from .models import ImagesAvatar, Profile

logger = logging.getLogger("user")


class AvatarSerializer(ModelSerializer):
    src = SerializerMethodField()
    alt = CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = ImagesAvatar
        fields = ["src", "alt"]

    def get_src(self, obj):
        # logger.debug("get_src called. Object: %s", obj)
        if obj is not None and hasattr(obj, "src") and obj.src:
            return obj.src.url if obj.src else None
        return None


class ProfileSerializer(ModelSerializer):
    avatar = AvatarSerializer(required=False, allow_null=True)
    email = SerializerMethodField(required=False)

    class Meta:
        model = Profile
        fields = ["fullName", "email", "phone", "avatar"]

    def get_email(self, obj):
        return obj.user.email

    def validate_email(self, value):
        # Проверка на пустое значение
        if not value:
            raise ValidationError("Email cannot be empty")

        # Проверка формата email
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, value):
            raise ValidationError("Invalid email format")

        # Проверка уникальности email (с учетом регистра)
        try:
            user = User.objects.get(email__iexact=value)
            if user:
                raise ValidationError("The email address is already occupied")
        except User.DoesNotExist:
            pass

        return value

    @classmethod
    def save_user_data(cls, profile: Profile, email: str = None, full_name: str = None):
        """Сохранить данные в таблице user."""
        if email is None and full_name is None:
            return

        if email:
            # print("email", email)
            profile.user.email = email

        if full_name:
            # print("full_name", full_name)
            first_name, last_name = full_name.split(" ", 1)
            profile.user.first_name = first_name
            profile.user.last_name = last_name

        profile.user.save()

    def create(self, validated_data):
        avatar_data = validated_data.pop("avatar", None)
        email_data = validated_data.pop("email", None)
        full_name = validated_data.get("fullName", None)

        with transaction.atomic():
            profile = Profile.objects.create(**validated_data)
            logger.debug("Profile created: %s", profile)

            self.save_user_data(profile=profile, email=email_data, full_name=full_name)

            if avatar_data:
                avatar = ImagesAvatar.objects.create(**avatar_data)
                profile.avatar = avatar
                profile.save()
                logger.debug("Avatar created: %s", avatar)

        return profile

    def update(self, instance, validated_data):
        email_data = validated_data.pop("email", None)
        avatar_data = validated_data.pop("avatar", None)
        full_name = validated_data.get("fullName", None)
        # print("update", email_data, avatar_data, full_name, validated_data)

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            logger.debug("Profile updated: %s", instance)

            self.save_user_data(profile=instance, email=email_data, full_name=full_name)

            if avatar_data is not None:
                if instance.avatar:
                    for attr, value in avatar_data.items():
                        setattr(instance.avatar, attr, value)
                    instance.avatar.save()
                    logger.debug("Avatar updated: %s", instance.avatar)
                else:
                    avatar = ImagesAvatar.objects.create(**avatar_data)
                    instance.avatar = avatar
                    instance.save()
                    logger.debug("Avatar created: %s", avatar)

        return instance


class ChangePasswordSerializer(ModelSerializer):
    currentPassword = CharField(required=True, write_only=True)
    newPassword = CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = [
            "currentPassword",
            "newPassword",
        ]


class SignInSerializer(Serializer):
    username = CharField(required=True)
    password = CharField(required=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise ValidationError("Both username and password are required")

        return attrs


class SignUpSerializer(Serializer):
    name = CharField(required=True, max_length=128)
    username = CharField(required=True)
    password = CharField(required=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise ValidationError("Username already exists")
        return value

    def validate(self, attrs):
        if not all([attrs.get("name"), attrs.get("username"), attrs.get("password")]):
            raise ValidationError("All fields are required")
        return attrs

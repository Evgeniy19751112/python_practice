import logging
import os

from api.exceptions import CustomAPIException
from api.services import get_data_from_request
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.backends import ModelBackend
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from megano import settings

from .models import (
    ImagesAvatar,
    Profile,
)
from .serializers import (
    ChangePasswordSerializer,
    ProfileSerializer,
    SignInSerializer,
    SignUpSerializer,
)
from .services import (
    change_user_password,
    create_user_profile,
)

logger = logging.getLogger("user")


class SignInView(APIView):
    def post(self, request) -> Response:
        """Аутентификация клиента."""
        message = "Failed to sign in"
        serializer = SignInSerializer(data=get_data_from_request(request))
        if serializer.is_valid():
            user = authenticate(
                request=request,
                username=serializer.validated_data.get("username"),
                password=serializer.validated_data.get("password"),
            )
            if user is not None:
                login(request, user)

                # Наверное костыль, но столкнулся с проблемой наличие юзера без профиля
                profile = Profile.objects.get_or_create(user=user)
                logger.debug(f"Use profile {profile} for user {user}")

                return Response(status=status.HTTP_200_OK)
        else:
            message += ": " + str(serializer.errors)

        raise CustomAPIException(
            detail=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SignUpView(APIView):
    def post(self, request) -> Response:
        """Регистрация клиента."""
        message = "Failed to sign up"
        serializer = SignUpSerializer(data=get_data_from_request(request))
        if serializer.is_valid():
            profile = create_user_profile(serializer.validated_data)
            if profile:
                user = authenticate(
                    request=request,
                    username=profile.user.username,
                    password=profile.user.password,
                )

                if user is not None:
                    login(request, user)
                else:
                    login(request, profile.user)

                return Response(status=status.HTTP_200_OK)
        else:
            message += ": " + str(serializer.errors)

        raise CustomAPIException(
            detail=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Создание и обновление профиля пользователя."""
        profile = request.user.profile
        # data = get_data_from_request(request)
        # print("data", data)

        serializer = ProfileSerializer(
            profile, data=get_data_from_request(request), partial=True
        )
        if serializer.is_valid():
            # logger.debug("serializer validated")
            try:
                serializer.save()

                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as error:
                logger.error(
                    "Error updating profile %s: %s",
                    type(error),
                    str(error),
                    exc_info=True,
                )
                raise CustomAPIException(
                    detail=serializer.errors,
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            logger.warning("Serializer errors: %s", serializer.errors)

        raise CustomAPIException(
            detail=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request: Request) -> Response:
        """Получение профиля пользователя."""
        profile = request.user.profile
        if profile is not None and profile.avatar is None:
            profile.avatar = ImagesAvatar.objects.create()
            profile.save()
        serializer = ProfileSerializer(profile)
        # print("profile serializer:", profile, serializer.data, sep="\n", end="\n\n")

        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfilePasswordSetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Смена пароля пользователя."""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if change_user_password(
                request.user,
                serializer.validated_data["currentPassword"],
                serializer.validated_data["newPassword"],
            ):
                # Обновим сессию
                auth_backend = ModelBackend()
                user = auth_backend.authenticate(
                    request,
                    username=request.user.username,
                    password=serializer.validated_data["newPassword"],
                )
                if user:
                    update_session_auth_hash(request, user)

                return Response(status=status.HTTP_200_OK)

            return Response(
                {"currentPassword": ["Wrong password"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raise CustomAPIException(
            detail=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
        )


class ChangeAvatarView(APIView):
    # queryset = Profile.objects.all()
    # serializer_class = AvatarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Создать или обновить аватарку пользователя."""
        # logger.debug(
        #     "ChangeAvatarView request.data: %s %s", type(request.data), request.data
        # )
        if "avatar" not in request.FILES:
            raise CustomAPIException(
                detail="No avatar file provided",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        profile = request.user.profile
        avatar_file = request.FILES["avatar"]
        alt_text = f"Avatar for {request.user.username}"
        # logger.debug(
        #     "profile: %s\n%s\n%s\n%s\n%s\n%s",
        #     type(profile),
        #     profile,
        #     profile.avatar.src if profile.avatar else None,
        #     profile.user,
        #     avatar_file,
        #     alt_text,
        # )

        # Удаляем предыдущую аватарку и добавляем новую в транзакции
        old_avatar_file = None
        with transaction.atomic():
            if not profile.avatar:
                new_avatar = ImagesAvatar.objects.create(src=avatar_file, alt=alt_text)
                profile.avatar = new_avatar
            else:
                if profile.avatar.src and profile.avatar.is_custom_avatar():
                    old_avatar_file = str(profile.avatar.src)

                profile.avatar.src = avatar_file
                profile.avatar.alt = alt_text
                profile.avatar.save()

            profile.save()

            # Удалим старый файл, если он был ранее в базе
            if old_avatar_file:
                try:
                    old_avatar_file = os.path.join(settings.MEDIA_ROOT, old_avatar_file)
                    os.remove(old_avatar_file)
                except FileNotFoundError as err:
                    logger.warning("Error deleting old avatar file: %s", err)
                logger.debug(
                    'File "%s" deleted result %s',
                    old_avatar_file,
                    not os.path.isfile(old_avatar_file),
                )

        return Response(
            ProfileSerializer(profile).data,
            status=status.HTTP_200_OK,
        )

import logging
from typing import Optional

from api.exceptions import CustomAPIException
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework import status

from .models import Profile, User

logger = logging.getLogger("user")


@transaction.atomic
def create_user_profile(user_data: dict) -> Optional[Profile]:
    """
    Создание пользователя и профиля
    """
    try:
        username = user_data.get("username", "")
        password = user_data.get("password", "")
        full_name = user_data.get("name", "")
        first_name, *last_name = full_name.split()
        last_name = " ".join(last_name)
        # logger.debug("Создание профиля для пользователя '%s'", username)

        # Создать пользователя и профиль
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        profile = Profile.objects.create(user=user, fullName=full_name)

        # Добавление в группу "Покупатель"
        try:
            user_group, _ = Group.objects.get_or_create(name="Покупатель")
            user_group.user_set.add(user)
        except Group.DoesNotExist:
            raise CustomAPIException(
                detail="Error accessing the 'Buyer' group.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return profile
    except Exception as e:
        logger.error("Error create user and profile: %s", e, exc_info=True)
        raise CustomAPIException(
            detail="Error create user and profile: %s" % e,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def change_user_password(user: User, current_password: str, new_password: str) -> bool:
    """
    Изменение пароля пользователя
    """
    if user.check_password(current_password):
        user.set_password(new_password)
        user.save()

        # logger.debug("Save new password for user '%s'.", user.username)
        return True

    logger.warning("Password change failed for user '%s'.", user.username)
    return False

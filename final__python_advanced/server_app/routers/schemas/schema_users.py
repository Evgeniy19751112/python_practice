"""
Набор схем для модели пользователя.
"""

from fastapi import APIRouter

from .schema_base import DefaultSchema, SuccessResponse

router = APIRouter(prefix="/api", tags=["users"])


class UserBaseSchema(DefaultSchema):
    """
    Схема информации о пользователе. Базовая.

    Attributes:
        id (int): ID пользователя.
        name (str): Имя пользователя.
    """

    id: int
    name: str


class UserSchema(UserBaseSchema):
    """
    Схема информации о пользователе. Основная рабочая.

    Дополнить базовую схему списками о подписчиках и подписок.

    Attributes:
        followers (list[UserBaseSchema]): Список подписчиков
        following (list[UserBaseSchema]): Список на кого подписан
    """

    followers: list[UserBaseSchema]
    following: list[UserBaseSchema]


class UserOutSchema(SuccessResponse):
    """
    Схема ответа о пользователе.

    Attributes:
        user (UserSchema): Схема с информацией о пользователе.
        result (bool): Унаследован от родительского класса. Равен True.
    """

    user: UserSchema

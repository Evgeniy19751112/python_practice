"""
Эндпоинты для /api/users
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy import and_, delete, insert, select

from server_app.database import Followers, db_manager
from server_app.database.crud import (
    read_follower_for_user,
    read_following_for_user,
    read_user_by_id,
)
from server_app.utils import log

from .schemas import SuccessResponse, UserBaseSchema, UserOutSchema, UserSchema
from .utils.authentication import get_current_user

router = APIRouter(prefix="/api", tags=["users"])


@router.post(
    "/users/{user_id}/follow",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse,
)
async def post_api_users_follow(
    user_id: int,
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Эндпоинт для подписки на пользователя.

    -----

    :param user_id: ID профиля пользователя.
    :param user: Текущий пользователь

    :return: Результат установки метки (см.схемы)
    """
    log.debug(
        "Подписаться на пользователя %s от клиента %s.",
        user_id,
        user.id if user is not None else None,
    )
    follows_query = db_manager.execute(
        select(Followers).where(
            and_(
                Followers.c.follower_id == user.id,
                Followers.c.following_id == user_id,
            )
        )
    )
    follows = (
        follows_query.scalar_one_or_none()
        if follows_query is not None
        else None
    )
    if follows is None:
        # Подписаться на пользователя
        db_manager.execute(
            insert(Followers).values(follower_id=user.id, following_id=user_id)
        )

    return SuccessResponse()


@router.delete(
    "/users/{user_id}/follow",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
)
async def delete_api_users_follow(
    user_id: int,
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Эндпоинт для отписки от пользователя.

    -----

    :param user_id: ID профиля пользователя.
    :param user: Текущий пользователь

    :return: Результат удаления метки (см.схемы)
    """
    log.debug(
        "Отписаться от пользователя %s от клиента %s.",
        user_id,
        user.id if user is not None else None,
    )
    follows_query = db_manager.execute(
        select(Followers.c.id).where(
            and_(
                Followers.c.follower_id == user.id,
                Followers.c.following_id == user_id,
            )
        )
    )
    follows: Optional[int] = (
        follows_query.scalar_one_or_none()
        if follows_query is not None
        else None
    )
    if follows is not None:
        # Отписаться от пользователя
        db_manager.execute(delete(Followers).where(Followers.c.id == follows))

    return SuccessResponse()


@router.get(
    "/users/me",
    status_code=status.HTTP_200_OK,
    response_model=UserOutSchema,
)
async def get_api_users_me(
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Эндпоинт получения информации о своём профиле.

    -----

    :return: Информация о профиле (см.схемы)
    """
    log.debug(
        "Получить информацию о профиле клиента %s.",
        user.id if user is not None else None,
    )
    follower = read_follower_for_user(user.id)
    users_followers = (
        [UserBaseSchema(**item) for item in follower]
        if follower is not None
        else []
    )

    following = read_following_for_user(user.id)
    users_following = (
        [UserBaseSchema(**item) for item in following]
        if following is not None
        else []
    )

    result = UserOutSchema(
        user=UserSchema(
            id=user.id,
            name=user.name,
            followers=users_followers,
            following=users_following,
        )
    )

    log.debug('Данные по пользователю "%s" получены.', user.name)
    return result


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserOutSchema,
)
async def get_api_users(
    user_id: int,
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Эндпоинт получения информации о произвольном профиле по его id.

    -----

    :param user_id: ID профиля пользователя.
    :param user: Текущий пользователь

    :return: Информация о профиле (см.схемы)
    """
    log.debug(
        "Получить информацию о профиле ID %s клиента %s.",
        user_id,
        user.id if user is not None else None,
    )
    user_data = read_user_by_id(user_id)
    user_profile = (
        [UserBaseSchema(id=item[0], name=item[1]) for item in user_data]
        if user_data is not None
        else None
    )

    follower = read_follower_for_user(user_id)
    users_followers = (
        [UserBaseSchema(**item) for item in follower]
        if follower is not None
        else []
    )

    following = read_following_for_user(user_id)
    users_following = (
        [UserBaseSchema(**item) for item in following]
        if following is not None
        else []
    )

    return UserOutSchema(
        user=UserSchema(
            id=user_profile[0].id if user_profile is not None else 0,
            name=user_profile[0].name if user_profile is not None else "",
            followers=users_followers,
            following=users_following,
        )
    )

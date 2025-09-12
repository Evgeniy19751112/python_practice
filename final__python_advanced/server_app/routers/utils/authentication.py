"""Модуль для аутентификации абонента по API ключу."""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from server_app.database.crud import read_user_by_api_key
from server_app.routers.schemas import UserBaseSchema
from server_app.utils import log

API_KEY = APIKeyHeader(name="api-key")


async def get_current_user(
    token: str = Depends(API_KEY),  # noqa: B008
) -> UserBaseSchema:
    """
    Получить сведения о текущем пользователе, если он есть в БД.
    Иначе вызвать исключение (ошибка 401).
    """
    log.debug('Запрос аутентификации пользователя "%s".', token)
    data = read_user_by_api_key(token)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong api-key authentication!",
            headers={"api-key": ""},
        )

    log.debug(
        "Аутентификация пользователя (результат): token=%s, id=%s, name=%s.",
        token,
        data.id,
        data.username,
    )

    return UserBaseSchema(id=data.id, name=data.username)

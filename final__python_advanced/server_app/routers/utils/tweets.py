"""Модуль для взаимодействия с БД по твитам."""

from typing import Any

from fastapi import HTTPException, status

from server_app.database.crud import (  # noqa
    read_files_by_tweet_id,
    read_likes_by_tweet_id,
    read_tweets_list,
    read_user_by_id,
)
from server_app.routers.schemas import (  # noqa
    LikeSchema,
    TweetOutSchema,
    UserBaseSchema,
)
from server_app.utils import log


async def get_users_list_in_tweets(
    users: int | list[int] | None,
) -> dict[int, UserBaseSchema] | None:
    """Получить список пользователей."""
    log.debug("Получить список пользователей с ID %s.", users)
    users_list = read_user_by_id(users)
    result: dict[int, UserBaseSchema] = dict()
    if users_list is not None:
        for user in users_list:
            result[user.id] = UserBaseSchema(id=user.id, name=user.username)
    return result


async def get_files_list_in_tweets(
    tweets: int | list[int] | None,
) -> dict[int, list[str]] | None:
    """Получить список файлов."""
    log.debug("Получить список файлов по твитам с ID %s.", tweets)
    files_list = read_files_by_tweet_id(tweets)
    result: dict[int, list[str]] = dict()
    if files_list is not None:
        for file in files_list:
            result.setdefault(file.tweet_id, [])
            result[file.tweet_id].append(file.local_file)
    return result


async def get_likes_list_in_tweets(
    tweets: int | list[int] | None,
) -> dict[int, list[LikeSchema]] | None:
    """Получить список лайков."""
    log.debug("Получить список лайков для твита с ID %s.", tweets)
    likes_list = read_likes_by_tweet_id(tweets)
    result: dict[int, list[LikeSchema]] = dict()
    if likes_list is not None:
        for like in likes_list:
            result.setdefault(like.tweet_id, [])
            result[like.tweet_id].append(
                LikeSchema(user_id=like.user_id, name=like.name)
            )
    return result


async def get_tweets_list(
    user: UserBaseSchema = None,
    offset: int = 0,
    limit: int = 0,
) -> TweetOutSchema:
    """
    Получить данные по всем твитам. Если пользователь указан,
    то вернуть только его твиты.
    """
    log.debug("Получить данные по твитам %s.", user)
    # Получить данные по твитам
    if user is None:
        data = read_tweets_list(offset=offset, limit=limit)
    else:
        data = read_tweets_list(user.id, offset=offset, limit=limit)

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data found for tweets!",
            headers={"api-key": ""},
        )

    # Формируем предварительную структуру для вывода списка твитов
    tweets_data: dict[int, Any] = dict()
    users_id: list[int] = list()
    tweet_id: list[int] = list()
    for item in data:
        users_id.append(item.user_id)
        tweet_id.append(item.id)
        tweets_data[item.id] = {
            "id": item.id,
            "content": item.text,
            "attachments": [],
            "author": item.user_id,
            "likes": [],
        }
    users_id = list(set(users_id))
    tweet_id = list(set(tweet_id))

    # Получить данные по авторам твитов
    users_list = await get_users_list_in_tweets(users_id)

    # Получить список файлов
    files_list = await get_files_list_in_tweets(tweet_id)

    # Получить список лайков
    likes_list = await get_likes_list_in_tweets(tweet_id)

    # Собрать твиты с дополнительными данными
    for tweet_item in tweets_data:
        tweet = tweets_data[tweet_item]
        tweet["author"] = (
            users_list[tweet["author"]] if users_list is not None else None
        )
        if files_list is not None and tweet["id"] in files_list:
            tweet["attachments"].extend(files_list[tweet["id"]])
        if likes_list is not None and tweet["id"] in likes_list:
            tweet["likes"].extend(likes_list[tweet["id"]])

    return TweetOutSchema(tweets=[tweets_data[tweet] for tweet in tweets_data])

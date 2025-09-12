"""
Схемы описания моделей твита и лайков.
"""

from typing import Optional

from .schema_base import DefaultSchema, SuccessResponse
from .schema_users import UserBaseSchema


class LikeSchema(DefaultSchema):
    """
    Схема лайков (кто и имя лайки)

    Attributes:
        user_id (int): ID пользователя, который лайкнул.
        name (str): Имя лайка (???)
    """

    user_id: int
    name: Optional[str]


class TweetInSchema(DefaultSchema):
    """
    Схема нового твита.

    Загрузка картинок будет происходить по endpoint /api/media.
    Фронтенд будет подгружать картинки туда автоматически при
    отправке твита и подставлять id оттуда в json.

    Attributes:
        tweet_data (str): Текст твита.
        tweet_media_ids (list[int]): Список ID медиафайлов,
        зарегистрированных в БД.
    """

    tweet_data: str
    tweet_media_ids: Optional[list[int]] = list()


class TweetCreateSchema(SuccessResponse):
    """
    Схема ответа с id созданного твита.

    Attributes:
        tweet_id (int): ID созданного твита.
        result (bool): Унаследован от родительского класса. Равен True.
    """

    tweet_id: int


class TweetSchema(DefaultSchema):
    """
    Схема твита для ленты пользователя.

    Attributes:
        id (int): ID твита.
        content (str): Текст твита.
        attachments (list[str]): Список ссылок на медиафайлы твита.
        author (UserBaseSchema): Автор твита.
        likes (list[LikeSchema]): Список лайков твита.
    """

    id: int
    content: str
    attachments: list[str]
    author: UserBaseSchema
    likes: list[LikeSchema]


class TweetOutSchema(DefaultSchema):
    """
    Схема списка твитов для ленты.

    Attributes:
        tweets (list[TweetSchema]): Список твитов для ленты.
    """

    tweets: list[TweetSchema]

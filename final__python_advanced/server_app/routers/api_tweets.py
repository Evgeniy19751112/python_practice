"""
Эндпоинты для /api/tweets
"""

import os.path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, select, update

from server_app.database import Likes, Medias, Tweets, db_manager
from server_app.settings import IMAGE_PATH
from server_app.utils import log

from .schemas import (
    ErrorResponse,
    SuccessResponse,
    TweetCreateSchema,
    TweetInSchema,
    TweetOutSchema,
    UserBaseSchema,
)
from .utils.authentication import get_current_user
from .utils.tweets import get_tweets_list

router = APIRouter(prefix="/api", tags=["tweets"])


@router.post(
    "/tweets",
    status_code=status.HTTP_201_CREATED,
    response_model=TweetCreateSchema,
)
async def post_api_tweets(
    tweet_in: TweetInSchema,
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Эндпоинт получения нового твита от клиента.

    Сохранить полученный твит и вернуть id записанного твита (см. схему)

    -----

    :param user: Текущий пользователь
    :param tweet_in: Входящие данные от клиента с текстом и с id изображений.

    :return: Результат сохранения твита (см. схемы).
    """
    log.debug(
        "Получить твит от клиента %s.", user.id if user is not None else None
    )
    print(tweet_in.tweet_data)
    print(tweet_in.tweet_media_ids)
    tweet = Tweets(
        user_id=user.id,
        text=tweet_in.tweet_data,
    )
    db_manager.session.add(tweet)
    db_manager.session.commit()

    if tweet_in.tweet_media_ids is not None:
        for media_id in tweet_in.tweet_media_ids:
            db_manager.execute(
                update(Medias)
                .where(Medias.id == media_id)
                .values(tweet_id=tweet.id)
            )

    return TweetCreateSchema(tweet_id=tweet.id)


@router.delete(
    "/tweets/{tweet_id}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
)
async def delete_api_tweets(
    tweet_id: int,
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Удалить свой твит.

    Выполнить поверку на принадлежность твита и удалить его, если
    твит свой, иначе отказ. Вернуть результат True ли False.

    -----

    :param tweet_id: ID твита на удаление.
    :param user: Текущий пользователь

    :return: Результат удаления твита (см. схемы).
    """
    log.debug(
        "Удалить твит %s клиента %s.",
        tweet_id,
        user.id if user is not None else None,
    )
    # Получить информацию твита по tweet_id, если его нет,
    # то выход с ошибкой 404
    try:
        tweet_query = db_manager.execute(
            select(Tweets).where(Tweets.id == tweet_id)
        )
        tweet = (
            tweet_query.scalar_one_or_none()
            if tweet_query is not None
            else None
        )
        log.debug("Найден твит %s", tweet)
    except Exception as err:
        log.error(
            "Ошибка получения твита %s для удаления: %s.",
            tweet_id,
            err,
            exc_info=True,
        )
        return (
            ErrorResponse(
                error_type=err.__class__.__name__, error_message=str(err)
            ),
            404,
        )
    if tweet is None:
        raise HTTPException(404, f"Твит не найден по id {tweet_id}!")

    # Принадлежность твита пользователю, если нет, то выход с ошибкой 400
    if tweet.user_id != user.id:
        log.error("Твит %s не принадлежит пользователю %s!", tweet_id, user.id)
        raise HTTPException(
            400, f"Твит {tweet_id} не принадлежит пользователю {user.id}!"
        )

    # Получить имена файлов, принадлежащих твиту
    files_query = db_manager.execute(
        select(Medias.local_file).where(Medias.tweet_id == tweet_id)
    )

    files: list[str] = (
        files_query.scalars().all() if files_query is not None else []
    )

    # Удалить твит из БД и удалить файлы
    try:
        db_manager.execute(delete(Tweets).where(Tweets.id == tweet_id))

        for file in files:
            file_name = os.path.join(IMAGE_PATH, os.path.basename(file))
            if os.path.isfile(file_name):
                os.remove(file_name)

    except Exception as err:
        log.error(
            "Ошибка удаления твита %s: %s.", tweet_id, err, exc_info=True
        )
        return (
            ErrorResponse(
                error_type=err.__class__.__name__, error_message=str(err)
            ),
            400,
        )

    return SuccessResponse()


@router.post(
    "/tweets/{tweet_id}/likes",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse,
)
async def post_api_tweets_likes(
    tweet_id: int,
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Лайкнуть любой твит.

    Установить метку LIKE, если её нет. Вернуть результат True ли False.

    -----

    :param tweet_id: ID твита для отметки.
    :param user: Текущий пользователь

    :return: Результат отметки твита лайком (см. схемы).
    """
    log.debug(
        "Поставить лайк твиту %s от клиента %s.",
        tweet_id,
        user.id if user is not None else None,
    )
    check_query = db_manager.execute(
        select(Likes.id).where(
            and_(Likes.user_id == user.id, Likes.tweet_id == tweet_id)
        )
    )
    check_like = check_query.scalars() if check_query is not None else None
    if check_like is None or len(check_like.all()) == 0:
        log.debug("Лайк требуется.")
        like = Likes(user_id=user.id, tweet_id=tweet_id)
        db_manager.session.add(like)
        db_manager.session.commit()
    else:
        log.debug(
            "Лайк уже есть %s для твита %s от клиента %s. %s",
            check_like.all(),
            tweet_id,
            user.id if user is not None else None,
            check_like.all(),
        )

    return SuccessResponse()


@router.delete(
    "/tweets/{tweet_id}/likes",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
)
async def delete_api_tweets_likes(
    tweet_id: int,
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Убрать свой лайк с любого твита.

    Снять метку LIKE, если она есть. Вернуть результат True ли False.

    -----

    :param tweet_id: ID твита для отметки.
    :param user: Текущий пользователь

    :return: Результат снятия метки твита лайком (см. схемы).
    """
    log.debug(
        "Удалить лайк твиту %s от клиента %s.",
        tweet_id,
        user.id if user is not None else None,
    )
    check_query = db_manager.execute(
        select(Likes.id).where(
            and_(Likes.user_id == user.id, Likes.tweet_id == tweet_id)
        )
    )
    check_like = (
        check_query.scalars().all() if check_query is not None else None
    )
    if check_like is not None and len(check_like) > 0:
        log.debug("Лайк требуется удалить. %s", check_like)
        db_manager.execute(delete(Likes).where(Likes.id.in_(check_like)))
    else:
        log.debug(
            "Лайк уже нет для твита %s от клиента %s.",
            tweet_id,
            user.id if user is not None else None,
        )

    return SuccessResponse()


@router.get(
    "/tweets",
    status_code=status.HTTP_200_OK,
    response_model=TweetOutSchema,
)
async def get_api_tweets(
    offset: int = Query(  # noqa: B008
        0, description="Номер страницы для отображения"
    ),
    limit: int = Query(  # noqa: B008
        0, description="Сколько твитов на странице (0 - все)"
    ),
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Эндпоинт для получения полного списка твитов.

    Сделать выборку всех твитов и вернуть клиенту (см. схему)

    -----

    :return: Результат выборки твитов (см. схемы).
    """
    log.debug(
        "Получение данных по всем твитам для пользователя %s",
        user.name if user is not None else None,
    )

    result = await get_tweets_list(user=user, offset=offset, limit=limit)

    log.debug("Всего твитов получено %s", len(result.tweets))

    return result

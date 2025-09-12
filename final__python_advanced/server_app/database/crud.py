"""
Основной модуль для взаимодействия с базой данных.
Содержит основные функции для создания и чтения записей.
"""

import os
from typing import Any, Optional

from sqlalchemy import select, text, update

from server_app.utils import log

from . import secret
from .db import db_manager
from .func_cache import cache_result
from .models import Followers, Likes, Medias, Tweets, Users


@cache_result(timeout=300)
def read_user_by_api_key(
    api_key: str,
) -> Users | None:
    """
    Получить данные из БД пользователя по его токену.

    :param api_key: Ключ пользователя для поиска в БД (открытый)

    :return: Модель таблицы пользователя, который авторизовался,
        либо None при отсутствии пользователя в БД
    """
    log.debug("Запрос пользователя по ключу %s.", api_key)
    result: Optional[Users] = None
    data = db_manager.execute(select(Users).where(Users.api_key.like("=%")))
    if data is not None:
        for row in data.scalars():
            log.debug("Проверяю ключ для %s (%s)", row.username, row.api_key)
            if secret.verify_secret_key(row.api_key, api_key):
                result = row
                log.debug("Найден ключ %s для %s", api_key, row.username)
                break
    if result is None:
        # Пробуем найти по открытому ключу
        log.debug(
            "Ключ %s пользователя не найден. "
            "Попытка поиска ключа без шифрования",
            api_key,
        )
        data = db_manager.execute(
            select(Users).where(Users.api_key == api_key)
        )
        result = data.scalar_one_or_none() if data is not None else None
        if result is not None:
            # Обновить в БД ключ на зашифрованный
            secret_key = secret.make_secret_key(api_key)
            db_manager.execute(
                update(Users)
                .where(Users.id == result.id)
                .values(api_key=secret_key)
            )
            log.debug('Назначен новый ключ "%s"', secret_key)
            result.api_key = secret_key
    else:
        log.debug("Получены данные %s по кодированному ключу", result)

    return result


def read_user_by_id(
    user_id: int | list[int] | None,
) -> list[Any] | None:
    """
    Получить данные из БД пользователей по их ID.
    Если не указан user_id, то извлечь всех.

    :param user_id: ID пользователя (или пользователей)

    :return: Список найденных сведений о пользователях
    """
    log.debug("Запрос пользователя по ID %s.", user_id)
    if user_id is not None:
        if isinstance(user_id, int):
            user_id = [user_id]

    query = (
        select(Users.id, Users.username)
        .filter(user_id is None or Users.id.in_(user_id))
        .order_by(Users.id)
    )
    result = None
    data = db_manager.execute(query)
    if data is not None:
        result = data.all()
    return result


def read_follows_by_query(
    query: Any,
) -> list[dict[str, Any]] | None:
    """
    Получить данные из БД кто подписан на пользователя.

    :param query: Запрос, который будет вызван менеджером БД (execute).

    :return: Результат, полученный из БД, в виде списка словарей,
        совместимых со схемой UserBaseSchema.
    """
    log.debug("Получить данные из БД кто подписан на пользователя.")
    data = db_manager.execute(query)
    return (
        [{"id": col[0], "name": col[1]} for col in data]
        if data is not None
        else None
    )


def read_follower_for_user(
    user_id: int,
) -> list[dict[str, Any]] | None:
    """
    Получить данные из БД кто подписан на пользователя.

    :param user_id: ID пользователя

    :return: Список читающих твиты пользователя.
    """
    log.debug("Запрос кто подписан на пользователя ID %s.", user_id)
    query = (
        select(Followers.c.follower_id, Users.username)
        .join(Users, Followers.c.follower_id == Users.id)
        .filter(Followers.c.following_id == user_id)
        .order_by(Followers.c.follower_id)
    )

    return read_follows_by_query(query) if query is not None else None


def read_following_for_user(
    user_id: int,
) -> list[dict[str, Any]] | None:
    """
    Получить данные из БД на кого подписан пользователь.

    :param user_id: ID пользователя

    :return: Список пишущих пользователей, которых читает указанный
    """
    log.debug("Запрос на кого подписан пользователь ID %s.", user_id)
    query = (
        select(Followers.c.following_id, Users.username)
        .join(Users, Followers.c.following_id == Users.id)
        .filter(Followers.c.follower_id == user_id)
        .order_by(Followers.c.following_id)
    )

    return read_follows_by_query(query) if query is not None else None


def read_tweets_list(
    user_id: int | None = None,
    offset: int = 0,
    limit: int = 0,
) -> list[Tweets] | None:
    """
    Получить данные из БД по твитам с сортировкой от наиболее популярных
    к менее для текущего пользователя.

    :param user_id: ID пользователя, по которому производится фильтрация
        (по умолчанию None).
    :param offset: Номер страницы. Если указать не более 0, то будет
        считаться как страница 1
    :param limit: Сколько твитов на странице. 0 - все твиты без разбивки

    :return: Список полученных твитов
    """
    log.debug("Запрос списка твитов пользователя ID %s.", user_id)
    sql = """
        drop table if exists temp_follows;
        drop table if exists temp_likes;

        select f.following_id as id
        into temporary table temp_follows
        from follows f
        where f.follower_id = :user_id;

        select l.id, l.tweet_id
        into temporary table temp_likes
        from likes l
        where l.user_id in (select id from temp_follows);

        select
            t.*,
            count(l.id) counter,
            case
                when t.user_id in (select id from temp_follows)
                then 0
                else 1
            end as priority,
            count(tl.id) tweets_count
        from tweets t
        left join public.likes l on t.id = l.tweet_id
        left join temp_likes tl on t.id = tl.tweet_id
        group by t.id
        order by priority,
            tweets_count desc,
            counter desc,
            t.id
    """

    # Делаем расчёт для разбивки на страницы, если limit > 0
    if limit > 0:
        offset_rows = max(offset - 1, 0) * limit
        sql += f" offset {offset_rows} limit {limit}"
    sql += ";"
    #
    #     drop table if exists temp_follows;
    #     drop table if exists temp_likes;
    # """

    query = text(sql)
    result = None
    data = db_manager.execute(query, params={"user_id": user_id})
    if data is not None:
        # result_data = data.scalars().all()
        result = [
            Tweets(
                id=row.id,
                user_id=row.user_id,
                text=row.text,
                created_at=row.created_at,
                last_edited=row.last_edited,
            )
            for row in data.fetchall()
        ]
    return result


def read_files_by_tweet_id(
    tweet_id: int | list[int] | None,
) -> list[Any] | None:
    """
    Получить данные из БД о файлах по ID твитов.
    Если не указан tweet_id, то извлечь все.

    :param tweet_id: ID искомого твита (или список кодов)

    :return: Список всех файлов для указных твитов
    """
    log.debug("Запрос списка файлов для твита ID %s.", tweet_id)
    if tweet_id is not None:
        if isinstance(tweet_id, int):
            tweet_id = [tweet_id]

    query = (
        select(Medias.id, Medias.local_file, Medias.tweet_id)
        .filter(tweet_id is None or Medias.tweet_id.in_(tweet_id))
        .order_by(Medias.tweet_id, Medias.id)
    )
    result = None
    data = db_manager.execute(query)
    if data is not None:
        result = data.all()

    return result


def read_likes_by_tweet_id(
    tweet_id: int | list[int] | None,
) -> list[Any] | None:
    """
    Получить данные из БД о лайках по ID твитов.
    Если не указан tweet_id, то извлечь все.

    :param tweet_id: ID искомого твита (или список кодов)

    :return: Список лайков для указанных твитов
    """
    log.debug("Запрос по лайкам для твита ID %s.", tweet_id)
    if tweet_id is not None:
        if isinstance(tweet_id, int):
            tweet_id = [tweet_id]

    query = (
        select(Likes.id, Likes.user_id, Likes.tweet_id, Likes.name)
        .filter(tweet_id is None or Likes.tweet_id.in_(tweet_id))
        .order_by(Likes.user_id, Likes.tweet_id, Likes.id)
    )
    result = None
    data = db_manager.execute(query)
    if data is not None:
        result = data.all()

    return result


def create_media(
    tweet_id: int,
    *,
    filename: Optional[str] = None,
    local_file: Optional[str] = None,
    pairs: Optional[list[tuple[str | None, str | None]]] = None,
) -> None:
    """
    Добавить сведения о файле в БД.

    :param tweet_id: ID твита, к которому относится файл.
    :param filename: Имя файла, которое пришло от клиента.
    :param local_file: Имя файла, под которым сохранён в локальном
        хранилище (например, в /images). Путь указывается от корня,
        где лежат статические файлы NGINX.
    :param pairs: Список кортежей пар "имя файла" + "локальное имя".
        Используется для группового добавления файлов в БД.

    :raises ValueError: Если указать имя файла и список пар.
    """
    log.debug(
        "Запрос на сохранение файла '%s' в БД для твита ID %s.",
        filename,
        tweet_id,
    )

    # Проверим на излишние или недостающие данные
    if filename is not None and local_file is not None and pairs is not None:
        raise ValueError(
            "Ожидается либо одиночные значения для имени файла, "
            "либо список пар значений."
        )
    if filename is None and local_file is None and pairs is None:
        raise ValueError(
            "Ожидается как минимум одиночные значения для имени файла, "
            "либо список пар значений."
        )
    elif filename is None and local_file is not None:
        filename = os.path.basename(local_file)
    if pairs is None:
        pairs = [(filename, local_file)]

    # Дальше забираем данные из pairs
    data = []
    for pair in pairs:
        data.append(
            Medias(tweet_id=tweet_id, filename=pair[0], local_file=pair[1])
        )
    if len(data) > 0:
        db_manager.session.add_all(data)
        db_manager.session.commit()


def read_tweet_by_id(tweet_id: int) -> Optional[Tweets]:
    """
    Получить твит по его ID.

    :param tweet_id: Код требуемого твита.

    :return: Найденный твит или None
    """
    data = db_manager.execute(select(Tweets).where(Tweets.id == tweet_id))
    return data.scalar_one_or_none() if data is not None else None

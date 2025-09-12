"""
Создаём фейковые данные для демонстрации приложения Tweeter-Clone.

Задачи:
- заполнить таблицу абонентами (users);
- заполнить таблицу твитами (tweets & medias);
- заполнить таблицу лайками (likes);
- заполнить таблицу подписчиками (follows).

Всего абонентов создадим 16 (имена "user_0" .. "user_f").
Для каждого пользователя сделаем от 1 до 5 твитов (рандомно),
для некоторых чётных твитов скачаем картинку с котятами. Лайки
расставим случайным образом, но с увеличенным шансом на твиты с
картинкой. Подписчиков назначим случайным образом.

Пример подготовки к запуску и запуск:
export POSTGRES_USER=test_login
export POSTGRES_PASSWORD=test_passw
export POSTGRES_DB=test_db
export POSTGRES_HOST=localhost:5432
python3 make_fake_data.py
"""

import asyncio
import json
import os
import random
from datetime import datetime
from time import sleep

import aiohttp
import dotenv
import requests
from faker import Faker
from sqlalchemy import desc, func, select
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from server_app.utils import what_image_ext

from server_app.database import (  # isort:skip
    Followers,
    Likes,
    Medias,
    Tweets,
    Users,
    db_manager,
)


def add_users(users: list[Users]) -> None:
    try:
        db_manager.session.add_all(users)
        db_manager.session.flush()
        db_manager.session.commit()
    except DatabaseError as err:
        print(type(err), err, sep="\n")
        db_manager.session.rollback()


def prepare_users(
    quantity: int,
) -> list[int]:
    """
    Заполнить таблицу пользователей в указанном количестве.

    :param quantity: Количество пользователей.
    :return: ID добавленных пользователей.
    """
    faker = Faker("ru_RU")

    # Подготовить данные пользователей
    users: list = [Users(api_key="test", username="test test")]
    for num in range(quantity + 1):
        users.append(
            Users(
                api_key=f"user_{hex(num)[2:]}",
                username=f"{faker.first_name()} {faker.last_name()}",
            )
        )

    # Добавить пользователей в базу
    add_users(users)

    # Прочитать ID пользователей
    result = []
    query = select(Users.id).order_by(Users.id)
    data = db_manager.session.execute(query)
    result.extend(data.scalars().all())
    return result


async def get_cat(client: aiohttp.ClientSession, url: str) -> bytes | None:
    image_data = None
    async with client.get(url) as response:
        if response.status == 200:
            result = await response.read()
            image_url = json.loads(result.decode()[1:-1])
            image_data = requests.get(image_url["url"]).content
        else:
            print("Response status", response.status)
    return image_data


def save_file(filename: str, content: bytes) -> None:
    """Записать данные в файл в синхронном варианте."""
    with open(filename, "wb") as file:
        file.write(content)


def get_image_type(image: bytes) -> str:
    """Определить тип изображения по двоичным данным."""
    return what_image_ext(None, image)


async def get_one_cats(user_id: int) -> str | None:
    """Скачать файл и сохранить его в images. Вернуть имя файла"""
    # URL: str = "https://cataas.com/cat"
    URL: str = "https://api.thecatapi.com/v1/images/search"
    OUT_PATH: str = "./server_nginx/static/images"
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(15)
    ) as client:
        try:
            image = await get_cat(client, URL)
            if image is None:
                raise Exception("No image data!")
            filetype = get_image_type(image)
            file_part1 = hex(user_id)[2:]
            file_part2 = hex(int(datetime.now().timestamp()))[2:]
            counter = 0
            while True:
                file_part3 = hex(counter)[2:]
                filename = "".join(
                    (file_part1, file_part2, file_part3, ".", filetype)
                )
                file_path = os.path.join(OUT_PATH, filename)
                if not os.path.exists(file_path):
                    break
                counter += 1
            save_file(file_path, image)
        except Exception as err:
            print(type(err), err)
            filename = None
    return filename


def prepare_tweets(
    max_quantity: int,
    users: list[int],
) -> list[int]:
    """
    Заполнить таблицу твитов пользователей в указанном количестве.

    :param max_quantity: Максимальное количество твитов на пользователя.
    :param users: Коды пользователей, кому добавляем твиты

    :return: ID добавленных твитов.
    """
    faker = Faker("ru_RU")

    # Подготовить данные пользователей (сколько твитов ждём от каждого)
    wait_tweets = list()
    for user in users:
        wait_tweets.extend(
            [user for _ in range(random.randint(1, max_quantity) + 1)]
        )
    random.shuffle(wait_tweets)  # Немного хаоса в очерёдность твитов
    print("random", wait_tweets)

    # Добавить твиты в базу
    tweets_with_image = []
    try:
        for num, user in enumerate(wait_tweets, 1):
            media_data = None
            if num % 2 == 0:
                # Чётный твит
                if random.choice((True, False, True, False, True)):
                    # Этот будет с картинкой
                    sleep(0.5)
                    filename = asyncio.run(get_one_cats(user))
                    if filename is not None:
                        size = random.randint(32, 128)
                        media_data = Medias(
                            filename=filename,
                            local_file=f"/images/{filename}",
                            tweet_id=0,
                        )
                    else:
                        # Ошибка при загрузке
                        size = random.randint(32, 256)
                else:
                    # Без картинки, но много текста
                    size = random.randint(128, 1024)
            else:
                # Средний объём текста
                size = random.randint(64, 512)

            text = faker.text(size)
            tweet_data = Tweets(
                user_id=user,
                text=text,
            )
            db_manager.session.add(tweet_data)
            db_manager.session.commit()
            if media_data is not None:
                query = select(Tweets.id).order_by(desc(Tweets.id)).limit(1)
                tweet_data = db_manager.session.execute(query)
                tweet_data = tweet_data.scalar()
                media_data.tweet_id = tweet_data
                db_manager.session.add(media_data)
                tweets_with_image.append(tweet_data)
                db_manager.session.commit()
    except DatabaseError as err:
        print(type(err), err, sep="\n")
        db_manager.session.rollback()

    # Прочитать ID твитов
    result = []
    query = select(Tweets.id).order_by(Tweets.id)
    data = db_manager.session.execute(query)
    result.extend(data.scalars().all())

    # Дополним твитами с картинкой (увеличиваем шанс лайка на картинке)
    print("result", len(result), result)
    print("images", len(tweets_with_image), tweets_with_image)
    result.extend(tweets_with_image)
    return result


def prepare_likes(
    max_quantity: int,
    users: list[int],
    tweets: list[int],
) -> list[int]:
    """
    Заполнить таблицу лайков.

    :param max_quantity: Сколько всего лайков сделать (общее количество).
    :param users: Список ID пользователей.
    :param tweets: Список ID твитов.
    :return: Список ID лайков из таблицы likes.
    """
    # Готовим список лайков
    likes: list[Likes] = []
    check_likes: list[tuple[int, int]] = []
    while len(likes) < max_quantity:
        user_id = random.choice(users)
        tweet_id = random.choice(tweets)
        if (user_id, tweet_id) in check_likes:
            continue
        like = Likes(user_id=user_id, tweet_id=tweet_id, name="heart")
        likes.append(like)
        check_likes.append((user_id, tweet_id))

    # Добавляем список в БД
    try:
        db_manager.session.add_all(likes)
        db_manager.session.commit()
    except DatabaseError as err:
        print(type(err), err, sep="\n")
        db_manager.session.rollback()

    # Прочитать ID лайков
    result = []
    query = select(Likes.id).order_by(Likes.id)
    data = db_manager.session.execute(query)
    result.extend(data.scalars().all())
    print("result", len(result), result)
    return result


def add_follow(follower_id: int, following_id: int) -> bool:
    result = False
    try:
        new_follow = Followers.insert().values(
            follower_id=follower_id, following_id=following_id
        )
        db_manager.execute(new_follow)
        db_manager.session.commit()
        result = True
    except SQLAlchemyError as err:
        db_manager.session.rollback()
        print(type(err), err)
    return result


def prepare_follows(
    min_likes: int,
    max_likes: int,
    users: list[int],
) -> list[int]:
    """
    Заполнить таблицу подписок. Берём по количеству кто больше
    лайкнул, тот и подписался. А также лидеры у которого больше лайков,
    на того и подписаны все остальные.

    :param min_likes: Сколько минимально требуется лайков для подписки.
    :param max_likes: Сколько лидеров по лайкам учитывать для подписок.
    :param users: Список ID пользователей.
    :return: Список ID подписок из таблицы follows.
    """
    # Готовим список пользователей, у которых лайков не менее порога
    query = (
        select(
            Likes.tweet_id,
            Tweets.user_id,
            func.count(Likes.user_id).label("count_users"),
        )
        .join(Tweets, Likes.tweet_id == Tweets.id)
        .group_by(Likes.tweet_id, Tweets.user_id)
        .having(func.count(Likes.user_id) >= min_likes)
        .order_by(func.count(Likes.user_id).desc())
    )
    data = db_manager.execute(query)
    # print("data:", data.all())

    # Создадим кеш подписчиков для снижения количества запросов к БД
    followers_result = db_manager.execute(
        select(Followers.c.follower_id, Followers.c.following_id).filter(
            Followers.c.follower_id.in_(users)
        )
    )
    followers = list(
        followers_result.all() if followers_result is not None else None
    )
    print("followers:", followers)

    # Добавляем подписки пользователям, если ещё не подписан
    followers_count = 0
    for rows in data:
        tweet_id, user_id, count_users = rows
        if followers_count >= max_likes:
            # Добавить только лайкнувших подписчиков
            likes_result = db_manager.execute(
                select(Likes.user_id).where(Likes.tweet_id == tweet_id)
            )
            likes = likes_result.scalars().all()
            for follower_id in likes:
                if follower_id == user_id:
                    continue
                if (
                    followers is not None
                    and (follower_id, user_id) in followers
                ):
                    continue
                add_result = add_follow(follower_id, user_id)
                if add_result:
                    followers.append((follower_id, user_id))
        else:
            # Добавить всех в качестве подписчиков
            for follower_id in users:
                if follower_id == user_id:
                    continue
                if (
                    followers is not None
                    and (follower_id, user_id) in followers
                ):
                    continue
                add_result = add_follow(follower_id, user_id)
                if add_result:
                    followers.append((follower_id, user_id))
        followers_count += 1

    # Прочитать ID подписок
    result: list[int] = []
    query = select(Followers.c.id).order_by(Followers.c.id)
    data = db_manager.session.execute(query)
    result.extend(data.scalars().all())
    print("result", len(result), result)
    return result


def main():
    """Подключение к БД и запуск функций для заполнения данных"""
    db_manager.init_db(True)

    users = prepare_users(15)
    # users = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    random.shuffle(users)
    print("users", type(users), users, sep="\n")

    tweets = prepare_tweets(10, users)
    # tweets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
    #           17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
    #           31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44,
    #           45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58,
    #           59, 60, 61, 62, 63, 6, 10, 12, 14, 18, 22, 24, 26, 28,
    #           30, 32, 34, 38, 40, 46, 48, 50, 54, 56, 58, 60]
    random.shuffle(tweets)
    print("tweets", type(tweets), tweets, sep="\n")

    likes = prepare_likes(250, users, tweets)
    # likes = [40, 79, 53, 63, 72, 32, 62, 46, 9, 35, 74, 43, 16, 15, 48,
    #          60, 30, 78, 20, 65, 37, 69, 64, 61, 76, 12, 11, 33, 34, 47,
    #          31, 8, 52, 10, 56, 49, 21, 58, 23, 24, 26, 22, 59, 41, 1,
    #          7, 39, 29, 75, 13, 55, 14, 80, 73, 44, 28, 2, 17, 38, 36,
    #          67, 51, 18, 77, 54, 25, 66, 3, 5, 50, 45, 27, 19, 68, 70, 6,
    #          57, 4, 71, 42]
    random.shuffle(likes)
    print("likes", type(likes), likes, sep="\n")

    follows = prepare_follows(3, 5, users)
    random.shuffle(follows)
    print("follows", type(follows), follows, sep="\n")

    db_manager.close_db()


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()

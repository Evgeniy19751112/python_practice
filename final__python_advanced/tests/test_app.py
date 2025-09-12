""" Тесты для приложения (непосредственно эндпоинты) """

import os
from io import BytesIO
from typing import Optional

import pytest
from fastapi import HTTPException
from pytest_subtests import SubTests
from sqlalchemy import and_, select

from server_app.database import Followers, Likes, Medias, Tweets, Users, crud
from server_app.routers.schemas import (  # noqa
    TweetOutSchema,
    TweetSchema,
    UserBaseSchema,
)
from server_app.routers.utils import get_tweets_list, get_users_list_in_tweets
from server_app.routers.utils.authentication import get_current_user
from server_app.routers.utils.medias import gen_local_filename


@pytest.mark.api
@pytest.mark.parametrize("route", ["/", "/docs", "/redoc", "/login"])
def test_get_methods(client, route):
    """Проверить код возврата 200 для эндпоинтов."""

    response = client.get(route, headers={"api-key": "test"})
    assert response.status_code == 200


@pytest.mark.api
def test_post_api_media_success(client, db, subtests: SubTests) -> None:
    """Отправить файл изображения и получить код возврата 201."""

    file_name = "some_test_image.jpeg"

    # Предварительно убираем файл результата
    image_path = os.getenv("APP_IMAGE_PATH", "/tmp/images")
    file_temp = os.path.join(image_path, file_name)
    if os.path.isfile(file_temp):
        os.remove(file_temp)
    file_result = gen_local_filename(image_path, 1, "jpeg")

    # Отправляем файл
    image_path = os.path.join(os.path.dirname(__file__), "data", file_name)
    files = {
        "file": ("some_test_image.jpeg", open(image_path, "rb"), "image/jpeg")
    }
    headers = {"api-key": "test"}
    response = client.post("/api/medias/", files=files, headers=headers)

    # Проверяем результат
    with subtests.test("Checking response for post media"):
        assert response.status_code == 201
        assert response.json().get("result") is True
        assert response.json().get("media_id", 0) == 6
        assert response.json().get("tweet_id") is None  # Дефолтное значение
        assert os.path.isfile(file_result)


@pytest.mark.api
def test_post_api_media_bad_name(client, db, subtests: SubTests) -> None:
    """
    Отправить что-то двоичное без имени файла и получить код возврата 400.
    """

    files = {"file": ("", BytesIO(b"invalid data"), "image/jpeg")}
    headers = {"api-key": "test"}
    response = client.post("/api/medias/", files=files, headers=headers)

    with subtests.test("Checking response for post bad media"):
        assert response.status_code == 422
        assert "Value error, Expected UploadFile" in response.text


@pytest.mark.api
def test_post_api_tweets(client, db, subtests: SubTests) -> None:
    """
    Отправить твит с тремя файлами разных типов и проверить результат.

    :param client:
    :param db:
    :param subtests:
    :return:
    """

    headers = {"api-key": "test"}
    files = (
        "some_test_image.jpeg",
        "some_test_image.gif",
        "some_test_image.png",
    )
    types = (
        "image/jpeg",
        "image/gif",
        "image/png",
    )

    # Готовим твит
    tweet_data: dict[str, str | list[int]] = {
        "tweet_data": "Some test text.",
        "tweet_media_ids": [],
    }
    for item_file, item_type in zip(files, types):
        image_path = os.path.join(os.path.dirname(__file__), "data", item_file)
        file = {"file": (item_file, open(image_path, "rb"), item_type)}
        response = client.post("/api/medias/", files=file, headers=headers)
        if isinstance(tweet_data["tweet_media_ids"], list):
            tweet_data["tweet_media_ids"].append(
                response.json().get("media_id", 0)
            )
    response = client.post("/api/tweets/", json=tweet_data, headers=headers)

    # Проверяем результат
    with subtests.test("Checking response for post tweets"):
        assert response.status_code == 201
        assert response.json().get("result") is True
        assert response.json().get("tweet_id") is not None


@pytest.mark.api
def test_post_api_tweets_likes(client, db, subtests: SubTests) -> None:
    """Установить лайк для твита."""

    user_id = 1
    headers = {"api-key": "test"}

    # Берём все твиты из БД
    response = db.execute(select(Tweets.id).order_by(Tweets.id))
    if response is not None:
        tweets: list[int] = response.scalars().all()
    else:
        tweets = []
    assert len(tweets) == 5

    # Есть первичные лайки - проверить их наличие
    likes_present = db.execute(
        select(Likes.id).where(
            and_(
                Likes.user_id == user_id,
                Likes.tweet_id.in_([tweet for tweet in tweets]),
            )
        )
    ).scalars()
    if likes_present is not None:
        likes_present = likes_present.all()
    with subtests.test("Check present likes"):
        assert len(likes_present) == 2
        assert likes_present == [1, 3]

    # Добавляем лайки на каждый твит
    for tweet in tweets:
        with subtests.test("Checking response for post likes", tweet=tweet):
            response = client.post(
                f"/api/tweets/{tweet}/likes", headers=headers
            )
            assert response.status_code == 201
            assert response.json().get("result") is True

    # Проверяем лайки в БД
    likes_new = db.execute(
        select(Likes.id).where(Likes.user_id == user_id)
    ).scalars()
    with subtests.test("Check new likes"):
        assert likes_new is not None
        likes_new = likes_new.all()
        assert len(likes_new) == 5
        assert likes_new == [1, 3, 5, 6, 7]


@pytest.mark.api
def test_delete_api_tweets_likes(client, db, subtests: SubTests) -> None:
    """Удалить лайк для твита."""

    headers = {"api-key": "test"}

    # Есть первичные лайки - убирать будем их все
    likes_present: list[Likes] = (
        db.execute(select(Likes).order_by(Likes.id)).scalars().all()
    )
    assert len(likes_present) == 4

    # Делаем попытку убрать каждый лайк
    for num, _ in enumerate(likes_present):
        with subtests.test("Checking response for delete likes", num=num):
            response = client.delete(
                f"/api/tweets/{likes_present[num].tweet_id}/likes",
                headers=headers,
            )
            assert response.status_code == 200
            assert response.json().get("result") is True

    # Проверяем лайки в БД
    likes_new: list[int] = (
        db.execute(select(Likes.id).order_by(Likes.id)).scalars().all()
    )
    assert likes_new is not None
    assert len(likes_new) == 2
    assert likes_new == [2, 4]


@pytest.mark.api
def test_delete_api_tweets_owner(client, db, subtests: SubTests) -> None:
    """Удалить твит владельца и картинки."""

    try_tweet_id = 4
    headers = {"api-key": "second"}

    tweet_present: Optional[Tweets] = crud.read_tweet_by_id(try_tweet_id)
    tweet_id: Optional[int] = (
        None if tweet_present is None else tweet_present.id
    )
    assert tweet_id is not None and tweet_id == try_tweet_id

    response = client.delete(f"/api/tweets/{tweet_id}", headers=headers)
    assert response.status_code == 200
    assert response.json().get("result") is True

    # Проверяем ссылки на файлы в БД
    medias: Optional[list[Medias]] = crud.read_files_by_tweet_id(tweet_id)
    assert medias is not None and len(medias) == 0

    # Проверяем наличие удалённого твита
    tweets: Optional[Tweets] = crud.read_tweet_by_id(tweet_id)
    assert tweets is None


@pytest.mark.api
def test_delete_api_tweets_alien(client, db, subtests: SubTests) -> None:
    """Удалить твит чужой."""

    user_id = 5
    headers = {"api-key": "second"}

    tweet_id: int = db.execute(
        select(Tweets.id).where(Tweets.user_id != user_id).limit(1)
    ).scalar_one_or_none()
    assert tweet_id is not None and tweet_id == 1

    response = client.delete(f"/api/tweets/{tweet_id}", headers=headers)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data.get("result") is False
    assert response_data.get("error_message") is not None
    assert "не принадлежит пользователю" in response_data.get("error_message")

    # Проверяем ссылки на файлы в БД
    medias: list[int] = (
        db.execute(select(Medias.id).where(Medias.tweet_id == tweet_id))
        .scalars()
        .all()
    )
    assert medias is not None and len(medias) == 1

    # Проверяем наличие удалённого твита
    tweets: list[int] = (
        db.execute(select(Tweets.id).where(Tweets.id == tweet_id))
        .scalars()
        .all()
    )
    assert tweets is not None and len(tweets) == 1


@pytest.mark.api
def test_delete_api_tweets_absent(client, db, subtests: SubTests) -> None:
    """Удалить твит не существующий."""

    headers = {"api-key": "test"}
    tweet_id = 100

    response = client.delete(f"/api/tweets/{tweet_id}", headers=headers)
    assert response.status_code == 404
    response_data = response.json()
    assert response_data.get("result") is False
    assert response_data.get("error_message") is not None
    assert "не найден" in response_data.get("error_message")


@pytest.mark.api
def test_post_api_users_follow(client, db, subtests: SubTests) -> None:
    """Проверить работу подписки на пользователя."""
    user_who_follow = 1
    user_for_follow = 5
    headers = {"api-key": "test"}

    response = client.post(
        f"/api/users/{user_for_follow}/follow", headers=headers
    )
    assert response.status_code == 201

    follows: int = db.execute(
        select(Followers.c.id).where(
            and_(
                Followers.c.follower_id == user_who_follow,
                Followers.c.following_id == user_for_follow,
            )
        )
    ).scalar_one_or_none()
    assert follows is not None and follows == 4


@pytest.mark.api
def test_delete_api_users_follow(client, db, subtests: SubTests) -> None:
    """Проверить работу отписки от пользователя."""
    user_who_follow = 3
    user_for_follow = 2
    headers = {"api-key": "team"}

    follows: int = db.execute(
        select(Followers.c.id).where(
            and_(
                Followers.c.follower_id == user_who_follow,
                Followers.c.following_id == user_for_follow,
            )
        )
    ).scalar_one_or_none()
    assert follows is not None and follows == 2

    response = client.delete(
        f"/api/users/{user_for_follow}/follow", headers=headers
    )
    assert response.status_code == 200

    follows = db.execute(
        select(Followers.c.id).where(
            and_(
                Followers.c.follower_id == user_who_follow,
                Followers.c.following_id == user_for_follow,
            )
        )
    ).scalar_one_or_none()
    assert follows is None


@pytest.mark.api
def test_get_api_users_me(client, db, subtests: SubTests) -> None:
    """Проверить работу получения информации о своём профиле."""
    user_id = 4
    headers = {"api-key": "first"}

    user: Users = db.execute(
        select(Users).where(Users.id == user_id)
    ).scalar_one_or_none()
    assert user is not None and user.username == "Mr. First"

    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    response_user = response.json().get("user")
    assert response_user is not None
    assert response_user.get("name") == "Mr. First"
    assert response_user.get("followers") == []
    assert response_user.get("following") == []


@pytest.mark.api
def test_get_api_users(client, db, subtests: SubTests) -> None:
    """
    Проверить работу получения информации о произвольном профиле по его id.
    """
    user_id = 3
    headers = {"api-key": "team"}

    user: Users = db.execute(
        select(Users).where(Users.id == user_id)
    ).scalar_one_or_none()
    assert user is not None and user.username == "team dream"

    response = client.get(f"/api/users/{user_id}", headers=headers)
    assert response.status_code == 200
    response_user = response.json().get("user")
    assert response_user is not None
    assert response_user.get("name") == "team dream"
    assert response_user.get("followers") == []
    assert response_user.get("following") == [
        {"id": 1, "name": "test only"},
        {"id": 2, "name": "dream team"},
    ]


@pytest.mark.parametrize("token", ("dream", "team", "first", "second"))
@pytest.mark.api
async def test_get_current_user_success(client, db, token) -> None:
    """Проверка функции получения данных о пользователе."""
    result = await get_current_user(token=token)
    assert isinstance(result, UserBaseSchema)
    assert result.id > 1
    assert token in result.name.lower()


@pytest.mark.api
async def test_get_current_user_failure(client, db) -> None:
    """
    Проверка функции на ошибку при получении данных
    о не существующем пользователе.
    """
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="incorrect_token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Wrong api-key authentication!"


@pytest.mark.api
async def test_get_users_list_in_tweets_one(client, db) -> None:
    """Получить список пользователей по коду твита."""
    result = await get_users_list_in_tweets(1)
    assert isinstance(result, dict)
    assert result.get(1) is not None
    assert isinstance(result[1], UserBaseSchema)
    assert result[1].name == "test only"


@pytest.mark.api
async def test_get_users_list_in_tweets_list(
    client, db, subtests: SubTests
) -> None:
    """Получить список пользователей по списку кодов твита."""
    test_list = [2, 4, 5]
    result = await get_users_list_in_tweets(test_list)
    assert isinstance(result, dict)
    assert result.get(1) is None
    for user in test_list:
        with subtests.test("Check user by id", user=user):
            assert result.get(user) is not None
            assert isinstance(result[user], UserBaseSchema)
            assert result[user].name != "test only"


@pytest.mark.api
async def test_get_tweets_list(client, db, subtests: SubTests) -> None:
    """Проверка получения списка твитов."""
    result = await get_tweets_list()
    assert isinstance(result, TweetOutSchema)
    assert isinstance(result.tweets, list)
    assert len(result.tweets) == 5
    for tweet in result.tweets:
        with subtests.test("Check all tweets", tweet_id=tweet.id):
            assert isinstance(tweet, TweetSchema)
            assert tweet.author is not None
            assert tweet.author.name is not None
            assert tweet.content is not None
            assert tweet.content[0].isdigit()
            assert tweet.content[1].isupper()
            assert tweet.content[2].islower()

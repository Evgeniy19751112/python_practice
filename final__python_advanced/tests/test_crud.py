""" Тесты для инструментов взаимодействия с базой данных. """

from typing import Any

import pytest
from pytest_subtests import SubTests
from sqlalchemy import func, select, text

import server_app.database.crud as crud
from server_app.database import Medias, Tweets, Users
from server_app.database.db import DatabaseSessionManager


@pytest.mark.db_utils
def test_read_user_by_api_key(
    db: DatabaseSessionManager, subtests: SubTests
) -> None:
    users: dict[str, str] = {
        "test": "test only",
        "dream": "dream team",
        "team": "team dream",
        "first": "Mr. First",
        "second": "Mr. Second",
    }

    for test_user in users:
        with subtests.test("Check user in DB", test_user=test_user):
            user = crud.read_user_by_api_key(test_user)
            assert user is not None
            assert type(user) is Users
            assert user.id != 0
            assert user.username == users.get(test_user, "???")


@pytest.mark.db_utils
def test_read_user_by_id(
    db: DatabaseSessionManager, subtests: SubTests
) -> None:
    user_id: int = 1
    user: list[tuple[int, str]] = crud.read_user_by_id(user_id)
    with subtests.test(f"Check user (ID={user_id}) in DB"):
        assert user is not None
        assert isinstance(user, list)
        assert len(user) == 1
        assert user[0][0] == user_id
        assert user[0][1].startswith("test")


@pytest.mark.db_utils
def test_read_follows_by_query(db: DatabaseSessionManager) -> None:
    query = text("SELECT 10, 'test'")
    data = crud.read_follows_by_query(query)

    assert data is not None
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0].get("id") == 10 and data[0].get("name") == "test"


@pytest.mark.db_utils
def test_read_follower_for_user(
    db: DatabaseSessionManager, subtests: SubTests
) -> None:
    data: list[dict[str, Any]] = crud.read_follower_for_user(2)

    assert data is not None
    assert isinstance(data, list)
    assert len(data) == 2
    control = [
        {"id": 1, "name": "test only"},
        {"id": 3, "name": "team dream"},
    ]
    for num, _ in enumerate(control):
        with subtests.test("Check follower", num=num):
            assert data[num] == control[num]


@pytest.mark.db_utils
def test_following_for_user(
    db: DatabaseSessionManager, subtests: SubTests
) -> None:
    data: list[dict[str, Any]] = crud.read_following_for_user(1)

    assert data is not None
    assert isinstance(data, list)
    assert len(data) == 1
    control = [
        {"id": 2, "name": "dream team"},
    ]
    for num, _ in enumerate(control):
        with subtests.test("Check following", num=num):
            assert data[num] == control[num]


@pytest.mark.db_utils
def test_read_tweets_list(
    db: DatabaseSessionManager, subtests: SubTests
) -> None:
    for num in range(4):
        with subtests.test("Check variants for tweets", num=num):
            match num:
                case 0:
                    data = crud.read_tweets_list()
                    assert data is not None
                    assert isinstance(data, list)
                    assert len(data) == 5
                    assert data[-1].user_id == 4
                    assert data[-1].text.startswith("5Test.")
                case 1:
                    data = crud.read_tweets_list(user_id=1)
                    assert data is not None
                    assert isinstance(data, list)
                    assert len(data) == 5
                    assert data[0].user_id == 2
                    assert data[0].text.startswith("2Three")
                case 2:
                    data = crud.read_tweets_list(offset=1, limit=2)
                    assert data is not None
                    assert isinstance(data, list)
                    assert len(data) == 2
                    assert data[1].user_id == 2
                    assert data[1].text.startswith("2Three")
                case 3:
                    data = crud.read_tweets_list(offset=3, limit=2)
                    assert data is not None
                    assert isinstance(data, list)
                    assert len(data) == 1
                    assert data[0].user_id == 4
                    assert data[0].text.startswith("5Test.")


@pytest.mark.db_utils
def test_read_files_by_tweet_id(
    db: DatabaseSessionManager, subtests: SubTests
) -> None:
    data: list[tuple[int, str, int]] = crud.read_files_by_tweet_id(2)

    assert data is not None
    assert isinstance(data, list)

    with subtests.test("Check media files for tweet"):
        assert len(data) == 2
        assert data[0][0] == 4
        assert data[0][1].startswith("/b")
        assert data[1][0] == 5
        assert data[1][1].startswith("/d")


@pytest.mark.db_utils
def test_read_likes_by_tweet_id(
    db: DatabaseSessionManager, subtests: SubTests
) -> None:
    data: list[tuple[int, int, int, str]] = crud.read_likes_by_tweet_id(1)

    assert data is not None
    assert isinstance(data, list)
    assert len(data) == 2
    for like in data:
        with subtests.test(msg=f"Check like for '{like[1]}'", like=like):
            assert like[3] == "smile"


@pytest.mark.db_utils
def test_create_media_no_params_except(db: DatabaseSessionManager):
    with pytest.raises(ValueError):
        crud.create_media(0)


@pytest.mark.db_utils
def test_create_media_all_params_except(db: DatabaseSessionManager):
    with pytest.raises(ValueError):
        crud.create_media(
            0,
            filename="file",
            local_file="name",
            pairs=[("file", "one"), ("file", "two")],
        )


@pytest.mark.db_utils
def test_create_media_add_one(db: DatabaseSessionManager):
    test_name = "some_test_file.pic"
    before = db.execute(select(Medias).where(Medias.filename == test_name))
    assert before is None or before.scalar_one_or_none() is None

    query = db.execute(select(Tweets.id).order_by(Tweets.id.desc()).limit(1))
    last_tweet = query.scalar_one_or_none() if query is not None else 0
    if last_tweet is None:
        last_tweet = 0

    crud.create_media(tweet_id=last_tweet, local_file=f"/{test_name}")

    after = db.execute(select(Medias).where(Medias.filename == test_name))
    assert after is not None

    after = after.scalar_one_or_none()
    assert type(after) is Medias
    assert after.local_file == f"/{test_name}"
    assert after.filename == test_name
    assert after.tweet_id == last_tweet


@pytest.mark.db_utils
def test_create_media_add_many(db: DatabaseSessionManager):
    files: list[tuple[str, str]] = [
        ("file1.pic", "no/file1.pic"),
        ("file2.pic", "no/file2.pic"),
        ("file3.pic", "no/file3.pic"),
        ("file4.pic", "no/file4.pic"),
        ("file5.pic", "no/file5.pic"),
    ]
    query = db.execute(select(func.count(Medias.id)))
    before_count = query.scalar_one_or_none() if query is not None else None

    crud.create_media(3, pairs=list(files))

    query = db.execute(select(func.count(Medias.id)))
    after_count = query.scalar_one_or_none() if query is not None else None

    assert before_count is not None and after_count is not None
    assert before_count + len(files) == after_count

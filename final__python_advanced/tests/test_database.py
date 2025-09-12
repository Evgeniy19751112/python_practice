""" Тесты для взаимодействия с базой данных. """

import pytest
from pytest_subtests import SubTests
from sqlalchemy import delete, func, insert, select, text
from sqlalchemy.exc import SQLAlchemyError

from server_app.database.db import DatabaseSessionManager, db_manager
from server_app.database.models import Followers, Likes, Medias, Tweets, Users


@pytest.mark.database
def test_db_connection(db: DatabaseSessionManager) -> None:
    """Проверка БД после её инициализации содержит свойства не равные None."""
    assert db is not None
    assert db.engine is not None
    assert db.session is not None
    assert db.engine.connect()


@pytest.mark.database
@pytest.mark.parametrize(
    "table",
    [
        Users.__tablename__,
        Tweets.__tablename__,
        Likes.__tablename__,
        Medias.__tablename__,
        Followers.name,  # Классическое описание модели
    ],
)
def test_table_existence(db: DatabaseSessionManager, table: str) -> None:
    """
    Проверить наличие таблиц в базе данных.

    :param table: Имя таблицы в БД (строка).
    """
    sql = text(
        "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'"
    )
    table_names = []
    result = db.execute(sql)
    if result is not None:
        table_names.extend([row[0] for row in result.fetchall()])
    # result.close()
    assert table in table_names


@pytest.mark.database
def test_permissions(db: DatabaseSessionManager, subtests: SubTests):
    """
    Проверить доступность базы данных для выполнения
    операндов select, insert, update, delete, create, alter.
    Если нет исключений, то всё хорошо.
    """
    query_list: dict[str, str] = {
        # проверяем права create table
        "CREATE": "CREATE TABLE test_table "
        "(id SERIAL PRIMARY KEY, name VARCHAR)",
        # проверяем права alter table
        "ALTER": "ALTER TABLE test_table ADD COLUMN data INT",
        # проверяем права insert
        "INSERT": "INSERT INTO test_table (name, data) "
        "VALUES ('test as test', 123)",
        # проверяем права update
        "UPDATE": "UPDATE test_table SET data=21 WHERE name like 'test%'",
        # проверяем права select
        "SELECT": "SELECT * FROM test_table",
        # проверяем права delete
        "DELETE": "DELETE FROM test_table WHERE data=21",
        # проверяем права drop
        "DROP": "DROP TABLE IF EXISTS test_table",
    }
    for query in query_list.keys():
        with subtests.test("Do query", query=query):
            assert db.execute(text(query_list[query])) is not None


@pytest.mark.database
def test_user_present(db: DatabaseSessionManager) -> None:
    """Проверяем наличие тестового юзера в БД по его api_key."""
    user = db.execute(
        select(Users).where(Users.api_key == "test")
    ).scalar_one_or_none()

    assert user is not None
    assert user.username.startswith("test")
    assert user.id == 1


@pytest.mark.database
@pytest.mark.parametrize(
    "data",
    [
        (Users.id, Users(api_key="test+", username="test only")),
        (Users.id, Users(api_key="dream+", username="dream team")),
        (Users.id, Users(api_key="team+", username="team dream")),
        (Tweets.id, Tweets(user_id=1, text="One Two Three")),
        (Tweets.id, Tweets(user_id=2, text="Three Two One")),
        (Likes.id, Likes(user_id=1, tweet_id=2, name="heart")),
        (Likes.id, Likes(user_id=2, tweet_id=2, name="star")),
        (Likes.id, Likes(user_id=1, tweet_id=1, name="smile")),
        (Likes.id, Likes(user_id=2, tweet_id=1, name="smile")),
        (
            Medias.id,
            Medias(tweet_id=1, filename="nothing1", local_file="anything1"),
        ),
        (
            Medias.id,
            Medias(tweet_id=2, filename="nothing2", local_file="anything2"),
        ),
        (
            Followers.c.id,
            Followers,
            {"follower_id": 1, "following_id": 2},
            {"follower_id": 3, "following_id": 2},
            {"follower_id": 3, "following_id": 1},
        ),
    ],
)
def test_add_data_by_query(db: DatabaseSessionManager, data: tuple) -> None:
    """
    Добавляем данные в каждую из таблиц ожидая, что таблица пустая.
    Исключение - таблица с пользователями (тестовый создан при инициализации).

    :param data: Кортеж из: поле id, для декларативных сущностей экземпляр
        для новой записи, а для классических сущностей непосредственно сам
        объект, но с последующим добавлением словарей для новых записей.
    """
    before_count = db.execute(select(func.count(data[0]))).scalar_one_or_none()
    assert before_count is not None

    wait_rows = 1
    if len(data) == 2:
        db.session.add(data[1])
        db.session.commit()
    elif len(data) >= 3:
        wait_rows = len(data) - 2
        db.execute(insert(data[1]), data[2:])

    after_count = db.execute(select(func.count(data[0]))).scalar_one_or_none()
    assert after_count is not None
    assert before_count + wait_rows == after_count

    if str(type(data[1])) == "<class 'sqlalchemy.sql.schema.Table'>":
        data = db.execute(select(data[0]).order_by(data[0].desc()).limit(1))
        last_id = data.scalar_one_or_none() if data is not None else 0
        assert last_id == after_count
    else:
        assert data[1].id == after_count
        assert "id" in str(data[1])


@pytest.mark.database
@pytest.mark.parametrize(
    "data",
    [
        {
            "user": 1,
            "tweets": [1],
            "likes": [1, 3, 4],
            "media": [1],
            "follows": [1, 3],
        }
    ],
)
def test_delete_data(
    db: DatabaseSessionManager, data: dict, subtests: SubTests
) -> None:
    """
    Проверка каскадного удаления добавленных записей. Ожидается, что
    при удалении пользователя будут удалены все записи, принадлежащие
    ему (твиты (а к ним медиа), лайки, подписки).

    :param data: Словарь, содержащий id пользователя для удаления и
        списки id по каждой таблице, которые ожидаются к удалению.
    """

    def get_id_from_table(table_name: str, key: str) -> list[int]:
        return (
            db.execute(
                text(
                    f"SELECT DISTINCT id FROM {table_name} "
                    f"WHERE {key} ORDER BY id;"
                )
            )
            .scalars()
            .all()
        )

    def get_all_ids_from_tables(user_id: int) -> dict[str, list[int] | int]:
        tweets: list[int] = get_id_from_table("tweets", f"user_id = {user_id}")
        if len(tweets) != 0:
            tweets_key: str = f"tweet_id in ({', '.join(map(str, tweets))})"
        else:
            # "Заглушка", чтобы не усложнять с "... OR ...".
            # Таких записей быть не можно
            tweets_key = "tweet_id IS NULL"
        likes: list[int] = get_id_from_table(
            "likes", f"user_id = {user_id} or {tweets_key}"
        )
        medias: list[int] = get_id_from_table("media", tweets_key)
        followers: list[int] = get_id_from_table(
            "follows", f"follower_id = {user_id} or following_id = {user_id}"
        )
        return {
            "user": user_id,
            "tweets": tweets,
            "likes": likes,
            "media": medias,
            "follows": followers,
        }

    before_count = db.execute(
        select(func.count(Users.id))
    ).scalar_one_or_none()
    with subtests.test("Check before delete"):
        assert before_count is not None
        assert before_count >= 1
        assert data == get_all_ids_from_tables(data.get("user", 0))

    db.execute(delete(Users).where(Users.id == data.get("user", 0)))

    empty: dict[str, list[int] | int] = {
        "user": data.get("user", 0),
        "tweets": [],
        "likes": [],
        "media": [],
        "follows": [],
    }

    after_count = db.execute(select(func.count(Users.id))).scalar_one_or_none()
    with subtests.test("Check after delete"):
        assert after_count is not None
        assert before_count - after_count == 1
        assert empty == get_all_ids_from_tables(data.get("user", 0))


@pytest.mark.database
def test_database_except_sql_error_by_execute(
    db: DatabaseSessionManager,
) -> None:
    """Получаем исключение для БД при ошибке запроса."""
    with pytest.raises(SQLAlchemyError):
        result = db_manager.execute(text("SELECT 1 FROM 1"))
        assert result is None or result.fetchall() is None


@pytest.mark.database
def test_database_except_io_error_by_execute() -> None:
    """Получаем исключение для БД без инициализации."""
    with pytest.raises(IOError):
        db_manager.execute(text("SELECT 1"))

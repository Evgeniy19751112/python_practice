""" Модуль для связи с базой данных приложения """

from typing import Any, Optional

from sqlalchemy import Engine, Executable, create_engine  # noqa
from sqlalchemy.engine import Result
from sqlalchemy.engine.interfaces import _CoreAnyExecuteParams
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from server_app.settings import DATABASE_URL, DEBUG
from server_app.utils import log


class Base(DeclarativeBase):
    """Базовый абстрактный класс для моделей таблиц."""

    __abstract__ = True
    pass


class DatabaseSessionManager:
    """
    Класс для взаимодействия с БД (инициализация, выполнение запросов,
    завершение работы с СУБД).
    """

    def __init__(self) -> None:
        log.debug("Инициализация менеджера СУБД.")
        self._engine: Optional[Engine] = None
        self._session: Optional[Session] = None

    def init_db(self, drop_first: bool = False) -> None:
        """
        Инициализация базы данных. Использует глобальные переменные
        DATABASE_URL (str, ссылка на базу данных) и DEBUG (bool,
        выводить отладочную информацию ORM или нет).

        :param drop_first: Есть истина, то пересоздать все таблицы
        """
        log.debug("Инициализация базы данных.")
        self._engine = create_engine(DATABASE_URL, echo=DEBUG)
        sync_session = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._session = sync_session()

        if drop_first:
            self.drop_db()
        self.create_db()

        log.debug(
            "Инициализация завершена: %s, %s",
            type(self._engine),
            type(self._session),
        )

    def close_db(self) -> None:
        """Закрыть базу данных."""
        log.debug("Закрытие базы данных.")
        if self._engine is None:
            return
        self._engine.dispose()
        self._engine = None
        self._session = None

    def execute(
        self,
        statement: Executable,
        params: Optional[_CoreAnyExecuteParams] = None,
        **kwargs: Any,
    ) -> Result | None:
        """
        Выполнить запрос к БД (text (SQL), select, insert, update, delete).
        Если запрос прошёл успешно, то коммит будет вызван, иначе будет откат.

        :param statement: Непосредственный запрос к БД
        :param params: Параметры для запроса (при необходимости)
        :param kwargs: Продолжение именованных параметров для запроса

        :return: Результат выполнения запроса.

        :raises SQLAlchemyError: Если произошла ошибка при выполнении запроса.
        """
        log.debug("Выполнение запроса.")
        if self._session is None:
            raise IOError("DatabaseSessionManager is not initialized")
        try:
            result = self._session.execute(
                statement=statement, params=params, **kwargs
            )
            self._session.flush()
            self._session.commit()
        except SQLAlchemyError as err:
            log.error("Ошибка выполнения запроса: %s", err, exc_info=True)
            self._session.rollback()
            raise
        return result

    @property
    def session(self):
        return self._session

    @property
    def engine(self):
        return self._engine

    def create_db(self) -> None:
        """Создать таблицы в БД."""
        log.debug("Создать все таблицы в базе данных.")
        Base.metadata.create_all(bind=self._engine)

    def drop_db(self) -> None:
        """Удалить таблицы из БД."""
        log.debug("Удалить все таблицы в базе данных.")
        Base.metadata.drop_all(bind=self._engine)


db_manager = DatabaseSessionManager()


if __name__ == "__main__":
    print(type(db_manager))

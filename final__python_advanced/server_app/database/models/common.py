""" Общий модуль для базовой модели таблиц базы данных. """

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column


class BaseModel:
    """
    Базовый класс для моделей таблиц.

    Attributes:
         id (int): Уникальный код записи
         created_at (datetime): Дата создания записи
         last_edited (datetime): Дата последнего редактирования записи
    """

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
    )
    last_edited: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.utcnow,
    )

    def to_json(self) -> dict[str, Any]:
        return {
            i_column.name: getattr(self, i_column.name)
            for i_column in self.__table__.columns
        }

    def __repr__(self):
        return str(self.to_json())

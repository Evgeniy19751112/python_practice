""" Модуль описания моделей таблиц сведений о файлах. """

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server_app.database import Base

from .common import BaseModel

if TYPE_CHECKING:
    from server_app.database.models.tweet import Tweets


class Medias(BaseModel, Base):
    """
    Модель таблицы для хранения сведений о медиа.

    Attributes:
        filename (str): Имя файла, полученное от клиента
        local_file (str): Имя файла, сохранённое в локальном хранилище,
            где путь указан от корня сайта
        tweet_id (int): ID твита, к которому принадлежит файл
    """

    __tablename__ = "media"

    filename: Mapped[str] = mapped_column(
        unique=False, comment="Имя файла, полученное от клиента"
    )
    local_file: Mapped[str] = mapped_column(
        unique=True, comment="Имя файла, сохранённое в локальном хранилище"
    )
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey(column="tweets.id", ondelete="CASCADE", onupdate="CASCADE"),
        unique=False,
        comment="ID твита, к которому принадлежит файл",
        default=None,
        nullable=True,
    )
    tweet: Mapped["Tweets"] = relationship(  # type: ignore[assignment]
        "Tweets",
        back_populates="media_tweets",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )

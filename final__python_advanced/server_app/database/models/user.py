""" Модуль описания моделей таблиц пользователей и подписчиков. """

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server_app.database import Base

from .common import BaseModel

if TYPE_CHECKING:
    from server_app.database.models.tweet import Tweets


Followers = Table(
    "follows",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True, index=True),
    Column(
        "created_at",
        DateTime,
        server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
    ),
    Column(
        "last_edited",
        DateTime,
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.utcnow,
    ),
    Column(
        "follower_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="ID кто подписался",
    ),
    Column(
        "following_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="ID на кого подписался",
    ),
)


class Users(BaseModel, Base):
    """
    Таблица со сведениями о пользователе.

    Attributes:
        api_key (str): Ключ пользователя (уникальный)
        username (str): Полное ФИО пользователя
    """

    __tablename__ = "users"

    api_key: Mapped[str] = mapped_column(
        unique=True,
        comment="Ключ пользователя для идентификации",
        index=True,
    )
    username: Mapped[str] = mapped_column(
        unique=False, comment="Полное имя пользователя", default="unknown user"
    )
    users_tweets: Mapped[List["Tweets"]] = relationship(  # type: ignore[assignment]  # noqa
        "Tweets",
        back_populates="users",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )
    following: Mapped[List["None"]] = relationship(  # type: ignore[assignment]
        "Users",
        secondary=Followers,
        primaryjoin=lambda: Users.id == Followers.c.follower_id,
        secondaryjoin=lambda: Users.id == Followers.c.following_id,
        backref="follows",
        lazy="selectin",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )

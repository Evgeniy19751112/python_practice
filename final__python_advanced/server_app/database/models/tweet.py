""" Модуль описания моделей таблиц твитов и лайков. """

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server_app.database import Base

from .common import BaseModel

if TYPE_CHECKING:
    from server_app.database.models.media import Medias
    from server_app.database.models.user import Users


class Tweets(BaseModel, Base):
    """
    Таблица с твитами.

    Attributes:
        user_id (int): ID пользователя, который оставил сообщение
        text (str): Текст сообщения твита
    """

    __tablename__ = "tweets"

    user_id: Mapped[int] = mapped_column(
        ForeignKey(column="users.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        comment="ID пользователя, который оставил сообщение",
    )
    text: Mapped[Optional[str]] = mapped_column(
        comment="Текст сообщения твита",
    )

    media_tweets: Mapped[List["Medias"]] = relationship(  # type: ignore[assignment]  # noqa
        "Medias",
        back_populates="tweet",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )
    like_tweets: Mapped[List["Likes"]] = relationship(  # type: ignore[assignment]  # noqa
        "Likes",
        back_populates="tweet",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )
    users: Mapped[Optional["Users"]] = relationship(  # type: ignore[assignment]  # noqa
        "Users",
        back_populates="users_tweets",
        cascade="save-update, merge, delete",
        passive_deletes=True,
    )


class Likes(BaseModel, Base):
    """
    Таблица со сведениями о лайках.

    Attributes:
        user_id (int): ID пользователя, кто лайкнул
        tweet_id (int): ID твита, которое лайкнули
        name (str): Тип лайка (предположительно)
    """

    __tablename__ = "likes"

    user_id: Mapped[int] = mapped_column(
        ForeignKey(column="users.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        comment="ID пользователя, кто лайкнул",
    )
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey(column="tweets.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        comment="ID твита, которое лайкнули",
    )
    name: Mapped[Optional[str]] = mapped_column(
        comment="Тип лайка",
        nullable=True,
    )
    tweet: Mapped[Optional["Tweets"]] = relationship(  # type: ignore[assignment]  # noqa
        "Tweets",
        back_populates="like_tweets",
    )

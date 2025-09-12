""" Модели таблиц для базы данных микроблогов """

from .media import Medias
from .tweet import Likes, Tweets
from .user import Followers, Users

__all__ = ["Medias", "Likes", "Tweets", "Users", "Followers"]

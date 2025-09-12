"""
Модуль, содержащий настройки приложения.
"""

import os
from typing import Optional

import dotenv

# Параметры для базы данных
if os.environ.get("POSTGRES_USER") is None:
    dotenv.load_dotenv()
__DB_USERNAME: Optional[str] = os.getenv("POSTGRES_USER")
__DB_USERPASS: Optional[str] = os.getenv("POSTGRES_PASSWORD")
__DB_HOST: Optional[str] = os.getenv("POSTGRES_HOST")
__DB_DB_NAME: Optional[str] = os.getenv("POSTGRES_DB")
if (
    __DB_USERNAME is None
    or __DB_USERPASS is None
    or __DB_HOST is None
    or __DB_DB_NAME is None
):
    raise ValueError("Нет данных для подключения к БД!")
DATABASE_URL: str = (
    "postgresql+psycopg2://"  # With "asyncpg" something wrong
    f"{__DB_USERNAME}:{__DB_USERPASS}"
    f"@{__DB_HOST}/{__DB_DB_NAME}"
)

# Режим отладки приложения
DEBUG: bool = bool(os.getenv("APP_DEBUG", True))

# Путь для хранения изображений, сохраняемые при добавлении клиентом
IMAGE_PATH: str = os.getenv("APP_IMAGE_PATH", "/usr/share/images")

# Параметры для запуска приложения
HOST: str = "0.0.0.0"
PORT: int = 8000

# Настройки для FastAPI
APP_NAME: str = "Microblogging service"
APP_VERSION: str = "1.0.0"

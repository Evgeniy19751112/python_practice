"""
Модуль "Событий продолжительности жизни".
Взял тут: https://fastapi.tiangolo.com/advanced/events/
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from server_app.database import db_manager
from server_app.utils import log


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Подготовительные и завершающие действия при работе FastAPI."""
    log.debug("Lifespan. Запуск")
    try:
        db_manager.init_db(False)
        yield
    except Exception as err:
        log.error(
            "Lifespan. Исключение: %s, %s",
            err.__class__.__name__,
            str(err),
            exc_info=True,
        )
    finally:
        db_manager.close_db()
    log.debug("Lifespan. Завершение")

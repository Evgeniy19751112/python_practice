"""
Модуль для кеширования работы медленных функций, которые часто требуются.
"""

from functools import wraps
from time import time
from typing import Any, Callable

from server_app.utils import log


def cache_result(timeout: int = 300):
    """
    Декоратор для кэширования результатов функции.

    :param timeout: Максимальное время жизни кэша в секундах
        (по умолчанию 300).
    """

    def decorator(func: Callable) -> Callable:
        cache: dict[tuple, tuple] = {}

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Ключ на основе имени функции и параметров
            key: tuple = (func.__name__, args, tuple(kwargs.items()))
            if key in cache and time() - cache[key][1] <= timeout:
                # Если кэш свежий, вернем сохраненный результат
                log.debug("Данные получены из кеша (%s)", key)
                return cache[key][0]
            else:
                # Выполним функцию и сохраним результат в кэш
                result = func(*args, **kwargs)
                cache[key] = (result, time())
                log.debug("Данные сохранены в кеш (%s)", key)
                return result

        return wrapper

    return decorator

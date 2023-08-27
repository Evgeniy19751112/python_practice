"""
Модуль с декоратором.

Декоратор возвращает ответ (response) из функции в виде словаря.

Использовались базовые знания по декораторам из учебного курса.
Некоторые детали по декораторам вспоминал, в том числе, тут:
https://habr.com/ru/articles/750312/
"""

from functools import wraps
from typing import Callable


def print_result(function: Callable) -> Callable:
    """
    Функция-декоратор. Выводит результат работы функции на консоль.
    Создана как альтернатива классу-декоратору, т.к. не работал для
    методов (кроме статического).

    :param function: Функция декорируемая

    :return: Функция-обёртка
    """

    @wraps(function)
    def wrapper(*args, **kwargs):
        result: str = function(*args, **kwargs)
        try:
            print(result)
        except BaseException as err:
            print('Ошибка вывода данных:', err)
        return result

    return wrapper


class PrintResult:
    """
    Класс-декоратор. Выводит результат работы функции на консоль
    """

    def __init__(self, function: Callable):
        self.function = function

    def __call__(self, *args, **kwargs):
        result = self.function(*args, **kwargs)
        try:
            print(result)
        except BaseException as err:
            print('Ошибка вывода данных:', err)
        return result

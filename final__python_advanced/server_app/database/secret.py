""" Модуль, содержащий функции для защиты ключа в базе данных. """

import hashlib
import os


def get_secret_key(salt: bytes, key: str) -> bytes:
    """
    Получить кодированную форму ключа. Внимание: функция необратимая!

    :param salt: Соль для кодирования
    :param key: Открытый ключ, который надо закодировать

    :return: Хешированные данные нашего ключа
    """
    return hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=key.encode("utf-8"),
        salt=salt,
        iterations=100,  # Желательно не менее 100 тыс.
        dklen=64,
    )


def make_secret_key(open_key: str) -> str:
    """
    Зашифровать открытый ключ. Возвращает 254 знака в шестнадцатеричной
    системе счисления, где каждая пара знаков соответствует байту в
    кодированной строке. + Префикс "=" необходим для идентификации открытых
    и закрытых ключей в БД.
    """
    salt = os.urandom(32)
    key = get_secret_key(salt, open_key)
    return "={}{}{}".format(salt.hex(), key.hex(), os.urandom(31).hex())


def split_secret_key(secret_key: str) -> tuple[str, str]:
    """Разделить секретный ключ на части."""
    return secret_key[1:65], secret_key[65:193]


def verify_secret_key(secret_key: str, open_key: str) -> bool:
    """Сравнить закрытый ключ и открытый."""
    salt, key = split_secret_key(secret_key)
    new_key = get_secret_key(bytes.fromhex(salt), open_key)
    return key == new_key.hex()

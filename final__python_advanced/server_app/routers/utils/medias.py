"""Вспомогательные инструменты для api_medias."""

import os
from datetime import datetime

from server_app.utils import log


def gen_local_filename(base_path: str, user_id: int, extension: str) -> str:
    """
    Формирует уникальное имя файлы в указанном каталоге.
    Возвращает полное имя файла.

    :param base_path: Базовый каталог, где будет создан файл.
    :param user_id: ID пользователя (для снижения шансов повторов имён
        и группировки по абонентам).
    :param extension: Расширение имени файла без ".".

    :return: Полное имя файла, содержащее hex id пользователя,
        hex даты и времени, и hex счётчика для одинаковых имён.
    """
    counter = 0
    while True:
        filename = "".join(
            (
                hex(user_id)[2:],
                hex(int(datetime.now().timestamp()))[2:],
                hex(counter)[2:],
                ".",
                extension,
            )
        )
        file_path = os.path.join(base_path, filename)
        if not os.path.exists(file_path):
            break
        counter += 1
    log.debug("Generated full file name: %s", file_path)
    return file_path


def save_file(file_path: str, data: bytes) -> None:
    """Сохранить двоичный файл."""
    with open(file_path, "wb") as file:
        file.write(data)

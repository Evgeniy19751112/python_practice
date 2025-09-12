""" Модуль синхронного логгера. """

import logging
import os
from logging.handlers import TimedRotatingFileHandler

log_dir = "/var/log/app"


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Поучить логгер с настройками."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '{"time": "%(asctime)s", '
        '"level": "%(levelname)s", '
        '"module": "%(module)s", '
        '"function": "%(funcName)s", '
        '"thread": "%(threadName)s", '
        '"message": "%(message)s", '
        '"lineno": "%(lineno)d"}'
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if level <= logging.WARNING:
        info_file_handler = TimedRotatingFileHandler(
            os.path.join(log_dir, "info.log"),
            when="midnight",
            interval=1,
            backupCount=15,
        )
        info_file_handler.setFormatter(formatter)
        info_file_handler.setLevel(level)
        logger.addHandler(info_file_handler)

    error_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        when="midnight",
        interval=1,
        backupCount=15,
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)
    logger.addHandler(error_file_handler)

    return logger


log = get_logger(__name__, logging.DEBUG)


if __name__ == "__main__":
    # Проверка работы логгера
    log.debug("1 debug")
    log.info("2 info")
    log.warning("3 warning")
    log.error("4 error")
    log.critical("5 crit")

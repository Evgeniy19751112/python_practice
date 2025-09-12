"""Утилиты к приложению, которые не используют ни БД, ни FastAPI."""

from .imghdr import what as what_image_ext  # noqa: F401
from .sync_logger import log  # noqa: F401

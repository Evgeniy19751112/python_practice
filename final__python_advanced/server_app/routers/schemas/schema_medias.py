"""
Схемы описания моделей медиа-файлов.
"""

from .schema_base import SuccessResponse


class MediaUploadSchema(SuccessResponse):
    """
    Схема для загрузки файлов из твита (ответ).

    Attributes:
        media_id (int): ID медиафайла.
        result (bool): Унаследован от родительского класса. Равен True.
    """

    media_id: int


class MediaDownloadSchema(SuccessResponse):
    """
    Схема для загрузки файлов твита (ответ). (???)

    Attributes:
        media_path (str): Ссылка на медиафайл.
        result (bool): Унаследован от родительского класса. Равен True.
    """

    media_path: str

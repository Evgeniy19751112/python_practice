"""
Эндпоинты для /api/medias.

Работа с медиафайлами на бэкэнде.
"""

import os
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.params import File

from server_app.database import Medias, db_manager
from server_app.routers.utils.medias import gen_local_filename, save_file
from server_app.settings import IMAGE_PATH
from server_app.utils import log, what_image_ext

from .schemas import ErrorResponse, MediaUploadSchema, UserBaseSchema
from .utils.authentication import get_current_user

router = APIRouter(prefix="/api", tags=["medias"])


@router.post(
    "/medias",
    status_code=status.HTTP_201_CREATED,
    response_model=MediaUploadSchema,
)
async def post_api_media(
    file: UploadFile = File(  # noqa: B008
        ...,
    ),  # type: ignore[assignment]
    user: Annotated[
        UserBaseSchema, "Текущий пользователь"
    ] = Depends(  # noqa: B008
        get_current_user
    ),
):
    """
    Эндпоинт получения файлов от клиента.

    Сохранить в файл в каталоге для изображений и
    вернуть id зарегистрированного файла в БД.

    -----

    :param file: Файл для приёма от клиента.
    :param user: Текущий пользователь

    :return: Результат сохранения и регистрации файла (см. схемы).
    """
    log.debug(
        "Получить файл от клиента %s.", user.id if user is not None else None
    )
    file_name: Optional[str] = file.filename
    if file_name is None:
        file_name = "unknown"
    image_data: bytes = await file.read()
    file_path: str = gen_local_filename(
        IMAGE_PATH, user.id, what_image_ext(None, image_data)
    )
    try:
        save_file(file_path, image_data)
        media_file = Medias(
            filename=file_name,
            local_file=f"/images/{os.path.basename(file_path)}",
        )
        db_manager.session.add(media_file)
        db_manager.session.commit()
        result = MediaUploadSchema(media_id=media_file.id)
    except FileNotFoundError as err:
        return (
            ErrorResponse(
                error_type=err.__class__.__name__, error_message=str(err)
            ),
            status.HTTP_400_BAD_REQUEST,
        )
    return result

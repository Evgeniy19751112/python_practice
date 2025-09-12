""" Модуль для обработчиков исключений FastAPI. """

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from server_app.utils import log

from .schemas.schema_base import ErrorResponse


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    log.debug("Exception occurred: %s", exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ErrorResponse(
                error_type=exc.__class__.__name__, error_message=str(exc)
            )
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    log.debug("Exception occurred: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            ErrorResponse(
                error_type=exc.__class__.__name__, error_message=str(exc)
            )
        ),
    )


async def other_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    log.debug("Exception occurred: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            ErrorResponse(
                error_type=exc.__class__.__name__, error_message=str(exc)
            )
        ),
    )

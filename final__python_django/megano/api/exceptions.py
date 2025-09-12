import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

from megano import settings

logger = logging.getLogger("api")


class CustomAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An error has occurred"
    default_code = "error"

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail, code=code)


def custom_exception_handler(exc, context):
    """
    Пользовательская функция перехвата ошибок для вывода
    в едином формате в пределах проекта.
    """
    response = exception_handler(exc, context)

    if response is not None:
        logger.warning(
            "Error code %d with message: %s\n",
            response.status_code,
            str(exc),
            exc_info=False,
        )

        response.data = {
            "success": False,
            "status": response.status_code,
            "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "data": str(context) if settings.DEBUG else None,
        }
    else:
        # Для необработанных исключений (500 ошибка)
        logger.error("Unhandled exception: %s\n", str(exc), exc_info=True)

        message = "Internal server error"
        if settings.DEBUG:
            message = message + ": " + str(exc)

        response = Response(
            {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": message,
                "data": str(context) if settings.DEBUG else None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response

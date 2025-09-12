"""
Набор базовых схем для ответов.
"""

from pydantic import BaseModel


class DefaultSchema(BaseModel):
    """
    Схема по умолчанию для всех.
    """

    # class Config:
    #     from_attributes: bool = True
    #     orm_mode: bool = True


class SuccessResponse(DefaultSchema):
    """
    Схема ответа для положительных результатов.

    Attributes:
        result (bool): Положительный результат ответа.
    """

    result: bool = True


class ErrorResponse(DefaultSchema):
    """
    Схема ответа при ошибках. Вернуть тип ошибки и сообщение о ней.

    Attributes:
        result (bool): Отрицательный результат ответа.
        error_type (str): Тип ошибки (или исключения).
        error_message (str): Текст сообщения ошибки.
    """

    result: bool = False
    error_type: str
    error_message: str

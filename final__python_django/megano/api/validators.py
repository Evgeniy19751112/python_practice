import calendar

from rest_framework.exceptions import ValidationError


def validate_sale_date_format(value: str) -> None:
    """
    Валидация даты для полей dateFrom и dateTo при распродажах.
    """
    if value is None:
        return

    error_msg = "Date must be in MM-DD format (ex. '02-28')"

    if len(value) != 5 or value[2] != "-":
        raise ValidationError(error_msg)

    try:
        month = int(value[:2])
        day = int(value[3:])
    except ValueError:
        raise ValidationError(error_msg)

    if month < 1 or month > 12:
        raise ValidationError("Month must be between 01 and 12")

    _, last_day = calendar.monthrange(2000, month)
    if day < 1 or day > last_day:
        raise ValidationError(
            f"Day must be between 01 and {last_day:02d} for month {month:02d}"
        )


def validate_image_size(file_size: int, max_size_mb: float = 5.0) -> None:
    """
    Валидация размера файла.

    :param file_size: Размер файла в байтах
    :type file_size: int
    :param max_size_mb: Максимальный размер файлы в МБ
    :type max_size_mb: float

    :return: None

    :raises: ValidationError - если размер файла превышает предел
    """
    max_size = max_size_mb * 1024 * 1024
    if file_size <= 0 or file_size > max_size:
        raise ValidationError(f"Допустимый размер файла от 0 до {max_size_mb:3.1f}MB")

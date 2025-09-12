import json
import logging
from typing import Any, Optional

from django.http import QueryDict
from rest_framework.request import Request

logger = logging.getLogger("api")


def get_key_from_square_brackets(item: str) -> Optional[tuple[str, str]]:
    """
    Извлечь из входной строки данные до квадратных скобок и в квадратных скобках.
    Примеры результатов работы: "some[name]" => ("some", "name"),
    "some[]" => ("some", None), "some" => None
    """
    if item is None or item == "":
        raise ValueError("item cannot be None")

    if "[" not in item or not item.endswith("]"):
        # Вариант без квадратных скобок
        return None

    main_key, bracket_part = item.split("[", 1)
    inner_key = bracket_part[:-1]
    if inner_key == "":
        inner_key = None
    # print(type(inner_key))

    return main_key, inner_key


def parse_query_params(query_params: QueryDict):
    """
    Парсит параметры запроса в структурированный словарь.
    Пример:
    Вход: {'filter[name]': ['phone'], 'filter[minPrice]': ['0'], 'tags[]': ['1', '2']}
    Выход: {'filter': {'name': 'phone', 'minPrice': '0'}, 'tags': ['1', '2']}
    """
    result = {}

    for key, values in query_params.lists():
        parsed_values = [value for value in values if value != ""]
        if not parsed_values:
            continue

        keys = get_key_from_square_brackets(key)
        if keys:
            main_key, inner_key = keys

            if inner_key:
                # Если внутри скобок есть текст - это ключ словаря
                if main_key not in result:
                    result[main_key] = {}

                # Для случая, когда одно значение - сохраняем как строку,
                # иначе как список
                if len(parsed_values) == 1:
                    result[main_key][inner_key] = parsed_values[0]
                else:
                    result[main_key][inner_key] = parsed_values
            else:
                # Пустые скобки - признак списка
                if main_key not in result:
                    result[main_key] = []

                # Добавляем все значения
                if len(parsed_values) == 1:
                    result[main_key].append(parsed_values[0])
                else:
                    result[main_key].extend(parsed_values)
        else:
            # Обычный ключ без скобок
            if len(values) == 1:
                result[key] = values[0]
            else:
                result[key] = values

    return result


def get_data_from_request(request: Request) -> dict[str, Any]:
    """
    Получаем данные в зависимости от content-type.
    """
    data = {}
    # Для тестирования через браузер, postman или curl облегчаем задачу
    if request.content_type == "application/json" and hasattr(request, "data"):
        data.update(request.data)
    else:
        # x-www-form-urlencoded или другие форматы
        data.update(request.POST.dict())
    if not data and hasattr(request, "query_params"):
        # если POST пустой, пробуем взять из query params
        data.update(parse_query_params(request.query_params))
    # print(type(data), data, len(data), type(data.keys()), type(data.values()))

    # Костыль! В какой-то момент перестала работать логика. В request.data
    # стал получать dict[dict[str, str], list['']].
    # Если в форме только одно поле, и оно похоже на JSON, то его юзаем
    if len(data) == 1 and next(iter(data.values())) == "":
        first_key = next(iter(data))
        # logger.debug(f"First key is {first_key} with type {type(first_key)}")
        try:
            # Пробуем распарсить ключ как JSON
            json_data = json.loads(first_key)
            if isinstance(json_data, dict):
                data = json_data
                # logger.debug("Successfully converted to json\n")
            else:
                logger.warning(f"Unsuccessfully converted to json: {type(json_data)}\n")
                pass
        except json.JSONDecodeError as err:
            logger.error(f"Failed to decode json: {err}\n")
            pass

    # logger.debug(
    #     "'%s' data received. Length = %d objects\nType %s; Data: %s\n",
    #     request.content_type,
    #     len(data),
    #     type(data),
    #     data,
    # )
    return data

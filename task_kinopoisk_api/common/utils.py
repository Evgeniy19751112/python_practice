"""
Это модуль с основной логикой запросов (utils).

1. Класс-исключение для возможных нештатных ситуаций.

2. Класс для подключения к сайту кинопоиска. При инициализации передаётся
базовый URL и токен. Возвращает ответ в формате словаря. Если есть ошибки,
то вызвать исключение.

3. Базовый класс с абстрактными методами получения сведений с сайта
кинопоиск и их выводом через класс сообщений (см. messages.py).

4. Классы-наследники (от 3) для получения определённых сведений с сайта
кинопоиска. Вывод сведений через родительский класс.
"""

from typing import Dict, List, Callable
from requests import Response, request
from abc import ABC, abstractmethod


class TaskNotFound(KeyError):
    """
    Класс-исключение для задач, которые не обозначены как элементы в
    "фабрике задач".
    """
    def __init__(self, message: str) -> None:
        """
        :param message: Текст сообщения об ошибке
        """
        super().__init__('Нет класса-обработчика {}'.format(message))


class ResponseNotOK(ValueError):
    """
    Класс-исключение для ответов с сайта с кодом != 200 (not OK).
    """
    def __init__(self, message: str, code: int) -> None:
        """
        :param message: Текст сообщения об ошибке
        :param code: Код ошибки
        """
        super().__init__('Ответ с кодом {num}: {msg}'.
                         format(num=code, msg=message))


class TakeResponse:
    """
    Получение ответа от сайта с информацией (кинопоиск например).

    arguments:
        timeout (int): Время ожидания ответа от сервера

        response_ok (int): Код ответа об успешном получении информации

    Functions:
        get - Получение ответа от сайта с информацией.
    """
    # В качестве констант время отклика и код ошибки
    timeout: int = 30
    response_ok: int = 200

    def __init__(self, base_url: str, headers: Dict = None) -> None:
        """
        :param base_url: Базовая часть адреса из настроек (например,
        https://api.kinopoisk.dev).

        :param headers: Заголовок запроса для доступа к API сайта.
        """
        self.base_url = base_url
        if headers is None:
            headers = dict()
        self.headers = headers

    def get(self, *params: Dict | str) -> Dict:
        """
        Получение ответа от сайта с информацией.

        :param params: Параметр в формате словаря, для параметрических
        запросов на сайте, и/или часть адреса (каталоги), после базовой
        части.
        :type params: dict | str

        :return: Ответ от сервера
        :rtype: dict

        :raises TypeError: Если указано больше 1 не пустого словаря в
        параметрах.
        :raises ResponseNotOK: Если код ответа получен не равный 200.
        """
        url_parts: List = [self.base_url]
        request_params = dict()
        if params is not None and len(params) > 0:
            if isinstance(params, dict):
                # Указан словарь, следовательно, путь не указан
                request_params = params
            elif isinstance(params, str):
                # Нет словаря, но есть только путь (одна часть)
                url_parts.append(params)
            else:
                # Параметры указаны как кортеж (вероятнее всего). Парсим их
                for i_item in params:
                    if isinstance(i_item, dict):
                        # Допустимо только 1 не пустой словарь!
                        if len(request_params) > 0:
                            # Словарь уже есть - ошибка!
                            raise TypeError('Указано больше 1 параметра '
                                            'типа словарь!')
                        request_params = i_item
                    else:
                        # Вероятнее всего тут будут строки (нет контроля)
                        url_parts.append(i_item)

        # Делаем запрос и возвращаем результат
        url: str = "/".join(url_parts)
        response: Response = request('GET',
                                     url,
                                     headers=self.headers,
                                     params=request_params,
                                     timeout=self.timeout
                                     )
        code: int = response.status_code
        if code != self.response_ok:
            raise ResponseNotOK('Ошибка получения сведений "{}"'.
                                format(response.text), code)
        return response.json()


# Пробуем реализацию фабрики с использованием подклассов
class FactorySubject(ABC):
    """
    Базовый класс для фабрики задач.
    """

    def __init__(self, response_func: Callable):
        """
        Инициализация. Базовый набор объектов

        :param response_func: Функция или метод для получения данных с сайта.
        :type response_func: Callable
        """
        self.response_func = response_func

    @property
    @abstractmethod
    def task_name(self) -> str:
        """
        Свойство - имя задачи (понятное пользователю) для вывода на экран.

        :return: Имя задачи.
        :rtype: str
        """
        return self.__class__.__name__

    @abstractmethod
    def get_response(self, *args: str) -> Dict:
        """
        Метод для выполнения определённого запроса. В каждом
        классе-наследнике параметры запроса определяются индивидуально.

        :param args: Любые параметры строкового типа для передачи в
        функцию дополнительных условий.
        :type args: str

        :return: Ответ в форме словаря
        :rtype: Dict
        """
        return dict()


class GetRandomFilm(FactorySubject):

    @property
    def task_name(self) -> str:
        """
        Наименование класса, понятного пользователю.

        :return: Наименование класса
        """
        return 'информация о случайном фильме'

    def get_response(self) -> Dict:
        """
        Получить информацию о случайном фильме.

        :return: Ответ в форме словаря.
        :rtype: Dict
        """
        return self.response_func('v1', 'movie', 'random')


class GetFullInfoByFilmId(FactorySubject):

    @property
    def task_name(self) -> str:
        """
        Наименование класса, понятного пользователю.

        :return: Наименование класса
        """
        return 'полная информация по id фильма'

    def get_response(self, param_id: str) -> Dict:
        """
        Получить информацию о случайном фильме.

        :param param_id: ID фильма в базе кинопоиска
        :type param_id: str

        :return: Ответ в форме словаря.
        :rtype: Dict
        """
        return self.response_func('v1', 'movie', param_id)


class GetInfoOfSeasons(FactorySubject):

    @property
    def task_name(self) -> str:
        """
        Наименование класса, понятного пользователю.

        :return: Наименование класса
        """
        return 'информация о выходе сезонов и серий'

    def get_response(self) -> Dict:
        """
        Получить информацию о случайном фильме.

        :return: Ответ в форме словаря.
        :rtype: Dict
        """
        return self.response_func('v1', 'season')


class GetReviewsOfFilm(FactorySubject):

    @property
    def task_name(self) -> str:
        """
        Наименование класса, понятного пользователю.

        :return: Наименование класса
        """
        return 'отзывы о фильме'

    def get_response(self) -> Dict:
        """
        Получить информацию о случайном фильме.

        :return: Ответ в форме словаря.
        :rtype: Dict
        """
        return self.response_func('v1', 'review')


class TasksFactory(object):
    """
    Класс, в котором используется возможность языка получить все подклассы
    определённого класса, чтобы создать словарь со всеми доступными
    FactorySubject's.

    Реализация интерфейса формирования меню и выполнения задач.

    Functions:
        get_menu_dict - Получить список зарегистрированных классов.

        get - Получить по имени класса ссылку на данный класс.
    """

    def __init__(self, response_func: Callable):
        self.response_func = response_func
        raw_subclasses: List = FactorySubject.__subclasses__()
        self.classes: Dict = {
            i_elem.__name__: i_elem(self.response_func)
            for i_elem in raw_subclasses
        }

    def get_menu_dict(self) -> Dict:
        """
        Получить список зарегистрированных классов в виде словаря, на
        основе которого можно вывести меню.

        :return: Словарь из зарегистрированных типов.
        :rtype: dict
        """
        result = dict()
        for i_num, i_elem in enumerate(self.classes, 1):
            result[i_num] = {
                'name': self.classes[i_elem].task_name.capitalize(),
                'class': i_elem
            }
        return result

    def get(self, class_name: str) -> FactorySubject:
        """
        Получить по имени класса ссылку на данный класс из словаря,
        который формируется на основе подклассов.

        :param class_name: Имя класса.
        :type class_name: str

        :return: Требуемый экземпляр класса
        :rtype: FactorySubject

        :raise ValueError: Если указан неверный тип объекта в параметрах.
        :raise TaskNotFound: Если такое имя класса не зарегистрировано в
        словаре.
        """

        # Ошибка в параметрах (неверно указан тип данных)
        if type(class_name) != str:
            raise ValueError('class_name must be a string!')

        class_ = self.classes.get(class_name, None)
        if class_ is not None:
            return class_

        # Ошибочка вышла. Вызвать исключение
        raise TaskNotFound(class_name)

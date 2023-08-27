"""
Это модуль с сообщениями (messages).

1. Словари сообщений на русском и английском тексте (словари, где ключи
это коды сообщений, а значения - текст сообщения).

2. Класс для вывода сообщений из словаря (п.1) по кодам, переданных в
параметрах, и с указанием словаря со значениями для вывода текста.
"""

import json
from typing import Dict
from .deco import print_result


# Словарь сообщений на русском языке
__messages_ru: Dict[str, str] = {
    'begin': 'Сборщик информации с сайта Кинопоиск запущен.',
    'end': 'На этом работа завершена. Благодарю за внимание.',
    'menu_exit': '0. Выход из программы',
    'health_result': 'Результат проверки доступа к базе сайта Кинопоиск:',
    'error_input': 'Введены недопустимые данные:',
    'error_response': 'Ошибка получения данных:',
    'query_result': 'Получен ответ:',
    'file_saved': 'Сведения сохранены в'
}

# Словарь сообщений на английском языке
__messages_en: Dict[str, str] = {
    'begin': 'The information collector from the Kinopoisk website has been '
             'launched.',
    'end': 'This completes the work. Thank you for your attention.',
    'menu_exit': '0. Exiting the program',
    'health_result': 'The result of checking access to the Kinopoisk site '
                     'database:',
    'error_input': 'Invalid data entered:',
    'error_response': 'Data acquisition error:',
    'query_result': 'Response received:',
    'file_saved': 'The information is saved in'
}

# Обобщённый набор словарей
_messages: Dict[str, dict] = {
    'RU': __messages_ru,
    'EN': __messages_en
}


# Класс для вывода сообщений из словаря
class ShowMessage:
    """
    Класс для вывода сообщений. При инициализации указывается словарь
    (например, 'RU'), на основе которого будут выбираться сообщения по
    ключу.

    Functions:
        show - Получает сообщение по ключу для последующего вывода.
    """
    def __init__(self, language: str):
        self.language = language.upper()
        self.messages = _messages.get(self.language)
        if self.messages is None:
            self.messages = dict()

    @print_result
    def show(self, message: str, *other_messages: str) -> str:
        """
        Вернуть сообщение для последующего вывода.

        :param message: Текст сообщения, который обязательно должен быть.
        :type message: str

        :param other_messages: Прочие фрагменты текстового сообщения,
        которые перечисляются через пробел после основного и после
        предшествующего фрагмента. Для многострочных сообщений символ
        переноса строки следует ставить вначале переносимой строки.
        :type other_messages: str

        :return: Полное (собранное в одну строку) сообщение.
        :rtype: str
        """

        # Ищем в словаре ключ
        result: str = self.messages.get(message)
        if result is None:
            raise ValueError('Код "{}" не найден в словаре сообщений'.
                             format(message))

        # Дополняем сообщение из кортежа строк
        if other_messages and len(other_messages) > 0:
            text = [result]
            for i_text in other_messages:
                if isinstance(i_text, dict):
                    i_text = json.dumps(i_text, ensure_ascii=False, indent=4)
                else:
                    i_text = str(i_text)
                if i_text in self.messages.keys():
                    text.append(self.messages.get(i_text))
                else:
                    text.append(i_text)
            result = ' '.join(text)

        # Сообщаем результат
        return result

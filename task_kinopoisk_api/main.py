"""
1. Повторили про декораторы. Реализован "print_result".
Выводим в консоль результат работы метода message.show.

2. Сделали импровизированную менюшку и обработчики к ним.

3. Результаты сохраняются в файл JSON. Имя файла по текущей дате/времени.

4. Оформляем и сдаём.
"""

import json
import os.path
import time
from common import (message,
                    site_settings,
                    TakeResponse,
                    TasksFactory,
                    ResponseNotOK
                    )


def main():
    """
    Основная функция, в которой выводится меню и обрабатывается выбор
    пользователя. Сохранения файла выполняется для каждого успешного
    ответа, но без обработчика файловых ошибок.

    :return: None
    """

    # Подгружаем настройки для сайта
    resp_api = TakeResponse(site_settings.host_api,
                            {"accept": "application/json",
                             "X-API-KEY": site_settings.api_key}
                            )

    # Делаем проверку доступа к сайту кинопоиска (в задании нет,
    # но такая проверка логична перед началом работы)
    try:
        res = resp_api.get('v1', 'health')
        message.show('health_result', res.get('status', 'n/a'))
    except ResponseNotOK as err:
        message.show('health_result', err)
        return  # Если сайт не работает, то данные не смогут быть получены

    print()  # Пустая строка в консоль

    # Управление через фабрику задач
    factory = TasksFactory(resp_api.get)
    menu = factory.get_menu_dict()
    while True:
        # Выводим меню
        for i_elem in menu:
            print(i_elem, menu.get(i_elem).get('name'), sep='. ')
        message.show('menu_exit')

        # Запрашиваем вариант действия
        try:
            query = int(input('\nВаш выбор: '))
            if query and query not in menu.keys():
                raise ValueError('Пункт меню {} не найден!\n'.format(query))
        except ValueError as err:
            message.show('error_input', err, '\n')
            continue

        # Проверяем что желает пользователь
        if query == 0:
            # Пользователь уйти желает
            return
        try:
            if query == 2:
                # Для получения сведений требуется ID фильма
                film_id = input('Укажите ID фильма: ')
                result = factory.get(menu.get(query).get('class')).\
                    get_response(film_id)
            else:
                # Не требуется уточнение по запросу
                result = factory.get(menu.get(query).get('class')).\
                    get_response()

            # Сообщить результат
            message.show('query_result', result, '\n')
        except ResponseNotOK as err:
            message.show('error_response', err)
            continue

        # Записать в файл полученный результат
        file_name = time.strftime('%Y-%m-%d_%H-%M-%S') + '.json'
        file_name = os.path.abspath(file_name)
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
        message.show('file_saved', file_name, '\n')


if __name__ == '__main__':
    message.show('begin')
    main()
    message.show('end')

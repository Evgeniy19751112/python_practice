"""
Модуль сервиса голосования. Содержит весь набор функций для реализации.
Для запуска используйте функцию run.
"""

# Словарь для хранения голосов {"предмет для выбора": "счётчик голосов"}
subject_of_voting = dict()


# Функции для выполнения отдельных подзадач

def voting_prepare(param_quantity: int) -> None:
    """
    Подготовить словарь для голосования.
    Выполняется однократно в пределах сеанса работы.

    :param param_quantity: Количество элементов для ввода в словарь.
    :type param_quantity: int

    :return: None
    """

    # Заполняем словарь, пока не достигнем нужного количества ключей
    counter = 1
    while len(subject_of_voting) != param_quantity:
        print("Введите модель", counter, end="")
        model = input("-го автомобиля: ").strip()

        # В словарь добавляем только тогда, когда значение уникально
        if model:
            if model in subject_of_voting:
                print("Такое значение уже есть в словаре!")
            elif model == "0":
                # Явный запрет на значение "0"!
                print("Это значение зарезервировано и не может быть введено!")
            else:
                subject_of_voting[model] = 0
                counter += 1
        else:
            print("Требуется ввести марку и модель автомобиля!")

    # Словарь успешно заполнен
    print("Голосование создано!")
    return


def voting_print_list() -> None:
    """
    Вывести список вариантов для голосования.
    Выполняется перед первым приглашением ввода выбора или после ошибочного
    ввода пользователем.

    :return: None
    """

    print("\nВыберите модель из списка:", end=" ")
    for i_model in subject_of_voting:
        print(i_model, end="; ")
    print("\nДля подсчёта голосов введите 0")
    return


def voting_print_result() -> None:
    """
    Вывести результат голосования.
    Выполняется по завершению голосования.

    :return: None
    """

    print("Голосование завершено!")
    max_key = max(subject_of_voting, key=subject_of_voting.get)
    print("Лучший автомобиль года:", max_key)
    print("Количество голосов:", subject_of_voting[max_key])
    return


def voting_select() -> int:
    """
    Запросить ввода выбранного элемента и увеличить счётчик голосов в
    списке. Используем контроль корректности введённого значения.

    :return: Результат принятия голоса. 1 - голос принят, -1 - голос не
            принят, 0 - закончить голосование.
    :rtype: int
    """

    selection = input("\nВаш выбор: ").strip().lower()
    if selection == "0":
        # Голосование завершено
        return 0
    elif selection not in subject_of_voting:
        print("Такого варианта не существует!")
        return -1

    # Добавить один голос в словарь
    subject_of_voting[selection] += 1
    return 1


# Основная функция для запуска
def run() -> None:
    """
    Запустить процесс голосования.

    :return: None
    """
    print("Голосование за автомобиль года\n")
    quantity = int(input("Сколько моделей авто участвуют в голосовании? "))

    # Сделаем контроль количества на строго больше нуля. Если число не
    # допустимо, то завершить скрипт
    if quantity <= 0:
        print("Введённое значение недопустимо!")
        return

    # Готовим список
    voting_prepare(quantity)

    # Работаем в бесконечном цикле, пока не завершится голосование
    voting_print_list()
    while subject_of_voting:  # Если список не создан, то итераций нет
        result = voting_select()
        if result == 1:
            print("Ваш голос принят!")
        elif result == -1:
            print("Ваш голос не принят из-за ошибки ввода!\n")
            voting_print_list()
        else:
            voting_print_result()
            break

    # Программа завершена. Всем спасибо
    return


# Если запускаем этот файл на выполнение, тогда работаем сразу
if __name__ == "__main__":
    run()

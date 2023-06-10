# https://replit.com/@Evgeniy19751112/MyProfileproject#main.py

SEPARATOR = '-' * 42
ONLY_DIGITS = '0123456789'

# user profile
user_name = ''
user_age = 0
user_phone = '+7'
user_email = ''
user_index = 0
user_address = ''
user_info = ''
# information about the entrepreneur
ogrnip = 0
inn = 0
# bank details
current_account = 0
bank_name = ''
BIC = 0
correspondent_account = 0

def general_info_user(name_parameter, \
                      age_parameter, \
                      phone_parameter, \
                      email_parameter, \
                      info_parameter):
    print(SEPARATOR)
    print('Имя:\t', name_parameter)
    if 11 <= age_parameter % 100 <= 19:
        years_parameter = 'лет'
    elif age_parameter % 10 == 1:
        years_parameter = 'год'
    elif 2 <= age_parameter % 10 <= 4:
        years_parameter = 'года'
    else:
        years_parameter = 'лет'


    print('Возраст:', age_parameter, years_parameter)
    print('Телефон:', phone_parameter)
    print('E-mail:\t', email_parameter)
    print('Индекс:\t' , user_index)
    print('Почтовый адрес:', user_address)
    if user_info:
        print('')
        print('Дополнительная информация:')
        print(info_parameter)

def save_only_this_chars(text_parameter, chars_parameter):
    out_text = ''
    for char in text_parameter:
        if char in chars_parameter:
            out_text += char
    return out_text

def input_with_length_check(length_parameter, message_parameter):
    while True:
        temp_string = input(message_parameter)
        temp_string = save_only_this_chars(temp_string, ONLY_DIGITS)
        if len(temp_string) == length_parameter:
            break
        ending = ''
        if (not length_parameter) or (11 <= length_parameter % 100 <= 19):
          ending = 'ов'
        elif 2 <= length_parameter % 10 <= 4:
          ending = 'а'          
        elif (5 <= length_parameter % 10 <= 9) or (length_parameter % 10 == 0):
          ending = 'ов'
        print(f'Ошибка ввода! Требуется {length_parameter} знак' + ending)
    return temp_string


print('Приложение MyProfile для предпринимателей')
print('Сохраняй информацию о себе и выводи ее в разных форматах')

while True:
    # main menu
    print(SEPARATOR)
    print('ГЛАВНОЕ МЕНЮ')
    print('1 - Ввести или обновить информацию')
    print('2 - Вывести информацию')
    print('0 - Завершить работу')

    option = int(input('Введите номер пункта меню: '))
    if option == 0:
        break

    if option == 1:
        # submenu 1: edit info
        while True:
            print(SEPARATOR)
            print('ВВЕСТИ ИЛИ ОБНОВИТЬ ИНФОРМАЦИЮ')
            print('1 - Личная информация')
            print('2 - Информация о предпринимателе')
            print('0 - Назад')

            option2 = int(input('Введите номер пункта меню: '))
            if option2 == 0:
                break
            if option2 == 1:
                # input general info
                user_name = input('Введите имя: ')
                while 1:
                    # validate user age
                    user_age = int(input('Введите возраст: '))
                    if user_age > 0:
                        break
                    print('Возраст должен быть положительным')

                temp_phone = input('Введите номер телефона (+7ХХХХХХХХХХ): ')
                user_phone = save_only_this_chars(temp_phone, '+' + ONLY_DIGITS)

                user_email = input('Введите адрес электронной почты: ')
                user_index = input_with_length_check(6, 'Введите почтовый индекс: ')
                user_address = input('Введите почтовый адрес (без индекса): ')
                user_info = input('Введите дополнительную информацию:\n')

            elif option2 == 2:
                # input about the entrepreneur
                ogrnip = int(input_with_length_check(15, 'Введите ОГРНИП: '))
                inn = int(input_with_length_check(12, 'Введите ИНН: '))
                # input bank details
                current_account = int(input_with_length_check(20, 'Введите расчётный счёт: '))
                bank_name = input('Введите название банка: ')
                BIC = int(input_with_length_check(9, 'Введите БИК: '))
                correspondent_account = int(input_with_length_check(20, 'Введите корреспондентский счёт: '))
            else: print('Введите корректный пункт меню')
    elif option == 2:
        # submenu 2: print info
        while True:
            print(SEPARATOR)
            print('ВЫВЕСТИ ИНФОРМАЦИЮ')
            print('1 - Личная информация')
            print('2 - Вся информация')
            print('0 - Назад')

            option2 = int(input('Введите номер пункта меню: '))
            if option2 == 0:
                break
            if option2 == 1:
                general_info_user(user_name, user_age, \
                                  user_phone, user_email, user_info)

            elif option2 == 2:
                general_info_user(user_name, user_age, \
                                  user_phone, user_email, user_info)

                # print bank details
                print('')
                print('Информация о предпринимателе')
                print('ОГРНИП:', ogrnip)
                print('ИНН:', inn)
                print('\nБанковские реквизиты')
                print('Расчётный счёт:', current_account)
                print('Название банка:', bank_name)
                print('БИК:', BIC)
                print('Корреспондентский счёт:', correspondent_account)
            else:
                print('Введите корректный пункт меню')
    else:
        print('Введите корректный пункт меню')

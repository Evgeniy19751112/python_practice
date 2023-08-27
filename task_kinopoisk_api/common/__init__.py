"""
Пакет для работы с API сайта Кинопоиск.

Objects:
    site_settings - Экземпляр класса для доступа к настройкам API.

    message - Экземпляр класса ShowMessage для вывода сообщений.
    В параметрах указывается двух-буквенное обозначение языковой группы.
    Вывод сообщений через метод show, где в качестве параметров
    указываются коды сообщений из словаря.
"""
from .messages import ShowMessage
from .settings import SiteSettings
from .utils import TakeResponse, TasksFactory, ResponseNotOK


# Настройки API сайта
site_settings = SiteSettings()

# Управление сообщениями
message = ShowMessage('RU')

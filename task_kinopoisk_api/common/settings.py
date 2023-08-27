"""
Модуль настройки приложения. Настройки интерфейсов доступа к сайту
вынесен в отдельный класс (SiteSettings).

Classes:
    SiteSettings() - класс доступа к настройкам API сайта
"""

import os
from dotenv import load_dotenv
import pydantic
from pydantic import BaseModel


# Грузим настройки приложения
load_dotenv()


class SiteSettings(BaseModel):
    """
    Класс настроек API сайта.
    """
    api_key: pydantic.SecretStr = os.getenv("SITE_API", None)
    host_api: pydantic.StrictStr = os.getenv("HOST_API", None)

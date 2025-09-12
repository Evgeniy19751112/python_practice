import logging

from django.apps import AppConfig

logger = logging.getLogger("api")


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    # def ready(self):
    #     from user.signals import create_profile
    #
    #     logger.debug(create_profile.__name__)
    #     pass

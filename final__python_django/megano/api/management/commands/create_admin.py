import getpass
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()
logger = logging.getLogger("api")


class Command(BaseCommand):
    help = (
        "Создает пользователя-администратора и добавляет его в группу 'Администратор'."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Имя пользователя (логин)",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Email адрес",
        )

    def handle(self, *args, **options):
        username = options["username"] or input("Введите имя пользователя: ")
        email = options["email"] or input("Введите email: ")
        password = getpass.getpass("Введите пароль: ")
        password_confirm = getpass.getpass("Подтвердите пароль: ")

        if password != password_confirm:
            self.stdout.write(self.style.ERROR("Пароли не совпадают."))
            logger.error("Пароли не совпадают при создании администратора.")
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'Пользователь с именем "{username}" уже существует.')
            )
            logger.error(f'Пользователь с именем "{username}" уже существует.')
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'Пользователь с email "{email}" уже существует.')
            )
            logger.error(f'Пользователь с email "{email}" уже существует.')
            return

        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            # Добавляем в группу "Администратор"
            admin_group, created = Group.objects.get_or_create(name="Администратор")
            user.groups.add(admin_group)
            user.is_superuser = False
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Суперпользователь "{username}" создан и добавлен '
                    'в группу "Администратор".'
                )
            )
            logger.info(
                f'Суперпользователь "{username}" создан и добавлен в '
                'группу "Администратор".'
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при создании пользователя: {e}")
            )
            logger.error(f"Ошибка при создании пользователя: {e}")

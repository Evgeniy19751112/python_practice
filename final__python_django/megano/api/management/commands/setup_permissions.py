import logging

from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

logger = logging.getLogger("api")


class Command(BaseCommand):
    help = (
        "Создает группы 'Администратор' и 'Покупатель' и "
        "настраивает для них права доступа."
    )

    def handle(self, *args, **options):
        # Словари с названиями групп и их разрешениями
        GROUPS_PERMISSIONS = {
            "Администратор": {
                # Все действия для всех моделей, кроме User и Group
                # добавим все разрешения, кроме тех, что связаны с User и Group
            },
            "Покупатель": {
                # Разрешения для чтения и создания
                "auth": ["add_user", "view_user"],
                "user": [
                    "view_profile",
                    "add_profile",
                    "change_profile",
                    "delete_profile",
                ],
                "product": [
                    "view_categories",
                    "view_subcategories",
                    "view_tags",
                    "view_product",
                    "view_review",
                    "view_specifications",
                    "view_sale",
                    "view_imagesproduct",
                    "view_imagessale",
                    "view_imagescategories",
                    "add_product",
                    "add_review",
                    "add_sale",
                    "add_categories",
                    "add_subcategories",
                    "add_tags",
                    "add_specifications",
                    "add_imagesproduct",
                    "add_imagessale",
                    "add_imagescategories",
                ],
                "order": [
                    "view_order",
                    "view_orderproduct",
                    "add_order",
                    "add_orderproduct",
                    "delete_order",
                    "delete_orderproduct",
                ],
                "basket": [
                    "view_basketitem",
                    "add_basketitem",
                    "delete_basketitem",
                ],
                "avatar": [
                    "view_imagesavatar",
                    "add_imagesavatar",
                    "change_imagesavatar",
                    "delete_imagesavatar",
                ],
            },
        }

        # Создаем группы
        for group_name in GROUPS_PERMISSIONS.keys():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Группа "{group_name}" создана.'))
                logger.info(f'Группа "{group_name}" создана.')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Группа "{group_name}" уже существует. Будет обновлена.'
                    )
                )
                logger.info(f'Группа "{group_name}" уже существует. Будет обновлена.')
                # Очищаем существующие разрешения перед добавлением новых
                group.permissions.clear()

            # Получаем список разрешений для группы
            if group_name == "Администратор":
                # Администратор: все разрешения, кроме управления пользователями
                # и группами
                excluded_apps = ["auth", "contenttypes", "sessions", "admin"]
                excluded_models = ["user", "group", "permission", "contenttype"]

                for app_config in apps.get_app_configs():
                    if app_config.name in excluded_apps:
                        continue
                    for model in app_config.get_models():
                        if model._meta.model_name in excluded_models:
                            continue
                        content_type = ContentType.objects.get_for_model(model)
                        for codename in ["add", "change", "delete", "view"]:
                            permission_codename = f"{codename}_{model._meta.model_name}"
                            try:
                                permission = Permission.objects.get(
                                    codename=permission_codename,
                                    content_type=content_type,
                                )
                                group.permissions.add(permission)
                            except Permission.DoesNotExist:
                                logger.warning(
                                    f"Разрешение {permission_codename} не найдено."
                                )
                                continue

                # Добавляем разрешения на просмотр пользователей
                # и групп (но не на изменение/удаление)
                for model_name in ["user", "group"]:
                    content_type = ContentType.objects.get(
                        app_label="auth", model=model_name
                    )
                    view_permission = Permission.objects.get(
                        codename=f"view_{model_name}",
                        content_type=content_type,
                    )
                    group.permissions.add(view_permission)

            else:
                # Покупатель: только указанные разрешения
                for app_label, perms in GROUPS_PERMISSIONS[group_name].items():
                    for perm_codename in perms:
                        try:
                            permission = Permission.objects.get(
                                codename=perm_codename,
                                content_type__app_label=app_label,
                            )
                            group.permissions.add(permission)
                        except Permission.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'Разрешение "{perm_codename}" '
                                    f'для приложения "{app_label}" не найдено.'
                                )
                            )
                            logger.error(
                                f'Разрешение "{perm_codename}" '
                                f'для приложения "{app_label}" не найдено.'
                            )

            group.save()
            self.stdout.write(
                self.style.SUCCESS(f'Права для группы "{group_name}" настроены.')
            )

        self.stdout.write(self.style.SUCCESS("Настройка групп и прав завершена."))
        logger.info("Настройка групп и прав завершена.")

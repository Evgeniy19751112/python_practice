import logging

# from django.db.models.signals import post_save
# from django.dispatch import receiver

# from .models import ImagesAvatar, Profile

logger = logging.getLogger("api")


# @receiver(post_save, sender=Profile)
# def create_profile(sender, instance, created=None, **kwargs):
#     if instance.avatar is None:
#         instance.avatar = ImagesAvatar.objects.create()
#         instance.save()

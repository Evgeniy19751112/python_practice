from django.contrib import admin

from .forms import ImagesAvatarForm, ProfileForm
from .models import (
    ImagesAvatar,
    Profile,
)

# Register your models here.


@admin.register(ImagesAvatar)
class ImagesAvatarAdmin(admin.ModelAdmin):
    form = ImagesAvatarForm
    list_display = ("id", "src", "alt")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileForm
    list_display = ("id", "user", "fullName", "phone", "user__email")
    list_display_links = ("id", "user", "fullName")
    ordering = ("id",)
    search_fields = ("user__username", "fullName", "phone", "user__email")
    empty_value_display = "-empty-"

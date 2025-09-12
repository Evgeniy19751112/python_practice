from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import (
    ChangeAvatarView,
    ProfilePasswordSetView,
    ProfileView,
    SignInView,
    SignUpView,
)

app_name = "user"

urlpatterns = [
    path("sign-in", SignInView.as_view(), name="sign-in"),
    path("sign-up", SignUpView.as_view(), name="sign-up"),
    path("sign-out", LogoutView.as_view(), name="sign-out"),
    path("profile", ProfileView.as_view(), name="profile"),
    path("profile/", ProfileView.as_view(), name="profile.get"),
    path("profile/password", ProfilePasswordSetView.as_view(), name="password.set"),
    path("profile/avatar", ChangeAvatarView.as_view(), name="avatar.change"),
]

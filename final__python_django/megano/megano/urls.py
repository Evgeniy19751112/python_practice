"""
URL configuration for megano project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import logging

from api.exceptions import CustomAPIException
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from rest_framework import status

logger = logging.getLogger("api")


def serve_custom_static(request, path=None, document_root=None, *args, **kwargs):
    """Кастомная view для отдачи статики с логированием для отладки."""
    # logger.debug("request: %s %s", type(request), request)
    # logger.debug("path: %s %s", type(path), path)
    # logger.debug("root_path: %s %s", type(document_root), document_root)
    # Если path не передан (например, из re_path), берём из request.path
    if path is None:
        path = request.path.lstrip("/")

    if document_root is None:
        document_root = f"{settings.STATIC_ROOT}/{document_root}"
    else:
        document_root = settings.STATIC_ROOT

    try:
        logger.debug("document_root: %s", document_root)
        return serve(request, path, document_root=document_root)
    except FileNotFoundError as e:
        logger.error(e, exc_info=True)
        raise CustomAPIException(detail=str(e), status_code=status.HTTP_404_NOT_FOUND)
        # return HttpResponseNotFound()


urlpatterns = [
    path("", include("frontend.urls")),
    path("admin/", admin.site.urls),
    # path("api/", include("api.urls")),
    path("api/", include("user.urls")),
    path("api/", include("product.urls")),
    path("api/", include("order.urls")),
    # Обработка статических файлов в корне сайта
    re_path(
        r"^favicon\.ico$",
        serve,
        {"path": "favicon.ico", "document_root": settings.STATIC_ROOT / "frontend"},
    ),
    re_path(
        r"^(\w+\.(png|jpe?g|gif|webp|svg))$",
        view=serve_custom_static,
        name="serve_custom_static",
    ),
]

if settings.DEBUG:
    urlpatterns.extend(
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    )
    urlpatterns.extend(static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))

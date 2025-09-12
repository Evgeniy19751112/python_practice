import logging

from django.http import JsonResponse
from rest_framework import status

from megano import settings

logger = logging.getLogger("api")


class CustomErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        logger.error("Middleware caught exception: %s", str(exception), exc_info=True)

        message = "Internal server error"
        if settings.DEBUG:
            message = message + ": " + str(exception)

        return JsonResponse(
            {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": message,
                "data": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

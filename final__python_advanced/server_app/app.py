"""
Основной модуль программы.
Пример запуска (как отдельный сервис):
    uvicorn --reload app:app --host=0.0.0.0 --port=8000
"""

import uvicorn
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request

from server_app.main_app import app
from server_app.routers import api_except, api_medias, api_tweets, api_users
from server_app.settings import DEBUG, HOST, PORT
from server_app.utils import log


@app.get("/", include_in_schema=False)
async def root(request: Request = None):
    """Стартовая страница просто информирует о документации к API"""
    info = (
        (
            f"Получен запрос от хоста \"{request.headers.get('host')}\" "
            f"по URL \"{request.headers.get('referer')}\" "
            f"от агента \"{request.headers.get('user-agent')}\"."
        )
        if request is not None
        else "n/a"
    )
    log.debug("Root page: %s", info)
    return {"message": "Use /docs or /redoc to get documentation"}


@app.get("/login")
async def login(request: Request = None):
    info = (
        (
            f"Получен запрос от хоста \"{request.headers.get('host')}\" "
            f"по URL \"{request.headers.get('referer')}\" "
            f"от агента \"{request.headers.get('user-agent')}\"."
        )
        if request is not None
        else "n/a"
    )
    log.debug("Login page: %s", info)
    return {"message": "Login page"}


app.include_router(api_tweets)
app.include_router(api_users)
app.include_router(api_medias)

app.add_exception_handler(
    RequestValidationError,
    api_except.validation_exception_handler,  # type: ignore[arg-type]
)
app.add_exception_handler(
    HTTPException, api_except.http_exception_handler  # type: ignore[arg-type]
)
app.add_exception_handler(Exception, api_except.other_exception_handler)


if __name__ == "__main__":
    log.info("Starting server")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=DEBUG)
    log.info("Server finish")

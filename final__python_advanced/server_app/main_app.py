from fastapi import FastAPI

from server_app.routers.api_lifespan import lifespan
from server_app.settings import APP_NAME, APP_VERSION, DEBUG

app: FastAPI = FastAPI(
    debug=DEBUG,
    title=APP_NAME,
    description="Бэкенд приложения для корпоративного сервиса микроблогов",
    tracemalloc=True,
    version=APP_VERSION,
    lifespan=lifespan,
)

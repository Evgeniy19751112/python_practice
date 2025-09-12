# Обходим ошибку "ImportError: attempted relative import beyond
# top-level package"
from .settings import IMAGE_PATH  # noqa: F401

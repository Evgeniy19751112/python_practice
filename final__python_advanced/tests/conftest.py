import pytest
from fastapi.testclient import TestClient

from server_app.app import app as _app
from server_app.database import db_manager
from tests.utils import fake_some_data


@pytest.fixture(scope="function", autouse=False)
def db():
    db_manager.init_db(drop_first=True)
    fake_some_data(db_manager)

    yield db_manager

    db_manager.close_db()


@pytest.fixture(autouse=True)
def app():
    yield _app


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://test") as client:
        yield client


if __name__ == "__main__":
    print("test app")

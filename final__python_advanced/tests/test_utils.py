"""Тестирование вспомогательных функций."""

import os

import pytest
from pytest_subtests import SubTests

from server_app.database import secret
from server_app.routers.utils.medias import gen_local_filename
from server_app.utils import imghdr


@pytest.mark.parametrize("base_path", ["/tmp/images", "/var/local/app"])
@pytest.mark.parametrize("user_id", [1, 12, 150])
@pytest.mark.parametrize("extension", [".jpg", ".png", ".gif"])
@pytest.mark.utils
def test_gen_local_filename(
    base_path, user_id, extension, subtests: SubTests
) -> None:
    result = gen_local_filename(base_path, user_id, extension)
    path = os.path.dirname(result)
    name, ext = os.path.splitext(os.path.basename(result))
    assert path == base_path
    assert name.startswith(hex(user_id)[2:])
    assert ext == extension


@pytest.mark.parametrize(
    "file_for_test",
    [
        "some_test_image.gif",
        "some_test_image.jpeg",
        "some_test_image.png",
        "some_test_image.bmp",
        "some_test_image.webp",
        "some_test_image.tiff",
    ],
)
@pytest.mark.utils
def test_imghdr_what_file(file_for_test: str, subtests: SubTests) -> None:
    file_name = os.path.join(os.path.dirname(__file__), "data", file_for_test)
    result = imghdr.what(file=file_name, h=None)
    assert result == os.path.splitext(file_for_test)[1][1:]


@pytest.mark.parametrize(
    "file_for_test",
    [
        "some_test_image.gif",
        "some_test_image.jpeg",
        "some_test_image.png",
        "some_test_image.bmp",
        "some_test_image.webp",
        "some_test_image.tiff",
    ],
)
@pytest.mark.utils
def test_imghdr_what_stream(file_for_test: str, subtests: SubTests) -> None:
    file_name = os.path.join(os.path.dirname(__file__), "data", file_for_test)
    with open(file_name, "rb") as file:
        data = file.read()
        result = imghdr.what(file=None, h=data)
    assert result == os.path.splitext(file_for_test)[1][1:]


@pytest.mark.utils
def test_split_secret_key(subtests: SubTests) -> None:
    prefix = "="
    salt_real = "0a" * 32
    salt_fake = "1f" * 31
    some_key = "2k" * 64
    key_data = f"{prefix}{salt_real}{some_key}{salt_fake}"
    new_data = secret.split_secret_key(key_data)
    with subtests.test("Check split secret key"):
        assert new_data[0] == salt_real
        assert new_data[1] == some_key


@pytest.mark.utils
def test_verify_secret_key(subtests: SubTests) -> None:
    open_key = "1a"
    first_key = secret.make_secret_key(open_key)
    second_key = secret.make_secret_key(open_key.upper())
    with subtests.test("Verify secret keys"):
        assert len(first_key) == len(second_key)
        assert first_key != second_key
        assert secret.verify_secret_key(first_key, open_key) is True
        assert secret.verify_secret_key(second_key, open_key) is False

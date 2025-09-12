from pathlib import Path

from django.http import QueryDict
from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.utils import json

from .services import (
    get_key_from_square_brackets,
    parse_query_params,
)
from .validators import validate_image_size, validate_sale_date_format

# Путь к фикстурам
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> json:
    """
    Загрузить файл фикстуры (json) и вернуть его содержимое.

    :param filename: Имя файла для загрузки (json, utf-8)
    """
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


class ValidatorsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.max_size: float = 1.5

    @classmethod
    def tearDownClass(cls):
        pass

    def test_validate_image_size(self):
        """Проверить валидацию размера файла."""
        self.assertIsNone(validate_image_size(1024, self.max_size))
        self.assertIsNone(validate_image_size(1024 * 1024, self.max_size))
        with self.assertRaises(ValidationError):
            validate_image_size(1024 * 1024 * 2, self.max_size)

    def test_validate_sale_date_format(self):
        """Проверить валидацию формата даты 'ММ-ДД' для таблицы распродаж."""
        correct_dates = (
            "01-01",
            "01-31",
            "02-28",
            "03-31",
            "04-30",
            "05-31",
            "06-30",
            "07-31",
            "08-31",
            "09-30",
            "10-31",
            "11-30",
            "12-31",
        )
        for check_date in correct_dates:
            self.assertIsNone(
                validate_sale_date_format(check_date),
                f"Check date format: {check_date}",
            )

        incorrect_dates = (
            "",
            "0-0",
            "00000",
            "00-00",
            "00-01",
            "31-01",
            "02-30",
            "03-32",
            "04-32",
            "05-32",
            "06-32",
            "07-32",
            "08-32",
            "09-31",
            "10-32",
            "11-31",
            "12-32",
            "13-13",
        )
        for check_date in incorrect_dates:
            with self.assertRaises(ValidationError):
                validate_sale_date_format(check_date)


class ServicesTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.request_factory = RequestFactory()

    def test_get_key_with_brackets(self):
        self.assertEqual(get_key_from_square_brackets("some[name]"), ("some", "name"))
        self.assertEqual(get_key_from_square_brackets("some[]"), ("some", None))
        self.assertIsNone(get_key_from_square_brackets("some"))
        self.assertIsNone(get_key_from_square_brackets("some[name]extra"))

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            get_key_from_square_brackets(None)
        with self.assertRaises(ValueError):
            get_key_from_square_brackets("")

    def test_parse_simple_params(self):
        query = QueryDict("filter[name]=phone&filter[minPrice]=0&tags[]=1&tags[]=2")
        expected = {"filter": {"name": "phone", "minPrice": "0"}, "tags": ["1", "2"]}
        self.assertEqual(parse_query_params(query), expected)

    def test_parse_empty_values(self):
        query = QueryDict("filter[name]=phone&filter[minPrice]=0&tags[]=1&tags[]=")
        expected = {"filter": {"name": "phone", "minPrice": "0"}, "tags": ["1"]}
        self.assertEqual(parse_query_params(query), expected)

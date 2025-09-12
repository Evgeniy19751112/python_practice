from pathlib import Path

from django.contrib.auth.models import User
from django.db.transaction import atomic
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.utils import json

from .models import Profile

# Путь к фикстурам
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> json:
    """
    Загрузить файл фикстуры (json) и вернуть его содержимое.

    :param filename: Имя файла для загрузки (json, utf-8)
    """
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


class SignViewTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = APIClient()
        cls.signup_url = reverse("user:sign-up")
        cls.content_type = "application/x-www-form-urlencoded"

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        """
        Подготовим данные перед каждым тестом.
        """
        self.data = {
            "username": "testuser",
            "password": "-PASSWORD-",
            "name": "Test User",
            "email": "net@tutorial.local",
        }

    def test_signup_success(self):
        """
        Тест успешной регистрации пользователя.
        """
        response = self.client.post(
            path=self.signup_url,
            data=json.dumps(self.data, ensure_ascii=False),
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with atomic():
            self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_signup_fail_username(self):
        """
        Тест ошибки регистрации без логина (username)
        """
        self.data.pop("username", None)
        response = self.client.post(
            path=self.signup_url,
            data=json.dumps(self.data, ensure_ascii=False),
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        with atomic():
            self.assertFalse(User.objects.filter(email="net@tutorial.local").exists())

    def test_signup_fail_double(self):
        """
        Тест отказа регистрации пользователя с повторяющимся именем.
        """
        response = self.client.post(
            path=self.signup_url,
            data=json.dumps(self.data, ensure_ascii=False),
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with atomic():
            self.assertTrue(User.objects.filter(username="testuser").exists())

        self.data["email"] = "net@tutorial.double"
        response = self.client.post(
            path=self.signup_url,
            data=json.dumps(self.data, ensure_ascii=False),
            content_type=self.content_type,
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(User.objects.filter(email="net@tutorial.double").exists())


class SignInViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="testpass123")
        cls.signin_url = reverse("user:sign-in")

    def test_signin_success(self):
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(
            self.signin_url,
            data=json.dumps(data),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_signin_success_with_json(self):
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(
            self.signin_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_signin_fail(self):
        data = {"username": "wronguser", "password": "wrongpass"}
        response = self.client.post(
            self.signin_url,
            data=json.dumps(data),
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="profileuser", password="profilepass", email="profile@example.com"
        )
        cls.profile = Profile.objects.create(
            user=cls.user, fullName="Test User", phone="1234567890"
        )
        cls.profile_url = reverse("user:profile")

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fullName"], "Test User")
        self.assertEqual(response.data["email"], "profile@example.com")

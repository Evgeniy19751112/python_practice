from pathlib import Path

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.utils import json
from user.models import Profile

from .models import (
    Categories,
    ImagesCategories,
    Product,
    Review,
    Tags,
)

# Путь к фикстурам
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> json:
    """
    Загрузить файл фикстуры (json) и вернуть его содержимое.

    :param filename: Имя файла для загрузки (json, utf-8)
    """
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


class DatabaseOperationsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = User.objects.create_user(
            username="dbtestuser", password="dbtestpass123", email="dbtest@example.com"
        )
        cls.profile = Profile.objects.create(
            user=cls.user, fullName="Test User", phone="1234567890"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_create_and_retrieve_product(self):
        # Загрузка тестовых данных
        product_data = load_fixture("product_data.json")

        # Создание продукта
        product = Product.objects.create(
            title=product_data["title"],
            price=product_data["price"],
            count=product_data["count"],
            description=product_data["description"],
            fullDescription=product_data["fullDescription"],
            freeDelivery=product_data["freeDelivery"],
            rating=product_data["rating"],
            category=Categories.objects.create(title=product_data["category"]["title"]),
        )

        # Создание связанных объектов
        tag = Tags.objects.create(name=product_data["tags"][0]["name"])
        product.tags.add(tag)

        # Проверка создания продукта
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(product.title, product_data["title"])

        # Проверка получения продукта через API
        response = self.client.get(
            reverse("product:product.details", args=[product.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка структуры ответа
        response_data = response.data
        self.assertEqual(response_data["title"], product_data["title"])
        self.assertEqual(float(response_data["price"]), product_data["price"])
        self.assertEqual(response_data["freeDelivery"], product_data["freeDelivery"])

    def test_create_and_retrieve_review(self):
        # Создаем продукт для отзыва
        product = Product.objects.create(
            title="Test Product",
            price=100.00,
            count=10,
            description="Test description",
            fullDescription="Full test description",
            freeDelivery=True,
            rating=0,
            category=Categories.objects.create(title="Test Category"),
        )

        # Загрузка данных отзыва
        review_data = load_fixture("review_data.json")

        # Создание отзыва
        review = Review.objects.create(
            author=self.user,
            email=review_data["email"],
            text=review_data["text"],
            date=review_data["date"],
        )
        product.reviews.add(review)

        # Проверка создания отзыва
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(review.text, review_data["text"])

        # Проверка получения отзыва через API
        response = self.client.get(
            reverse("product:product.details", args=[product.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["reviews"]), 1)
        self.assertEqual(response.data["reviews"][0]["text"], review_data["text"])

    def test_create_and_retrieve_category(self):
        # Загрузка данных категории
        category_data = load_fixture("category_data.json")

        # Создание изображения для категории
        image = ImagesCategories.objects.create(
            src="app/category_test.jpg",
            alt=category_data["image"]["alt"],
        )

        # Создание категории
        category = Categories.objects.create(title=category_data["title"], image=image)

        # Проверка создания категории
        self.assertEqual(Categories.objects.count(), 1)
        self.assertEqual(category.title, category_data["title"])

        # Проверка получения категории через API
        response = self.client.get(reverse("product:categories"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], category_data["title"])


class BannersViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Categories.objects.create(title="Test Category")
        cls.banners_url = reverse("product:banners")

        for i in range(10):
            Product.objects.create(
                title=f"Banner Product {i}",
                price=100 * (i + 1),
                count=10,
                category=cls.category,
            )

    def test_get_banners(self):
        response = self.client.get(self.banners_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)


class TagsViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tag1 = Tags.objects.create(name="Tag 1")
        cls.tag2 = Tags.objects.create(name="Tag 2")
        cls.tags_url = reverse("product:tags")

    def test_get_tags(self):
        response = self.client.get(self.tags_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)
        self.assertIsInstance(response.data[0], dict)
        self.assertEqual(response.data[0], {"id": 1, "name": "Tag 1"})
        self.assertIsInstance(response.data[1], dict)
        self.assertEqual(response.data[1], {"id": 2, "name": "Tag 2"})

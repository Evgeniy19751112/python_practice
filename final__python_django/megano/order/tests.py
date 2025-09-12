from pathlib import Path

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.utils import json
from user.models import Profile

from .models import Categories, Order, OrderProduct, Product

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

    def test_create_and_retrieve_order(self):
        # Создаем тестовые данные
        product = Product.objects.create(
            title="Order Product",
            price=50.00,
            count=5,
            description="Product for order",
            freeDelivery=True,
            rating=4.5,
            category=Categories.objects.create(title="Test Category"),
        )

        # Загрузка данных заказа
        order_data = load_fixture("order_data.json")

        # Создание товара в заказе
        order_product = OrderProduct.objects.create(
            title=product.title,
            price=product.price,
            count=2,
            description=product.description,
            freeDelivery=product.freeDelivery,
            rating=product.rating,
            category=product.category,
        )
        order_product.tags.set(product.tags.all())

        # Создание заказа
        order = Order.objects.create(
            user=self.user,
            createdAt=order_data["createdAt"],
            fullName=order_data["fullName"],
            email=order_data["email"],
            phone=order_data["phone"],
            deliveryType=order_data["deliveryType"],
            paymentType=order_data["paymentType"],
            totalCost=order_data["totalCost"],
            status=order_data["status"],
            city=order_data["city"],
            address=order_data["address"],
        )
        order.products.set([order_product])

        # Проверка создания заказа
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.fullName, order_data["fullName"])

        # Проверка получения заказа через API
        response = self.client.get(reverse("order:orders"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["fullName"], order_data["fullName"])


class OrdersByIdViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="orderuser", password="orderpass")
        cls.profile = Profile.objects.create(user=cls.user)
        cls.category = Categories.objects.create(title="Test Category")

        cls.order = Order.objects.create(
            user=cls.user,
            fullName="Test User",
            email="test@example.com",
            phone="1234567890",
            deliveryType="free",
            paymentType="online",
            totalCost=100.00,
            status="new",
            city="Test City",
            address="Test Address",
            createdAt="2023-01-01",
        )

        cls.order_product = OrderProduct.objects.create(
            title="Test Product",
            price=100.00,
            count=1,
            description="Test Description",
            freeDelivery=True,
            category=cls.category,
        )
        cls.order.products.add(cls.order_product)

        cls.order_url = reverse("order:orders_details", args=[cls.order.id])

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_get_order(self):
        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.order.id)
        self.assertEqual(len(response.data["products"]), 1)

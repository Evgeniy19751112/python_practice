import logging
from datetime import datetime

from api.serializers import (
    BaseImageSerializer,
)
from product.serializers import BaseTagSerializer, ProductBaseSerializerMixin
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    IntegerField,
    ModelSerializer,
    Serializer,
)

from .models import (
    BasketItem,
    Order,
    OrderProduct,
    Product,
)

logger = logging.getLogger("order")


class ProductShortSerializer(ProductBaseSerializerMixin, ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "rating",
        ]


class OrderProductSerializer(ProductBaseSerializerMixin, ModelSerializer):
    price = DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    rating = DecimalField(max_digits=3, decimal_places=1, coerce_to_string=False)
    images = BaseImageSerializer(many=True)
    tags = BaseTagSerializer(many=True)

    class Meta:
        model = OrderProduct
        fields = [
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "rating",
        ]


class BasketItemSerializer(ModelSerializer):
    id = IntegerField(source="product.id")
    category = IntegerField(source="product.category.id")
    price = DecimalField(
        source="product.price", max_digits=10, decimal_places=2, coerce_to_string=False
    )
    title = CharField(source="product.title")
    description = CharField(source="product.description", allow_null=True)
    freeDelivery = BooleanField(source="product.freeDelivery")
    images = BaseImageSerializer(source="product.images", many=True)
    tags = BaseTagSerializer(source="product.tags", many=True)
    reviews = IntegerField(source="product.reviews.count")
    rating = DecimalField(
        source="product.rating", max_digits=3, decimal_places=1, coerce_to_string=False
    )
    date = CharField(source="product.date", allow_null=True)

    class Meta:
        model = BasketItem
        fields = [
            "id",
            "category",
            "price",
            "count",
            "date",
            "title",
            "description",
            "freeDelivery",
            "images",
            "tags",
            "reviews",
            "rating",
        ]

    def validate(self, data):
        if not self.context.get("user"):
            raise ValidationError("User is required")
        return data


class BasketItemPostSerializer(Serializer):
    id = IntegerField()
    count = IntegerField(min_value=1)

    class Meta:
        model = BasketItem
        fields = ["id", "count"]


class OrderDetailSerializer(ModelSerializer):
    products = OrderProductSerializer(many=True, read_only=True)
    createdAt = DateTimeField(read_only=True)
    deliveryType = CharField(read_only=True)
    paymentType = CharField(read_only=True)
    totalCost = DecimalField(
        max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "createdAt",
            "fullName",
            "email",
            "phone",
            "deliveryType",
            "paymentType",
            "totalCost",
            "status",
            "city",
            "address",
            "products",
        ]


class OrderCreateSerializer(ModelSerializer):
    id = IntegerField()
    count = IntegerField(min_value=1)

    class Meta:
        model = Product
        fields = ["id", "count"]


class PaymentSerializer(ModelSerializer):
    number = CharField(max_length=16, min_length=16)
    name = CharField(max_length=128)
    month = CharField(max_length=2, min_length=2)
    year = CharField(max_length=4, min_length=4)
    code = CharField(max_length=3, min_length=3)

    def validate(self, data):
        """
        Валидация даты карты.
        """
        month = int(data["month"])
        year = int(data["year"])
        if month < 1 or month > 12:
            raise ValidationError("Invalid month")
        if year < datetime.now().year:
            raise ValidationError("Card expired")
        return data

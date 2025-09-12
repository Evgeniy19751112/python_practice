import logging
from datetime import datetime

from api.serializers import BaseImageSerializer
from api.validators import validate_sale_date_format
from rest_framework.exceptions import ValidationError
from rest_framework.fields import (
    BooleanField,
    DateTimeField,
    DecimalField,
    DictField,
    empty,
)
from rest_framework.serializers import (
    CharField,
    EmailField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
)

from .models import (
    Categories,
    Product,
    Review,
    Sale,
    Specifications,
    Subcategories,
    Tags,
)

logger = logging.getLogger("product")


class BaseTagSerializer(ModelSerializer):
    class Meta:
        model = Tags
        fields = ["id", "name"]


class ProductBaseSerializerMixin:
    price = DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False, source="products.price"
    )
    rating = DecimalField(
        max_digits=5, decimal_places=1, coerce_to_string=False, source="products.rating"
    )
    images = BaseImageSerializer(many=True)
    tags = BaseTagSerializer(many=True)
    reviews = IntegerField(source="reviews.count")
    freeDelivery = BooleanField()

    class Meta:
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


class ReviewSerializer(ModelSerializer):
    author = CharField(source="author.username")
    email = EmailField(source="author.email")
    rate = IntegerField(min_value=1, max_value=5)
    date = DateTimeField(format="%Y-%m-%d %H:%M", default=datetime.now)

    class Meta:
        model = Review
        fields = ["author", "email", "text", "rate", "date"]


class SpecificationSerializer(ModelSerializer):
    class Meta:
        model = Specifications
        fields = ["name", "value"]


class ProductShortSerializer(ProductBaseSerializerMixin, ModelSerializer):
    price = DecimalField(coerce_to_string=False, decimal_places=2, max_digits=10)
    images = BaseImageSerializer(many=True)
    tags = BaseTagSerializer(many=True)
    reviews = IntegerField(source="reviews.count")
    rating = DecimalField(max_digits=3, decimal_places=1, coerce_to_string=False)

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


class ProductFullSerializer(ProductShortSerializer):
    fullDescription = CharField()
    specifications = SpecificationSerializer(many=True)
    reviews = ReviewSerializer(many=True)

    class Meta(ProductShortSerializer.Meta):
        fields = ProductShortSerializer.Meta.fields + [
            "fullDescription",
            "specifications",
            "reviews",
        ]


class SubcategorySerializer(ModelSerializer):
    title = CharField()
    image = BaseImageSerializer()

    class Meta:
        model = Subcategories
        fields = ["id", "title", "image"]


class CategorySerializer(ModelSerializer):
    image = BaseImageSerializer()
    subcategories = SubcategorySerializer(many=True)

    class Meta:
        model = Categories
        fields = ["id", "title", "image", "subcategories"]


class SaleItemSerializer(ModelSerializer):
    price = DecimalField(decimal_places=2, max_digits=10, required=True)
    salePrice = DecimalField(decimal_places=2, max_digits=10, required=True)
    dateFrom = CharField(min_length=5, max_length=5, required=False)
    dateTo = CharField(min_length=5, max_length=5, required=False)
    title = CharField(required=True, min_length=1)
    images = BaseImageSerializer(many=True, required=False)

    class Meta:
        model = Sale
        fields = ["id", "price", "salePrice", "dateFrom", "dateTo", "title", "images"]

    def validate_dateFrom(self, value):
        validate_sale_date_format(value)
        return value

    def validate_dateTo(self, value):
        validate_sale_date_format(value)
        return value


class CatalogQueryParamsSerializer(Serializer):
    filter = DictField(required=False)
    category = IntegerField(required=False)
    tags = ListField(child=IntegerField(), required=False)
    sort = CharField(required=False)
    sort_type = CharField(source="sortType", required=False)
    limit = IntegerField(min_value=1, required=False)
    current_page = IntegerField(min_value=1, source="currentPage", required=False)

    def __init__(
        self,
        instance=None,
        data=empty,
        categories_model=None,
        tags_model=None,
        **kwargs,
    ):
        # print("\ninstance", instance)
        # print("data", data)
        # print("categories_model", categories_model)
        # print("tags_model", tags_model)
        # print("kwargs", kwargs, "\n")

        super().__init__(instance=instance, data=data, **kwargs)
        self._categories_model = categories_model
        self._tags_model = tags_model

    def validate_category(self, value):
        if value is not None:
            if (
                not self._categories_model
                or not self._categories_model.objects.filter(id=value).exists()
            ):
                raise ValidationError("Invalid category ID")
        return value

    def validate_tags(self, value):
        if value and self._tags_model:
            existing_tags = set(
                self._tags_model.objects.filter(id__in=value).values_list(
                    "id", flat=True
                )
            )
            if len(existing_tags) != len(value):
                raise ValidationError("One or more tag IDs are invalid")
        return value

    def validate_sort(self, value):
        valid_sorts = ("rating", "price", "reviews", "date")
        if value not in valid_sorts:
            raise ValidationError(
                f"Invalid sort parameter. Must be one of: {valid_sorts}"
            )
        return value

    def validate_sort_type(self, value):
        if value not in ("dec", "inc"):
            raise ValidationError("Invalid sortType parameter. Must be 'dec' or 'inc'")
        return value

    def validate_filter(self, value):
        if value:
            valid_filters = {
                "name",
                "minPrice",
                "maxPrice",
                "freeDelivery",
                "available",
            }
            for key in value:
                if key not in valid_filters:
                    raise ValidationError(f"Invalid filter parameter: {key}")

            if "minPrice" in value:
                try:
                    value["minPrice"] = float(value["minPrice"])
                except (ValueError, TypeError):
                    raise ValidationError("minPrice must be a number")

            if "maxPrice" in value:
                try:
                    value["maxPrice"] = float(value["maxPrice"])
                except (ValueError, TypeError):
                    raise ValidationError("maxPrice must be a number")

            if "freeDelivery" in value:
                value["freeDelivery"] = value["freeDelivery"].lower() == "true"

            if "available" in value:
                value["available"] = value["available"].lower() == "true"

        return value

    def to_internal_value(self, data):
        # Обрабатываем параметры фильтрации и выбор тегов
        filter_data = {}
        tags_data = []
        for key in list(data.keys()):
            if key.startswith("filter[") and key.endswith("]"):
                # Извлекаем имя параметра между 'filter[' и ']'
                param_name = key[key.find("[") + 1 : -1]  # noqa: E203
                filter_data[param_name] = data.pop(key)

            if key == "tags[]":
                # Получаем код тэга
                tags_data.append(data.pop(key))

        if filter_data:
            data["filter"] = filter_data
        if tags_data:
            data["tags"] = tags_data

        # Преобразуем camelCase в snake_case перед валидацией
        if "sortType" in data:
            data["sort_type"] = data.pop("sortType")
        if "currentPage" in data:
            data["current_page"] = data.pop("currentPage")

        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Преобразуем camelCase от клиента в snake_case для бэкэнда
        if "sort_type" in data:
            data["sortType"] = data.pop("sort_type")
        if "current_page" in data:
            data["currentPage"] = data.pop("current_page")

        return data

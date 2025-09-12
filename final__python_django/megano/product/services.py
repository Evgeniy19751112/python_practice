import logging
from datetime import timedelta
from typing import Optional

from api.exceptions import CustomAPIException
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Prefetch, Q, QuerySet
from django.utils import timezone
from order.models import BasketItem, Order, OrderProduct
from rest_framework import status

from .models import (
    Categories,
    Product,
    Review,
    Sale,
    Tags,
    User,
)
from .serializers import ProductShortSerializer, ReviewSerializer

logger = logging.getLogger("product")


def get_product_details(product_id: int) -> Product:
    """
    Получение деталей товара
    """
    product = (
        Product.objects.select_related("category")
        .prefetch_related(
            Prefetch("tags"),
            Prefetch("images"),
            Prefetch("reviews", queryset=Review.objects.select_related("author")),
            Prefetch("specifications"),
        )
        .get(pk=product_id)
    )
    # logger.debug("Get product details: %s", product)
    return product


def get_products_limited() -> QuerySet:
    """
    Получение ограниченного списка товаров
    """
    products = (
        Product.objects.filter(count__gt=0)
        .select_related("category")
        .prefetch_related("images", "tags")[:5]
    )
    # logger.debug("Get products limited: %s", str(products))
    return products


def get_popular_products() -> QuerySet:
    """
    Получение популярных товаров
    """
    products = (
        Product.objects.order_by("-rating")
        .select_related("category")
        .prefetch_related("images", "tags")[:5]
    )
    # logger.debug("Get popular products: %s", str(products))
    return products


def get_categories() -> QuerySet:
    """
    Получение категорий
    """
    categories = Categories.objects.prefetch_related(
        "image", "subcategories__image"
    ).all()
    # logger.debug("Get categories:\n%s", str(categories))
    return categories


def get_banners() -> QuerySet:
    """
    Получение баннеров
    """
    products = (
        Product.objects.order_by("?")
        .select_related("category")
        .prefetch_related("images", "tags")[:5]
    )
    # logger.debug("Get banners: %s", str(products))
    return products


@transaction.atomic
def create_product_review(product_id: int, user: User, data: dict) -> Optional[dict]:
    """
    Создание отзыва о товаре
    """
    product = Product.objects.select_related("category").get(pk=product_id)
    review = Review.objects.create(
        author=user,
        email=user.email,
        text=data["text"],
        rate=data["rate"],
        date=data["date"],
    )
    product.reviews.add(review)
    product.update_rating()
    # logger.debug("Review created: %s\nFor product: %s", str(review), str(product))
    return ReviewSerializer(product.reviews, many=True).data


def get_catalog_products(
    filter: dict = None,
    category: int = None,
    tags: list = None,
    sort: str = None,
    sort_type: str = None,
    limit: int = 5,
    current_page: int = 1,
    # **kwargs,
) -> dict:
    """
    Получение товаров для каталога с фильтрацией, сортировкой и пагинацией
    """
    # print(
    #     "params",
    #     filter,
    #     category,
    #     tags,
    #     sort,
    #     sort_type,
    #     limit,
    #     current_page,
    #     # **kwargs,
    #     sep="\n...",
    #     end="\n\n",
    # )
    products = Product.objects.select_related("category").prefetch_related(
        "tags", "images", "specifications", "reviews"
    )

    # Фильтрация по категории
    if category:
        products = products.filter(category_id=category)

    # Фильтрация по тегам
    if tags:
        products = products.filter(tags__id__in=tags).distinct()

    # Применение дополнительных фильтров
    if filter:
        # print("Filtering products by", filter)
        if filter.get("name"):
            products = products.filter(title__icontains=filter["name"])
        if filter.get("minPrice"):
            products = products.filter(price__gte=filter["minPrice"])
        if filter.get("maxPrice"):
            products = products.filter(price__lte=filter["maxPrice"])
        if filter.get("freeDelivery"):
            products = products.filter(freeDelivery=filter["freeDelivery"])
        if filter.get("available"):
            products = products.filter(count__gt=0)

    # Сортировка
    sort_field = sort if sort else "rating"
    if sort_type == "dec":
        sort_field = f"-{sort_field}"
    # logger.debug("Sort field %s and type %s", sort_field, sort_type)

    products = products.order_by(sort_field)
    # logger.debug("Products after order: %s\n", products)

    # Пагинация
    paginator = Paginator(products, limit)
    last_page = paginator.num_pages
    if current_page > last_page:
        raise CustomAPIException(
            detail="No data at page %d" % current_page,
            status_code=status.HTTP_404_NOT_FOUND,
        )
    products = paginator.page(current_page)

    # total_products = products.count()
    # last_page = (total_products + limit - 1) // limit
    # offset = (current_page - 1) * limit
    # products = products[offset : offset + limit]
    # logger.debug(
    #     "Paging for products: total_products %i; last_page %i; offset %i",
    #     total_products,
    #     last_page,
    #     offset,
    # )
    # logger.debug("Products after paging: %s", products)

    return {
        "items": ProductShortSerializer(products, many=True).data,
        "currentPage": current_page,
        "lastPage": last_page,
    }


def get_current_and_future_dates():
    """Возвращает текущую дату и дату через 10 дней в формате 'MM-DD'"""
    today = timezone.now().date()
    future_date = today + timedelta(days=10)
    return today.strftime("%m-%d"), future_date.strftime("%m-%d")


def get_sales() -> QuerySet:
    """
    Получение списка скидок без товаров.
    """
    today_str, future_str = get_current_and_future_dates()

    # Создаем условия для фильтрации дат
    date_conditions = Q(
        # Случай 1: Нет дат - включаем скидку
        Q(dateFrom__isnull=True) & Q(dateTo__isnull=True)
        |
        # Случай 2: Есть обе даты
        Q(
            # Если период скидки пересекается с нашим диапазоном
            Q(dateFrom__isnull=False)
            & Q(dateTo__isnull=False)
            & Q(dateFrom__lte=future_str)
            & Q(dateTo__gte=today_str)
        )
        |
        # Случай 3: Только дата начала
        Q(
            Q(dateFrom__isnull=False)
            & Q(dateTo__isnull=True)
            & Q(dateFrom__lte=future_str)
        )
        |
        # Случай 4: Только дата окончания
        Q(Q(dateFrom__isnull=True) & Q(dateTo__isnull=False) & Q(dateTo__gte=today_str))
    )

    # Получаем скидки
    sales = (
        Sale.objects.filter(salePrice__isnull=False)
        .filter(date_conditions)
        .prefetch_related("images", "products")
    ).all()
    # logger.debug("Sales after offset: %s", sales)
    return sales


@transaction.atomic
def create_order(user: User, order_data: dict) -> Optional[int]:
    """
    Создание нового заказа
    """
    # Создаем продукты заказа
    order_products = [
        OrderProduct(
            category_id=product_data["category"],
            price=product_data["price"],
            count=product_data["count"],
            title=product_data["title"],
            description=product_data["description"],
            freeDelivery=product_data["freeDelivery"],
        )
        for product_data in order_data["products"]
    ]

    # Создаем сам заказ
    created_products = OrderProduct.objects.bulk_create(order_products)
    # logger.debug("Created order: %s", str(created_products))
    order = Order.objects.create(
        user=user,
        fullName=order_data.get("fullName", user.profile.fullName),
        email=order_data.get("email", user.email),
        phone=order_data.get("phone", user.profile.phone),
        deliveryType=order_data.get("deliveryType", "free"),
        paymentType=order_data.get("paymentType", "online"),
        totalCost=order_data.get("totalCost", 0),
        status="new",
        city=order_data.get("city", ""),
        address=order_data.get("address", ""),
    )
    order.products.set(created_products)

    # Очищаем корзину
    BasketItem.objects.filter(profile=user.profile).delete()

    return order.id


def get_tags() -> QuerySet:
    """
    Получение списка тегов
    """
    tags = Tags.objects.all()
    # logger.debug("Tags: %s", tags)
    return tags

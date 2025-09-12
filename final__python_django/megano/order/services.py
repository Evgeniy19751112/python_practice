import logging
from datetime import datetime
from typing import Any, Optional

from api.exceptions import CustomAPIException
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import status

from .models import BasketItem, Order, OrderProduct, Product, User

logger = logging.getLogger("order")


def get_user_basket(user: User) -> QuerySet:
    """
    Получение корзины пользователя
    """
    # logger.debug("get user's basket for user: %s", user)
    if user is None or user.is_anonymous:
        return BasketItem.objects.none()
    return (
        BasketItem.objects.filter(profile=user.profile)
        .select_related("product")
        .prefetch_related(
            "product__images",
            "product__tags",
            "product__category",
        )
    )


def get_product_from_basket_by_id(user: User, product_id: int) -> Optional[BasketItem]:
    """
    Получить товар по id из корзины для текущего пользователя.
    """
    return BasketItem.objects.filter(
        profile=user.profile, product_id=product_id
    ).first()


def add_to_basket(user: User, product_id: int, count: int) -> None:
    """
    Добавление товаров в корзину.
    """
    product = Product.objects.get(pk=product_id)
    item_in_basket = get_product_from_basket_by_id(user, product_id)
    if item_in_basket is not None:
        count += item_in_basket.count

    with transaction.atomic():
        BasketItem.objects.update_or_create(
            profile=user.profile, product=product, defaults={"count": count}
        )


@transaction.atomic
def remove_from_basket(user: User, product_id: int, count: int = None) -> bool:
    """
    Удаление товара из корзины. Если count не указан или не менее
    кол-ва товаров в корзине, то удалить сам товар, иначе уменьшить
    количество.
    """
    # print("params:\n", "user_id:", user.id, "product_id:", product_id, "count:", count)
    deleted = 0
    product = get_product_from_basket_by_id(user, product_id)
    if product:
        quantity = product.count
        # print("product.id:", product.id, "quantity:", quantity)
        if count is None or count >= quantity:
            deleted, _ = product.delete()
        else:
            product.count -= count
            product.save()
            deleted = count
    # deleted, _ = BasketItem.objects.filter(
    #     profile=user.profile, product_id=product_id
    # ).delete()
    # print("deleted:", deleted)
    return deleted > 0


def get_user_orders(user: User) -> QuerySet:
    """
    Получение списка заказов пользователя
    """
    return (
        Order.objects.filter(user=user)
        .select_related("user")
        .prefetch_related(
            "products", "products__category", "products__tags", "products__images"
        )
    )


def get_order_by_id(user: User, order_id: int) -> Optional[Order]:
    """
    Получение конкретного заказа пользователя
    """
    try:
        return (
            Order.objects.filter(user=user, pk=order_id)
            .select_related("user")
            .prefetch_related(
                "products", "products__category", "products__tags", "products__images"
            )
            .first()
        )
    except Order.DoesNotExist as e:
        logging.error(e)
        return None


@transaction.atomic
def create_order(user: User, order_data: list[dict[str, Any]]) -> Optional[int]:
    """
    Создание нового заказа
    """
    # logger.debug("Create order data in quantity %s records", len(order_data))
    try:
        # Создаем продукты заказа
        product_ids = [item["id"] for item in order_data]
        products = Product.objects.filter(id__in=product_ids, count__gt=0).in_bulk()

        if len(products) != len(product_ids):
            missing_ids = set(product_ids) - set(products.keys())
            raise Product.DoesNotExist(
                f"Products not found or out of stock: {missing_ids}"
            )

        order_products = []
        for product_data in order_data:
            product = products.get(product_data["id"])
            if not product:
                raise Product.DoesNotExist(f"Product {product_data['id']} not found")

            order_products.append(
                OrderProduct(
                    price=product.price,
                    count=product_data["count"],
                    title=product.title,
                    description=product.description,
                    freeDelivery=product.freeDelivery,
                    reviews=product.reviews.count(),
                    rating=float(product.rating),
                    category=product.category,
                )
            )
        created_products = OrderProduct.objects.bulk_create(order_products)

        # Устанавливаем связи для всех продуктов
        for op, product in zip(created_products, products.values()):
            op.tags.set(product.tags.all())
            op.images.set(product.images.all())
        # logger.debug(f"Created {len(created_products)} products:\n{created_products}")

        # Создаем сам заказ
        profile = user.profile
        order = Order.objects.create(
            user=user,
            fullName=profile.fullName,
            email=user.email if user.email else "example@email.net",
            phone=profile.phone if profile.phone else "80001234567",
            deliveryType="free",
            paymentType="online",
            totalCost=round(sum(op.price * op.count for op in created_products), 2),
            status="new",
            city="",
            address="",
            createdAt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        order.products.set(created_products)
        # logger.info(f"Created order {order.id} successfully")

        # Очищаем корзину
        BasketItem.objects.filter(profile=profile).delete()

        return order.id
    except Exception as e:
        logger.error("Error creating order: %s", str(e), exc_info=True)
        raise CustomAPIException(
            detail=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@transaction.atomic
def process_payment(user: User, order_id: int, payment_data: dict) -> bool:
    """
    Обработка платежа
    """
    try:
        order = Order.objects.get(pk=order_id, user=user)
        # TODO: Тут наверное надо придумать как фиксируется оплата
        order.status = "paid"
        order.save()
        return True
    except Order.DoesNotExist:
        return False

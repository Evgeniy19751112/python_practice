from django.contrib.auth.models import User
from django.db import models
from product.models import Categories, ImagesProduct, Product, Tags
from user.models import Profile


class OrderProduct(models.Model):
    """
    Модель для хранения сведений о заказанных товарах.
    """

    class Meta:
        verbose_name = "Order product"
        verbose_name_plural = "Order products"

    category = models.ForeignKey(
        Categories,
        on_delete=models.PROTECT,
        verbose_name="Product's category in order",
        null=False,
        blank=False,
    )
    price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=0,
        verbose_name="Price of product in order",
        null=False,
        blank=False,
    )
    count = models.PositiveIntegerField(
        default=0,
        verbose_name="Number of products in order",
        null=False,
        blank=False,
    )
    date = models.CharField(
        max_length=128,
        verbose_name="Date when the product was added to the order",
        null=True,
        blank=True,
    )
    title = models.CharField(
        max_length=128,
        verbose_name="Title of the product in order",
        null=False,
        blank=False,
    )
    description = models.CharField(
        max_length=128,
        verbose_name="Description of the product in order",
        null=True,
        blank=True,
    )
    freeDelivery = models.BooleanField(
        default=False,
        verbose_name="Free delivery",
        null=False,
        blank=False,
    )
    images = models.ManyToManyField(
        ImagesProduct,
        related_name="order_product",
        verbose_name="Product's images in order",
    )
    tags = models.ManyToManyField(
        Tags,
        related_name="order_product",
        verbose_name="Product's tags in order",
    )
    reviews = models.IntegerField(
        default=0,
        verbose_name="Reviews",
        null=False,
        blank=False,
    )
    rating = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        default=0,
        verbose_name="Rating",
        null=False,
        blank=False,
    )

    def __str__(self):
        return f'Product #{self.id} in order; title: "{self.title}"'


class Order(models.Model):
    """
    Модель для хранения заказов.
    """

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="User",
        blank=True,
        null=True,
        default=None,
    )
    createdAt = models.CharField(
        max_length=32,
        verbose_name="Created at",
        null=False,
        blank=False,
    )
    fullName = models.CharField(
        max_length=128,
        verbose_name="Full name",
        null=False,
        blank=False,
    )
    email = models.EmailField(
        max_length=128,
        verbose_name="Email",
        null=False,
        blank=False,
    )
    phone = models.CharField(
        max_length=32,
        verbose_name="Phone",
        null=False,
        blank=False,
    )
    deliveryType = models.CharField(
        max_length=128,
        verbose_name="Delivery type",
        null=False,
        blank=False,
        default="free",
    )
    paymentType = models.CharField(
        max_length=128,
        verbose_name="Payment type",
        null=False,
        blank=False,
        default="online",
    )
    totalCost = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=0,
        verbose_name="Total cost",
        null=False,
        blank=False,
    )
    status = models.CharField(
        max_length=128, verbose_name="Status", null=False, blank=False, default="new"
    )
    city = models.CharField(
        max_length=128,
        verbose_name="City",
        null=False,
        blank=False,
    )
    address = models.CharField(
        max_length=128,
        verbose_name="Address",
        null=False,
        blank=False,
    )
    products = models.ManyToManyField(
        OrderProduct,
        related_name="order",
        verbose_name="Products in order",
    )

    def __str__(self):
        return (
            f"Order #{self.id} for user {self.user}; "
            f"total cost: {self.totalCost}; city: {self.city}; "
            f"address: {self.address}"
        )


class BasketItem(models.Model):
    """
    Модель для хранения товаров в корзине пользователя
    """

    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="basket_items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1, verbose_name="Quantity")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Added at")

    class Meta:
        verbose_name = "Basket item"
        verbose_name_plural = "Basket items"
        unique_together = ("profile", "product")
        ordering = ("-created_at",)

    def __str__(self):
        return f'{self.product} in basket of "{self.profile.user.username}"'

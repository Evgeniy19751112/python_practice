import os

from api.validators import validate_image_size, validate_sale_date_format
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError


def image_directory_path(instance: models.Model, filename: str) -> str:
    """Формируем путь к изображениям для справочников."""
    pattern: str = "app/{}/img_{}"
    object_name = instance._meta.model_name
    print("object_name", object_name)
    if object_name is None:
        object_name = instance.__class__.__name__
        print("object_name 2", object_name)

    # Формируем новое имя файла
    now = timezone.now()
    datetime_str = now.strftime("%Y%m%d%H%M%S%f")
    *name, ext = os.path.splitext(filename)
    new_filename = f"{datetime_str}{ext}"

    result_path = pattern.format(object_name, new_filename)
    print("result_path", result_path)
    return result_path


class BaseImageModel(models.Model):
    """
    Абстрактная базовая модель для хранения изображений.
    """

    src = models.ImageField(
        verbose_name="Link to the image",
        null=True,
        blank=True,
        upload_to=image_directory_path,
    )
    alt = models.CharField(
        max_length=128,
        verbose_name="Image description",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
        verbose_name = None

    def __str__(self):
        return f"Image #{self.id}; src: {self.src}; alt: {self.alt}"

    @classmethod
    def get_default_image(cls):
        """
        Возвращает путь к изображению по умолчанию.
        Должен быть переопределен в дочерних классах.
        """
        raise NotImplementedError(
            "Метод get_default_image должен быть переопределен в дочернем классе"
        )

    @classmethod
    def get_allowed_extensions(cls):
        """
        Возвращает список разрешенных расширений файлов.
        По умолчанию разрешены некоторые форматы файлов изображений.
        """
        return ["png", "jpg", "jpeg", "gif", "svg"]

    def save(self, *args, **kwargs):
        """
        Переопределяем save для установки upload_to и валидации.
        """
        if not self.src:
            # Если изображение не указано, устанавливаем по умолчанию
            self.src = self.get_default_image()
        else:
            # Валидация расширения файла
            ext = os.path.splitext(self.src.name)[1][1:].lower()
            if ext not in self.get_allowed_extensions():
                raise ValidationError(
                    "Недопустимое расширение файла. "
                    f"Разрешены: {', '.join(self.get_allowed_extensions())}"
                )

            # Валидация размера файла
            validate_image_size(self.src.size)

        super().save(*args, **kwargs)


class ImagesProduct(BaseImageModel):
    """
    Модель для хранения изображений товаров.
    """

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    @classmethod
    def get_default_image(cls):
        return "app/no_photo.png"


class ImagesSale(BaseImageModel):
    """
    Модель для хранения изображений для распродаж.
    """

    class Meta:
        verbose_name = "Sale Image"
        verbose_name_plural = "Sale Images"

    @classmethod
    def get_default_image(cls):
        return "app/no_sale_image.jpg"


class ImagesCategories(BaseImageModel):
    """
    Модель для хранения изображений для категорий и подкатегорий.
    """

    class Meta:
        verbose_name = "Category Image"
        verbose_name_plural = "Category Images"

    @classmethod
    def get_default_image(cls):
        return "app/no_category_image.jpeg"


class Subcategories(models.Model):
    """
    Модель справочника подкатегорий.
    """

    class Meta:
        verbose_name = "Subcategory"
        verbose_name_plural = "Subcategories"

    title = models.CharField(
        max_length=128,
        verbose_name="Title of subcategory",
        null=False,
        blank=False,
        unique=True,
    )
    image = models.ForeignKey(
        ImagesCategories,
        related_name="subcategories",
        verbose_name="Image of subcategory",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Subcategory #{self.id}; title: {self.title}"


class Categories(models.Model):
    """
    Модель справочника категорий.
    """

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    title = models.CharField(
        max_length=128,
        verbose_name="Title of category",
        null=False,
        blank=False,
        unique=True,
    )
    image = models.ForeignKey(
        ImagesCategories,
        related_name="categories",
        verbose_name="Image of category",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    subcategories = models.ManyToManyField(
        Subcategories,
        related_name="categories",
        verbose_name="Subcategory",
        blank=True,
    )

    def __str__(self):
        return f"Category #{self.id}; title: {self.title}"


class Tags(models.Model):
    """
    Модель для хранения меток (тэгов).
    """

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    name = models.CharField(
        max_length=128,
        verbose_name="Name of the tag",
        null=False,
        blank=False,
        unique=True,
    )

    def __str__(self):
        return f"Tag #{self.id}; name: {self.name}"


class Review(models.Model):
    """
    Модель для хранения описания товара.
    """

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Author of review",
        null=False,
        blank=False,
    )
    email = models.EmailField(
        max_length=128,
        verbose_name="Email of reviewer",
        null=False,
        blank=False,
    )
    text = models.TextField(
        max_length=1024,
        verbose_name="Text of review",
        null=False,
        blank=False,
    )
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date of the review",
        null=False,
        blank=False,
    )
    rate = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=0,
        verbose_name="Rating",
        null=False,
        blank=False,
    )

    def __str__(self):
        return f"Review #{self.id}; author: {self.author.username}; date: {self.date}"


class Specifications(models.Model):
    """
    Модель для хранения спецификации товаров.
    """

    class Meta:
        verbose_name = "Specification"
        verbose_name_plural = "Specifications"

    name = models.CharField(
        max_length=128,
        verbose_name="Name of specification",
        null=False,
        blank=False,
    )
    value = models.CharField(
        max_length=128,
        verbose_name="Value of specification",
        null=False,
        blank=False,
    )

    def __str__(self):
        return f"Specification #{self.id}; name: {self.name}; value: {self.value}"


class Sale(models.Model):
    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ("id",)

    price = models.DecimalField(
        decimal_places=2, max_digits=10, verbose_name="Price of product"
    )
    salePrice = models.DecimalField(
        decimal_places=2, max_digits=10, verbose_name="Sale price"
    )
    dateFrom = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name="Date of sale start",
        validators=[validate_sale_date_format],
    )
    dateTo = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name="Date of sale end",
        validators=[validate_sale_date_format],
    )
    title = models.CharField(
        max_length=128, verbose_name="Title of sale", null=False, blank=False
    )
    images = models.ManyToManyField(
        ImagesSale,
        related_name="sales",
        verbose_name="Image of sales",
        blank=True,
    )
    products = models.ManyToManyField(
        "Product",
        related_name="sales",
        verbose_name="Products of sale",
        blank=True,
    )

    def clean(self):
        if self.dateFrom and self.dateTo:
            if self.dateFrom > self.dateTo:
                raise ValidationError("End date cannot be before start date")

    def __str__(self):
        return (
            f"Sale #{self.id}; title: {self.title}; price: {self.price}; "
            f"dateFrom: {self.dateFrom}; dateTo: {self.dateTo}"
        )


class Product(models.Model):
    """
    Модель для хранения всех свойств продукта.
    """

    class Meta:
        verbose_name = "Product full"
        verbose_name_plural = "Products full"

    category = models.ForeignKey(
        Categories,
        on_delete=models.PROTECT,
        verbose_name="Product category in store",
        null=False,
        blank=False,
    )
    price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=0,
        verbose_name="Price of product in store",
        null=False,
        blank=False,
    )
    count = models.PositiveIntegerField(
        default=0,
        verbose_name="Number of products in store",
        null=False,
        blank=False,
    )
    date = models.CharField(
        max_length=128,
        verbose_name="Date when the product was added to the store",
        null=True,
        blank=True,
    )
    title = models.CharField(
        max_length=128,
        verbose_name="Title of the product in store",
        null=False,
        blank=False,
    )
    description = models.CharField(
        max_length=128,
        verbose_name="Description of the product in store",
        null=True,
        blank=True,
    )
    fullDescription = models.TextField(
        max_length=1024,
        verbose_name="Full description of the product in store",
    )
    freeDelivery = models.BooleanField(
        default=False,
        verbose_name="Free delivery",
        null=False,
        blank=False,
    )
    images = models.ManyToManyField(
        ImagesProduct,
        related_name="products",
        blank=True,
        verbose_name="Image of product",
    )
    tags = models.ManyToManyField(
        Tags,
        related_name="products",
        blank=True,
    )
    reviews = models.ManyToManyField(
        Review,
        related_name="products",
        blank=True,
    )
    specifications = models.ManyToManyField(
        Specifications,
        related_name="products",
        blank=True,
    )
    rating = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=0,
        verbose_name="Rating",
        null=False,
        blank=False,
    )

    def update_rating(self):
        """Обновить статистику рейтингов для товара."""
        reviews = self.reviews.all()
        if reviews.exists():
            self.rating = round(sum(r.rate for r in reviews) / reviews.count(), 2)
            self.save()

    def save(self, *args, **kwargs):
        """Обновляем дату, если не заполнено."""
        if not self.date:
            self.date = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Product #{self.id}; title: "{self.title}"; price: {self.price}'

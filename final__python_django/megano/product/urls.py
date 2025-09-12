from django.urls import path

from .views import (
    BannersView,
    CatalogView,
    CategoriesView,
    ProductDetailsView,
    ProductReviewView,
    ProductsLimitedView,
    ProductsPopularView,
    SalesView,
    TagsView,
)

app_name = "product"

urlpatterns = [
    path("products/limited", ProductsLimitedView.as_view(), name="products.limited"),
    path("categories", CategoriesView.as_view(), name="categories"),
    path("catalog", CatalogView.as_view(), name="catalog"),
    path("products/popular", ProductsPopularView.as_view(), name="products.popular"),
    path("sales", SalesView.as_view(), name="sales"),
    path("banners", BannersView.as_view(), name="banners"),
    path("tags", TagsView.as_view(), name="tags"),
    path("product/<int:id>", ProductDetailsView.as_view(), name="product.details"),
    path(
        "product/<int:id>/reviews",
        ProductReviewView.as_view(),
        name="product.review",
    ),
]

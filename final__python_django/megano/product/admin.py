from django.contrib import admin

from .models import (
    Categories,
    ImagesCategories,
    ImagesProduct,
    ImagesSale,
    Product,
    Review,
    Sale,
    Specifications,
    Subcategories,
    Tags,
)

admin.site.register(Categories)
admin.site.register(Subcategories)
admin.site.register(Sale)
admin.site.register(Product)
# admin.site.register(ImagesProduct)
# admin.site.register(ImagesSale)
# admin.site.register(ImagesCategories)
admin.site.register(Tags)
admin.site.register(Review)
admin.site.register(Specifications)


@admin.register(ImagesProduct)
class ImagesProductAdmin(admin.ModelAdmin):
    list_display = ("id", "src", "alt")
    list_display_links = ("id", "src", "alt")
    search_fields = ("src", "alt")
    empty_value_display = "-empty-"
    ordering = ("alt", "id")


@admin.register(ImagesSale)
class ImagesSaleAdmin(admin.ModelAdmin):
    list_display = ("id", "src", "alt")
    list_display_links = ("id", "src", "alt")
    search_fields = ("src", "alt")
    empty_value_display = "-empty-"
    ordering = ("alt", "id")


@admin.register(ImagesCategories)
class ImagesCategoriesAdmin(admin.ModelAdmin):
    list_display = ("id", "src", "alt")
    list_display_links = ("id", "src", "alt")
    search_fields = ("src", "alt")
    empty_value_display = "-empty-"
    ordering = ("alt", "id")

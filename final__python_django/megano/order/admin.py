from django.contrib import admin

from .models import BasketItem, Order, OrderProduct

admin.site.register(Order)
admin.site.register(OrderProduct)
admin.site.register(BasketItem)

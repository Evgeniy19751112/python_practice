from django.urls import path

from .views import BasketView, OrdersByIdView, OrdersView, PaymentView

app_name = "order"

urlpatterns = [
    path("basket", BasketView.as_view(), name="basket"),
    path("orders", OrdersView.as_view(), name="orders"),
    # Возможно ошибка в frontend или в swagger.yaml! Оставил оба варианта
    # Проблема возникает при оформлении заказа. В консоле ошибка 404 для
    # /api/order/<id>
    path("order/<int:id>", OrdersByIdView.as_view(), name="order_details"),
    path("orders/<int:id>", OrdersByIdView.as_view(), name="orders_details"),
    path("payment", PaymentView.as_view(), name="payment"),
]

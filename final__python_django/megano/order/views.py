import logging

from api.exceptions import CustomAPIException
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Product
from .serializers import (
    BasketItemPostSerializer,
    BasketItemSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    PaymentSerializer,
)
from .services import (
    add_to_basket,
    create_order,
    get_order_by_id,
    get_user_basket,
    get_user_orders,
    process_payment,
    remove_from_basket,
)

logger = logging.getLogger("order")


class BasketView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        basket_items = get_user_basket(request.user)
        # logger.debug("Basket items:\n%s", basket_items)
        serializer = BasketItemSerializer(
            basket_items,
            many=True,
            context={"request": request},
        )
        data = serializer.data
        # logger.debug("BasketView serialized data:\n%s", data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        serializer = BasketItemPostSerializer(
            data=request.data, context={"user": request.user}
        )
        if serializer.is_valid():
            # logger.debug("BasketView serializer data: %s", serializer.validated_data)
            try:
                add_to_basket(
                    user=request.user,
                    product_id=serializer.validated_data["id"],
                    count=serializer.validated_data["count"],
                )
                # logger.debug("BasketView: add to basket success")
                return self.get(request)
            except Product.DoesNotExist as e:
                logger.error("Error adding to basket: %s", str(e), exc_info=True)
                raise CustomAPIException(
                    detail="Product not found: %s" % str(e),
                    status_code=status.HTTP_404_NOT_FOUND,
                )
        logger.warning("BasketView serializer error: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request) -> Response:
        serializer = BasketItemPostSerializer(
            data=request.data, context={"user": request.user}
        )
        if serializer.is_valid():
            # logger.debug("BasketView serializer data: %s", serializer.validated_data)
            if remove_from_basket(
                user=request.user,
                product_id=serializer.validated_data["id"],
                count=serializer.validated_data["count"],
            ):
                # logger.debug("BasketView: remove from basket success")
                return self.get(request)
            logger.warning("Item not found in basket")
            return Response(
                {"error": "Item not found in basket"}, status=status.HTTP_404_NOT_FOUND
            )
        logger.warning("Error removing from basket: %s", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        orders = get_user_orders(request.user)
        serializer = OrderDetailSerializer(orders, many=True)
        data = serializer.data
        # logger.debug("Orders get data:\n%s", data)
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request: Request) -> Response:
        # logger.debug("OrdersView post data:\n%s", request.data)
        serializer = OrderCreateSerializer(data=request.data, many=True)
        if not serializer.is_valid():
            logger.warning("BasketView serializer error: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = create_order(request.user, serializer.validated_data)
        if order_id:
            data = {"orderId": order_id}
            return Response(data, status=status.HTTP_200_OK)
        return Response(
            {"error": "Failed to create order"}, status=status.HTTP_400_BAD_REQUEST
        )


class OrdersByIdView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, id: int) -> Response:
        # logger.debug("OrdersByIdView get data: id %d; user '%s'", id, request.user)
        order = get_order_by_id(request.user, id)
        if order:
            serializer = OrderDetailSerializer(order)
            data = serializer.data
            # logger.debug("OrdersByIdView success. Data:\n%s", data)
            return Response(data, status=status.HTTP_200_OK)
        return Response(
            {"error": f"Order not found - id {id}"}, status=status.HTTP_404_NOT_FOUND
        )

    def post(self, request: Request, id: int) -> Response:
        order = get_order_by_id(request.user, id)
        if order:
            serializer = OrderDetailSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                order.status = "accepted"
                order.save()
                data = serializer.data
                # logger.debug("OrdersByIdView save success. Data: %s", data)
                return Response(data, status=status.HTTP_200_OK)

            logger.warning("OrdersByIdView serializer error: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"error": f"Order not found - id {id}"}, status=status.HTTP_404_NOT_FOUND
        )


class PaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        logger.debug("Payment view")
        # TODO: "GET /payment/undefined/ HTTP/1.1" 404 7553

        serializer = PaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order_id = serializer.validated_data.get("orderId")
        if process_payment(request.user, order_id, serializer.validated_data):
            return Response(status=status.HTTP_200_OK)

        logger.warning("Payment view error: %s", serializer.errors)
        return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

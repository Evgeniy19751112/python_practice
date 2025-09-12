import logging

from api.exceptions import CustomAPIException
from api.services import get_data_from_request
from django.core.paginator import Paginator
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Categories, Product, Tags
from .serializers import (
    BaseTagSerializer,
    CatalogQueryParamsSerializer,
    CategorySerializer,
    ProductFullSerializer,
    ProductShortSerializer,
    ReviewSerializer,
    SaleItemSerializer,
)
from .services import (
    create_product_review,
    get_banners,
    get_catalog_products,
    get_categories,
    get_popular_products,
    get_product_details,
    get_products_limited,
    get_sales,
    get_tags,
)

logger = logging.getLogger("product")


class ProductsLimitedView(APIView):

    def get(self, request: Request) -> Response:
        products = get_products_limited()
        serializer = ProductShortSerializer(products, many=True)
        data = serializer.data
        # logger.debug("Products Limited View serialized data: %s", str(data))
        return Response(data, status=status.HTTP_200_OK)


class CategoriesView(APIView):

    def get(self, request: Request) -> Response:
        categories = get_categories()
        serializer = CategorySerializer(categories, many=True)
        data = serializer.data

        # logger.debug("Categories View serialized data:\n%s", data)
        return Response(data, status=status.HTTP_200_OK)


class CatalogView(APIView):

    def get(self, request: Request) -> Response:
        # logger.debug(
        #     "Catalog View before serialize:\ndata: %s\nquery: %s\n",
        #     request.data,
        #     request.query_params,
        # )

        serializer = CatalogQueryParamsSerializer(
            data=get_data_from_request(request),
            categories_model=Categories,
            tags_model=Tags,
        )
        if not serializer.is_valid():
            raise CustomAPIException(
                detail=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        # logger.debug("Catalog View serialized data:\n%s\n", validated_data)
        data = get_catalog_products(
            sort_type=validated_data.pop("sortType", "dec"),
            current_page=validated_data.pop("currentPage", 1),
            **validated_data
        )
        # logger.debug("CatalogView data:\n%s\n", data)

        return Response(data, status=status.HTTP_200_OK)


class ProductsPopularView(APIView):

    def get(self, request: Request) -> Response:
        products = get_popular_products()
        serializer = ProductShortSerializer(products, many=True)
        data = serializer.data
        # logger.debug("Products Popular View data: %s", data)

        return Response(data, status=status.HTTP_200_OK)


class SalesView(APIView):

    def get(self, request: Request) -> Response:
        request_data = get_data_from_request(request)
        current_page = int(request_data.get("currentPage", 1))
        limit = 3

        sales_queryset = get_sales()
        paginator = Paginator(sales_queryset, limit)
        if paginator.num_pages < current_page:
            raise CustomAPIException(
                detail="No data at page %d" % current_page,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = SaleItemSerializer(paginator.page(current_page), many=True)
        data = serializer.data
        # logger.debug("Sales View serialized data: %s", data)

        return Response(
            {
                "items": data,
                "currentPage": current_page,
                "lastPage": (len(sales_queryset) + 1) // limit,
            },
            status=status.HTTP_200_OK,
        )


class BannersView(APIView):

    def get(self, request: Request) -> Response:
        products = get_banners()
        serializer = ProductShortSerializer(products, many=True)
        data = serializer.data
        # logger.debug("Banners View data: %s", data)

        return Response(data, status=status.HTTP_200_OK)


class TagsView(APIView):

    def get(self, request: Request) -> Response:
        tags = get_tags()
        serializer = BaseTagSerializer(tags, many=True)
        data = serializer.data
        # logger.debug("Tags View serialized data: %s", data)

        return Response(data, status=status.HTTP_200_OK)


class ProductDetailsView(APIView):

    def get(self, request: Request, id: int) -> Response:
        try:
            product = get_product_details(id)
            serializer = ProductFullSerializer(product)
            data = serializer.data
            # logger.debug("ProductDetailsView data: %s", data)

            return Response(data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            logger.warning("Product with id %s does not exist", id)
            return Response(status=status.HTTP_404_NOT_FOUND)


class ProductReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, id: int) -> Response:
        # logger.debug("ProductReviewView received data:\n%s\nid: %d", request.data, id)
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            data = create_product_review(id, request.user, serializer.validated_data)
            if data:
                return Response(data, status=status.HTTP_200_OK)
        logger.warning("ProductReviewView received invalid data: %s", serializer.errors)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

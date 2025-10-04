"""
apps/products/views.py — Views для Products API

ViewSets обрабатывают HTTP запросы и возвращают данные.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, ProductReview
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductReviewSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для категорий товаров.

    Endpoints:
    - GET /api/products/categories/ - список категорий
    - GET /api/products/categories/{id}/ - детали категории
    - GET /api/products/categories/tree/ - дерево категорий
    """

    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Возвращает категории текущего магазина.

        Фильтрует по request.store (установлен в middleware).
        """
        return Category.objects.filter(
            store=self.request.store,
            is_active=True
        ).select_related('parent').prefetch_related('children')

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Возвращает дерево категорий (только корневые с подкатегориями).

        GET /api/products/categories/tree/

        Структура:
        [
            {
                "id": 1,
                "name": "Дайвинг",
                "children": [
                    {"id": 2, "name": "Маски"},
                    {"id": 3, "name": "Ласты"}
                ]
            }
        ]
        """
        # Получаем только корневые категории (parent=None)
        root_categories = self.get_queryset().filter(parent=None)

        tree_data = []
        for category in root_categories:
            category_data = self.get_serializer(category).data
            # Добавляем подкатегории
            category_data['children'] = CategorySerializer(
                category.children.filter(is_active=True),
                many=True
            ).data
            tree_data.append(category_data)

        return Response(tree_data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для товаров.

    Endpoints:
    - GET /api/products/ - список товаров
    - GET /api/products/{slug}/ - детали товара
    - GET /api/products/{slug}/reviews/ - отзывы товара

    Фильтры:
    - ?category=diving-masks - товары категории
    - ?min_price=1000&max_price=10000 - по цене
    - ?search=маска - поиск по названию
    - ?ordering=-created - сортировка
    """

    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'available']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['created', 'retail_price', 'rating', 'sales_count']
    ordering = ['-created']

    def get_queryset(self):
        """
        Возвращает товары текущего магазина.

        Оптимизация:
        - select_related() - загружает связанные объекты (категория, магазин)
        - prefetch_related() - загружает связанные списки (фото, отзывы)
        """
        queryset = Product.objects.filter(
            store=self.request.store,
            available=True
        ).select_related(
            'category',
            'store'
        ).prefetch_related(
            'images',
            'reviews'
        )

        # Фильтрация по цене
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(retail_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(retail_price__lte=max_price)

        return queryset

    def get_serializer_class(self):
        """
        Выбирает сериализатор в зависимости от действия.

        - Список товаров -> ProductListSerializer (облегчённый)
        - Детали товара -> ProductDetailSerializer (полный)
        """
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Получение детальной информации о товаре.

        Дополнительно увеличивает счётчик просмотров.
        """
        instance = self.get_object()

        # Увеличиваем счётчик просмотров
        instance.views_count += 1
        instance.save(update_fields=['views_count'])

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """
        Получение отзывов о товаре.

        GET /api/products/{slug}/reviews/
        """
        product = self.get_object()
        reviews = product.reviews.filter(
            is_approved=True).select_related('user')
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_review(self, request, slug=None):
        """
        Добавление отзыва о товаре.

        POST /api/products/{slug}/add_review/
        Body: {"rating": 5, "comment": "Отличный товар!"}

        Требуется авторизация.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Требуется авторизация'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        product = self.get_object()

        # Проверяем, не оставлял ли пользователь уже отзыв
        if ProductReview.objects.filter(product=product, user=request.user).exists():
            return Response(
                {'error': 'Вы уже оставили отзыв на этот товар'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                product=product,
                user=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для отзывов (общий список всех отзывов магазина).

    Endpoints:
    - GET /api/products/reviews/ - все отзывы
    """

    serializer_class = ProductReviewSerializer

    def get_queryset(self):
        """Возвращает одобренные отзывы текущего магазина"""
        return ProductReview.objects.filter(
            product__store=self.request.store,
            is_approved=True
        ).select_related('product', 'user').order_by('-created')
# """
# apps/products/views.py — API Views для товаров
# """

# from rest_framework import generics, filters
# from rest_framework.permissions import AllowAny
# from django_filters.rest_framework import DjangoFilterBackend
# from apps.products.models import Category, Product, ProductReview
# from apps.products.serializers import (
#     CategorySerializer,
#     ProductListSerializer,
#     ProductDetailSerializer,
#     ProductReviewSerializer,
# )


# class CategoryListView(generics.ListAPIView):
#     """
#     GET /api/products/categories/
#     Список категорий
#     """
#     serializer_class = CategorySerializer
#     permission_classes = [AllowAny]

#     def get_queryset(self):
#         return Category.objects.filter(
#             store__domain=self.request.get_host(),
#             is_active=True,
#             is_deleted=False
#         )


# class ProductListView(generics.ListAPIView):
#     """
#     GET /api/products/
#     Список товаров с фильтрацией
#     """
#     serializer_class = ProductListSerializer
#     permission_classes = [AllowAny]
#     filter_backends = [DjangoFilterBackend,
#                        filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ['category', 'available']
#     search_fields = ['name', 'description', 'sku']
#     ordering_fields = ['retail_price', 'rating', 'created']
#     ordering = ['-created']

#     def get_queryset(self):
#         return Product.objects.filter(
#             store__domain=self.request.get_host(),
#             available=True,
#             is_deleted=False
#         ).select_related('category').prefetch_related('images')


# class ProductDetailView(generics.RetrieveAPIView):
#     """
#     GET /api/products/{slug}/
#     Детальная информация о товаре
#     """
#     serializer_class = ProductDetailSerializer
#     permission_classes = [AllowAny]
#     lookup_field = 'slug'

#     def get_queryset(self):
#         return Product.objects.filter(
#             store__domain=self.request.get_host(),
#             is_deleted=False
#         ).select_related('category').prefetch_related('images')

#     def retrieve(self, request, *args, **kwargs):
#         """Увеличиваем счётчик просмотров"""
#         instance = self.get_object()
#         instance.views_count += 1
#         instance.save(update_fields=['views_count'])
#         return super().retrieve(request, *args, **kwargs)


# class ProductReviewListView(generics.ListAPIView):
#     """
#     GET /api/products/{product_id}/reviews/
#     Отзывы о товаре
#     """
#     serializer_class = ProductReviewSerializer
#     permission_classes = [AllowAny]

#     def get_queryset(self):
#         product_id = self.kwargs['product_id']
#         return ProductReview.objects.filter(
#             product_id=product_id,
#             is_approved=True
#         )

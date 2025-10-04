"""
apps/products/views.py — API Views для товаров
"""

from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from apps.products.models import Category, Product, ProductReview
from apps.products.serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductReviewSerializer,
)


class CategoryListView(generics.ListAPIView):
    """
    GET /api/products/categories/
    Список категорий
    """
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Category.objects.filter(
            store__domain=self.request.get_host(),
            is_active=True,
            is_deleted=False
        )


class ProductListView(generics.ListAPIView):
    """
    GET /api/products/
    Список товаров с фильтрацией
    """
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'available']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['retail_price', 'rating', 'created']
    ordering = ['-created']

    def get_queryset(self):
        return Product.objects.filter(
            store__domain=self.request.get_host(),
            available=True,
            is_deleted=False
        ).select_related('category').prefetch_related('images')


class ProductDetailView(generics.RetrieveAPIView):
    """
    GET /api/products/{slug}/
    Детальная информация о товаре
    """
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(
            store__domain=self.request.get_host(),
            is_deleted=False
        ).select_related('category').prefetch_related('images')

    def retrieve(self, request, *args, **kwargs):
        """Увеличиваем счётчик просмотров"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        return super().retrieve(request, *args, **kwargs)


class ProductReviewListView(generics.ListAPIView):
    """
    GET /api/products/{product_id}/reviews/
    Отзывы о товаре
    """
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductReview.objects.filter(
            product_id=product_id,
            is_approved=True
        )

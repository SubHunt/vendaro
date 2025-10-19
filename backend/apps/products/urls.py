"""
apps/products/urls.py — URL маршруты для Products API

Используем ViewSets с DefaultRouter для автоматической генерации URL.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаём роутер для автоматической генерации URL
router = DefaultRouter()

# Регистрируем ViewSets
router.register(r'categories', views.CategoryViewSet, basename='category')
# Товары на корневом уровне
router.register(r'', views.ProductViewSet, basename='product')
router.register(r'reviews', views.ProductReviewViewSet, basename='review')

# URL patterns
urlpatterns = [
    # Подключаем все маршруты из роутера
    # Автоматически создаются:
    # GET    /api/products/                     - список товаров
    # GET    /api/products/{slug}/              - детали товара
    # GET    /api/products/{slug}/reviews/      - отзывы товара
    # POST   /api/products/{slug}/add_review/   - добавить отзыв
    # GET    /api/products/categories/          - список категорий
    # GET    /api/products/categories/{slug}/   - детали категории
    # GET    /api/products/categories/tree/     - дерево категорий
    # GET    /api/products/reviews/             - все отзывы
    path('', include(router.urls)),
]

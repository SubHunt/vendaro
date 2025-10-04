"""
apps/products/urls.py — URL маршруты для Products API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ProductReviewViewSet

# DefaultRouter автоматически создаёт URL для ViewSet
# Генерирует стандартные REST endpoints:
# - GET /categories/ - список
# - GET /categories/{slug}/ - детали
# - и т.д.
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'', ProductViewSet, basename='product')
router.register(r'reviews', ProductReviewViewSet, basename='review')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
]
# """
# apps/products/urls.py — URL маршруты для Products API
# """

# from django.urls import path
# from apps.products import views

# app_name = 'products'

# urlpatterns = [
#     path('categories/', views.CategoryListView.as_view(), name='category-list'),
#     path('', views.ProductListView.as_view(), name='product-list'),
#     path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
#     path('<int:product_id>/reviews/',
#          views.ProductReviewListView.as_view(), name='product-reviews'),
# ]

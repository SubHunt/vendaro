"""
apps/products/urls.py — URL маршруты для Products API
"""

from django.urls import path
from apps.products import views

app_name = 'products'

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('', views.ProductListView.as_view(), name='product-list'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('<int:product_id>/reviews/',
         views.ProductReviewListView.as_view(), name='product-reviews'),
]

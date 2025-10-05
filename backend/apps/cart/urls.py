"""
apps/cart/urls.py — URL маршруты для Cart API
"""

from django.urls import path
from .views import CartViewSet

app_name = 'cart'

urlpatterns = [
    # Получить корзину
    path('', CartViewSet.as_view({'get': 'list'}), name='cart-list'),

    # Добавить товар
    path('add/', CartViewSet.as_view({'post': 'add'}), name='cart-add'),

    # Очистить корзину
    path('clear/', CartViewSet.as_view({'post': 'clear'}), name='cart-clear'),

    # Обновить/удалить товар (один URL для обоих методов)
    path('items/<int:item_id>/', CartViewSet.as_view({
        'patch': 'update_item',
        'delete': 'remove_item'
    }), name='cart-item'),
]

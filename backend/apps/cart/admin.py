"""
apps/cart/admin.py — Регистрация моделей корзины в Django Admin
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Инлайн для товаров в корзине"""
    model = CartItem
    extra = 0
    readonly_fields = ['price', 'get_subtotal']

    def get_subtotal(self, obj):
        """Показывает стоимость позиции"""
        return obj.get_subtotal()
    get_subtotal.short_description = _('Subtotal')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Админка для корзин"""

    list_display = ['user', 'store', 'is_active',
                    'get_items_count', 'created', 'updated']
    list_filter = ['is_active', 'created', 'store']
    search_fields = ['user__email', 'session_key']
    ordering = ['-updated']

    inlines = [CartItemInline]
    readonly_fields = ['created', 'updated']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Админка для товаров в корзине"""

    list_display = ['cart', 'product', 'quantity',
                    'price', 'is_wholesale', 'get_subtotal']
    list_filter = ['is_wholesale', 'created']
    search_fields = ['product__name', 'cart__user__email']
    ordering = ['-created']
    readonly_fields = ['price', 'created', 'updated']

    def get_subtotal(self, obj):
        """Показывает стоимость позиции"""
        return obj.get_subtotal()
    get_subtotal.short_description = _('Subtotal')

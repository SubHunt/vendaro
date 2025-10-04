"""
apps/orders/admin.py — Регистрация моделей заказов в Django Admin
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Инлайн для товаров в заказе"""
    model = OrderItem
    extra = 0
    readonly_fields = ['price', 'get_subtotal']

    def get_subtotal(self, obj):
        """Показывает стоимость позиции"""
        return obj.get_subtotal()
    get_subtotal.short_description = _('Subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка для заказов"""

    list_display = ['order_number', 'user',
                    'store', 'status', 'total', 'created']
    list_filter = ['status', 'is_wholesale', 'created', 'store']
    search_fields = ['order_number', 'user__email', 'email', 'phone']
    ordering = ['-created']

    inlines = [OrderItemInline]

    fieldsets = (
        (_('Order Info'), {
            'fields': ('order_number', 'store', 'user', 'status')
        }),
        (_('Customer Info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        (_('Shipping Address'), {
            'fields': ('shipping_address_line1', 'shipping_address_line2', 'shipping_city', 'shipping_postal_code', 'shipping_country')
        }),
        (_('Amounts'), {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount', 'total')
        }),
        (_('Additional'), {
            'fields': ('is_wholesale', 'customer_note', 'admin_note', 'tracking_number')
        }),
        (_('Dates'), {
            'fields': ('paid_at', 'shipped_at', 'delivered_at', 'created', 'updated')
        }),
    )

    readonly_fields = ['order_number', 'created', 'updated']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Админка для товаров в заказе"""

    list_display = ['order', 'product_name', 'quantity',
                    'price', 'is_wholesale', 'get_subtotal']
    list_filter = ['is_wholesale', 'order__status', 'order__created']
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    readonly_fields = ['price', 'created', 'updated']

    def get_subtotal(self, obj):
        """Показывает стоимость позиции"""
        return obj.get_subtotal()
    get_subtotal.short_description = _('Subtotal')

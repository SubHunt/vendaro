"""
apps/payments/admin.py — Регистрация моделей платежей в Django Admin
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Админка для платежей"""

    list_display = ['order', 'method', 'status',
                    'amount', 'currency', 'created']
    list_filter = ['status', 'method', 'created', 'store']
    search_fields = ['order__order_number', 'note']
    ordering = ['-created']

    fieldsets = (
        (_('Payment Info'), {
            'fields': ('order', 'store', 'method', 'status', 'amount', 'currency')
        }),
        (_('Additional'), {
            'fields': ('note', 'paid_at')
        }),
        (_('Dates'), {
            'fields': ('created', 'updated')
        }),
    )

    readonly_fields = ['created', 'updated']

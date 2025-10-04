"""
apps/stores/admin.py — Регистрация моделей магазинов в Django Admin
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Store, StoreSettings, StoreSocialMedia


class StoreSettingsInline(admin.StackedInline):
    """Инлайн для настроек магазина (редактируется прямо в форме Store)"""
    model = StoreSettings
    can_delete = False
    verbose_name_plural = _('Settings')


class StoreSocialMediaInline(admin.TabularInline):
    """Инлайн для социальных сетей магазина"""
    model = StoreSocialMedia
    extra = 1
    verbose_name_plural = _('Social Media')


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """Админка для магазинов"""

    list_display = ['name', 'domain', 'is_active',
                    'enable_wholesale', 'owner', 'created']
    list_filter = ['is_active', 'enable_wholesale', 'currency', 'created']
    search_fields = ['name', 'domain', 'email', 'slug']
    ordering = ['name']

    # Встроенные формы
    inlines = [StoreSettingsInline, StoreSocialMediaInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('domain', 'name', 'slug', 'description', 'owner')
        }),
        (_('Contact Information'), {
            'fields': ('email', 'phone', 'address', 'city', 'postal_code', 'country')
        }),
        (_('Branding'), {
            'fields': ('logo', 'favicon', 'primary_color', 'secondary_color')
        }),
        (_('Wholesale (B2B)'), {
            'fields': ('enable_wholesale', 'wholesale_discount_percent', 'min_wholesale_order')
        }),
        (_('Currency'), {
            'fields': ('currency', 'currency_symbol')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description')
        }),
        (_('Integrations'), {
            'fields': ('google_analytics_id', 'yandex_metrika_id')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )

    prepopulated_fields = {'slug': ('name',)}


@admin.register(StoreSettings)
class StoreSettingsAdmin(admin.ModelAdmin):
    """Админка для настроек магазина (на случай если нужно редактировать отдельно)"""

    list_display = ['store', 'enable_free_shipping',
                    'free_shipping_threshold', 'min_order_amount']
    search_fields = ['store__name']

    fieldsets = (
        (_('Shipping'), {
            'fields': ('enable_free_shipping', 'free_shipping_threshold', 'shipping_cost')
        }),
        (_('Orders'), {
            'fields': ('min_order_amount', 'max_order_amount')
        }),
        (_('Taxes'), {
            'fields': ('tax_rate', 'tax_included')
        }),
        (_('Notifications'), {
            'fields': ('order_notification_email', 'send_order_confirmation')
        }),
        (_('Policies'), {
            'fields': ('terms_and_conditions', 'privacy_policy', 'return_policy')
        }),
    )


@admin.register(StoreSocialMedia)
class StoreSocialMediaAdmin(admin.ModelAdmin):
    """Админка для социальных сетей"""

    list_display = ['store', 'platform', 'url', 'is_active', 'order']
    list_filter = ['platform', 'is_active']
    search_fields = ['store__name', 'url']
    ordering = ['store', 'order']

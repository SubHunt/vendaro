"""
apps/products/admin.py — Регистрация моделей товаров в Django Admin
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductReview, Size, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий"""

    list_display = ['name', 'parent', 'store', 'is_active', 'order']
    list_filter = ['is_active', 'store', 'created']
    search_fields = ['name', 'slug']
    ordering = ['order', 'name']

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('store', 'name', 'slug', 'description', 'parent')
        }),
        (_('Display'), {
            'fields': ('image', 'order', 'is_active')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description')
        }),
    )

    prepopulated_fields = {'slug': ('name',)}


# ============================================
# СПРАВОЧНИК РАЗМЕРОВ
# ============================================

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    """Админка для размеров"""

    list_display = ['value', 'type', 'order', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['value']
    ordering = ['type', 'order', 'value']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('type', 'value')
        }),
        (_('Настройки'), {
            'fields': ('order', 'is_active')
        }),
    )

    # Действия
    actions = ['activate_sizes', 'deactivate_sizes']

    def activate_sizes(self, request, queryset):
        """Активировать выбранные размеры"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано размеров: {updated}')
    activate_sizes.short_description = "Активировать выбранные размеры"

    def deactivate_sizes(self, request, queryset):
        """Деактивировать выбранные размеры"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано размеров: {updated}')
    deactivate_sizes.short_description = "Деактивировать выбранные размеры"


# ============================================
# ВАРИАНТЫ ТОВАРОВ (INLINE)
# ============================================

class ProductVariantInline(admin.TabularInline):
    """Инлайн для вариантов товара (размеры)"""

    model = ProductVariant
    extra = 0
    fields = [
        'size',
        'stock',
        'price_override',
        'wholesale_price_override',
        'sku',
        'is_active',
        'sales_count',
    ]
    readonly_fields = ['sales_count']

    # Автозаполнение для выбора размера
    autocomplete_fields = ['size']

    def get_queryset(self, request):
        """Оптимизация запросов"""
        qs = super().get_queryset(request)
        return qs.select_related('size')


# ============================================
# ИЗОБРАЖЕНИЯ ТОВАРА (INLINE)
# ============================================

class ProductImageInline(admin.TabularInline):
    """Инлайн для фотографий товара"""
    model = ProductImage
    extra = 1
    fields = ['image', 'is_main', 'order', 'alt_text']


# ============================================
# ТОВАРЫ
# ============================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""

    list_display = [
        'name',
        'category',
        'store',
        'has_variants_display',
        'retail_price',
        'stock_display',
        'available',
    ]
    list_filter = ['available', 'has_variants', 'category', 'store', 'created']
    search_fields = ['name', 'slug', 'sku']
    ordering = ['-created']

    inlines = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'store',
                'category',
                'name',
                'slug',
                'description',
                'short_description'
            )
        }),
        (_('Variants'), {
            'fields': ('has_variants',),
            'description': 'Если товар имеет варианты (размеры), установите галочку. '
            'Затем добавьте варианты в разделе "Варианты товаров" ниже.'
        }),
        (_('Pricing'), {
            'fields': (
                'retail_price',
                'wholesale_price',
                'discount_price',
                'compare_at_price',
                'cost_price'
            )
        }),
        (_('Inventory'), {
            'fields': ('stock', 'available', 'sku', 'barcode', 'track_stock'),
            'description': 'Если товар имеет варианты, stock управляется через варианты.'
        }),
        (_('Specifications'), {
            'fields': ('specifications',)
        }),
        (_('Statistics'), {
            'fields': ('rating', 'reviews_count', 'views_count', 'sales_count'),
            'classes': ('collapse',)
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )

    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['rating', 'reviews_count', 'views_count', 'sales_count']

    def has_variants_display(self, obj):
        """Отображение наличия вариантов"""
        if obj.has_variants:
            count = obj.variants.filter(is_active=True).count()
            return format_html(
                '<span style="color: green;">✓</span> {} шт.',
                count
            )
        return format_html('<span style="color: gray;">—</span>')
    has_variants_display.short_description = 'Варианты'

    def stock_display(self, obj):
        """Отображение остатков"""
        if obj.has_variants:
            total_stock = obj.get_total_stock()
            variants_in_stock = obj.variants.filter(
                stock__gt=0, is_active=True).count()
            return format_html(
                '{} шт. ({} вар.)',
                total_stock,
                variants_in_stock
            )
        return obj.stock
    stock_display.short_description = 'Stock'


# ============================================
# ВАРИАНТЫ ТОВАРОВ (отдельная админка)
# ============================================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Админка для вариантов товаров"""

    list_display = [
        'product',
        'size',
        'stock',
        'price_display',
        'sku',
        'is_active',
        'sales_count',
    ]
    list_filter = ['is_active', 'size__type', 'product__store']
    search_fields = [
        'product__name',
        'size__value',
        'sku',
    ]
    ordering = ['product', 'size__order']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('product', 'size', 'is_active')
        }),
        (_('Склад'), {
            'fields': ('stock', 'sales_count')
        }),
        (_('Цены'), {
            'fields': ('price_override', 'wholesale_price_override'),
            'description': 'Оставьте пустым, чтобы использовать цены товара.'
        }),
        (_('Артикулы'), {
            'fields': ('sku', 'barcode')
        }),
    )

    readonly_fields = ['sales_count']
    autocomplete_fields = ['product', 'size']

    def price_display(self, obj):
        """Отображение цены"""
        retail = obj.get_retail_price()
        if obj.price_override:
            return format_html(
                '<strong>{}</strong> ₽',
                retail
            )
        return f'{retail} ₽'
    price_display.short_description = 'Цена'

    # Действия
    actions = ['activate_variants', 'deactivate_variants', 'reset_prices']

    def activate_variants(self, request, queryset):
        """Активировать варианты"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано вариантов: {updated}')
    activate_variants.short_description = "Активировать выбранные варианты"

    def deactivate_variants(self, request, queryset):
        """Деактивировать варианты"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано вариантов: {updated}')
    deactivate_variants.short_description = "Деактивировать выбранные варианты"

    def reset_prices(self, request, queryset):
        """Сбросить переопределённые цены (использовать цены товара)"""
        updated = queryset.update(
            price_override=None,
            wholesale_price_override=None
        )
        self.message_user(request, f'Сброшены цены для {updated} вариантов')
    reset_prices.short_description = "Сбросить переопределённые цены"


# ============================================
# ИЗОБРАЖЕНИЯ И ОТЗЫВЫ
# ============================================

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Админка для фотографий товаров"""

    list_display = ['product', 'is_main', 'order']
    list_filter = ['is_main']
    search_fields = ['product__name']
    ordering = ['product', 'order']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Админка для отзывов"""

    list_display = ['product', 'user', 'rating',
                    'is_verified', 'is_approved', 'created']
    list_filter = ['rating', 'is_verified', 'is_approved', 'created']
    search_fields = ['product__name', 'user__email', 'comment']
    ordering = ['-created']

    fieldsets = (
        (_('Review'), {
            'fields': ('product', 'user', 'rating', 'comment')
        }),
        (_('Status'), {
            'fields': ('is_verified', 'is_approved')
        }),
    )

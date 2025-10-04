"""
apps/products/admin.py — Регистрация моделей товаров в Django Admin
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, ProductImage, ProductReview


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


class ProductImageInline(admin.TabularInline):
    """Инлайн для фотографий товара"""
    model = ProductImage
    extra = 1
    fields = ['image', 'is_main', 'order', 'alt_text']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""

    list_display = ['name', 'category', 'store',
                    'retail_price', 'wholesale_price', 'stock', 'available']
    list_filter = ['available', 'category', 'store', 'created']
    search_fields = ['name', 'slug', 'sku']
    ordering = ['-created']

    inlines = [ProductImageInline]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('store', 'category', 'name', 'slug', 'description', 'short_description')
        }),
        (_('Pricing'), {
            'fields': ('retail_price', 'wholesale_price', 'discount_price', 'compare_at_price', 'cost_price')
        }),
        (_('Inventory'), {
            'fields': ('stock', 'available', 'sku', 'barcode', 'track_stock')
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

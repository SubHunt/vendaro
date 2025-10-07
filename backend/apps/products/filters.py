"""
apps/products/filters.py — Фильтры для Products API
"""

import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Фильтры для товаров.

    Использование:
    /api/products/?min_price=1000&max_price=5000&in_stock=true&category=1
    """

    # Фильтры по цене
    min_price = django_filters.NumberFilter(
        field_name='retail_price',
        lookup_expr='gte',
        label='Минимальная цена'
    )
    max_price = django_filters.NumberFilter(
        field_name='retail_price',
        lookup_expr='lte',
        label='Максимальная цена'
    )

    # Фильтр по наличию
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock',
        label='Только в наличии'
    )

    # Фильтр по рейтингу
    min_rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte',
        label='Минимальный рейтинг'
    )

    # Фильтр по категории (включая подкатегории)
    category_tree = django_filters.NumberFilter(
        method='filter_category_tree',
        label='Категория (с подкатегориями)'
    )

    class Meta:
        model = Product
        fields = {
            'category': ['exact'],
            'available': ['exact'],
        }

    def filter_in_stock(self, queryset, name, value):
        """Фильтр товаров в наличии"""
        if value:
            return queryset.filter(stock__gt=0, track_stock=True) | queryset.filter(track_stock=False)
        return queryset

    def filter_category_tree(self, queryset, name, value):
        """Фильтр по категории включая все подкатегории"""
        from apps.products.models import Category

        try:
            category = Category.objects.get(id=value)
            # Получаем все подкатегории рекурсивно
            categories = [category.id]

            def get_children(cat):
                for child in cat.children.all():
                    categories.append(child.id)
                    get_children(child)

            get_children(category)
            return queryset.filter(category__id__in=categories)
        except Category.DoesNotExist:
            return queryset.none()

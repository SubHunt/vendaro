"""
apps/products/serializers.py — Сериализаторы для Products API

ИСПРАВЛЕНО: Убрано source='variants.filter()' - теперь используется prefetch
"""

from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview, Size, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""

    full_path = serializers.CharField(source='get_full_path', read_only=True)
    children_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'parent',
            'full_path',
            'image',
            'order',
            'is_active',
            'children_count',
            'products_count',
            'meta_title',
            'meta_description',
            'created',
            'updated',
        ]
        read_only_fields = ['created', 'updated']

    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count()

    def get_products_count(self, obj):
        return obj.products.filter(available=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    """Сериализатор для фотографий товара"""

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_main', 'order', 'alt_text']


class ProductReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов"""

    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            'id',
            'user',
            'user_name',
            'rating',
            'comment',
            'is_verified',
            'is_approved',
            'created',
        ]
        read_only_fields = ['user', 'is_verified', 'is_approved', 'created']


# ============================================
# РАЗМЕРЫ И ВАРИАНТЫ
# ============================================

class SizeSerializer(serializers.ModelSerializer):
    """Сериализатор для размеров"""

    type_display = serializers.CharField(
        source='get_type_display', read_only=True)

    class Meta:
        model = Size
        fields = ['id', 'type', 'type_display', 'value', 'order']


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вариантов товара.

    Пример JSON:
    {
        "id": 1,
        "size": {"id": 5, "value": "M", "type": "clothing"},
        "stock": 10,
        "price": 15000.00,
        "wholesale_price": 12500.00,
        "sku": "WETSUIT-5MM-M",
        "is_in_stock": true,
        "is_active": true
    }
    """

    size = SizeSerializer(read_only=True)
    price = serializers.SerializerMethodField()
    wholesale_price = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'size',
            'stock',
            'price',
            'wholesale_price',
            'sku',
            'is_in_stock',
            'is_active',
        ]

    def get_price(self, obj):
        """Розничная цена варианта"""
        return float(obj.get_retail_price())

    def get_wholesale_price(self, obj):
        """Оптовая цена варианта"""
        return float(obj.get_wholesale_price())

    def get_is_in_stock(self, obj):
        """Проверка наличия варианта на складе"""
        return obj.is_in_stock()


class ProductVariantDetailSerializer(ProductVariantSerializer):
    """
    Детальный сериализатор варианта (для корзины, заказов).

    Включает информацию о товаре.
    """

    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)

    class Meta(ProductVariantSerializer.Meta):
        fields = ProductVariantSerializer.Meta.fields + [
            'product_name',
            'product_slug',
        ]


# ============================================
# ТОВАРЫ
# ============================================

class ProductListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка товаров.

    Облегчённая версия для каталога.
    """

    category_name = serializers.CharField(
        source='category.name', read_only=True)
    main_image = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()
    price_info = serializers.SerializerMethodField()

    # Информация о вариантах
    has_variants = serializers.BooleanField(read_only=True)
    variants_count = serializers.SerializerMethodField()
    available_sizes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'short_description',
            'category',
            'category_name',
            'main_image',
            'retail_price',
            'wholesale_price',
            'discount_price',
            'current_price',
            'price_info',
            'stock',
            'available',
            'rating',
            'reviews_count',
            'has_variants',
            'variants_count',
            'available_sizes',
            'created',
        ]

    def get_main_image(self, obj):
        """Получаем главное фото товара"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
        return None

    def get_current_price(self, obj):
        """Актуальная цена для текущего пользователя"""
        request = self.context.get('request')
        user = request.user if request else None
        price, is_wholesale = obj.get_price_for_user(user)
        return float(price)

    def get_price_info(self, obj):
        """Информация о ценах для фронтенда"""
        request = self.context.get('request')
        user = request.user if request else None
        price, is_wholesale = obj.get_price_for_user(user)

        info = {
            'price': float(price),
            'is_wholesale': is_wholesale,
        }

        if obj.has_discount():
            info['original_price'] = float(obj.retail_price)
            discount_percent = (
                (obj.retail_price - price) / obj.retail_price) * 100
            info['discount_percent'] = round(discount_percent)

        if is_wholesale and obj.wholesale_price:
            info['retail_price'] = float(obj.retail_price)

        return info

    def get_variants_count(self, obj):
        """Количество активных вариантов"""
        if not obj.has_variants:
            return 0
        return obj.variants.filter(is_active=True).count()

    def get_available_sizes(self, obj):
        """Список доступных размеров (краткий)"""
        if not obj.has_variants:
            return []

        variants = obj.variants.filter(
            stock__gt=0,
            is_active=True
        ).select_related('size').order_by('size__order')

        return [v.size.value for v in variants]


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детальной страницы товара.

    Полная версия со всеми данными, включая варианты.

    ИСПРАВЛЕНИЕ: Убрано source='variants.filter()' - теперь варианты
    загружаются через prefetch_related в views.py
    """

    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    current_price = serializers.SerializerMethodField()
    price_info = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(source='is_in_stock', read_only=True)
    available_sizes = serializers.SerializerMethodField()

    # ИСПРАВЛЕНО: Убрано source - варианты приходят из prefetch
    variants = ProductVariantSerializer(many=True, read_only=True)
    total_stock = serializers.IntegerField(
        source='get_total_stock', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'short_description',
            'category',
            'images',
            'retail_price',
            'wholesale_price',
            'discount_price',
            'compare_at_price',
            'current_price',
            'price_info',
            'stock',
            'available',
            'in_stock',
            'sku',
            'barcode',
            'specifications',
            'rating',
            'reviews_count',
            'reviews',
            'views_count',
            'sales_count',
            'has_variants',
            'variants',  # ← Загружается через prefetch
            'total_stock',
            'available_sizes',
            'meta_title',
            'meta_description',
            'created',
            'updated',
        ]
        read_only_fields = [
            'rating',
            'reviews_count',
            'views_count',
            'sales_count',
            'created',
            'updated'
        ]

    def get_available_sizes(self, obj):
        """Список доступных размеров (только в наличии)"""
        if not obj.has_variants:
            return []

        # Используем prefetch - варианты уже загружены!
        variants = [v for v in obj.variants.all() if v.stock >
                    0 and v.is_active]
        return [v.size.value for v in variants]

    def get_current_price(self, obj):
        """Актуальная цена для текущего пользователя"""
        request = self.context.get('request')
        user = request.user if request else None
        price, is_wholesale = obj.get_price_for_user(user)
        return float(price)

    def get_price_info(self, obj):
        """Полная информация о ценах"""
        request = self.context.get('request')
        user = request.user if request else None
        price, is_wholesale = obj.get_price_for_user(user)

        info = {
            'price': float(price),
            'is_wholesale': is_wholesale,
            'currency': obj.store.currency_symbol,
        }

        if obj.has_discount():
            info['original_price'] = float(obj.retail_price)
            discount_percent = (
                (obj.retail_price - price) / obj.retail_price) * 100
            info['discount_percent'] = round(discount_percent)

        if is_wholesale and obj.wholesale_price:
            info['retail_price'] = float(obj.retail_price)
            info['wholesale_savings'] = float(obj.retail_price - price)

        return info
# """
# apps/products/serializers.py — Сериализаторы для Products API

# Добавлена поддержка вариантов товаров (размеры).
# """

# from rest_framework import serializers
# from .models import Category, Product, ProductImage, ProductReview, Size, ProductVariant


# class CategorySerializer(serializers.ModelSerializer):
#     """Сериализатор для категорий"""

#     full_path = serializers.CharField(source='get_full_path', read_only=True)
#     children_count = serializers.SerializerMethodField()
#     products_count = serializers.SerializerMethodField()

#     class Meta:
#         model = Category
#         fields = [
#             'id',
#             'name',
#             'slug',
#             'description',
#             'parent',
#             'full_path',
#             'image',
#             'order',
#             'is_active',
#             'children_count',
#             'products_count',
#             'meta_title',
#             'meta_description',
#             'created',
#             'updated',
#         ]
#         read_only_fields = ['created', 'updated']

#     def get_children_count(self, obj):
#         return obj.children.filter(is_active=True).count()

#     def get_products_count(self, obj):
#         return obj.products.filter(available=True).count()


# class ProductImageSerializer(serializers.ModelSerializer):
#     """Сериализатор для фотографий товара"""

#     class Meta:
#         model = ProductImage
#         fields = ['id', 'image', 'is_main', 'order', 'alt_text']


# class ProductReviewSerializer(serializers.ModelSerializer):
#     """Сериализатор для отзывов"""

#     user_name = serializers.CharField(
#         source='user.get_full_name', read_only=True)

#     class Meta:
#         model = ProductReview
#         fields = [
#             'id',
#             'user',
#             'user_name',
#             'rating',
#             'comment',
#             'is_verified',
#             'is_approved',
#             'created',
#         ]
#         read_only_fields = ['user', 'is_verified', 'is_approved', 'created']


# # ============================================
# # РАЗМЕРЫ И ВАРИАНТЫ
# # ============================================

# class SizeSerializer(serializers.ModelSerializer):
#     """Сериализатор для размеров"""

#     type_display = serializers.CharField(
#         source='get_type_display', read_only=True)

#     class Meta:
#         model = Size
#         fields = ['id', 'type', 'type_display', 'value', 'order']


# class ProductVariantSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор для вариантов товара.

#     Пример JSON:
#     {
#         "id": 1,
#         "size": {"id": 5, "value": "M", "type": "clothing"},
#         "stock": 10,
#         "price": 15000.00,
#         "wholesale_price": 12500.00,
#         "sku": "WETSUIT-5MM-M",
#         "is_in_stock": true,
#         "is_active": true
#     }
#     """

#     size = SizeSerializer(read_only=True)
#     price = serializers.SerializerMethodField()
#     wholesale_price = serializers.SerializerMethodField()
#     # is_in_stock = serializers.BooleanField(
#     #     source='is_in_stock', read_only=True)
#     is_in_stock = serializers.SerializerMethodField()

#     class Meta:
#         model = ProductVariant
#         fields = [
#             'id',
#             'size',
#             'stock',
#             'price',
#             'wholesale_price',
#             'sku',
#             'is_in_stock',
#             'is_active',
#         ]

#     def get_price(self, obj):
#         """Розничная цена варианта"""
#         return float(obj.get_retail_price())

#     def get_wholesale_price(self, obj):
#         """Оптовая цена варианта"""
#         return float(obj.get_wholesale_price())

#     def get_is_in_stock(self, obj):
#         """Проверка наличия варианта на складе"""
#         return obj.is_in_stock()


# class ProductVariantDetailSerializer(ProductVariantSerializer):
#     """
#     Детальный сериализатор варианта (для корзины, заказов).

#     Включает информацию о товаре.
#     """

#     product_name = serializers.CharField(source='product.name', read_only=True)
#     product_slug = serializers.CharField(source='product.slug', read_only=True)

#     class Meta(ProductVariantSerializer.Meta):
#         fields = ProductVariantSerializer.Meta.fields + [
#             'product_name',
#             'product_slug',
#         ]


# # ============================================
# # ТОВАРЫ
# # ============================================

# class ProductListSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор для списка товаров.

#     Облегчённая версия для каталога.
#     """

#     category_name = serializers.CharField(
#         source='category.name', read_only=True)
#     main_image = serializers.SerializerMethodField()
#     current_price = serializers.SerializerMethodField()
#     price_info = serializers.SerializerMethodField()

#     # Информация о вариантах
#     has_variants = serializers.BooleanField(read_only=True)
#     variants_count = serializers.SerializerMethodField()
#     available_sizes = serializers.SerializerMethodField()

#     class Meta:
#         model = Product
#         fields = [
#             'id',
#             'name',
#             'slug',
#             'short_description',
#             'category',
#             'category_name',
#             'main_image',
#             'retail_price',
#             'wholesale_price',
#             'discount_price',
#             'current_price',
#             'price_info',
#             'stock',
#             'available',
#             'rating',
#             'reviews_count',
#             'has_variants',
#             'variants_count',
#             'available_sizes',
#             'created',
#         ]

#     def get_main_image(self, obj):
#         """Получаем главное фото товара"""
#         main_image = obj.images.filter(is_main=True).first()
#         if main_image:
#             request = self.context.get('request')
#             if request:
#                 return request.build_absolute_uri(main_image.image.url)
#         return None

#     def get_current_price(self, obj):
#         """Актуальная цена для текущего пользователя"""
#         request = self.context.get('request')
#         user = request.user if request else None
#         price, is_wholesale = obj.get_price_for_user(user)
#         return float(price)

#     def get_price_info(self, obj):
#         """Информация о ценах для фронтенда"""
#         request = self.context.get('request')
#         user = request.user if request else None
#         price, is_wholesale = obj.get_price_for_user(user)

#         info = {
#             'price': float(price),
#             'is_wholesale': is_wholesale,
#         }

#         if obj.has_discount():
#             info['original_price'] = float(obj.retail_price)
#             discount_percent = (
#                 (obj.retail_price - price) / obj.retail_price) * 100
#             info['discount_percent'] = round(discount_percent)

#         if is_wholesale and obj.wholesale_price:
#             info['retail_price'] = float(obj.retail_price)

#         return info

#     def get_variants_count(self, obj):
#         """Количество активных вариантов"""
#         if not obj.has_variants:
#             return 0
#         return obj.variants.filter(is_active=True).count()

#     def get_available_sizes(self, obj):
#         """Список доступных размеров (краткий)"""
#         if not obj.has_variants:
#             return []

#         variants = obj.variants.filter(
#             stock__gt=0,
#             is_active=True
#         ).select_related('size').order_by('size__order')

#         return [v.size.value for v in variants]


# class ProductDetailSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор для детальной страницы товара.

#     Полная версия со всеми данными, включая варианты.
#     """

#     category = CategorySerializer(read_only=True)
#     images = ProductImageSerializer(many=True, read_only=True)
#     reviews = ProductReviewSerializer(many=True, read_only=True)
#     current_price = serializers.SerializerMethodField()
#     price_info = serializers.SerializerMethodField()
#     in_stock = serializers.BooleanField(source='is_in_stock', read_only=True)
#     available_sizes = serializers.SerializerMethodField()

#     # Варианты
#     variants = ProductVariantSerializer(
#         many=True, read_only=True, source='variants.filter(is_active=True)')
#     total_stock = serializers.IntegerField(
#         source='get_total_stock', read_only=True)

#     class Meta:
#         model = Product
#         fields = [
#             'id',
#             'name',
#             'slug',
#             'description',
#             'short_description',
#             'category',
#             'images',
#             'retail_price',
#             'wholesale_price',
#             'discount_price',
#             'compare_at_price',
#             'current_price',
#             'price_info',
#             'stock',
#             'available',
#             'in_stock',
#             'sku',
#             'barcode',
#             'specifications',
#             'rating',
#             'reviews_count',
#             'reviews',
#             'views_count',
#             'sales_count',
#             'has_variants',
#             'variants',
#             'total_stock',
#             'meta_title',
#             'meta_description',
#             'created',
#             'updated',
#             'available_sizes',
#         ]
#         read_only_fields = [
#             'rating',
#             'reviews_count',
#             'views_count',
#             'sales_count',
#             'created',
#             'updated'
#         ]

#     def get_available_sizes(self, obj):
#         """Список доступных размеров"""
#         if not obj.has_variants:
#             return []
#         variants = obj.variants.filter(
#             stock__gt=0, is_active=True).select_related('size')
#         return [v.size.value for v in variants]

#     def get_current_price(self, obj):
#         """Актуальная цена для текущего пользователя"""
#         request = self.context.get('request')
#         user = request.user if request else None
#         price, is_wholesale = obj.get_price_for_user(user)
#         return float(price)

#     def get_price_info(self, obj):
#         """Полная информация о ценах"""
#         request = self.context.get('request')
#         user = request.user if request else None
#         price, is_wholesale = obj.get_price_for_user(user)

#         info = {
#             'price': float(price),
#             'is_wholesale': is_wholesale,
#             'currency': obj.store.currency_symbol,
#         }

#         if obj.has_discount():
#             info['original_price'] = float(obj.retail_price)
#             discount_percent = (
#                 (obj.retail_price - price) / obj.retail_price) * 100
#             info['discount_percent'] = round(discount_percent)

#         if is_wholesale and obj.wholesale_price:
#             info['retail_price'] = float(obj.retail_price)
#             info['wholesale_savings'] = float(obj.retail_price - price)

#         return info

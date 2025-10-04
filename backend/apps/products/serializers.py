"""
apps/products/serializers.py — Сериализаторы для Products API

Сериализаторы преобразуют модели Django в JSON и обратно.
"""

from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""

    # Добавляем вычисляемые поля
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
        """Количество подкатегорий"""
        return obj.children.filter(is_active=True).count()

    def get_products_count(self, obj):
        """Количество товаров в категории"""
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


class ProductListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка товаров.

    Облегчённая версия - без полного описания и характеристик.
    """

    category_name = serializers.CharField(
        source='category.name', read_only=True)
    main_image = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()
    price_info = serializers.SerializerMethodField()

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
        """
        Информация о ценах для фронтенда.

        Возвращает:
        {
            'price': 8900.00,           # Текущая цена
            'original_price': 10000.00, # Если есть скидка
            'is_wholesale': False,
            'discount_percent': 10
        }
        """
        request = self.context.get('request')
        user = request.user if request else None
        price, is_wholesale = obj.get_price_for_user(user)

        info = {
            'price': float(price),
            'is_wholesale': is_wholesale,
        }

        # Если есть скидка
        if obj.has_discount():
            info['original_price'] = float(obj.retail_price)
            discount_percent = (
                (obj.retail_price - price) / obj.retail_price) * 100
            info['discount_percent'] = round(discount_percent)

        # Если оптовая цена
        if is_wholesale and obj.wholesale_price:
            info['retail_price'] = float(obj.retail_price)

        return info


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детальной страницы товара.

    Полная версия со всеми данными.
    """

    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    current_price = serializers.SerializerMethodField()
    price_info = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(source='is_in_stock', read_only=True)

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
            'meta_title',
            'meta_description',
            'created',
            'updated',
        ]
        read_only_fields = ['rating', 'reviews_count',
                            'views_count', 'sales_count', 'created', 'updated']

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
# apps/products/serializers.py — Serializers для API товаров

# Serializers преобразуют Python объекты (модели Django) в JSON
# и наоборот (JSON → Python объекты).

# Это нужно для REST API — фронтенд (React) общается с бэкендом через JSON.
# """

# from rest_framework import serializers
# from apps.products.models import Category, Product, ProductImage, ProductReview


# # ============================================
# # SERIALIZER ДЛЯ ИЗОБРАЖЕНИЙ ТОВАРА
# # ============================================

# class ProductImageSerializer(serializers.ModelSerializer):
#     """
#     Serializer для изображений товара.

#     Преобразует:
#     ProductImage → JSON

#     Пример JSON:
#     {
#       "id": 1,
#       "image": "http://localhost:8000/media/products/2025/01/mask.jpg",
#       "is_main": true,
#       "alt_text": "Маска Cressi"
#     }
#     """

#     class Meta:
#         model = ProductImage
#         fields = ['id', 'image', 'is_main', 'order', 'alt_text']


# # ============================================
# # SERIALIZER ДЛЯ КАТЕГОРИЙ
# # ============================================

# class CategorySerializer(serializers.ModelSerializer):
#     """
#     Serializer для категорий товаров.

#     Пример JSON:
#     {
#       "id": 1,
#       "name": "Маски для дайвинга",
#       "slug": "maski-dlya-dayvinga",
#       "parent": null,
#       "image": "...",
#       "products_count": 15
#     }
#     """

#     # products_count — количество товаров в категории
#     # SerializerMethodField — вычисляемое поле (не из модели)
#     products_count = serializers.SerializerMethodField()

#     class Meta:
#         model = Category
#         fields = [
#             'id',
#             'name',
#             'slug',
#             'description',
#             'parent',
#             'image',
#             'order',
#             'is_active',
#             'products_count',
#         ]

#     def get_products_count(self, obj):
#         """
#         Вычисляет количество товаров в категории.

#         Параметры:
#         - obj: объект Category

#         Возвращает:
#         - int: количество товаров
#         """
#         return obj.products.filter(available=True, is_deleted=False).count()


# # ============================================
# # SERIALIZER ДЛЯ СПИСКА ТОВАРОВ (краткий)
# # ============================================

# class ProductListSerializer(serializers.ModelSerializer):
#     """
#     Краткий serializer для списка товаров.

#     Используется в каталоге товаров (список карточек).
#     Не включает полное описание, характеристики — только основное.

#     Пример JSON:
#     {
#       "id": 1,
#       "name": "Маска Cressi Big Eyes",
#       "slug": "maska-cressi-big-eyes",
#       "retail_price": "8900.00",
#       "wholesale_price": "7500.00",
#       "main_image": "http://...",
#       "rating": "4.50",
#       "reviews_count": 12,
#       "available": true,
#       "in_stock": true
#     }
#     """

#     # main_image — главное изображение товара
#     main_image = serializers.SerializerMethodField()

#     # in_stock — есть ли товар на складе
#     in_stock = serializers.SerializerMethodField()

#     # category_name — название категории
#     category_name = serializers.CharField(
#         source='category.name', read_only=True)

#     class Meta:
#         model = Product
#         fields = [
#             'id',
#             'name',
#             'slug',
#             'short_description',
#             'retail_price',
#             'wholesale_price',
#             'discount_price',
#             'category_name',
#             'main_image',
#             'rating',
#             'reviews_count',
#             'available',
#             'in_stock',
#         ]

#     def get_main_image(self, obj):
#         """
#         Возвращает URL главного изображения товара.

#         Если есть is_main=True — возвращаем его.
#         Иначе возвращаем первое изображение.
#         """
#         # Ищем главное изображение
#         main_image = obj.images.filter(is_main=True).first()

#         # Если нет главного — берём первое
#         if not main_image:
#             main_image = obj.images.first()

#         # Возвращаем URL
#         if main_image:
#             request = self.context.get('request')
#             return request.build_absolute_uri(main_image.image.url) if request else main_image.image.url

#         return None

#     def get_in_stock(self, obj):
#         """Проверяет есть ли товар на складе"""
#         return obj.is_in_stock()


# # ============================================
# # SERIALIZER ДЛЯ ДЕТАЛЬНОЙ СТРАНИЦЫ ТОВАРА
# # ============================================

# class ProductDetailSerializer(serializers.ModelSerializer):
#     """
#     Полный serializer для детальной страницы товара.

#     Включает всё: описание, характеристики, фото, отзывы.

#     Пример JSON:
#     {
#       "id": 1,
#       "name": "Маска Cressi Big Eyes Evolution",
#       "description": "Полное описание...",
#       "retail_price": "8900.00",
#       "wholesale_price": "7500.00",
#       "specifications": {
#         "material": "Силикон",
#         "color": "Черный"
#       },
#       "images": [...],
#       "category": {...},
#       "rating": "4.50",
#       "reviews_count": 12
#     }
#     """

#     # images — все изображения товара
#     images = ProductImageSerializer(many=True, read_only=True)

#     # category — полная информация о категории
#     category = CategorySerializer(read_only=True)

#     # in_stock
#     in_stock = serializers.SerializerMethodField()

#     # price_for_user — цена для текущего пользователя (B2B/B2C)
#     price_for_user = serializers.SerializerMethodField()

#     class Meta:
#         model = Product
#         fields = [
#             'id',
#             'name',
#             'slug',
#             'description',
#             'short_description',
#             'retail_price',
#             'wholesale_price',
#             'discount_price',
#             'compare_at_price',
#             'sku',
#             'stock',
#             'available',
#             'in_stock',
#             'specifications',
#             'rating',
#             'reviews_count',
#             'views_count',
#             'category',
#             'images',
#             'price_for_user',
#             'created',
#             'updated',
#         ]

#     def get_in_stock(self, obj):
#         """Проверяет наличие на складе"""
#         return obj.is_in_stock()

#     def get_price_for_user(self, obj):
#         """
#         Возвращает цену для текущего пользователя.

#         Учитывает является ли пользователь оптовиком (B2B).

#         Возвращает:
#         {
#           "price": "8500.00",
#           "is_wholesale": true
#         }
#         """
#         request = self.context.get('request')
#         user = request.user if request and request.user.is_authenticated else None

#         price, is_wholesale = obj.get_price_for_user(user)

#         return {
#             'price': str(price),
#             'is_wholesale': is_wholesale,
#         }


# # ============================================
# # SERIALIZER ДЛЯ ОТЗЫВОВ
# # ============================================

# class ProductReviewSerializer(serializers.ModelSerializer):
#     """
#     Serializer для отзывов о товаре.

#     Пример JSON:
#     {
#       "id": 1,
#       "user_name": "Иван П.",
#       "rating": 5,
#       "comment": "Отличная маска!",
#       "is_verified": true,
#       "created": "2025-01-03T10:00:00Z"
#     }
#     """

#     # user_name — имя пользователя (без email для приватности)
#     user_name = serializers.CharField(
#         source='user.get_short_name', read_only=True)

#     class Meta:
#         model = ProductReview
#         fields = [
#             'id',
#             'user_name',
#             'rating',
#             'comment',
#             'is_verified',
#             'is_approved',
#             'created',
#         ]
#         read_only_fields = ['is_verified', 'is_approved', 'created']


# # ============================================
# # ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# # ============================================

# # В views.py:
# #
# # from rest_framework import generics
# # from apps.products.models import Product
# # from apps.products.serializers import ProductListSerializer
# #
# # class ProductListView(generics.ListAPIView):
# #     queryset = Product.objects.filter(available=True)
# #     serializer_class = ProductListSerializer
# #
# # Запрос: GET /api/products/
# # Ответ:
# # [
# #   {
# #     "id": 1,
# #     "name": "Маска Cressi",
# #     "retail_price": "8900.00",
# #     ...
# #   },
# #   ...
# # ]

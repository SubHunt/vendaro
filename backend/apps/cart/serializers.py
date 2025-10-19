"""
apps/cart/serializers.py — Сериализаторы для Cart API

Обновлено: добавлена поддержка вариантов товаров.
"""

from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import Product, ProductVariant


class CartItemProductSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор товара для корзины"""

    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'main_image',
                  'stock', 'available', 'has_variants']

    def get_main_image(self, obj):
        """Главное фото товара"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
        return None


class CartItemVariantSerializer(serializers.ModelSerializer):
    """Сериализатор варианта для корзины"""

    size_value = serializers.CharField(source='size.value', read_only=True)
    size_type = serializers.CharField(source='size.type', read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'size_value', 'size_type', 'stock', 'sku']


class CartItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для товара в корзине.

    Пример JSON:
    {
        "id": 1,
        "product": {...},
        "variant": {"id": 5, "size_value": "M", "stock": 10},
        "quantity": 2,
        "price": 15000.00,
        "subtotal": 30000.00,
        "is_available": true
    }
    """

    product = CartItemProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    variant = CartItemVariantSerializer(read_only=True)
    variant_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True)

    subtotal = serializers.DecimalField(
        source='get_subtotal',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    # is_available = serializers.BooleanField(
    #     source='is_available',
    #     read_only=True
    # )
    is_available = serializers.SerializerMethodField()
    available_stock = serializers.SerializerMethodField()
    # available_stock = serializers.IntegerField(
    #     source='get_available_stock',
    #     read_only=True
    # )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_id',
            'variant',
            'variant_id',
            'quantity',
            'price',
            'is_wholesale',
            'subtotal',
            'is_available',
            'available_stock',
            'created',
            'updated',
        ]
        read_only_fields = ['price', 'is_wholesale', 'created', 'updated']

    def validate_product_id(self, value):
        """Проверка что товар существует и доступен"""
        try:
            product = Product.objects.get(
                id=value,
                store=self.context['request'].store,
                available=True
            )
        except Product.DoesNotExist:
            raise serializers.ValidationError('Товар не найден или недоступен')

        # Сохраняем для использования в validate()
        self.product = product
        return value

    def validate_variant_id(self, value):
        """Проверка что вариант существует и доступен"""
        if value is None:
            return None

        try:
            variant = ProductVariant.objects.get(
                id=value,
                is_active=True
            )
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError(
                'Вариант не найден или недоступен')

        # Сохраняем для использования в validate()
        self.variant = variant
        return value

    def get_is_available(self, obj):
        """Проверка доступности товара"""
        return obj.is_available()

    def get_available_stock(self, obj):
        """Получить доступный stock"""
        return obj.get_available_stock()

    def validate_quantity(self, value):
        """Проверка количества"""
        if value < 1:
            raise serializers.ValidationError(
                'Количество должно быть больше 0')
        if value > 9999:
            raise serializers.ValidationError('Слишком большое количество')
        return value

    def validate(self, attrs):
        """
        Комплексная валидация.

        Проверяет:
        - Если товар has_variants - требуется variant_id
        - Если товар без вариантов - variant_id не нужен
        - Соответствие варианта товару
        - Наличие на складе
        """
        product_id = attrs.get('product_id')
        variant_id = attrs.get('variant_id')
        quantity = attrs.get('quantity', 1)

        # Получаем product и variant из validate_*
        product = getattr(self, 'product', None)
        variant = getattr(self, 'variant', None)

        if not product:
            return attrs

        # Проверка: товар с вариантами требует variant_id
        if product.has_variants and not variant_id:
            raise serializers.ValidationError({
                'variant_id': 'Для этого товара необходимо выбрать размер'
            })

        # Проверка: товар без вариантов не должен иметь variant_id
        if not product.has_variants and variant_id:
            raise serializers.ValidationError({
                'variant_id': 'Этот товар не имеет вариантов'
            })

        # Проверка: вариант принадлежит товару
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({
                'variant_id': 'Этот вариант не принадлежит выбранному товару'
            })

        # Проверка наличия на складе
        if variant:
            if variant.stock < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара на складе. Доступно: {variant.stock}'
                })
        else:
            if product.track_stock and product.stock < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара на складе. Доступно: {product.stock}'
                })

        return attrs


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины"""

    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(
        source='get_items_count', read_only=True)
    total_price = serializers.DecimalField(
        source='get_total_price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    currency = serializers.CharField(
        source='store.currency_symbol', read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id',
            'items',
            'items_count',
            'total_price',
            'currency',
            'created',
            'updated',
        ]
        read_only_fields = ['created', 'updated']


class AddToCartSerializer(serializers.Serializer):
    """
    Сериализатор для добавления товара в корзину.

    Пример запроса:
    {
        "product_id": 1,
        "variant_id": 5,  // опционально, только для товаров с вариантами
        "quantity": 2
    }
    """

    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1, min_value=1, max_value=9999)

    def validate_product_id(self, value):
        """Проверка товара"""
        request = self.context.get('request')

        try:
            product = Product.objects.get(
                id=value,
                store=request.store,
                available=True
            )
        except Product.DoesNotExist:
            raise serializers.ValidationError('Товар не найден или недоступен')

        self.product = product
        return value

    def validate_variant_id(self, value):
        """Проверка варианта"""
        if value is None:
            return None

        try:
            variant = ProductVariant.objects.get(
                id=value,
                is_active=True
            )
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError(
                'Вариант не найден или недоступен')

        self.variant = variant
        return value

    def validate(self, attrs):
        """Проверка наличия товара на складе и соответствия варианта"""
        quantity = attrs.get('quantity', 1)
        variant_id = attrs.get('variant_id')

        product = getattr(self, 'product', None)
        variant = getattr(self, 'variant', None)

        if not product:
            return attrs

        # Проверка: товар с вариантами требует variant_id
        if product.has_variants and not variant_id:
            raise serializers.ValidationError({
                'variant_id': 'Для этого товара необходимо выбрать размер'
            })

        # Проверка: товар без вариантов не должен иметь variant_id
        if not product.has_variants and variant_id:
            raise serializers.ValidationError({
                'variant_id': 'Этот товар не имеет вариантов'
            })

        # Проверка: вариант принадлежит товару
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({
                'variant_id': 'Этот вариант не принадлежит выбранному товару'
            })

        # Проверка наличия на складе
        if variant:
            if variant.stock < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара на складе. Доступно: {variant.stock}'
                })
        else:
            if product.track_stock and product.stock < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара на складе. Доступно: {product.stock}'
                })

        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """Сериализатор для обновления количества товара в корзине"""

    quantity = serializers.IntegerField(min_value=1, max_value=9999)

    def validate_quantity(self, value):
        """Проверка количества и наличия на складе"""
        cart_item = self.context.get('cart_item')

        if not cart_item:
            return value

        # Проверка наличия на складе
        if cart_item.variant:
            # Товар с вариантом
            if cart_item.variant.stock < value:
                raise serializers.ValidationError(
                    f'Недостаточно товара на складе. Доступно: {cart_item.variant.stock}'
                )
        else:
            # Обычный товар
            if cart_item.product.track_stock and cart_item.product.stock < value:
                raise serializers.ValidationError(
                    f'Недостаточно товара на складе. Доступно: {cart_item.product.stock}'
                )

        return value

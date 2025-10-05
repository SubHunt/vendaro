"""
apps/cart/serializers.py — Сериализаторы для Cart API
"""

from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import Product


class CartItemProductSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор товара для корзины"""

    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'main_image', 'stock', 'available']

    def get_main_image(self, obj):
        """Главное фото товара"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товара в корзине"""

    product = CartItemProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(
        source='get_subtotal',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_id',
            'quantity',
            'price',
            'is_wholesale',
            'subtotal',
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

        return value

    def validate_quantity(self, value):
        """Проверка количества"""
        if value < 1:
            raise serializers.ValidationError(
                'Количество должно быть больше 0')
        if value > 9999:
            raise serializers.ValidationError('Слишком большое количество')
        return value


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
    """Сериализатор для добавления товара в корзину"""

    product_id = serializers.IntegerField()
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

        # Сохраняем товар для использования в create()
        self.product = product
        return value

    def validate(self, attrs):
        """Проверка наличия товара на складе"""
        quantity = attrs.get('quantity', 1)

        if hasattr(self, 'product'):
            if self.product.track_stock and self.product.stock < quantity:
                raise serializers.ValidationError({
                    'quantity': f'Недостаточно товара на складе. Доступно: {self.product.stock}'
                })

        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """Сериализатор для обновления количества товара в корзине"""

    quantity = serializers.IntegerField(min_value=1, max_value=9999)

    def validate_quantity(self, value):
        """Проверка количества и наличия на складе"""
        cart_item = self.context.get('cart_item')

        if cart_item and cart_item.product.track_stock:
            if cart_item.product.stock < value:
                raise serializers.ValidationError(
                    f'Недостаточно товара на складе. Доступно: {cart_item.product.stock}'
                )

        return value

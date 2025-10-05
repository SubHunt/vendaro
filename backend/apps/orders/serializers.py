"""
apps/orders/serializers.py — Сериализаторы для Orders API
"""

from rest_framework import serializers
from .models import Order, OrderItem
from apps.cart.models import Cart
from decimal import Decimal


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для товара в заказе"""

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product_name',
            'product_sku',
            'quantity',
            'price',
            'is_wholesale',
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра заказа"""

    items = OrderItemSerializer(many=True, read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    shipping_address = serializers.CharField(
        source='get_shipping_address', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone',
            'shipping_address_line1',
            'shipping_address_line2',
            'shipping_city',
            'shipping_postal_code',
            'shipping_country',
            'shipping_address',
            'subtotal',
            'shipping_cost',
            'tax',
            'discount',
            'total',
            'is_wholesale',
            'customer_note',
            'tracking_number',
            'items',
            'paid_at',
            'shipped_at',
            'delivered_at',
            'created',
            'updated',
        ]
        read_only_fields = [
            'order_number',
            'status',
            'subtotal',
            'shipping_cost',
            'tax',
            'discount',
            'total',
            'is_wholesale',
            'paid_at',
            'shipped_at',
            'delivered_at',
            'created',
            'updated',
        ]


class CreateOrderSerializer(serializers.Serializer):
    """Сериализатор для создания заказа"""

    # Данные покупателя
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)

    # Адрес доставки
    shipping_address_line1 = serializers.CharField(max_length=255)
    shipping_address_line2 = serializers.CharField(
        max_length=255, required=False, allow_blank=True)
    shipping_city = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20)
    shipping_country = serializers.CharField(max_length=2, default='RU')

    # Комментарий
    customer_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Проверка что корзина не пустая"""
        request = self.context.get('request')

        # Получаем корзину
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(
                    store=request.store,
                    user=request.user,
                    is_active=True
                )
            except Cart.DoesNotExist:
                raise serializers.ValidationError('Корзина пуста')
        else:
            session_key = request.session.session_key
            if not session_key:
                raise serializers.ValidationError('Корзина пуста')

            try:
                cart = Cart.objects.get(
                    store=request.store,
                    session_key=session_key,
                    is_active=True
                )
            except Cart.DoesNotExist:
                raise serializers.ValidationError('Корзина пуста')

        # Проверяем что в корзине есть товары
        if not cart.items.exists():
            raise serializers.ValidationError('Корзина пуста')

        # Сохраняем корзину для использования в create()
        self.cart = cart

        return attrs

    def create(self, validated_data):
        """Создание заказа из корзины"""
        request = self.context.get('request')
        cart = self.cart
        store = request.store
        user = request.user if request.user.is_authenticated else None

        # Вычисляем стоимость
        subtotal = cart.get_total_price()

        # Стоимость доставки (берём из настроек магазина)
        store_settings = store.settings
        shipping_cost = Decimal('0.00')

        if store_settings.enable_free_shipping:
            if subtotal < store_settings.free_shipping_threshold:
                shipping_cost = store_settings.shipping_cost
        else:
            shipping_cost = store_settings.shipping_cost

        # Налог (если включён)
        tax = Decimal('0.00')
        if not store_settings.tax_included and store_settings.tax_rate > 0:
            tax = subtotal * (store_settings.tax_rate / Decimal('100'))

        # Итого
        total = subtotal + shipping_cost + tax

        # Проверка минимальной суммы заказа
        if total < store_settings.min_order_amount:
            raise serializers.ValidationError(
                f'Минимальная сумма заказа: {store_settings.min_order_amount} ₽'
            )

        # Создаём заказ
        order = Order.objects.create(
            store=store,
            user=user,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            shipping_address_line1=validated_data['shipping_address_line1'],
            shipping_address_line2=validated_data.get(
                'shipping_address_line2', ''),
            shipping_city=validated_data['shipping_city'],
            shipping_postal_code=validated_data['shipping_postal_code'],
            shipping_country=validated_data.get('shipping_country', 'RU'),
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
            is_wholesale=user.is_wholesale if user else False,
            customer_note=validated_data.get('customer_note', ''),
            status='new',
        )

        # Добавляем товары из корзины в заказ
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku,
                quantity=cart_item.quantity,
                price=cart_item.price,
                is_wholesale=cart_item.is_wholesale,
            )

            # Уменьшаем stock товара (если отслеживается)
            if cart_item.product.track_stock:
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save(update_fields=['stock'])

        # Очищаем корзину
        cart.clear()
        cart.is_active = False
        cart.save()

        return order


class OrderListSerializer(serializers.ModelSerializer):
    """Облегчённый сериализатор для списка заказов"""

    items_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'total',
            'items_count',
            'created',
        ]

    def get_items_count(self, obj):
        """Количество товаров в заказе"""
        return obj.items.count()

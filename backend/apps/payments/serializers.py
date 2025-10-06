"""
apps/payments/serializers.py — Сериализаторы для Payments API
"""

from rest_framework import serializers
from .models import Payment
from apps.orders.models import Order


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра платежа"""

    order_number = serializers.CharField(
        source='order.order_number', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)
    method_display = serializers.CharField(
        source='get_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'order_number',
            'amount',
            'currency',
            'status',
            'status_display',
            'method',
            'method_display',
            'note',
            'paid_at',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated']


class CreatePaymentSerializer(serializers.Serializer):
    """Сериализатор для создания платежа"""

    order_number = serializers.CharField()
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)

    def validate_order_number(self, value):
        """Проверка что заказ существует"""
        request = self.context.get('request')

        try:
            order = Order.objects.get(
                order_number=value,
                store=request.store
            )
        except Order.DoesNotExist:
            raise serializers.ValidationError('Заказ не найден')

        # Проверяем что заказ ещё не оплачен
        if order.status == 'paid':
            raise serializers.ValidationError('Заказ уже оплачен')

        # Сохраняем заказ для использования в create()
        self.order = order
        return value

    def create(self, validated_data):
        """Создание платежа"""
        order = self.order
        store = self.context['request'].store

        # Создаём платёж
        payment = Payment.objects.create(
            order=order,
            store=store,
            amount=order.total,
            currency=store.currency,
            method=validated_data['method'],
            status='pending',
        )

        return payment

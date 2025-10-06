"""
apps/payments/views.py — Views для Payments API
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для платежей.

    Endpoints:
    - GET /api/payments/ - список платежей
    - GET /api/payments/{id}/ - детали платежа
    - POST /api/payments/create/ - создать платёж для заказа
    """

    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Возвращает платежи текущего магазина"""
        return Payment.objects.filter(
            store=self.request.store
        ).select_related('order').order_by('-created')

    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        """
        Создание платежа для заказа.

        POST /api/payments/create_payment/
        Body: {
            "order_number": "ORD-20251005-ABC123",
            "method": "cash_on_delivery"
        }
        """
        serializer = CreatePaymentSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        payment = serializer.save()

        # Возвращаем созданный платёж
        payment_serializer = PaymentSerializer(
            payment, context={'request': request})
        return Response(payment_serializer.data, status=status.HTTP_201_CREATED)

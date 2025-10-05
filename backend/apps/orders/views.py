"""
apps/orders/views.py — Views для Orders API
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Order
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    CreateOrderSerializer,
)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для заказов.

    Endpoints:
    - GET /api/orders/ - список заказов пользователя
    - GET /api/orders/{order_number}/ - детали заказа
    - POST /api/orders/create/ - создать заказ из корзины
    """

    lookup_field = 'order_number'

    def get_permissions(self):
        """Создание заказа доступно всем, просмотр только авторизованным"""
        if self.action == 'create_order':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Возвращает заказы текущего пользователя.

        Фильтрует по:
        - Магазину (request.store)
        - Пользователю (request.user)
        """
        return Order.objects.filter(
            store=self.request.store,
            user=self.request.user
        ).prefetch_related('items').order_by('-created')

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия"""
        if self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def create_order(self, request):
        """
        Создание заказа из корзины.

        POST /api/orders/create/
        Body: {
            "first_name": "Иван",
            "last_name": "Петров",
            "email": "ivan@example.com",
            "phone": "+79001234567",
            "shipping_address_line1": "ул. Ленина, д. 10, кв. 5",
            "shipping_city": "Москва",
            "shipping_postal_code": "101000",
            "shipping_country": "RU",
            "customer_note": "Позвонить за час"
        }
        """
        serializer = CreateOrderSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        order = serializer.save()

        # Возвращаем созданный заказ
        order_serializer = OrderSerializer(order, context={'request': request})
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)

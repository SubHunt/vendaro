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


class OrderViewSet(viewsets.ModelViewSet):
    """
    API для заказов.

    Endpoints:
    - GET /api/orders/ - список заказов пользователя
    - GET /api/orders/{order_number}/ - детали заказа
    - POST /api/orders/create/ - создать заказ из корзины
    """

    lookup_field = 'order_number'
    http_method_names = ['get', 'post']  # Разрешаем только GET и POST

    def get_permissions(self):
        """Создание заказа доступно всем, просмотр только авторизованным"""
        if self.action == 'create_order':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Возвращает заказы текущего пользователя"""
        if self.request.user.is_authenticated:
            return Order.objects.filter(
                store=self.request.store,
                user=self.request.user
            ).prefetch_related('items').order_by('-created')
        return Order.objects.none()

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия"""
        if self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def create_order(self, request):
        """
        Создание заказа из корзины.

        POST /api/orders/create_order/
        """
        serializer = CreateOrderSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        order = serializer.save()

        # Возвращаем созданный заказ
        order_serializer = OrderSerializer(order, context={'request': request})
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)

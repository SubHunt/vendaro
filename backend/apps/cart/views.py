"""
apps/cart/views.py — Views для Cart API

ИСПРАВЛЕНО:
1. update_item() возвращает CartItemSerializer
2. list() всегда возвращает 200 (даже для пустой корзины)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)


class CartViewSet(viewsets.ViewSet):
    """
    API для корзины покупок.

    Endpoints:
    - GET /api/cart/ - получить корзину
    - POST /api/cart/add/ - добавить товар
    - PATCH /api/cart/items/{id}/ - изменить количество
    - DELETE /api/cart/items/{id}/ - удалить товар
    - POST /api/cart/clear/ - очистить корзину
    """

    permission_classes = [AllowAny]  # Корзина доступна всем (включая анонимов)

    def get_or_create_cart(self, request):
        """
        Получает или создаёт корзину для пользователя.

        Логика:
        - Если пользователь авторизован → корзина по user
        - Если анонимный → корзина по session_key
        """
        store = request.store

        if request.user.is_authenticated:
            # Авторизованный пользователь
            cart, created = Cart.objects.get_or_create(
                store=store,
                user=request.user,
                defaults={'is_active': True}
            )
        else:
            # Анонимный пользователь
            # Получаем или создаём session key
            if not request.session.session_key:
                request.session.create()

            session_key = request.session.session_key

            cart, created = Cart.objects.get_or_create(
                store=store,
                session_key=session_key,
                user=None,
                defaults={'is_active': True}
            )

        return cart

    def list(self, request):
        """
        Получение корзины.

        GET /api/cart/

        ИСПРАВЛЕНО: Всегда возвращает 200, даже если корзина пустая
        """
        cart = self.get_or_create_cart(request)
        serializer = CartSerializer(cart, context={'request': request})
        # Явно указываем status=200 для пустой корзины
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def add(self, request):
        """
        Добавление товара в корзину.

        POST /api/cart/add/
        Body: {
            "product_id": 1,
            "variant_id": 5,  // опционально, для товаров с вариантами
            "quantity": 2
        }

        ОБНОВЛЕНО: Добавлена поддержка variant_id
        """
        serializer = AddToCartSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        variant_id = serializer.validated_data.get('variant_id')
        quantity = serializer.validated_data['quantity']
        product = serializer.product
        variant = getattr(serializer, 'variant', None)

        cart = self.get_or_create_cart(request)

        # Проверяем есть ли товар+вариант уже в корзине
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,  # ← Учитываем вариант
            defaults={'quantity': quantity}
        )

        if not created:
            # Товар уже есть - увеличиваем количество
            cart_item.quantity += quantity

            # Проверка stock (учитываем вариант)
            available_stock = variant.stock if variant else product.stock

            if cart_item.quantity > available_stock:
                return Response(
                    {'error': f'Недостаточно товара на складе. Доступно: {available_stock}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.save()

        # Возвращаем обновлённую корзину
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        """
        Обновление количества товара в корзине.

        PATCH /api/cart/items/{item_id}/
        Body: {"quantity": 3}

        ИСПРАВЛЕНО: Возвращает CartItemSerializer (содержит quantity)
        """
        cart = self.get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.select_related(
                'product',
                'variant',
                'variant__size'
            ).get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UpdateCartItemSerializer(
            data=request.data,
            context={'cart_item': cart_item}
        )
        serializer.is_valid(raise_exception=True)

        cart_item.quantity = serializer.validated_data['quantity']
        cart_item.save()

        # ИСПРАВЛЕНИЕ: Возвращаем CartItemSerializer (содержит quantity на верхнем уровне)
        item_serializer = CartItemSerializer(
            cart_item, context={'request': request})
        return Response(item_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        """
        Удаление товара из корзины.

        DELETE /api/cart/items/{item_id}/
        """
        cart = self.get_or_create_cart(request)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Возвращаем обновлённую корзину
        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Очистка корзины (удаление всех товаров).

        POST /api/cart/clear/
        """
        cart = self.get_or_create_cart(request)
        cart.clear()

        cart_serializer = CartSerializer(cart, context={'request': request})
        return Response(cart_serializer.data)

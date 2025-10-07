"""
conftest.py — Фикстуры для pytest (общие для всех тестов)
"""

import pytest
from django.contrib.auth import get_user_model
from apps.stores.models import Store, StoreSettings
from apps.products.models import Category, Product
from decimal import Decimal

User = get_user_model()


@pytest.fixture
def store(db):
    """Создаёт тестовый магазин"""
    store = Store.objects.create(
        domain='test.local',
        name='Test Store',
        slug='test-store',
        email='test@test.com',
        phone='+79001234567',
        primary_color='#000000',
        secondary_color='#FFFFFF',
        currency='RUB',
        currency_symbol='₽',
        is_active=True,
    )

    # Создаём настройки магазина
    StoreSettings.objects.create(
        store=store,
        enable_free_shipping=True,
        free_shipping_threshold=Decimal('5000.00'),
        shipping_cost=Decimal('500.00'),
        min_order_amount=Decimal('1000.00'),
        tax_rate=Decimal('20.00'),
        tax_included=True,
    )

    return store


@pytest.fixture
def user(db, store):
    """Создаёт обычного пользователя"""
    return User.objects.create_user(
        email='user@test.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        store=store,
    )


@pytest.fixture
def wholesale_user(db, store):
    """Создаёт оптового клиента"""
    return User.objects.create_user(
        email='wholesale@test.com',
        password='testpass123',
        first_name='Wholesale',
        last_name='User',
        is_wholesale=True,
        company_name='Test Company',
        store=store,
    )


@pytest.fixture
def category(db, store):
    """Создаёт категорию"""
    return Category.objects.create(
        store=store,
        name='Test Category',
        slug='test-category',
        is_active=True,
    )


@pytest.fixture
def product(db, store, category):
    """Создаёт товар"""
    return Product.objects.create(
        store=store,
        category=category,
        name='Test Product',
        slug='test-product',
        description='Test description',
        retail_price=Decimal('1000.00'),
        wholesale_price=Decimal('800.00'),
        stock=10,
        available=True,
        sku='TEST-001',
    )


@pytest.fixture
def api_client():
    """API клиент для тестирования"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Авторизованный API клиент"""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client

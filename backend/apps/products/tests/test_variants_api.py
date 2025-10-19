"""
apps/products/tests/test_variants_api.py

API тесты для вариантов товаров.
"""

import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.products.models import Size, Product, ProductVariant, Category
from apps.stores.models import Store
from apps.cart.models import Cart

User = get_user_model()


@pytest.fixture
def api_client():
    """API клиент"""
    return APIClient()


@pytest.fixture
def store(db):
    """Тестовый магазин"""
    return Store.objects.create(
        name='Test Store',
        slug='test-store',
        domain='localhost',
        email='test@store.com',
        enable_wholesale=True,
        wholesale_discount_percent=15,
    )


@pytest.fixture
def category(store):
    """Тестовая категория"""
    return Category.objects.create(
        store=store,
        name='Гидрокостюмы',
        slug='wetsuits',
    )


@pytest.fixture
def sizes(db):
    """Набор размеров"""
    return {
        'S': Size.objects.create(type='clothing', value='S', order=30),
        'M': Size.objects.create(type='clothing', value='M', order=40),
        'L': Size.objects.create(type='clothing', value='L', order=50),
        'XL': Size.objects.create(type='clothing', value='XL', order=60),
    }


@pytest.fixture
def product_with_variants(store, category, sizes):
    """Товар с вариантами"""
    product = Product.objects.create(
        store=store,
        category=category,
        name='Гидрокостюм Cressi 5мм',
        slug='wetsuit-cressi-5mm',
        retail_price=Decimal('15000'),
        wholesale_price=Decimal('12500'),
        has_variants=True,
        available=True,
    )

    variants = {}
    for size_name, size_obj in sizes.items():
        stock = {'S': 5, 'M': 10, 'L': 3, 'XL': 7}[size_name]
        variants[size_name] = ProductVariant.objects.create(
            product=product,
            size=size_obj,
            stock=stock,
            is_active=True,
            sku=f'WETSUIT-{size_name}',
        )

    return product, variants


@pytest.fixture
def product_without_variants(store, category):
    """Обычный товар без вариантов"""
    return Product.objects.create(
        store=store,
        category=category,
        name='Маска для дайвинга',
        slug='diving-mask',
        retail_price=Decimal('5000'),
        stock=20,
        has_variants=False,
        available=True,
    )


@pytest.fixture
def user(db):
    """Обычный пользователь"""
    return User.objects.create_user(
        email='user@test.com',
        password='testpass123',
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Аутентифицированный клиент"""
    api_client.force_authenticate(user=user)
    return api_client


# ============================================
# ТЕСТЫ API PRODUCTS (с вариантами)
# ============================================

@pytest.mark.django_db
class TestProductsAPIWithVariants:
    """Тесты API товаров с вариантами"""

    def test_get_product_with_variants(self, api_client, product_with_variants):
        """Тест получения товара с вариантами"""
        product, variants = product_with_variants

        response = api_client.get(f'/api/products/{product.slug}/')

        assert response.status_code == 200
        data = response.json()

        # Проверяем основные поля
        assert data['name'] == 'Гидрокостюм Cressi 5мм'
        assert data['has_variants'] is True
        assert data['total_stock'] == 25  # 5+10+3+7

        # Проверяем варианты
        assert 'variants' in data
        assert len(data['variants']) == 4

        # Проверяем структуру варианта
        variants = data['variants'][0]
        assert 'id' in variants
        assert 'size' in variants
        assert 'stock' in variants
        assert 'price' in variants
        assert 'is_in_stock' in variants

        # Проверяем размер
        assert variants['size']['value'] in ['S', 'M', 'L', 'XL']
        assert variants['size']['type'] == 'clothing'

    def test_get_product_variants_filtered_by_stock(self, api_client, product_with_variants):
        """Тест что в available_sizes только размеры в наличии"""
        product, variants = product_with_variants

        # Обнуляем stock размера L
        variants['L'].stock = 0
        variants['L'].save()

        response = api_client.get(f'/api/products/{product.slug}/')
        data = response.json()

        # L не должен быть в available_sizes
        assert 'L' not in data.get('available_sizes', [])
        assert len(data['available_sizes']) == 3  # S, M, XL

    def test_get_product_without_variants(self, api_client, product_without_variants):
        """Тест получения обычного товара без вариантов"""
        product = product_without_variants

        response = api_client.get(f'/api/products/{product.slug}/')
        data = response.json()

        assert data['has_variants'] is False
        # assert data['variants'] == []
        assert data['stock'] == 20
        assert data['total_stock'] == 20

    def test_product_list_shows_variants_info(self, api_client, product_with_variants):
        """Тест что список товаров показывает информацию о вариантах"""
        product, variants = product_with_variants

        response = api_client.get('/api/products/')

        assert response.status_code == 200
        data = response.json()

        # Находим наш товар
        product_data = None
        for item in data['results']:
            if item['slug'] == 'wetsuit-cressi-5mm':
                product_data = item
                break

        assert product_data is not None
        assert product_data['has_variants'] is True
        assert product_data['variants_count'] == 4
        assert len(product_data['available_sizes']) == 4


# ============================================
# ТЕСТЫ API CART (с вариантами)
# ============================================

@pytest.mark.django_db
class TestCartAPIWithVariants:
    """Тесты API корзины с вариантами"""

    def test_add_product_with_variant_to_cart(self, authenticated_client, store, product_with_variants):
        """Тест добавления товара с размером в корзину"""
        product, variants = product_with_variants
        variant_m = variants['M']

        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variant_m.id,
            'quantity': 2,
        })

        assert response.status_code == 201
        data = response.json()

        # Проверяем ответ
        assert 'cart_item' in data or 'items' in data

    def test_add_product_with_variant_missing_variant_id(self, authenticated_client, product_with_variants):
        """Тест что товар с вариантами требует variant_id"""
        product, variants = product_with_variants

        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            # variant_id НЕ указан!
            'quantity': 1,
        })

        # Должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert 'variant_id' in data or 'non_field_errors' in data

    def test_add_product_without_variant(self, authenticated_client, product_without_variants):
        """Тест добавления обычного товара без варианта"""
        product = product_without_variants

        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            # variant_id не указываем
            'quantity': 1,
        })

        # Должно работать
        assert response.status_code == 201

    def test_add_product_without_variant_but_with_variant_id(self, authenticated_client, product_without_variants, product_with_variants):
        """Тест что обычный товар не должен иметь variant_id"""
        product = product_without_variants
        _, variants = product_with_variants

        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            # Указываем variant_id
            'variant_id': list(variants.values())[0].id,
            'quantity': 1,
        })

        # Должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert 'variant_id' in data

    def test_add_variant_insufficient_stock(self, authenticated_client, product_with_variants):
        """Тест что нельзя добавить больше чем есть на складе"""
        product, variants = product_with_variants
        variant_s = variants['S']  # Stock = 5

        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variant_s.id,
            'quantity': 10,  # Больше чем stock!
        })

        # Должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert 'quantity' in data
        assert 'Доступно: 5' in str(data)

    def test_add_wrong_variant_to_product(self, authenticated_client, store, category, sizes):
        """Тест что вариант должен принадлежать товару"""
        # Создаём два разных товара
        product1 = Product.objects.create(
            store=store,
            category=category,
            name='Товар 1',
            slug='product-1',
            retail_price=Decimal('10000'),
            has_variants=True,
            available=True,
        )

        product2 = Product.objects.create(
            store=store,
            category=category,
            name='Товар 2',
            slug='product-2',
            retail_price=Decimal('15000'),
            has_variants=True,
            available=True,
        )

        # Создаём варианты
        variant1 = ProductVariant.objects.create(
            product=product1,
            size=sizes['M'],
            stock=10,
        )

        variant2 = ProductVariant.objects.create(
            product=product2,
            size=sizes['M'],
            stock=10,
        )

        # Пытаемся добавить товар1 с вариантом от товара2
        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product1.id,
            'variant_id': variant2.id,  # Чужой вариант!
            'quantity': 1,
        })

        # Должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert 'variant_id' in data

    def test_get_cart_with_variants(self, authenticated_client, store, user, product_with_variants):
        """Тест получения корзины с вариантами"""
        product, variants = product_with_variants

        # Создаём корзину и добавляем товар
        cart = Cart.objects.create(store=store, user=user)
        from apps.cart.models import CartItem
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['M'],
            quantity=2,
        )

        response = authenticated_client.get('/api/cart/')

        assert response.status_code == 200
        data = response.json()

        # Проверяем корзину
        assert data['items_count'] == 2
        assert len(data['items']) == 1

        # Проверяем item
        item = data['items'][0]
        assert 'variant' in item
        assert item['variant']['size_value'] == 'M'
        assert item['variant']['size_type'] == 'clothing'
        assert item['variant']['stock'] == 10
        assert item['available_stock'] == 10
        assert item['is_available'] is True

    def test_cart_with_different_variants(self, authenticated_client, store, user, product_with_variants):
        """Тест что разные размеры - это разные позиции в корзине"""
        product, variants = product_with_variants

        # Добавляем размер M
        response1 = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variants['M'].id,
            'quantity': 1,
        })
        assert response1.status_code == 201

        # Добавляем размер L
        response2 = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variants['L'].id,
            'quantity': 1,
        })
        assert response2.status_code == 201

        # Получаем корзину
        response = authenticated_client.get('/api/cart/')
        data = response.json()

        # Должно быть 2 позиции
        assert len(data['items']) == 2
        assert data['items_count'] == 2

        # Проверяем что это разные размеры
        sizes_in_cart = {item['variant']['size_value']
                         for item in data['items']}
        assert sizes_in_cart == {'M', 'L'}

    def test_update_cart_item_quantity(self, authenticated_client, store, user, product_with_variants):
        """Тест изменения количества товара с вариантом"""
        product, variants = product_with_variants

        # Создаём корзину
        cart = Cart.objects.create(store=store, user=user)
        from apps.cart.models import CartItem
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['M'],
            quantity=2,
        )

        # Увеличиваем количество
        response = authenticated_client.patch(f'/api/cart/items/{cart_item.id}/', {
            'quantity': 5,
        })

        assert response.status_code == 200
        data = response.json()
        assert data['quantity'] == 5

    def test_update_cart_item_exceeds_stock(self, authenticated_client, store, user, product_with_variants):
        """Тест что нельзя установить quantity больше stock"""
        product, variants = product_with_variants

        cart = Cart.objects.create(store=store, user=user)
        from apps.cart.models import CartItem
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['S'],  # Stock = 5
            quantity=2,
        )

        # Пытаемся установить 10 (больше чем stock)
        response = authenticated_client.patch(f'/api/cart/items/{cart_item.id}/', {
            'quantity': 10,
        })

        # Должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert 'quantity' in data


# ============================================
# ТЕСТЫ ВАЛИДАЦИИ
# ============================================

@pytest.mark.django_db
class TestVariantsValidation:
    """Тесты валидации вариантов"""

    def test_cannot_add_inactive_variant(self, authenticated_client, product_with_variants):
        """Тест что нельзя добавить неактивный вариант"""
        product, variants = product_with_variants
        variant = variants['M']

        # Деактивируем вариант
        variant.is_active = False
        variant.save()

        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variant.id,
            'quantity': 1,
        })

        # Должна быть ошибка
        assert response.status_code == 400

    def test_cannot_add_variant_with_zero_stock(self, authenticated_client, product_with_variants):
        """Тест что нельзя добавить вариант без наличия"""
        product, variants = product_with_variants
        variant = variants['M']

        # Обнуляем stock
        variant.stock = 0
        variant.save()

        response = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variant.id,
            'quantity': 1,
        })

        # Должна быть ошибка
        assert response.status_code == 400
        data = response.json()
        assert 'quantity' in data or 'stock' in str(data).lower()


# ============================================
# ТЕСТЫ ЦЕН (B2B/B2C)
# ============================================

@pytest.mark.django_db
class TestVariantsPricing:
    """Тесты ценообразования вариантов"""

    def test_variant_price_for_retail_user(self, api_client, user, product_with_variants):
        """Тест что обычный пользователь видит розничную цену"""
        api_client.force_authenticate(user=user)
        product, variants = product_with_variants

        response = api_client.get(f'/api/products/{product.slug}/')
        data = response.json()

        variant = data['variants'][0]
        assert variant['price'] == 15000.00

    def test_variant_price_for_wholesale_user(self, api_client, product_with_variants):
        """Тест что оптовик видит оптовую цену"""
        # Создаём оптовика
        wholesale_user = User.objects.create_user(
            email='wholesale@test.com',
            password='test123',
            is_wholesale=True,
        )
        api_client.force_authenticate(user=wholesale_user)

        product, variants = product_with_variants

        response = api_client.get(f'/api/products/{product.slug}/')
        data = response.json()

        variant = data['variants'][0]
        assert variant['wholesale_price'] == 12500.00

    def test_variant_with_price_override(self, api_client, product_with_variants):
        """Тест переопределённой цены варианта"""
        product, variants = product_with_variants

        # Устанавливаем переопределённую цену для XL
        variant_xl = variants['XL']
        variant_xl.price_override = Decimal('16000')
        variant_xl.save()

        response = api_client.get(f'/api/products/{product.slug}/')
        data = response.json()

        # Находим вариант XL
        xl_data = None
        for v in data['variants']:
            if v['size']['value'] == 'XL':
                xl_data = v
                break

        assert xl_data is not None
        assert xl_data['price'] == 16000.00  # Переопределённая цена


# ============================================
# EDGE CASES
# ============================================

@pytest.mark.django_db
class TestVariantsEdgeCases:
    """Тесты граничных случаев"""

    def test_product_with_no_active_variants(self, api_client, product_with_variants):
        """Тест товара когда все варианты неактивны"""
        product, variants = product_with_variants

        # Деактивируем все варианты
        for variant in variants.values():
            variant.is_active = False
            variant.save()

        response = api_client.get(f'/api/products/{product.slug}/')
        data = response.json()

        assert data['has_variants'] is True
        assert len(data['variants']) == 0  # Неактивные не показываются
        assert data['available_sizes'] == []

    def test_add_same_variant_multiple_times(self, authenticated_client, product_with_variants):
        """Тест добавления одного и того же варианта несколько раз"""
        product, variants = product_with_variants
        variant = variants['M']

        # Первое добавление
        response1 = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variant.id,
            'quantity': 2,
        })
        assert response1.status_code == 201

        # Второе добавление того же варианта
        # Должно увеличить quantity или вернуть ошибку
        response2 = authenticated_client.post('/api/cart/add/', {
            'product_id': product.id,
            'variant_id': variant.id,
            'quantity': 3,
        })

        # Либо 201 (quantity увеличен), либо 400 (уже есть)
        assert response2.status_code in [201, 400]

    def test_empty_cart_with_variants(self, authenticated_client):
        """Тест пустой корзины"""
        response = authenticated_client.get('/api/cart/')

        assert response.status_code == 200
        data = response.json()
        assert data['items'] == []
        assert data['items_count'] == 0
        assert data['total_price'] == '0.00'


# ============================================
# ЗАПУСК ТЕСТОВ
# ============================================

# pytest apps/products/tests/test_variants_api.py -v
# pytest apps/products/tests/test_variants_api.py --cov=apps.products --cov=apps.cart
# pytest apps/products/tests/test_variants_api.py -k "cart" -v

"""
apps/products/tests/test_variants.py

Тесты для вариантов товаров (Size, ProductVariant).
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.products.models import Size, Product, ProductVariant, Category
from apps.stores.models import Store
from apps.cart.models import Cart, CartItem

User = get_user_model()


@pytest.fixture
def store(db):
    """Создаёт тестовый магазин"""
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
    """Создаёт тестовую категорию"""
    return Category.objects.create(
        store=store,
        name='Гидрокостюмы',
        slug='wetsuits',
    )


@pytest.fixture
def sizes(db):
    """Создаёт набор размеров для тестирования"""
    sizes = {
        'S': Size.objects.create(type='clothing', value='S', order=30),
        'M': Size.objects.create(type='clothing', value='M', order=40),
        'L': Size.objects.create(type='clothing', value='L', order=50),
        'XL': Size.objects.create(type='clothing', value='XL', order=60),
    }
    return sizes


@pytest.fixture
def product_with_variants(store, category, sizes):
    """Создаёт товар с вариантами (размерами)"""
    product = Product.objects.create(
        store=store,
        category=category,
        name='Гидрокостюм Cressi 5мм',
        slug='wetsuit-cressi-5mm',
        retail_price=Decimal('15000'),
        wholesale_price=Decimal('12500'),
        has_variants=True,  # Товар имеет варианты!
        available=True,
    )

    # Добавляем варианты (размеры)
    variants = {}
    for size_name, size_obj in sizes.items():
        stock = {'S': 5, 'M': 10, 'L': 3, 'XL': 7}[size_name]
        variants[size_name] = ProductVariant.objects.create(
            product=product,
            size=size_obj,
            stock=stock,
            is_active=True,
        )

    return product, variants


@pytest.fixture
def product_without_variants(store, category):
    """Создаёт обычный товар без вариантов"""
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
def user(db, store):
    """Создаёт обычного пользователя"""
    return User.objects.create_user(
        email='user@test.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def wholesale_user(db, store):
    """Создаёт оптового пользователя (B2B)"""
    return User.objects.create_user(
        email='wholesale@test.com',
        password='testpass123',
        first_name='Wholesale',
        last_name='User',
        is_wholesale=True,
    )


# ============================================
# ТЕСТЫ МОДЕЛИ SIZE
# ============================================

@pytest.mark.django_db
class TestSizeModel:
    """Тесты модели Size"""

    def test_create_size(self):
        """Тест создания размера"""
        size = Size.objects.create(
            type='clothing',
            value='M',
            order=40,
            is_active=True,
        )

        assert size.type == 'clothing'
        assert size.value == 'M'
        assert size.order == 40
        assert size.is_active is True
        assert str(size) == 'Одежда (XXS-XXXXL): M'

    def test_size_types(self):
        """Тест различных типов размеров"""
        # Одежда
        clothing = Size.objects.create(type='clothing', value='L', order=50)
        assert clothing.get_type_display() == 'Одежда (XXS-XXXXL)'

        # Обувь
        footwear = Size.objects.create(type='footwear', value='42', order=420)
        assert footwear.get_type_display() == 'Обувь (размеры)'

        # Диапазон
        range_size = Size.objects.create(
            type='range', value='40-41', order=4041)
        assert range_size.get_type_display() == 'Диапазон размеров'

    def test_size_ordering(self):
        """Тест сортировки размеров"""
        Size.objects.create(type='clothing', value='L', order=50)
        Size.objects.create(type='clothing', value='S', order=30)
        Size.objects.create(type='clothing', value='M', order=40)

        sizes = list(Size.objects.filter(
            type='clothing').values_list('value', flat=True))
        assert sizes == ['S', 'M', 'L']

    def test_size_unique_constraint(self):
        """Тест уникальности (type, value)"""
        Size.objects.create(type='clothing', value='M', order=40)

        # Попытка создать дубликат
        with pytest.raises(Exception):  # IntegrityError
            Size.objects.create(type='clothing', value='M', order=40)


# ============================================
# ТЕСТЫ МОДЕЛИ PRODUCTVARIANT
# ============================================

@pytest.mark.django_db
class TestProductVariantModel:
    """Тесты модели ProductVariant"""

    def test_create_variant(self, product_with_variants):
        """Тест создания варианта"""
        product, variants = product_with_variants
        variant_m = variants['M']

        assert variant_m.product == product
        assert variant_m.size.value == 'M'
        assert variant_m.stock == 10
        assert variant_m.is_active is True
        assert str(variant_m) == 'Гидрокостюм Cressi 5мм - M'

    def test_variant_price_inheritance(self, product_with_variants):
        """Тест наследования цены от товара"""
        product, variants = product_with_variants
        variant = variants['M']

        # Цена не переопределена → используется цена товара
        assert variant.get_retail_price() == product.retail_price
        assert variant.get_wholesale_price() == product.wholesale_price

    def test_variant_price_override(self, product_with_variants):
        """Тест переопределения цены варианта"""
        product, variants = product_with_variants
        variant = variants['XL']

        # Устанавливаем переопределённую цену для XL (он дороже)
        variant.price_override = Decimal('16000')
        variant.wholesale_price_override = Decimal('13500')
        variant.save()

        # Проверяем что используется переопределённая цена
        assert variant.get_retail_price() == Decimal('16000')
        assert variant.get_wholesale_price() == Decimal('13500')

        # Другие варианты используют цену товара
        assert variants['M'].get_retail_price() == product.retail_price

    def test_variant_price_for_user(self, product_with_variants, user, wholesale_user):
        """Тест получения цены для пользователя"""
        product, variants = product_with_variants
        variant = variants['M']

        # Обычный пользователь
        price, is_wholesale = variant.get_price_for_user(user)
        assert price == Decimal('15000')
        assert is_wholesale is False

        # Оптовый пользователь
        price, is_wholesale = variant.get_price_for_user(wholesale_user)
        assert price == Decimal('12500')
        assert is_wholesale is True

    def test_variant_is_in_stock(self, product_with_variants):
        """Тест проверки наличия варианта на складе"""
        product, variants = product_with_variants

        # Вариант с stock > 0
        assert variants['M'].is_in_stock() is True

        # Вариант с stock = 0
        variants['M'].stock = 0
        variants['M'].save()
        assert variants['M'].is_in_stock() is False

        # Неактивный вариант
        variants['L'].is_active = False
        variants['L'].save()
        assert variants['L'].is_in_stock() is False

    def test_variant_unique_constraint(self, product_with_variants, sizes):
        """Тест уникальности (product, size)"""
        product, variants = product_with_variants

        # Попытка создать дубликат размера M для того же товара
        with pytest.raises(Exception):  # IntegrityError
            ProductVariant.objects.create(
                product=product,
                size=sizes['M'],
                stock=5,
            )


# ============================================
# ТЕСТЫ МОДЕЛИ PRODUCT (с вариантами)
# ============================================

@pytest.mark.django_db
class TestProductWithVariants:
    """Тесты товара с вариантами"""

    def test_product_has_variants_flag(self, product_with_variants, product_without_variants):
        """Тест флага has_variants"""
        product, variants = product_with_variants

        assert product.has_variants is True
        assert product_without_variants.has_variants is False

    def test_product_is_in_stock_with_variants(self, product_with_variants):
        """Тест наличия товара с вариантами"""
        product, variants = product_with_variants

        # Есть варианты в наличии
        assert product.is_in_stock() is True

        # Обнуляем все варианты
        for variant in variants.values():
            variant.stock = 0
            variant.save()

        # Товар закончился
        assert product.is_in_stock() is False

    def test_product_get_total_stock(self, product_with_variants):
        """Тест подсчёта общего stock"""
        product, variants = product_with_variants

        # S=5, M=10, L=3, XL=7
        total = product.get_total_stock()
        assert total == 25

    def test_product_get_available_sizes(self, product_with_variants):
        """Тест получения доступных размеров"""
        product, variants = product_with_variants

        available = product.get_available_sizes()

        # Должны быть все 4 размера (все в наличии)
        assert available.count() == 4

        # Обнуляем размер L
        variants['L'].stock = 0
        variants['L'].save()

        available = product.get_available_sizes()
        assert available.count() == 3  # L исчез
        assert 'L' not in [v.size.value for v in available]

    def test_product_without_variants_stock(self, product_without_variants):
        """Тест обычного товара без вариантов"""
        product = product_without_variants

        # Stock управляется через Product.stock
        assert product.stock == 20
        assert product.is_in_stock() is True
        assert product.get_total_stock() == 20


# ============================================
# ТЕСТЫ КОРЗИНЫ С ВАРИАНТАМИ
# ============================================

@pytest.mark.django_db
class TestCartWithVariants:
    """Тесты корзины с вариантами товаров"""

    def test_add_variant_to_cart(self, user, store, product_with_variants):
        """Тест добавления товара с размером в корзину"""
        product, variants = product_with_variants
        variant_m = variants['M']

        # Создаём корзину
        cart = Cart.objects.create(store=store, user=user)

        # Добавляем товар с размером M
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant_m,
            quantity=2,
        )

        assert cart_item.variant == variant_m
        assert cart_item.quantity == 2
        assert cart_item.price == Decimal('15000')  # Цена товара
        assert cart_item.get_subtotal() == Decimal('30000')

    def test_add_different_variants_separately(self, user, store, product_with_variants):
        """Тест добавления разных размеров как отдельных позиций"""
        product, variants = product_with_variants
        cart = Cart.objects.create(store=store, user=user)

        # Добавляем размер M
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['M'],
            quantity=1,
        )

        # Добавляем размер L
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['L'],
            quantity=1,
        )

        # Должно быть 2 позиции (разные размеры)
        assert cart.items.count() == 2
        assert cart.get_items_count() == 2

    def test_cart_item_unique_constraint(self, user, store, product_with_variants):
        """Тест уникальности (cart, product, variant)"""
        product, variants = product_with_variants
        cart = Cart.objects.create(store=store, user=user)

        # Добавляем размер M
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['M'],
            quantity=1,
        )

        # Попытка добавить тот же размер M ещё раз
        with pytest.raises(Exception):  # IntegrityError
            CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variants['M'],
                quantity=1,
            )

    def test_cart_item_available_stock(self, user, store, product_with_variants):
        """Тест получения доступного stock"""
        product, variants = product_with_variants
        cart = Cart.objects.create(store=store, user=user)

        # Товар с вариантом
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['M'],
            quantity=2,
        )

        # Stock берётся из варианта
        assert cart_item.get_available_stock() == 10  # Stock размера M

    def test_cart_item_is_available(self, user, store, product_with_variants):
        """Тест проверки доступности товара в корзине"""
        product, variants = product_with_variants
        cart = Cart.objects.create(store=store, user=user)

        # Добавляем 2 штуки размера M (stock=10)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['M'],
            quantity=2,
        )

        # Товар доступен
        assert cart_item.is_available() is True

        # Устанавливаем quantity больше чем stock
        cart_item.quantity = 15
        cart_item.save()

        # Товар недоступен
        assert cart_item.is_available() is False

    def test_cart_without_variant(self, user, store, product_without_variants):
        """Тест обычного товара без варианта в корзине"""
        product = product_without_variants
        cart = Cart.objects.create(store=store, user=user)

        # Добавляем без варианта
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=None,  # Нет варианта
            quantity=1,
        )

        assert cart_item.variant is None
        assert cart_item.get_available_stock() == 20  # Stock товара
        assert str(cart_item) == '1x Маска для дайвинга'

    def test_cart_total_with_variants(self, user, store, product_with_variants):
        """Тест подсчёта общей стоимости корзины с вариантами"""
        product, variants = product_with_variants
        cart = Cart.objects.create(store=store, user=user)

        # Добавляем размер M (цена 15000)
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['M'],
            quantity=2,
        )

        # Добавляем размер L (цена 15000)
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variants['L'],
            quantity=1,
        )

        # Итого: 2*15000 + 1*15000 = 45000
        assert cart.get_total_price() == Decimal('45000')


# ============================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ============================================

@pytest.mark.django_db
class TestVariantsIntegration:
    """Интеграционные тесты полного цикла"""

    def test_full_workflow(self, user, store, category, sizes):
        """Тест полного рабочего процесса с вариантами"""

        # 1. Создаём товар с вариантами
        product = Product.objects.create(
            store=store,
            category=category,
            name='Гидрокостюм Test',
            slug='wetsuit-test',
            retail_price=Decimal('20000'),
            has_variants=True,
            available=True,
        )

        # 2. Добавляем размеры S и M
        variant_s = ProductVariant.objects.create(
            product=product,
            size=sizes['S'],
            stock=5,
        )
        variant_m = ProductVariant.objects.create(
            product=product,
            size=sizes['M'],
            stock=10,
        )

        # 3. Проверяем что товар в наличии
        assert product.is_in_stock() is True
        assert product.get_total_stock() == 15

        # 4. Добавляем в корзину
        cart = Cart.objects.create(store=store, user=user)
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant_m,
            quantity=3,
        )

        # 5. Проверяем корзину
        assert cart.get_items_count() == 3
        assert cart.get_total_price() == Decimal('60000')
        assert cart_item.is_available() is True

        # 6. Уменьшаем stock (эмуляция продажи)
        variant_m.stock = 2
        variant_m.save()

        # 7. Товар в корзине стал недоступен (quantity=3, но stock=2)
        cart_item.refresh_from_db()
        assert cart_item.is_available() is False

        # 8. Уменьшаем quantity до доступного
        cart_item.quantity = 2
        cart_item.save()

        # 9. Снова доступен
        assert cart_item.is_available() is True


# ============================================
# ЗАПУСК ТЕСТОВ
# ============================================

# pytest apps/products/tests/test_variants.py -v
# pytest apps/products/tests/test_variants.py --cov=apps.products --cov=apps.cart

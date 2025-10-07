"""
apps/products/tests/test_models.py — Тесты для моделей товаров
"""

import pytest
from decimal import Decimal
from apps.products.models import Product, ProductReview


@pytest.mark.django_db
class TestProduct:
    """Тесты модели Product"""

    def test_product_creation(self, product):
        """Тест создания товара"""
        assert product.name == 'Test Product'
        assert product.retail_price == Decimal('1000.00')
        assert product.stock == 10
        assert product.available is True

    def test_slug_generation(self, store, category):
        """Тест автогенерации slug"""
        product = Product.objects.create(
            store=store,
            category=category,
            name='Новый товар',
            retail_price=Decimal('500.00'),
            stock=5,
        )
        assert product.slug == 'novyj-tovar'

    def test_get_retail_price(self, product):
        """Тест получения розничной цены"""
        assert product.get_retail_price() == Decimal('1000.00')

        # С discount_price
        product.discount_price = Decimal('800.00')
        product.save()
        assert product.get_retail_price() == Decimal('800.00')

    def test_get_wholesale_price(self, product, wholesale_user):
        """Тест получения оптовой цены"""
        # Магазин должен разрешать опт
        product.store.enable_wholesale = True
        product.store.save()

        # Индивидуальная оптовая цена
        price, is_wholesale = product.get_price_for_user(wholesale_user)
        assert price == Decimal('800.00')
        assert is_wholesale is True

    def test_get_price_for_regular_user(self, product, user):
        """Тест цены для обычного пользователя"""
        price, is_wholesale = product.get_price_for_user(user)
        assert price == Decimal('1000.00')
        assert is_wholesale is False

    def test_is_in_stock(self, product):
        """Тест проверки наличия"""
        assert product.is_in_stock() is True

        product.stock = 0
        assert product.is_in_stock() is False

    def test_has_discount(self, product):
        """Тест проверки скидки"""
        assert product.has_discount() is False

        product.discount_price = Decimal('800.00')
        assert product.has_discount() is True


@pytest.mark.django_db
class TestProductReview:
    """Тесты модели ProductReview"""

    def test_review_creation(self, product, user):
        """Тест создания отзыва"""
        review = ProductReview.objects.create(
            product=product,
            user=user,
            rating=5,
            comment='Great product!',
            is_approved=True,
        )
        assert review.rating == 5
        assert review.comment == 'Great product!'

    def test_unique_review_per_user(self, product, user):
        """Тест что один пользователь = один отзыв"""
        ProductReview.objects.create(
            product=product,
            user=user,
            rating=5,
            comment='First review',
        )

        # Попытка создать второй отзыв должна вызвать ошибку
        with pytest.raises(Exception):
            ProductReview.objects.create(
                product=product,
                user=user,
                rating=4,
                comment='Second review',
            )

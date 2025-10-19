"""
apps/cart/models.py — Модель корзины покупок для Vendaro CMS

Обновлено: добавлена поддержка вариантов товаров (размеры).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from decimal import Decimal


class Cart(TimeStampedModel):
    """Корзина покупок пользователя"""

    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name=_('store'),
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True,
        verbose_name=_('user'),
    )

    session_key = models.CharField(
        _('session key'),
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
    )

    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        indexes = [
            models.Index(fields=['store', 'user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['store', 'user']

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email} in {self.store.name}"
        return f"Anonymous cart {self.session_key} in {self.store.name}"

    def get_items_count(self):
        """Возвращает общее количество товаров в корзине"""
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        """Вычисляет общую стоимость корзины"""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.get_subtotal()
        return total

    def clear(self):
        """Очищает корзину"""
        self.items.all().delete()
        self.save()

    def merge_with(self, other_cart):
        """Объединяет текущую корзину с другой корзиной"""
        for item in other_cart.items.all():
            # Проверяем есть ли такой товар+вариант в текущей корзине
            existing_item = self.items.filter(
                product=item.product,
                variant=item.variant
            ).first()

            if existing_item:
                existing_item.quantity += item.quantity
                existing_item.save()
            else:
                item.cart = self
                item.save()

        other_cart.delete()


class CartItem(TimeStampedModel):
    """
    Товар в корзине.

    Поддержка вариантов:
    - Если variant=None: обычный товар без вариантов
    - Если variant установлен: товар с выбранным размером
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart'),
    )

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('product'),
    )

    # ========================================
    # ВАРИАНТ ТОВАРА (размер)
    # ========================================

    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('variant'),
        null=True,
        blank=True,
        help_text=_(
            'Вариант товара (размер). Пусто для товаров без вариантов.'),
    )

    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)],
    )

    price = models.DecimalField(
        _('price per unit'),
        max_digits=10,
        decimal_places=2,
    )

    is_wholesale = models.BooleanField(_('wholesale price'), default=False)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        ordering = ['-created']

        # Уникальность: один товар+вариант в корзине
        # Если вариант не указан (None), можно добавить только один раз
        unique_together = ['cart', 'product', 'variant']

    def __str__(self):
        if self.variant:
            return f"{self.quantity}x {self.product.name} ({self.variant.size.value})"
        return f"{self.quantity}x {self.product.name}"

    def get_subtotal(self):
        """Вычисляет стоимость этой позиции"""
        return self.price * self.quantity

    def update_price(self):
        """
        Обновляет цену товара (актуальная цена).

        Учитывает:
        - Наличие варианта (цена варианта или товара)
        - B2B/B2C статус пользователя
        """
        user = self.cart.user

        if self.variant:
            # Цена варианта
            price, is_wholesale = self.variant.get_price_for_user(user)
        else:
            # Цена обычного товара
            price, is_wholesale = self.product.get_price_for_user(user)

        self.price = price
        self.is_wholesale = is_wholesale
        self.save(update_fields=['price', 'is_wholesale', 'updated'])

    def get_available_stock(self):
        """
        Возвращает доступное количество на складе.

        Если товар с вариантом - проверяем stock варианта.
        Если обычный товар - проверяем stock товара.
        """
        if self.variant:
            return self.variant.stock
        return self.product.stock

    def is_available(self):
        """
        Проверяет доступность товара для заказа.

        Проверяет:
        - Активность товара
        - Наличие на складе
        - Активность варианта (если есть)
        """
        # Проверка товара
        if not self.product.available:
            return False

        # Проверка варианта
        if self.variant:
            if not self.variant.is_active:
                return False
            if self.variant.stock < self.quantity:
                return False
        else:
            # Проверка обычного товара
            if self.product.track_stock and self.product.stock < self.quantity:
                return False

        return True

    def save(self, *args, **kwargs):
        """
        Переопределяем save() для автоматической установки цены.
        """
        if not self.pk:
            user = self.cart.user

            if self.variant:
                price, is_wholesale = self.variant.get_price_for_user(user)
            else:
                price, is_wholesale = self.product.get_price_for_user(user)

            self.price = price
            self.is_wholesale = is_wholesale

        super().save(*args, **kwargs)


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================

# Добавление обычного товара (без вариантов):
# cart_item, created = CartItem.objects.get_or_create(
#     cart=cart,
#     product=product,
#     variant=None,  # Нет варианта
#     defaults={'quantity': 1}
# )

# Добавление товара с размером:
# variant = ProductVariant.objects.get(product=product, size__value='M')
# cart_item, created = CartItem.objects.get_or_create(
#     cart=cart,
#     product=product,
#     variant=variant,  # Указываем вариант
#     defaults={'quantity': 1}
# )

# Проверка доступности перед оформлением:
# for item in cart.items.all():
#     if not item.is_available():
#         print(f"Товар {item} недоступен!")

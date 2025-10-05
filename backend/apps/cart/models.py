"""
apps/cart/models.py — Модель корзины покупок для Vendaro CMS

Корзина позволяет пользователям:
- Добавлять товары
- Изменять количество
- Удалять товары
- Видеть общую стоимость с учётом B2B/B2C цен

Каждый пользователь имеет свою корзину в каждом магазине.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from decimal import Decimal

# ============================================
# КОРЗИНА
# ============================================


class Cart(TimeStampedModel):
    """
    Корзина покупок пользователя.

    Связь: один пользователь = одна корзина в магазине

    Важно:
    - Анонимные пользователи тоже могут иметь корзину (для session-based корзин)
    - При регистрации анонимная корзина переносится на пользователя
    """

    # store — магазин (корзина привязана к магазину)
    # Пользователь может иметь несколько корзин в разных магазинах
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name=_('store'),
    )

    # user — пользователь (владелец корзины)
    # null=True — может быть анонимная корзина
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True,
        verbose_name=_('user'),
    )

    # session_key — ключ сессии для анонимных пользователей
    # Используется для хранения корзины в сессии Django
    #
    # Логика:
    # - Если user=None: корзина анонимная, ищем по session_key
    # - Если user есть: session_key не используется
    session_key = models.CharField(
        _('session key'),
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
    )

    # is_active — активна ли корзина
    # False = корзина заброшена или превращена в заказ
    is_active = models.BooleanField(
        _('active'),
        default=True,
    )

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

        # Индексы для быстрого поиска
        indexes = [
            models.Index(fields=['store', 'user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active']),
        ]

        # unique_together — один пользователь = одна корзина в магазине
        # Если user=None (анонимная корзина), ограничение не действует
        unique_together = ['store', 'user']

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email} in {self.store.name}"
        return f"Anonymous cart {self.session_key} in {self.store.name}"

    def get_items_count(self):
        """
        Возвращает общее количество товаров в корзине.

        Пример:
        - 2 маски + 3 ласты = 5 товаров

        Возвращает: int
        """
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        """
        Вычисляет общую стоимость корзины.

        Учитывает:
        - Количество каждого товара
        - B2B/B2C цены (если пользователь оптовик)

        Возвращает: Decimal
        """
        total = Decimal('0.00')

        for item in self.items.all():
            total += item.get_subtotal()

        return total

    def clear(self):
        """
        Очищает корзину (удаляет все товары).

        Используется после оформления заказа.
        """
        self.items.all().delete()
        self.save()

    def merge_with(self, other_cart):
        """
        Объединяет текущую корзину с другой корзиной.

        Используется когда:
        - Пользователь был анонимным (корзина в сессии)
        - Пользователь залогинился (корзина переносится на аккаунт)

        Параметры:
        - other_cart: другая корзина (Cart)

        Логика:
        - Если товар уже есть в текущей корзине — увеличиваем количество
        - Если товара нет — добавляем
        """
        for item in other_cart.items.all():
            # Проверяем есть ли такой товар в текущей корзине
            existing_item = self.items.filter(product=item.product).first()

            if existing_item:
                # Увеличиваем количество
                existing_item.quantity += item.quantity
                existing_item.save()
            else:
                # Добавляем товар
                item.cart = self
                item.save()

        # Удаляем старую корзину
        other_cart.delete()


# ============================================
# ТОВАР В КОРЗИНЕ
# ============================================

class CartItem(TimeStampedModel):
    """
    Товар в корзине.

    Хранит:
    - Какой товар
    - Сколько штук
    - По какой цене (фиксируется при добавлении)
    """

    # cart — корзина
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart'),
    )

    # product — товар
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('product'),
    )

    # quantity — количество
    # MinValueValidator(1) — минимум 1 штука
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)],
    )

    # price — цена за единицу товара
    # Фиксируется при добавлении в корзину
    #
    # Зачем фиксировать цену:
    # - Цена товара может измениться пока товар в корзине
    # - Мы показываем пользователю цену, по которой он добавил товар
    # - При оформлении заказа используется актуальная цена
    price = models.DecimalField(
        _('price per unit'),
        max_digits=10,
        decimal_places=2,
    )

    # is_wholesale — оптовая ли цена
    # True = цена для B2B клиента
    # False = цена для обычного покупателя
    is_wholesale = models.BooleanField(
        _('wholesale price'),
        default=False,
    )

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        ordering = ['-created']

        # unique_together — один товар может быть только один раз в корзине
        # Если хотят добавить ещё — увеличиваем quantity
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def get_subtotal(self):
        """
        Вычисляет стоимость этой позиции.

        subtotal = price * quantity

        Пример:
        - price = 1000₽
        - quantity = 3
        - subtotal = 3000₽

        Возвращает: Decimal
        """
        return self.price * self.quantity

    def update_price(self):
        """
        Обновляет цену товара (актуальная цена из Product).

        Вызывается:
        - При изменении количества
        - При оформлении заказа
        - Вручную через API

        Учитывает B2B/B2C статус пользователя.
        """
        user = self.cart.user

        # Получаем актуальную цену для пользователя
        price, is_wholesale = self.product.get_price_for_user(user)

        self.price = price
        self.is_wholesale = is_wholesale
        self.save(update_fields=['price', 'is_wholesale', 'updated'])

    def save(self, *args, **kwargs):
        """
        Переопределяем save() чтобы автоматически устанавливать цену.

        При первом добавлении товара в корзину цена фиксируется.
        """
        # Если это новая запись (нет pk) — устанавливаем цену
        if not self.pk:
            user = self.cart.user
            price, is_wholesale = self.product.get_price_for_user(user)
            self.price = price
            self.is_wholesale = is_wholesale

        super().save(*args, **kwargs)


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# Получение или создание корзины для пользователя:
# cart, created = Cart.objects.get_or_create(
#     store=store,
#     user=user,
#     defaults={'is_active': True}
# )

# Добавление товара в корзину:
# cart_item, created = CartItem.objects.get_or_create(
#     cart=cart,
#     product=product,
#     defaults={'quantity': 1}
# )
# if not created:
#     # Товар уже был в корзине — увеличиваем количество
#     cart_item.quantity += 1
#     cart_item.save()

# Получение общей стоимости:
# total = cart.get_total_price()
# print(f"Итого: {total}₽")

# Очистка корзины после заказа:
# cart.clear()

# Объединение анонимной корзины с корзиной пользователя:
# # Пользователь был анонимным
# anonymous_cart = Cart.objects.get(session_key=request.session.session_key)
#
# # Пользователь залогинился
# user_cart, created = Cart.objects.get_or_create(store=store, user=user)
#
# # Объединяем корзины
# user_cart.merge_with(anonymous_cart)

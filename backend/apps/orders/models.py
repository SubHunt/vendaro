"""
apps/orders/models.py — Модель заказов для Vendaro CMS

Заказ создаётся когда пользователь оформляет покупку.
Содержит информацию о товарах, ценах, доставке, статусе.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from decimal import Decimal
import uuid

# ============================================
# ЗАКАЗ
# ============================================


class Order(TimeStampedModel):
    """
    Заказ покупателя.

    Жизненный цикл заказа:
    1. pending — создан, ожидает оплаты
    2. paid — оплачен
    3. processing — в обработке (комплектуется)
    4. shipped — отправлен
    5. delivered — доставлен
    6. cancelled — отменён
    """

    # Статусы заказа
    STATUS_CHOICES = [
        ('new', _('New')),                      # Новый заказ (только что создан)
        ('contacted', _('Contacted')),          # Связались с клиентом
        ('confirmed', _('Confirmed')),          # Подтверждён клиентом
        ('paid', _('Paid')),                    # Оплачен
        ('processing', _('Processing')),        # В обработке (комплектуется)
        ('shipped', _('Shipped')),              # Отправлен
        ('delivered', _('Delivered')),          # Доставлен
        ('cancelled', _('Cancelled')),          # Отменён
    ]

    # Тип заказа
    ORDER_TYPE_CHOICES = [
        ('standard', _('Standard Order')),      # Обычный заказ (через корзину)
        ('one_click', _('One Click Order')),    # Заказ в 1 клик
    ]

    # ========================================
    # ОСНОВНЫЕ ПОЛЯ
    # ========================================

    # order_number — уникальный номер заказа
    # Показывается клиенту, используется для трекинга
    # Формат: ORD-20250102-A1B2C3
    order_number = models.CharField(
        _('order number'),
        max_length=50,
        unique=True,
        db_index=True,
        editable=False,
    )

    # store — магазин
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('store'),
    )

    # user — покупатель
    # null=True — может быть гостевой заказ (без регистрации)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True,
        verbose_name=_('user'),
    )

    # status — статус заказа
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )

    # ========================================
    # ИНФОРМАЦИЯ О ПОКУПАТЕЛЕ
    # ========================================

    # Имя и контакты
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    email = models.EmailField(_('email'))
    phone = models.CharField(_('phone'), max_length=20)

    # ========================================
    # АДРЕС ДОСТАВКИ
    # ========================================

    shipping_address_line1 = models.CharField(
        _('address line 1'), max_length=255)
    shipping_address_line2 = models.CharField(
        _('address line 2'), max_length=255, blank=True)
    shipping_city = models.CharField(_('city'), max_length=100)
    shipping_postal_code = models.CharField(_('postal code'), max_length=20)
    shipping_country = models.CharField(
        _('country'), max_length=2, default='RU')

    # ========================================
    # СТОИМОСТЬ
    # ========================================

    # subtotal — стоимость товаров (без доставки, без налогов)
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=10,
        decimal_places=2,
    )

    # shipping_cost — стоимость доставки
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    # tax — налог (НДС)
    tax = models.DecimalField(
        _('tax'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    # discount — скидка (если применён промокод)
    discount = models.DecimalField(
        _('discount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    # total — итоговая сумма заказа
    # total = subtotal + shipping_cost + tax - discount
    total = models.DecimalField(
        _('total'),
        max_digits=10,
        decimal_places=2,
    )

    # ========================================
    # ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ
    # ========================================

    # is_wholesale — оптовый ли заказ
    # True = заказ от B2B клиента (применялись оптовые цены)
    is_wholesale = models.BooleanField(
        _('wholesale order'),
        default=False,
    )

    # customer_note — комментарий покупателя к заказу
    customer_note = models.TextField(
        _('customer note'),
        blank=True,
        help_text=_('Additional notes from customer'),
    )

    # admin_note — внутренний комментарий (для менеджеров)
    admin_note = models.TextField(
        _('admin note'),
        blank=True,
        help_text=_('Internal notes (not visible to customer)'),
    )

    # tracking_number — номер отслеживания доставки
    # Заполняется когда заказ отправлен
    tracking_number = models.CharField(
        _('tracking number'),
        max_length=100,
        blank=True,
    )

    # paid_at — дата и время оплаты
    paid_at = models.DateTimeField(
        _('paid at'),
        null=True,
        blank=True,
    )

    # shipped_at — дата и время отправки
    shipped_at = models.DateTimeField(
        _('shipped at'),
        null=True,
        blank=True,
    )

    # delivered_at — дата и время доставки
    delivered_at = models.DateTimeField(
        _('delivered at'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created']

        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['store', 'status']),
            models.Index(fields=['user']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        """
        Переопределяем save() чтобы автоматически генерировать order_number.
        """
        if not self.order_number:
            # Генерируем уникальный номер заказа
            # Формат: ORD-20250102-A1B2C3D4
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            unique_id = uuid.uuid4().hex[:8].upper()
            self.order_number = f"ORD-{date_str}-{unique_id}"

        super().save(*args, **kwargs)

    def calculate_total(self):
        """
        Вычисляет итоговую сумму заказа.

        total = subtotal + shipping_cost + tax - discount

        Возвращает: Decimal
        """
        total = self.subtotal + self.shipping_cost + self.tax - self.discount
        return max(total, Decimal('0.00'))  # Минимум 0

    def get_full_name(self):
        """Возвращает полное имя покупателя"""
        return f"{self.first_name} {self.last_name}"

    def get_shipping_address(self):
        """
        Возвращает полный адрес доставки в виде строки.

        Пример: "ул. Ленина, д. 10, кв. 5, Москва, 101000, Россия"
        """
        parts = [
            self.shipping_address_line1,
            self.shipping_address_line2,
            self.shipping_city,
            self.shipping_postal_code,
        ]
        return ', '.join(filter(None, parts))

    def mark_as_paid(self):
        """
        Помечает заказ как оплаченный.

        Вызывается после успешной оплаты через Stripe.
        """
        from django.utils import timezone

        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated'])

    def mark_as_shipped(self, tracking_number=None):
        """
        Помечает заказ как отправленный.

        Параметры:
        - tracking_number: номер отслеживания (опционально)
        """
        from django.utils import timezone

        self.status = 'shipped'
        self.shipped_at = timezone.now()

        if tracking_number:
            self.tracking_number = tracking_number

        self.save(update_fields=['status', 'shipped_at',
                  'tracking_number', 'updated'])

    def mark_as_delivered(self):
        """Помечает заказ как доставленный"""
        from django.utils import timezone

        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated'])

    def cancel(self, reason=None):
        """
        Отменяет заказ.

        Параметры:
        - reason: причина отмены (сохраняется в admin_note)
        """
        self.status = 'cancelled'

        if reason:
            self.admin_note = f"Отменён: {reason}\n{self.admin_note}"

        self.save(update_fields=['status', 'admin_note', 'updated'])


# ============================================
# ТОВАР В ЗАКАЗЕ
# ============================================

class OrderItem(TimeStampedModel):
    """
    Товар в заказе.

    Фиксирует:
    - Какой товар был заказан
    - Сколько штук
    - По какой цене (на момент заказа)

    Важно: цена фиксируется! Даже если цена товара изменится,
    в заказе остаётся та цена, по которой покупатель оформил заказ.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order'),
    )

    # product — товар
    # SET_NULL — если товар удалён, заказ остаётся (product=None)
    # Храним всю информацию о товаре в order item
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        related_name='order_items',
        null=True,
        blank=True,
        verbose_name=_('product'),
    )

    # product_name — название товара
    # Фиксируем на случай если товар удалят или переименуют
    product_name = models.CharField(
        _('product name'),
        max_length=255,
    )

    # product_sku — артикул товара
    product_sku = models.CharField(
        _('product SKU'),
        max_length=100,
        blank=True,
    )

    # quantity — количество
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
    )

    # price — цена за единицу (на момент заказа)
    price = models.DecimalField(
        _('price per unit'),
        max_digits=10,
        decimal_places=2,
    )

    # is_wholesale — оптовая ли цена применялась
    is_wholesale = models.BooleanField(
        _('wholesale price'),
        default=False,
    )

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    def get_subtotal(self):
        """
        Вычисляет стоимость этой позиции.

        subtotal = price * quantity

        Возвращает: Decimal
        """
        return self.price * self.quantity


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# Создание заказа из корзины:
# order = Order.objects.create(
#     store=store,
#     user=user,
#     first_name=user.first_name,
#     last_name=user.last_name,
#     email=user.email,
#     phone=user.phone,
#     shipping_address_line1='ул. Ленина, 10',
#     shipping_city='Москва',
#     shipping_postal_code='101000',
#     subtotal=cart.get_total_price(),
#     shipping_cost=Decimal('500'),
#     total=cart.get_total_price() + Decimal('500'),
#     is_wholesale=user.is_wholesale,
# )
#
# # Добавляем товары из корзины
# for cart_item in cart.items.all():
#     OrderItem.objects.create(
#         order=order,
#         product=cart_item.product,
#         product_name=cart_item.product.name,
#         product_sku=cart_item.product.sku,
#         quantity=cart_item.quantity,
#         price=cart_item.price,
#         is_wholesale=cart_item.is_wholesale,
#     )
#
# # Очищаем корзину
# cart.clear()

# Получение заказов пользователя:
# orders = Order.objects.filter(user=user, store=store).order_by('-created')

# Обновление статуса заказа:
# order.mark_as_paid()
# order.mark_as_shipped(tracking_number='RU123456789')
# order.mark_as_delivered()

# Отмена заказа:
# order.cancel(reason='Клиент передумал')

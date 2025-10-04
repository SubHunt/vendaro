"""
apps/payments/models.py — Модель платежей для Vendaro CMS

Простая модель без онлайн-оплаты.
Основные способы оплаты: при получении, банковский перевод.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from decimal import Decimal

# ============================================
# ПЛАТЁЖ
# ============================================


class Payment(TimeStampedModel):
    """
    Платёж за заказ.

    Простая модель для фиксации факта оплаты.
    Без интеграции с платёжными системами.
    """

    # Статусы платежа
    STATUS_CHOICES = [
        ('pending', _('Pending')),              # Ожидает оплаты
        ('paid', _('Paid')),                    # Оплачен
        ('cancelled', _('Cancelled')),          # Отменён
        ('refunded', _('Refunded')),            # Возврат средств
    ]

    # Методы оплаты
    METHOD_CHOICES = [
        ('cash_on_delivery', _('Cash on Delivery')),    # Наличными при получении
        ('card_on_delivery', _('Card on Delivery')),    # Картой при получении
        ('bank_transfer', _('Bank Transfer')),          # Банковский перевод
        ('cash', _('Cash')),                            # Наличные в офисе
    ]

    # ========================================
    # ОСНОВНЫЕ ПОЛЯ
    # ========================================

    # order — заказ
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('order'),
    )

    # store — магазин
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('store'),
    )

    # amount — сумма платежа
    amount = models.DecimalField(
        _('amount'),
        max_digits=10,
        decimal_places=2,
    )

    # currency — валюта
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='RUB',
    )

    # status — статус платежа
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )

    # method — метод оплаты
    method = models.CharField(
        _('payment method'),
        max_length=30,
        choices=METHOD_CHOICES,
        default='cash_on_delivery',
    )

    # ========================================
    # ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ
    # ========================================

    # note — примечание к платежу
    # Например: "Оплачено картой курьеру 15.01.2025"
    note = models.TextField(
        _('note'),
        blank=True,
        help_text=_('Additional payment notes'),
    )

    # paid_at — дата и время оплаты
    paid_at = models.DateTimeField(
        _('paid at'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created']

        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['-created']),
        ]

    def __str__(self):
        return f"Payment for Order {self.order.order_number} - {self.get_status_display()}"

    def mark_as_paid(self, note=None):
        """
        Помечает платёж как оплаченный.

        Вызывается вручную администратором после подтверждения оплаты.

        Параметры:
        - note: примечание (например: "Оплачено 15.01.2025")
        """
        from django.utils import timezone

        self.status = 'paid'
        self.paid_at = timezone.now()

        if note:
            self.note = note

        self.save(update_fields=['status', 'paid_at', 'note', 'updated'])

        # Обновляем статус заказа
        self.order.mark_as_paid()


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# Создание платежа при оформлении заказа:
# payment = Payment.objects.create(
#     order=order,
#     store=store,
#     amount=order.total,
#     currency='RUB',
#     method='cash_on_delivery',  # Оплата при получении
#     status='pending',
# )

# Пометка заказа как оплаченного (администратором):
# payment.mark_as_paid(note='Оплачено наличными курьеру 15.01.2025')

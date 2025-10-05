"""
apps/orders/signals.py — Сигналы для заказов

Автоматизация процессов при создании/изменении заказов.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def update_product_sales_count(sender, instance, created, **kwargs):
    """
    Обновляет счётчик продаж товаров при оплате заказа.

    Срабатывает:
    - Когда заказ переходит в статус 'paid' (оплачен)

    Что делает:
    - Увеличивает sales_count у каждого товара в заказе
    """
    # Проверяем что заказ оплачен
    if instance.status == 'paid':
        # Проверяем что это изменение статуса (не создание)
        if not created:
            # Проверяем что статус действительно изменился на 'paid'
            try:
                old_instance = Order.objects.get(pk=instance.pk)
                # Если статус был не 'paid', а стал 'paid'
                if old_instance.status != 'paid':
                    # Обновляем счётчик продаж для каждого товара
                    for item in instance.items.all():
                        if item.product:
                            item.product.sales_count += item.quantity
                            item.product.save(update_fields=['sales_count'])
            except Order.DoesNotExist:
                pass

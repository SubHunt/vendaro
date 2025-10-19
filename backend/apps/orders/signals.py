"""
apps/orders/signals.py — Django Signals для автоматической отправки email

Signals — это механизм Django для автоматического выполнения действий
при определённых событиях (например: создание заказа).

Когда создаётся новый заказ → автоматически отправляются email.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.orders.tasks import send_order_confirmation_to_customer, send_order_notification_to_admin


@receiver(post_save, sender=Order)
def send_order_notifications(sender, instance, created, **kwargs):
    """
    Signal handler для отправки email при создании заказа.

    Параметры:
    - sender: модель Order
    - instance: созданный объект заказа
    - created: True если объект только что создан, False если обновлён
    - **kwargs: дополнительные параметры

    Что делает:
    - Если заказ только создан (created=True) → отправляем email
    - Если заказ обновлён (created=False) → ничего не делаем
    """

    # Отправляем email только для новых заказов
    if created:
        # Запускаем Celery задачи в фоне
        # delay() — асинхронный запуск задачи
        send_order_confirmation_to_customer.delay(instance.id)
        send_order_notification_to_admin.delay(instance.id)

        print(
            f"✉️ Email notifications sent for Order #{instance.order_number}")
# """
# apps/orders/signals.py — Сигналы для заказов

# Автоматизация процессов при создании/изменении заказов.
# """

# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Order


# @receiver(post_save, sender=Order)
# def update_product_sales_count(sender, instance, created, **kwargs):
#     """
#     Обновляет счётчик продаж товаров при оплате заказа.

#     Срабатывает:
#     - Когда заказ переходит в статус 'paid' (оплачен)

#     Что делает:
#     - Увеличивает sales_count у каждого товара в заказе
#     """
#     # Проверяем что заказ оплачен
#     if instance.status == 'paid':
#         # Проверяем что это изменение статуса (не создание)
#         if not created:
#             # Проверяем что статус действительно изменился на 'paid'
#             try:
#                 old_instance = Order.objects.get(pk=instance.pk)
#                 # Если статус был не 'paid', а стал 'paid'
#                 if old_instance.status != 'paid':
#                     # Обновляем счётчик продаж для каждого товара
#                     for item in instance.items.all():
#                         if item.product:
#                             item.product.sales_count += item.quantity
#                             item.product.save(update_fields=['sales_count'])
#             except Order.DoesNotExist:
#                 pass

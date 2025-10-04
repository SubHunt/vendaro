"""
apps/orders/tasks.py — Celery задачи для отправки email уведомлений

Celery — это система для выполнения задач в фоне (асинхронно).
Email отправляется не сразу, а в фоновом режиме, чтобы не блокировать пользователя.
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


@shared_task
def send_order_confirmation_to_customer(order_id):
    """
    Отправка email клиенту о принятии заказа.

    Параметры:
    - order_id: ID заказа

    Что делает:
    1. Получает заказ из БД
    2. Формирует письмо
    3. Отправляет клиенту
    """
    from apps.orders.models import Order

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return f"Order {order_id} not found"

    # Формируем тему письма
    subject = f'Ваш заказ #{order.order_number} принят'

    # Формируем текст письма
    message = f"""
Здравствуйте, {order.first_name}!

Спасибо за ваш заказ в {order.store.name}!

Номер заказа: {order.order_number}
Сумма заказа: {order.total} {order.store.currency_symbol}

Мы получили ваш заказ и скоро свяжемся с вами для уточнения деталей доставки и оплаты.

Товары в заказе:
"""

    # Добавляем список товаров
    for item in order.items.all():
        message += f"\n- {item.product_name} x {item.quantity} = {item.get_subtotal()} {order.store.currency_symbol}"

    message += f"""

Если у вас есть вопросы, свяжитесь с нами:
Email: {order.store.email}
Телефон: {order.store.phone}

С уважением,
Команда {order.store.name}
"""

    # Отправляем email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=False,
    )

    return f"Email sent to {order.email}"


@shared_task
def send_order_notification_to_admin(order_id):
    """
    Отправка email администратору о новом заказе.

    Параметры:
    - order_id: ID заказа

    Что делает:
    1. Получает заказ из БД
    2. Формирует письмо с деталями заказа
    3. Отправляет администратору магазина
    """
    from apps.orders.models import Order

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return f"Order {order_id} not found"

    # Email администратора магазина
    admin_email = order.store.settings.order_notification_email or order.store.email

    # Тип заказа
    order_type_display = '🛒 Обычный заказ' if order.order_type == 'standard' else '⚡ Заказ в 1 клик'

    # Формируем тему письма
    subject = f'🔔 Новый заказ #{order.order_number} в {order.store.name}'

    # Формируем текст письма
    message = f"""
{order_type_display}

===================================
ИНФОРМАЦИЯ О ЗАКАЗЕ
===================================

Номер заказа: {order.order_number}
Дата: {order.created.strftime('%d.%m.%Y %H:%M')}
Статус: {order.get_status_display()}

===================================
ДАННЫЕ ПОКУПАТЕЛЯ
===================================

Имя: {order.first_name} {order.last_name}
Email: {order.email}
Телефон: {order.phone}
"""

    # Адрес доставки (если указан)
    if order.shipping_city:
        message += f"""
Адрес доставки:
{order.get_shipping_address()}
"""

    # Комментарий клиента (если есть)
    if order.customer_note:
        message += f"""
Комментарий клиента:
{order.customer_note}
"""

    # Список товаров
    message += f"""

===================================
ТОВАРЫ В ЗАКАЗЕ
===================================
"""

    for item in order.items.all():
        wholesale_mark = ' (ОПТО Велосипед)' if item.is_wholesale else ''
        message += f"""
• {item.product_name} {wholesale_mark}
  Артикул: {item.product_sku}
  Количество: {item.quantity} шт
  Цена за шт: {item.price} {order.store.currency_symbol}
  Сумма: {item.get_subtotal()} {order.store.currency_symbol}
"""

    # Итого
    message += f"""

===================================
ИТОГО
===================================

Стоимость товаров: {order.subtotal} {order.store.currency_symbol}
Доставка: {order.shipping_cost} {order.store.currency_symbol}
Скидка: {order.discount} {order.store.currency_symbol}

ИТОГО К ОПЛАТЕ: {order.total} {order.store.currency_symbol}

===================================

⚠️ Свяжитесь с покупателем для уточнения деталей!

Админ-панель: {settings.SITE_URL}/admin/orders/order/{order.id}/
"""

    # Отправляем email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[admin_email],
        fail_silently=False,
    )

    return f"Admin notification sent to {admin_email}"


@shared_task
def send_one_click_order_notification(order_id):
    """
    Отправка уведомлений для заказа в 1 клик.

    Отправляет:
    1. Клиенту — подтверждение
    2. Администратору — уведомление

    Параметры:
    - order_id: ID заказа
    """
    # Отправляем оба письма
    send_order_confirmation_to_customer(order_id)
    send_order_notification_to_admin(order_id)

    return f"One-click order notifications sent for order {order_id}"

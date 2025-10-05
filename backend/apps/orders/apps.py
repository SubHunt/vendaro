"""
apps/orders/apps.py — Конфигурация приложения Orders

Этот файл нужен чтобы Django знал о приложении и его настройках.
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Конфигурация приложения Orders.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Orders'

    def ready(self):
        """
        Метод ready() вызывается когда Django загрузил приложение.

        Здесь мы импортируем signals чтобы они зарегистрировались.
        """
        # Импортируем signals (это активирует их)
        import apps.orders.signals
        # pass

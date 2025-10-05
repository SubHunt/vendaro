"""
apps/products/apps.py — Конфигурация приложения Products
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = 'Products'

    def ready(self):
        """
        Вызывается когда Django загружает приложение.
        Здесь подключаем signals.
        """
        import apps.products.signals  # Импортируем signals

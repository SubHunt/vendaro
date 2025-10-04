"""
config/__init__.py

Импортируем Celery чтобы Django знал о нём.
"""

# Это гарантирует что Celery app загружается когда Django стартует
from .celery import app as celery_app

__all__ = ('celery_app',)

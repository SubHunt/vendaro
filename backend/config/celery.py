"""
config/celery.py — Настройка Celery для фоновых задач

Celery — система для выполнения задач в фоне (асинхронно).
Используется для отправки email, генерации отчётов, и т.д.
"""

import os
from celery import Celery

# Устанавливаем переменную окружения для Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Создаём приложение Celery
app = Celery('vendaro')

# Загружаем настройки из Django settings
# namespace='CELERY' означает что все настройки Celery начинаются с CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в файлах tasks.py во всех приложениях
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """
    Тестовая задача для проверки что Celery работает.

    Запуск:
    from config.celery import debug_task
    debug_task.delay()
    """
    print(f'Request: {self.request!r}')

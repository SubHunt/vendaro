"""
config/settings/__init__.py

Автоматически выбирает правильные настройки
в зависимости от переменной окружения ENVIRONMENT.
"""

import os

# Получаем значение ENVIRONMENT из .env
# Возможные значения: 'development', 'production'
environment = os.getenv('ENVIRONMENT', 'development')

# Импортируем соответствующие настройки
if environment == 'production':
    from .production import *
else:
    from .development import *

# Выводим какие настройки используются
print(f"🚀 Vendaro CMS using settings: {environment}")

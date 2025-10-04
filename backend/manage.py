#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Устанавливаем путь к настройкам Django
    # По умолчанию используем настройки для разработки (development)
    #
    # os.environ.setdefault() — устанавливает переменную окружения,
    # если она ещё не установлена
    #
    # 'config.settings.development' означает:
    #   config/ — папка с настройками
    #   settings/ — подпапка
    #   development.py — файл с настройками для разработки
    #
    # Для продакшена можно переопределить через переменную окружения:
    # export DJANGO_SETTINGS_MODULE=config.settings.production
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

# ============================================
# ОСНОВНЫЕ КОМАНДЫ MANAGE.PY
# ============================================

# 1. ЗАПУСК СЕРВЕРА РАЗРАБОТКИ
# python manage.py runserver
# Запускает Django на http://127.0.0.1:8000/
#
# На другом порту:
# python manage.py runserver 8080
#
# На всех интерфейсах (для доступа с других устройств):
# python manage.py runserver 0.0.0.0:8000

# 2. СОЗДАНИЕ МИГРАЦИЙ
# python manage.py makemigrations
# Анализирует изменения в models.py и создаёт файлы миграций
# Миграции — это инструкции для изменения структуры БД
#
# Для конкретного приложения:
# python manage.py makemigrations products

# 3. ПРИМЕНЕНИЕ МИГРАЦИЙ
# python manage.py migrate
# Применяет миграции к базе данных (создаёт/изменяет таблицы)
# Первый запуск создаёт стандартные таблицы Django (users, sessions, и т.д.)

# 4. СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ (администратора)
# python manage.py createsuperuser
# Создаёт пользователя с доступом к Django Admin (/admin/)
# Спросит: email, имя, фамилию, пароль

# 5. ЗАПУСК ИНТЕРАКТИВНОЙ КОНСОЛИ PYTHON
# python manage.py shell
# Открывает Python консоль с загруженным Django
# Можно тестировать модели, делать запросы к БД
#
# Улучшенная версия (если установлен django-extensions):
# python manage.py shell_plus

# 6. СОЗДАНИЕ НОВОГО ПРИЛОЖЕНИЯ
# python manage.py startapp myapp
# Создаёт структуру папок для нового Django приложения
# НО! Мы не используем эту команду, т.к. создаём структуру вручную в apps/

# 7. СБОР СТАТИЧЕСКИХ ФАЙЛОВ (для продакшена)
# python manage.py collectstatic
# Собирает все static файлы (CSS, JS, images) в одну папку
# Нужно для деплоя (Nginx отдаёт статику из этой папки)

# 8. ПРОВЕРКА ПРОЕКТА НА ОШИБКИ
# python manage.py check
# Проверяет настройки и модели на ошибки конфигурации
#
# Проверка для продакшена:
# python manage.py check --deploy
# Показывает предупреждения о безопасности

# 9. ПОКАЗАТЬ ВСЕ URL МАРШРУТЫ
# python manage.py show_urls
# (Требует django-extensions)
# Показывает список всех URL в проекте

# 10. ЗАПУСК ТЕСТОВ
# python manage.py test
# Запускает все тесты проекта
#
# Тесты конкретного приложения:
# python manage.py test apps.products

# 11. СОЗДАНИЕ ФИКСТУР (тестовые данные)
# python manage.py dumpdata products --indent 2 > fixtures/products.json
# Экспортирует данные из БД в JSON файл
#
# Загрузка фикстур:
# python manage.py loaddata fixtures/products.json

# 12. ОЧИСТКА БД (ОСТОРОЖНО!)
# python manage.py flush
# Удаляет ВСЕ данные из БД (кроме суперпользователя)

# 13. ПОКАЗАТЬ СПИСОК МИГРАЦИЙ
# python manage.py showmigrations
# Показывает какие миграции применены (✓), а какие нет

# 14. ОТКАТИТЬ МИГРАЦИЮ
# python manage.py migrate products 0003
# Откатывает миграции до указанной (0003)

# ============================================
# ПЕРВЫЙ ЗАПУСК ПРОЕКТА
# ============================================

# После создания проекта выполните по порядку:
#
# 1. Применить миграции (создать таблицы в БД):
#    python manage.py migrate
#
# 2. Создать суперпользователя (для доступа в /admin/):
#    python manage.py createsuperuser
#
# 3. Запустить сервер:
#    python manage.py runserver
#
# 4. Открыть в браузере:
#    http://127.0.0.1:8000/
#    http://127.0.0.1:8000/admin/  (админка)

# ============================================
# ВАЖНО: ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ
# ============================================

# ВСЕГДА активируйте виртуальное окружение перед запуском команд!
#
# Активация:
#   Windows: venv\Scripts\activate
#   Mac/Linux: source venv/bin/activate
#
# Должны видеть (venv) в начале строки терминала:
#   (venv) C:\vendaro\backend>
#
# Деактивация:
#   deactivate

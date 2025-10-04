"""
config/settings/base.py — Базовые настройки Django для Vendaro CMS

Этот файл содержит настройки, общие для всех окружений (development, production).
Специфичные настройки находятся в development.py и production.py
"""

from datetime import timedelta
import os
from pathlib import Path
import environ  # django-environ для чтения .env файла

# ============================================
# ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ============================================

# environ.Env() создаёт объект для чтения переменных из .env файла
# Это безопасный способ хранения секретов (пароли, API ключи)
env = environ.Env(
    # Значения по умолчанию, если переменная не найдена в .env
    DEBUG=(bool, False),  # DEBUG по умолчанию False (безопасно)
)

# ============================================
# ПУТИ К ПАПКАМ ПРОЕКТА
# ============================================

# BASE_DIR — корневая папка проекта (где находится manage.py)
#
# Path(__file__) — путь к текущему файлу (base.py)
# .resolve() — преобразует в абсолютный путь
# .parent — поднимается на уровень выше
#
# Структура:
# BASE_DIR/                    ← BASE_DIR указывает сюда
#   ├── manage.py
#   ├── config/
#   │   └── settings/
#   │       └── base.py        ← __file__ это этот файл
#   └── apps/
#
# .parent -> config/settings/
# .parent.parent -> config/
# .parent.parent.parent -> BASE_DIR/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Читаем .env файл из корня проекта
env_file = BASE_DIR / '.env'

# Если .env файл существует, читаем его
if env_file.exists():
    environ.Env.read_env(env_file)

# ============================================
# БЕЗОПАСНОСТЬ
# ============================================

# SECRET_KEY — секретный ключ Django для криптографии
# Используется для:
# - Подписи сессий (cookies)
# - CSRF токенов (защита от подделки запросов)
# - Генерации паролей
#
# ВАЖНО: В продакшене должен быть длинным и случайным!
# Генерация: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = env('SECRET_KEY')

# DEBUG — режим отладки
# True: показывает подробные ошибки (ТОЛЬКО для разработки!)
# False: скрывает ошибки, показывает страницы 404/500 (для продакшена)
DEBUG = env.bool('DEBUG', default=False)

# ALLOWED_HOSTS — список доменов, которым разрешён доступ к Django
# Защита от HTTP Host header атак
#
# Для разработки: ['localhost', '127.0.0.1']
# Для продакшена: ['vendaro.ru', 'www.vendaro.ru', 'deepreef.ru']
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# ============================================
# ПРИЛОЖЕНИЯ DJANGO
# ============================================

# INSTALLED_APPS — список всех приложений (модулей) в проекте
# Django загружает их при старте
INSTALLED_APPS = [
    # ========================================
    # Встроенные приложения Django
    # ========================================
    'django.contrib.admin',          # Админ-панель Django (/admin/)
    'django.contrib.auth',           # Система аутентификации и пользователей
    # Система типов контента (связи между моделями)
    'django.contrib.contenttypes',
    # Сессии пользователей (хранение состояния)
    'django.contrib.sessions',
    'django.contrib.messages',       # Система сообщений (flash messages)
    # Работа со статическими файлами (CSS, JS, images)
    'django.contrib.staticfiles',

    # ========================================
    # Сторонние приложения (библиотеки)
    # ========================================
    'rest_framework',                # Django REST Framework (для API)
    'rest_framework_simplejwt',      # JWT аутентификация
    'corsheaders',                   # CORS headers (для связи с React)
    'django_filters',                # Фильтрация данных в API
    'drf_spectacular',               # Автогенерация документации API (Swagger)

    # ========================================
    # Наши приложения Vendaro CMS
    # ========================================
    'apps.core',                     # Ядро системы (базовые модели, утилиты)
    'apps.accounts',                 # Пользователи и аутентификация
    'apps.stores',                   # Multi-tenant магазины
    'apps.products',                 # Каталог товаров
    'apps.cart',                     # Корзина покупок
    'apps.orders',                   # Заказы
    'apps.payments',                 # Платежи (Stripe)
    'apps.cms',                      # CMS (статические страницы, блог)
]

# ============================================
# MIDDLEWARE
# ============================================

# MIDDLEWARE — слои обработки запросов
# Каждый HTTP запрос проходит через middleware сверху вниз (request)
# Каждый HTTP ответ проходит снизу вверх (response)
#
# Порядок ВАЖЕН!
MIDDLEWARE = [
    # SecurityMiddleware — добавляет заголовки безопасности
    'django.middleware.security.SecurityMiddleware',

    # SessionMiddleware — управляет сессиями пользователей
    'django.contrib.sessions.middleware.SessionMiddleware',

    # CorsMiddleware — обрабатывает CORS headers
    # Должен быть как можно раньше (до CommonMiddleware)
    'corsheaders.middleware.CorsMiddleware',

    # CommonMiddleware — общие функции
    'django.middleware.common.CommonMiddleware',

    # CsrfViewMiddleware — защита от CSRF атак
    'django.middleware.csrf.CsrfViewMiddleware',

    # AuthenticationMiddleware — добавляет request.user
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # MessageMiddleware — система сообщений Django
    'django.contrib.messages.middleware.MessageMiddleware',

    # XFrameOptionsMiddleware — защита от clickjacking
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# URL КОНФИГУРАЦИЯ
# ============================================

# ROOT_URLCONF — главный файл с URL маршрутами
ROOT_URLCONF = 'config.urls'

# ============================================
# ШАБЛОНЫ (Templates)
# ============================================

# TEMPLATES — настройки системы шаблонов Django
# Мы не будем использовать шаблоны (у нас React фронтенд),
# но они нужны для Django Admin
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================
# WSGI / ASGI
# ============================================

# WSGI_APPLICATION — путь к WSGI приложению для деплоя
WSGI_APPLICATION = 'config.wsgi.application'

# ASGI_APPLICATION — путь к ASGI приложению (для WebSockets в будущем)
ASGI_APPLICATION = 'config.asgi.application'

# ============================================
# БАЗА ДАННЫХ
# ============================================

# DATABASES — настройки подключения к базе данных
# Используем PostgreSQL (production-ready БД)
#
# env.db() автоматически парсит DATABASE_URL из .env:
# DATABASE_URL=postgresql://vendaro_user:password@localhost:5432/vendaro_db
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# ============================================
# КАСТОМНАЯ МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================

# AUTH_USER_MODEL — указывает Django использовать нашу модель User
# Вместо стандартной django.contrib.auth.models.User
#
# Формат: 'app_label.ModelName'
# 'accounts' — название приложения
# 'User' — название модели
AUTH_USER_MODEL = 'accounts.User'

# ============================================
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# ============================================

# AUTH_PASSWORD_VALIDATORS — правила для паролей пользователей
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================
# ИНТЕРНАЦИОНАЛИЗАЦИЯ
# ============================================

# LANGUAGE_CODE — язык по умолчанию
LANGUAGE_CODE = 'ru'

# TIME_ZONE — часовой пояс
TIME_ZONE = 'UTC'

# USE_I18N — включить интернационализацию
USE_I18N = True

# USE_TZ — использовать timezone-aware datetime
USE_TZ = True

# ============================================
# СТАТИЧЕСКИЕ ФАЙЛЫ (CSS, JavaScript, Images)
# ============================================

# STATIC_URL — URL префикс для статических файлов
STATIC_URL = '/static/'

# STATIC_ROOT — папка куда собираются статические файлы
STATIC_ROOT = BASE_DIR / 'staticfiles'

# STATICFILES_DIRS — дополнительные папки со статикой
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# ============================================
# МЕДИА ФАЙЛЫ (загруженные пользователями)
# ============================================

# MEDIA_URL — URL префикс для медиа файлов
MEDIA_URL = '/media/'

# MEDIA_ROOT — папка для хранения загруженных файлов
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================
# DJANGO REST FRAMEWORK (DRF)
# ============================================

REST_FRAMEWORK = {
    # Способы аутентификации API
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # Права доступа по умолчанию
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),

    # Фильтрация и поиск
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),

    # Пагинация
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,

    # Форматы ответа API
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),

    # Форматы входящих данных
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),

    # Формат даты и времени
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S%z',

    # OpenAPI схема
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ============================================
# JWT НАСТРОЙКИ
# ============================================


SIMPLE_JWT = {
    # Время жизни access токена
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),

    # Время жизни refresh токена
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Создавать новый refresh при обновлении
    'ROTATE_REFRESH_TOKENS': True,

    # Добавлять старый refresh в чёрный список
    'BLACKLIST_AFTER_ROTATION': True,

    # Алгоритм шифрования
    'ALGORITHM': 'HS256',

    # Ключ для подписи
    'SIGNING_KEY': SECRET_KEY,

    # Тип заголовка
    'AUTH_HEADER_TYPES': ('Bearer',),

    # Поле ID пользователя
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ============================================
# CORS
# ============================================

# Разрешённые домены фронтенда
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:3000', 'http://127.0.0.1:3000']
)

# Разрешить отправку cookies
CORS_ALLOW_CREDENTIALS = True

# ============================================
# DRF SPECTACULAR (Swagger)
# ============================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Vendaro CMS API',
    'DESCRIPTION': 'Multi-tenant E-commerce Platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# ============================================
# DEFAULT PRIMARY KEY
# ============================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# CELERY НАСТРОЙКИ
# ============================================

# CELERY_BROKER_URL — URL брокера сообщений (Redis)
CELERY_BROKER_URL = env('CELERY_BROKER_URL',
                        default='redis://localhost:6379/0')

# CELERY_RESULT_BACKEND — где хранить результаты задач
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND',
                            default='redis://localhost:6379/0')

# CELERY_ACCEPT_CONTENT — форматы данных
CELERY_ACCEPT_CONTENT = ['json']

# CELERY_TASK_SERIALIZER — формат сериализации задач
CELERY_TASK_SERIALIZER = 'json'

# CELERY_RESULT_SERIALIZER — формат сериализации результатов
CELERY_RESULT_SERIALIZER = 'json'

# CELERY_TIMEZONE — часовой пояс
CELERY_TIMEZONE = TIME_ZONE

# ============================================
# EMAIL НАСТРОЙКИ
# ============================================

# DEFAULT_FROM_EMAIL — отправитель по умолчанию
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@vendaro.ru')

# SITE_URL — URL сайта (для ссылок в email)
SITE_URL = env('SITE_URL', default='http://localhost:8000')

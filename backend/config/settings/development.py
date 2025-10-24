"""
config/settings/development.py — Настройки для локальной разработки

ИСПРАВЛЕНО: Debug Toolbar корректно настроен с проверкой на тесты
"""

from .base import *
import sys

# ============================================
# ПРОВЕРКА НА ТЕСТЫ
# ============================================

TESTING = 'pytest' in sys.modules or 'test' in sys.argv

# ============================================
# РЕЖИМ ОТЛАДКИ
# ============================================

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1',
                 '0.0.0.0', 'test.local', 'testserver']

# ============================================
# УСТАНОВЛЕННЫЕ ПРИЛОЖЕНИЯ
# ============================================

# Debug Toolbar ТОЛЬКО если НЕ тесты
if DEBUG and not TESTING:
    INSTALLED_APPS += [
        'debug_toolbar',
        'django_extensions',
    ]

# ============================================
# MIDDLEWARE
# ============================================

# Debug Toolbar middleware ТОЛЬКО если НЕ тесты
if DEBUG and not TESTING:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# ============================================
# EMAIL (для разработки)
# ============================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================
# КЭШИРОВАНИЕ (для разработки)
# ============================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# ============================================
# DJANGO DEBUG TOOLBAR
# ============================================

if DEBUG and not TESTING:
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG and not TESTING,
    }

# ============================================
# CORS (для разработки)
# ============================================

CORS_ALLOW_ALL_ORIGINS = True

# ============================================
# ЛОГИРОВАНИЕ
# ============================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',  # SQL запросы
        },
    },
}

# ============================================
# БЕЗОПАСНОСТЬ (ослабляем для разработки)
# ============================================

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
# """
# config/settings/development.py — Настройки для локальной разработки

# Этот файл используется когда вы работаете на своём компьютере.
# Наследует все настройки из base.py и переопределяет некоторые для удобства.
# """

# # Импортируем ВСЕ настройки из base.py
# from .base import *
# import sys

# # ============================================
# # ПРОВЕРКА НА ТЕСТЫ
# # ============================================

# # Определяем запущены ли тесты
# TESTING = 'pytest' in sys.modules or 'test' in sys.argv

# # ============================================
# # РЕЖИМ ОТЛАДКИ
# # ============================================

# # DEBUG — включаем для разработки
# # Показывает подробные ошибки с traceback
# DEBUG = True

# # ALLOWED_HOSTS — для разработки разрешаем localhost
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'test.local']

# # ============================================
# # УСТАНОВЛЕННЫЕ ПРИЛОЖЕНИЯ (дополнения)
# # ============================================

# # Добавляем Debug Toolbar ТОЛЬКО если НЕ тесты
# if not TESTING:
#     INSTALLED_APPS += [
#         'debug_toolbar',
#         'django_extensions',
#     ]
# # INSTALLED_APPS += [
# #     'debug_toolbar',
# #     'django_extensions',
# # ]

# # ============================================
# # MIDDLEWARE (дополнения)
# # ============================================

# # Добавляем Debug Toolbar middleware в начало
# # Добавляем Debug Toolbar middleware ТОЛЬКО если НЕ тесты
# if not TESTING:
#     MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# # MIDDLEWARE = [
# #     'debug_toolbar.middleware.DebugToolbarMiddleware',
# #     'django.middleware.security.SecurityMiddleware',
# #     'django.contrib.sessions.middleware.SessionMiddleware',
# #     'corsheaders.middleware.CorsMiddleware',
# #     'django.middleware.common.CommonMiddleware',
# #     'django.middleware.csrf.CsrfViewMiddleware',
# #     'django.contrib.auth.middleware.AuthenticationMiddleware',
# #     'django.contrib.messages.middleware.MessageMiddleware',
# #     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# # ] + MIDDLEWARE[1:]

# # ============================================
# # EMAIL (для разработки)
# # ============================================

# # Выводим email в консоль (не отправляем настоящие)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# # ============================================
# # КЭШИРОВАНИЕ (для разработки)
# # ============================================

# # Dummy cache — не сохраняет ничего (для отладки удобно)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
#     }
# }

# # ============================================
# # DJANGO DEBUG TOOLBAR
# # ============================================

# # IP адреса которым показывать Debug Toolbar
# INTERNAL_IPS = [
#     '127.0.0.1',
#     'localhost',
# ]

# # Настройки Debug Toolbar
# DEBUG_TOOLBAR_CONFIG = {
#     'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
# }

# # ============================================
# # CORS (для разработки)
# # ============================================

# # Разрешаем все origins (Next.js может быть на разных портах)
# CORS_ALLOW_ALL_ORIGINS = True

# # ============================================
# # ЛОГИРОВАНИЕ
# # ============================================

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console'],
#             'level': 'INFO',
#         },
#         'django.db.backends': {
#             'handlers': ['console'],
#             'level': 'DEBUG',  # Показывать SQL запросы
#         },
#     },
# }

# # ============================================
# # БЕЗОПАСНОСТЬ (ослабляем для разработки)
# # ============================================

# CSRF_COOKIE_SECURE = False
# SESSION_COOKIE_SECURE = False
# SECURE_SSL_REDIRECT = False

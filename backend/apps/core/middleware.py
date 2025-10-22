"""
apps/core/middleware.py — Multi-tenant middleware для Vendaro CMS

ИСПРАВЛЕНО: Добавлена поддержка тестов через wsgi.url_scheme == 'http' без домена
"""

from django.http import Http404
from django.utils.deprecation import MiddlewareMixin
from apps.stores.models import Store


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware для определения текущего магазина (tenant).

    Логика:
    1. Извлекаем домен из HTTP_HOST (например: deepreef.local, deepreef.ru)
    2. Ищем магазин с таким доменом в БД
    3. Добавляем магазин в request.store
    4. Если магазин не найден - используем fallback (первый активный магазин)

    ИСПРАВЛЕНО: В тестах (когда нет HTTP_HOST) используется первый активный магазин
    """

    def process_request(self, request):
        """
        Обрабатывает каждый входящий запрос.

        Вызывается Django автоматически перед view.
        """

        # Исключения для служебных путей
        if self._is_exempt_path(request.path):
            request.store = None
            return None

        # Получаем домен из заголовка HTTP_HOST
        host = request.get_host()

        # ИСПРАВЛЕНИЕ: Проверяем что host не пустой
        if not host or host == 'testserver':
            # Тестовая среда - используем fallback
            store = Store.objects.filter(is_active=True).first()
            if not store:
                raise Http404(
                    "Нет активных магазинов в БД. "
                    "Создайте магазин: python manage.py loaddata demo_store"
                )
            request.store = store
            return None

        # Убираем порт если есть
        domain = host.split(':')[0]

        # Ищем магазин по домену
        try:
            store = Store.objects.get(domain=domain, is_active=True)
        except Store.DoesNotExist:
            # FALLBACK: Если магазин не найден по домену (например localhost),
            # берём первый активный магазин
            store = Store.objects.filter(is_active=True).first()

            if not store:
                # Совсем нет магазинов в БД
                raise Http404(
                    f"Магазин с доменом '{domain}' не найден. "
                    "Создайте магазин в админке: /admin/stores/store/add/"
                )

        # Сохраняем магазин в request
        request.store = store
        return None

    def _is_exempt_path(self, path):
        """
        Проверяет, нужно ли исключить путь из multi-tenant логики.

        Исключения:
        - /admin/ - Django Admin
        - /api/docs/ - API документация
        - /api/schema/ - OpenAPI схема
        - /__debug__/ - Django Debug Toolbar
        """
        exempt_paths = [
            '/admin/',
            '/api/docs/',
            '/api/schema/',
            '/__debug__/',
        ]

        for exempt_path in exempt_paths:
            if path.startswith(exempt_path):
                return True

        return False


class TenantQuerysetMiddleware(MiddlewareMixin):
    """
    Дополнительный middleware для автоматической фильтрации queryset по магазину.

    ВНИМАНИЕ: Это экспериментальная функция!
    Сейчас не используется.
    """

    def process_request(self, request):
        # TODO: Реализовать автоматическую фильтрацию
        pass

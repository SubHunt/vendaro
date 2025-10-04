"""
apps/core/middleware.py — Multi-tenant middleware для Vendaro CMS

Определяет текущий магазин по домену запроса и добавляет его в request.
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
    4. Если магазин не найден или неактивен - 404

    Использование в views:
    def my_view(request):
        store = request.store  # Текущий магазин
        products = Product.objects.filter(store=store)
    """

    def process_request(self, request):
        """
        Обрабатывает каждый входящий запрос.

        Вызывается Django автоматически перед view.
        """

        # Получаем домен из заголовка HTTP_HOST
        # Примеры:
        # - deepreef.local:8000 -> deepreef.local
        # - deepreef.ru -> deepreef.ru
        # - localhost:8000 -> localhost
        host = request.get_host()

        # Убираем порт если есть
        # deepreef.local:8000 -> deepreef.local
        domain = host.split(':')[0]

        # Исключения для служебных путей
        # Django Admin и API docs работают без привязки к магазину
        if self._is_exempt_path(request.path):
            request.store = None
            return None

        # Ищем магазин по домену
        try:
            store = Store.objects.get(domain=domain, is_active=True)
        except Store.DoesNotExist:
            # Магазин не найден - показываем 404
            raise Http404(f"Магазин с доменом '{domain}' не найден")

        # Сохраняем магазин в request
        # Теперь во всех views доступен: request.store
        request.store = store

        return None

    def _is_exempt_path(self, path):
        """
        Проверяет, нужно ли исключить путь из multi-tenant логики.

        Исключения:
        - /admin/ - Django Admin (работает для всех магазинов)
        - /api/docs/ - API документация
        - /api/schema/ - OpenAPI схема
        - /__debug__/ - Django Debug Toolbar

        Параметры:
        - path: строка пути (например: '/admin/stores/store/')

        Возвращает:
        - True если путь исключён
        - False если нужно проверять магазин
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
    Использовать с осторожностью, может конфликтовать с другими middleware.

    Автоматически добавляет filter(store=request.store) ко всем queryset.
    Сейчас не используется, но можно включить в будущем.
    """

    def process_request(self, request):
        # TODO: Реализовать автоматическую фильтрацию
        # Требует патчинг Django ORM
        pass

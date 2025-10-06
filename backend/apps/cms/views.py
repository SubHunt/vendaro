"""
apps/cms/views.py — Views для CMS API
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Page, BlogPost, Menu
from .serializers import (
    PageSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    MenuSerializer,
)


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для статических страниц.

    Endpoints:
    - GET /api/cms/pages/ - список страниц
    - GET /api/cms/pages/{slug}/ - страница по slug
    """

    serializer_class = PageSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        """Возвращает опубликованные страницы текущего магазина"""
        return Page.objects.filter(
            store=self.request.store,
            is_published=True
        ).order_by('title')


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для блога.

    Endpoints:
    - GET /api/cms/blog/ - список постов
    - GET /api/cms/blog/{slug}/ - пост по slug
    """

    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        """Возвращает опубликованные посты текущего магазина"""
        return BlogPost.objects.filter(
            store=self.request.store,
            is_published=True
        ).select_related('author').order_by('-published_at')

    def get_serializer_class(self):
        """Выбирает сериализатор в зависимости от действия"""
        if self.action == 'retrieve':
            return BlogPostDetailSerializer
        return BlogPostListSerializer


class MenuViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API для меню навигации.

    Endpoints:
    - GET /api/cms/menus/ - список меню
    - GET /api/cms/menus/{location}/ - меню по location
    """

    serializer_class = MenuSerializer
    permission_classes = [AllowAny]
    lookup_field = 'location'

    def get_queryset(self):
        """Возвращает активные меню текущего магазина"""
        return Menu.objects.filter(
            store=self.request.store,
            is_active=True
        ).prefetch_related('items__children')

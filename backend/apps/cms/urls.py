"""
apps/cms/urls.py — URL маршруты для CMS API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, BlogPostViewSet, MenuViewSet

router = DefaultRouter()
router.register(r'pages', PageViewSet, basename='page')
router.register(r'blog', BlogPostViewSet, basename='blog')
router.register(r'menus', MenuViewSet, basename='menu')

app_name = 'cms'

urlpatterns = [
    path('', include(router.urls)),
]

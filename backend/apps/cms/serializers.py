"""
apps/cms/serializers.py — Сериализаторы для CMS API
"""

from rest_framework import serializers
from .models import Page, BlogPost, Menu, MenuItem


class PageSerializer(serializers.ModelSerializer):
    """Сериализатор для статических страниц"""

    class Meta:
        model = Page
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'meta_title',
            'meta_description',
            'is_published',
            'created',
            'updated',
        ]


class BlogPostListSerializer(serializers.ModelSerializer):
    """Облегчённый сериализатор для списка постов блога"""

    author_name = serializers.CharField(
        source='author.get_full_name', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'featured_image',
            'author_name',
            'published_at',
            'created',
        ]


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор для детальной страницы поста"""

    author_name = serializers.CharField(
        source='author.get_full_name', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id',
            'title',
            'slug',
            'content',
            'excerpt',
            'featured_image',
            'author',
            'author_name',
            'meta_title',
            'meta_description',
            'is_published',
            'published_at',
            'created',
            'updated',
        ]


class MenuItemSerializer(serializers.ModelSerializer):
    """Сериализатор для пункта меню"""

    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id',
            'title',
            'url',
            'order',
            'is_active',
            'children',
        ]

    def get_children(self, obj):
        """Получаем подпункты меню"""
        children = obj.children.filter(is_active=True).order_by('order')
        return MenuItemSerializer(children, many=True).data


class MenuSerializer(serializers.ModelSerializer):
    """Сериализатор для меню"""

    items = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            'id',
            'name',
            'location',
            'items',
        ]

    def get_items(self, obj):
        """Получаем только корневые пункты меню (без parent)"""
        root_items = obj.items.filter(
            parent=None, is_active=True).order_by('order')
        return MenuItemSerializer(root_items, many=True).data

"""
apps/cms/admin.py — Регистрация моделей CMS в Django Admin
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Page, BlogPost, Menu, MenuItem


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Админка для статических страниц"""

    list_display = ['title', 'store', 'slug', 'is_published', 'created']
    list_filter = ['is_published', 'store', 'created']
    search_fields = ['title', 'slug', 'content']
    ordering = ['-created']

    fieldsets = (
        (_('Basic Info'), {
            'fields': ('store', 'title', 'slug', 'content')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description')
        }),
        (_('Status'), {
            'fields': ('is_published',)
        }),
    )

    prepopulated_fields = {'slug': ('title',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Админка для блога"""

    list_display = ['title', 'store', 'author',
                    'is_published', 'published_at', 'created']
    list_filter = ['is_published', 'store', 'published_at']
    search_fields = ['title', 'slug', 'content']
    ordering = ['-published_at']

    fieldsets = (
        (_('Basic Info'), {
            'fields': ('store', 'title', 'slug', 'author', 'content', 'excerpt')
        }),
        (_('Media'), {
            'fields': ('featured_image',)
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description')
        }),
        (_('Publishing'), {
            'fields': ('is_published', 'published_at')
        }),
    )

    prepopulated_fields = {'slug': ('title',)}


class MenuItemInline(admin.TabularInline):
    """Инлайн для пунктов меню"""
    model = MenuItem
    extra = 1


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    """Админка для меню"""

    list_display = ['name', 'store', 'location', 'is_active']
    list_filter = ['is_active', 'location', 'store']
    search_fields = ['name']

    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Админка для пунктов меню"""

    list_display = ['title', 'menu', 'parent', 'order', 'is_active']
    list_filter = ['is_active', 'menu']
    search_fields = ['title', 'url']
    ordering = ['menu', 'order']

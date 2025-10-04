"""
apps/cms/models.py — Модели CMS для Vendaro

Статические страницы, блог, меню навигации.
Каждый магазин может иметь свои страницы и блог.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel, TimeStampedModel

# ============================================
# СТАТИЧЕСКАЯ СТРАНИЦА
# ============================================


class Page(BaseModel):
    """
    Статическая страница сайта.

    Примеры:
    - О нас
    - Контакты
    - Условия использования
    - Политика конфиденциальности
    - Доставка и оплата
    """

    title = models.CharField(
        _('title'),
        max_length=200,
    )

    # content — контент страницы (HTML)
    # Может содержать HTML разметку
    content = models.TextField(
        _('content'),
    )

    # is_published — опубликована ли страница
    # False = черновик, не показывается на сайте
    is_published = models.BooleanField(
        _('published'),
        default=True,
        db_index=True,
    )

    # published_at — дата публикации
    # Можно запланировать публикацию на будущее
    published_at = models.DateTimeField(
        _('published at'),
        null=True,
        blank=True,
    )

    # SEO
    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)

    # order — порядок в меню
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
    )

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ['order', 'title']

        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published']),
            models.Index(fields=['store', 'is_published']),
        ]

    def __str__(self):
        return self.title

    def get_slug_source(self):
        """Slug генерируется из заголовка"""
        return self.title


# ============================================
# БЛОГ
# ============================================

class BlogPost(BaseModel):
    """
    Пост в блоге.

    Примеры для DeepReef:
    - "10 лучших мест для дайвинга в России"
    - "Как выбрать маску для подводной охоты"
    - "История фридайвинга"
    """

    title = models.CharField(
        _('title'),
        max_length=200,
    )

    # excerpt — краткое описание (анонс)
    # Показывается в списке постов
    excerpt = models.TextField(
        _('excerpt'),
        max_length=500,
        help_text=_('Short description for blog list'),
    )

    # content — полный текст поста (HTML)
    content = models.TextField(
        _('content'),
    )

    # featured_image — главное изображение поста
    featured_image = models.ImageField(
        _('featured image'),
        upload_to='blog/%Y/%m/',
        blank=True,
        null=True,
    )

    # author — автор поста
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name='blog_posts',
        null=True,
        blank=True,
        verbose_name=_('author'),
    )

    # category — категория поста (опционально)
    # Можно создать отдельную модель BlogCategory, но для простоты используем строку
    category = models.CharField(
        _('category'),
        max_length=100,
        blank=True,
        help_text=_('Blog category (e.g. News, Guides, Reviews)'),
    )

    # tags — теги через запятую
    # Пример: "дайвинг, маска, снаряжение"
    tags = models.CharField(
        _('tags'),
        max_length=255,
        blank=True,
        help_text=_('Comma-separated tags'),
    )

    # is_published — опубликован ли пост
    is_published = models.BooleanField(
        _('published'),
        default=False,
        db_index=True,
    )

    # published_at — дата публикации
    published_at = models.DateTimeField(
        _('published at'),
        null=True,
        blank=True,
    )

    # views_count — количество просмотров
    views_count = models.PositiveIntegerField(
        _('views count'),
        default=0,
    )

    # SEO
    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)

    class Meta:
        verbose_name = _('blog post')
        verbose_name_plural = _('blog posts')
        ordering = ['-published_at', '-created']

        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published', '-published_at']),
            models.Index(fields=['store', 'is_published']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

    def get_slug_source(self):
        """Slug генерируется из заголовка"""
        return self.title

    def get_tags_list(self):
        """
        Возвращает список тегов.

        Пример:
        tags = "дайвинг, маска, снаряжение"
        return ['дайвинг', 'маска', 'снаряжение']
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]


# ============================================
# МЕНЮ НАВИГАЦИИ
# ============================================

class Menu(TimeStampedModel):
    """
    Меню навигации сайта.

    Примеры:
    - Главное меню (header)
    - Меню в подвале (footer)
    - Боковое меню

    Каждый магазин может иметь несколько меню.
    """

    # Расположение меню
    LOCATION_CHOICES = [
        ('header', _('Header')),                # Шапка сайта
        ('footer', _('Footer')),                # Подвал
        ('sidebar', _('Sidebar')),              # Боковая панель
        ('mobile', _('Mobile')),                # Мобильное меню
    ]

    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='menus',
        verbose_name=_('store'),
    )

    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Internal name (e.g. Main Menu, Footer Menu)'),
    )

    # location — где отображается меню
    location = models.CharField(
        _('location'),
        max_length=20,
        choices=LOCATION_CHOICES,
        default='header',
    )

    # is_active — активно ли меню
    is_active = models.BooleanField(
        _('active'),
        default=True,
    )

    class Meta:
        verbose_name = _('menu')
        verbose_name_plural = _('menus')
        ordering = ['location', 'name']

        # unique_together — одно меню на одно расположение в магазине
        unique_together = ['store', 'location']

    def __str__(self):
        return f"{self.name} ({self.get_location_display()})"


# ============================================
# ПУНКТ МЕНЮ
# ============================================

class MenuItem(models.Model):
    """
    Пункт меню навигации.

    Примеры:
    - Главная
    - Каталог
    - О нас
    - Контакты
    - Блог

    Поддерживает вложенность (подменю).
    """

    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('menu'),
    )

    # parent — родительский пункт (для подменю)
    # null=True — может быть корневым пунктом
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
        verbose_name=_('parent item'),
    )

    title = models.CharField(
        _('title'),
        max_length=100,
        help_text=_('Menu item title'),
    )

    # url — ссылка
    # Может быть:
    # - Внутренняя: /products/ или /about/
    # - Внешняя: https://instagram.com/deepreef
    url = models.CharField(
        _('URL'),
        max_length=255,
        help_text=_('URL or path (e.g. /products/ or https://...)'),
    )

    # open_in_new_tab — открывать в новой вкладке
    # True для внешних ссылок
    open_in_new_tab = models.BooleanField(
        _('open in new tab'),
        default=False,
    )

    # order — порядок отображения
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
    )

    # is_active — активен ли пункт меню
    is_active = models.BooleanField(
        _('active'),
        default=True,
    )

    class Meta:
        verbose_name = _('menu item')
        verbose_name_plural = _('menu items')
        ordering = ['order']

    def __str__(self):
        return self.title


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# Создание статической страницы:
# page = Page.objects.create(
#     store=deepreef_store,
#     title='О компании DeepReef',
#     slug='about',
#     content='<h1>О нас</h1><p>Мы продаем снаряжение...</p>',
#     is_published=True,
# )

# Создание поста в блоге:
# post = BlogPost.objects.create(
#     store=deepreef_store,
#     title='10 лучших мест для дайвинга в России',
#     excerpt='Откройте для себя самые живописные места...',
#     content='<p>Полный текст статьи...</p>',
#     author=user,
#     category='Гайды',
#     tags='дайвинг, путешествия, россия',
#     is_published=True,
# )

# Создание меню:
# header_menu = Menu.objects.create(
#     store=deepreef_store,
#     name='Главное меню',
#     location='header',
# )
#
# # Добавление пунктов меню:
# MenuItem.objects.create(
#     menu=header_menu,
#     title='Главная',
#     url='/',
#     order=1,
# )
# MenuItem.objects.create(
#     menu=header_menu,
#     title='Каталог',
#     url='/products/',
#     order=2,
# )
# MenuItem.objects.create(
#     menu=header_menu,
#     title='О нас',
#     url='/about/',
#     order=3,
# )

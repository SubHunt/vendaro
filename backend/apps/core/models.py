"""
apps/core/models.py — Базовые (абстрактные) модели для всех приложений Vendaro

Эти модели не создают таблицы в БД, а служат шаблонами для других моделей.
Все наши модели (Product, Order, и т.д.) будут наследоваться от этих базовых моделей.

Принцип DRY (Don't Repeat Yourself) — не повторяйся.
Вместо того чтобы в каждой модели писать поля created, updated, store —
мы пишем их один раз здесь, а потом просто наследуемся.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
# gettext_lazy — функция для перевода текста на другие языки
# _() — короткая форма записи gettext_lazy()

# ============================================
# БАЗОВАЯ МОДЕЛЬ С TIMESTAMPS
# ============================================


class TimeStampedModel(models.Model):
    """
    Абстрактная модель с полями created и updated.

    Почти у всех моделей есть эти поля:
    - created — когда запись создана
    - updated — когда последний раз изменена

    Наследуя от этой модели, автоматически получаем эти поля.

    Пример использования:
    class Product(TimeStampedModel):
        name = models.CharField(max_length=200)
        # created и updated добавятся автоматически!
    """

    # created — дата и время создания записи
    #
    # DateTimeField — поле для хранения даты и времени
    # auto_now_add=True — автоматически устанавливается при создании записи
    #                     и больше НИКОГДА не меняется
    # editable=False — нельзя изменить вручную в админке
    # db_index=True — создаёт индекс в БД для быстрой сортировки по дате
    created = models.DateTimeField(
        _('created'),
        auto_now_add=True,
        editable=False,
        db_index=True,
    )

    # updated — дата и время последнего изменения
    #
    # auto_now=True — автоматически обновляется при каждом сохранении (save())
    # Каждый раз когда вы меняете запись, updated обновляется
    updated = models.DateTimeField(
        _('updated'),
        auto_now=True,
        editable=False,
    )

    class Meta:
        # abstract=True — это абстрактная модель
        # Таблица в БД НЕ создаётся
        # Используется только как родительский класс
        abstract = True

        # ordering — порядок по умолчанию при SELECT * FROM table
        # ['-created'] — сортировка по дате создания, новые первыми
        # '-' означает DESC (descending, по убыванию)
        ordering = ['-created']

    def __str__(self):
        """
        Строковое представление модели.
        Используется в Django Admin и логах.
        """
        return f"{self.__class__.__name__} {self.pk} (created: {self.created})"


# ============================================
# МОДЕЛЬ С SOFT DELETE (мягкое удаление)
# ============================================

class SoftDeleteModel(TimeStampedModel):
    """
    Абстрактная модель с мягким удалением (soft delete).

    Мягкое удаление — запись не удаляется из БД, а помечается как удалённая.

    Зачем это нужно:
    1. Можно восстановить случайно удалённые данные
    2. Сохраняется история (для отчётов, аналитики)
    3. Связанные записи не ломаются

    Пример:
    Товар удалили, но он есть в старых заказах.
    Если физически удалить товар — заказы сломаются (FK constraint error).
    С soft delete: товар скрыт, но данные в заказах остались.
    """

    # is_deleted — флаг "удалён ли объект"
    #
    # BooleanField — поле типа True/False
    # default=False — по умолчанию объект НЕ удалён
    # db_index=True — индекс для быстрой фильтрации
    #                 WHERE is_deleted = False будет быстрым
    is_deleted = models.BooleanField(
        _('is deleted'),
        default=False,
        db_index=True,
    )

    # deleted_at — когда объект был удалён
    #
    # null=True — может быть NULL в БД
    # blank=True — может быть пустым в формах Django Admin
    # Если is_deleted=False, то deleted_at=None
    deleted_at = models.DateTimeField(
        _('deleted at'),
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        Переопределяем метод delete().
        Вместо удаления из БД — помечаем как удалённый.

        Использование:
        product.delete()  
        # Не удаляет физически, а устанавливает:
        # is_deleted=True
        # deleted_at=сейчас
        """
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        # update_fields — обновить только эти поля (оптимизация)
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self):
        """
        Настоящее удаление из БД (физическое удаление).

        Использование:
        product.hard_delete()  # Удалит запись НАВСЕГДА
        """
        # super() — вызов метода родительского класса
        # Вызываем оригинальный delete() из models.Model
        super().delete()

    def restore(self):
        """
        Восстановление удалённого объекта.

        Использование:
        product.restore()  # is_deleted=False, deleted_at=None
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


# ============================================
# КАСТОМНЫЙ МЕНЕДЖЕР ДЛЯ SOFT DELETE
# ============================================

class SoftDeleteManager(models.Manager):
    """
    Кастомный менеджер для работы с SoftDeleteModel.

    Менеджер — это интерфейс для запросов к БД.
    Product.objects — это менеджер.
    Product.objects.all() — запрос через менеджер.

    По умолчанию Product.objects.all() возвращает ВСЕ записи (включая удалённые).
    С этим менеджером — возвращает только НЕ удалённые.
    """

    def get_queryset(self):
        """
        Переопределяем базовый queryset.
        Фильтруем только не удалённые записи.

        Теперь:
        Product.objects.all() вернёт только is_deleted=False
        """
        return super().get_queryset().filter(is_deleted=False)

    def deleted(self):
        """
        Получить только удалённые записи.

        Использование:
        Product.objects.deleted()  # Вернёт только удалённые товары
        """
        return super().get_queryset().filter(is_deleted=True)

    def with_deleted(self):
        """
        Получить все записи (включая удалённые).

        Использование:
        Product.objects.with_deleted()  # Вернёт ВСЕ товары
        """
        return super().get_queryset()


# ============================================
# МОДЕЛЬ С SLUG (URL-friendly строка)
# ============================================

class SlugModel(models.Model):
    """
    Абстрактная модель с полем slug.

    Slug — URL-friendly строка для использования в адресах.
    Пример: "Маска для дайвинга Cressi" → "maska-dlya-dayvinga-cressi"

    URL товара: /products/maska-dlya-dayvinga-cressi/
    Вместо: /products/123/ (по ID)

    Преимущества slug:
    1. SEO — поисковики любят человекочитаемые URL
    2. Понятно пользователю что за страница
    3. Можно менять название без изменения URL
    """

    # slug — URL-friendly строка
    #
    # SlugField — специальное поле для slug
    # Разрешает только: a-z, 0-9, дефисы, подчёркивания
    # max_length=255 — максимальная длина
    # unique=True — должен быть уникальным (нельзя два товара с одинаковым slug)
    # blank=True — может быть пустым (заполнится автоматически)
    # db_index=True — индекс для быстрого поиска по slug
    slug = models.SlugField(
        _('slug'),
        max_length=255,
        unique=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Переопределяем метод save().
        Автоматически генерируем slug из названия, если slug пустой.
        """
        from django.utils.text import slugify

        # Если slug пустой — генерируем
        if not self.slug:
            # get_slug_source() — метод который вернёт строку для slug
            # Должен быть реализован в дочернем классе
            slug_source = self.get_slug_source()

            if slug_source:
                # slugify() — преобразует строку в slug
                # "Маска Cressi" → "maska-cressi"
                # allow_unicode=True — разрешить русские буквы (транслитерация)
                self.slug = slugify(slug_source, allow_unicode=True)

                # Проверка уникальности slug
                # Если такой slug уже есть, добавляем номер: "maska-cressi-2"
                original_slug = self.slug
                counter = 1

                # Проверяем существует ли объект с таким slug
                # self.__class__ — это класс модели (Product, Category, и т.д.)
                while self.__class__.objects.filter(slug=self.slug).exists():
                    self.slug = f"{original_slug}-{counter}"
                    counter += 1

        # Вызываем оригинальный save()
        super().save(*args, **kwargs)

    def get_slug_source(self):
        """
        Метод для получения строки, из которой создаётся slug.
        Должен быть переопределён в дочерних классах.

        Пример в Product:
        def get_slug_source(self):
            return self.name
        """
        raise NotImplementedError(
            'Subclasses must implement get_slug_source()')


# ============================================
# МОДЕЛЬ ДЛЯ MULTI-TENANT
# ============================================

class TenantModel(TimeStampedModel):
    """
    Абстрактная модель для multi-tenant системы.

    Все записи привязаны к магазину (Store).
    Товар, заказ, категория — всё принадлежит конкретному магазину.

    Это основа Vendaro CMS — один код, много магазинов.
    """

    # store — связь с магазином (ForeignKey)
    #
    # ForeignKey — связь "многие к одному"
    # Много товаров → один магазин
    #
    # 'stores.Store' — модель Store из приложения stores
    # on_delete=models.CASCADE — если магазин удалён, удалить все его товары
    # related_name='+' — не создавать обратную связь
    #                    (переопределяется в дочерних классах)
    # db_index=True — индекс для быстрой фильтрации по магазину
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=_('store'),
        db_index=True,
    )

    class Meta:
        abstract = True


# ============================================
# ИТОГОВАЯ КОМБИНИРОВАННАЯ МОДЕЛЬ
# ============================================

class BaseModel(TenantModel, SoftDeleteModel, SlugModel):
    """
    Универсальная базовая модель со всеми возможностями:
    - Привязка к магазину (TenantModel)
    - Timestamps (created, updated) 
    - Soft delete (is_deleted)
    - Slug для URL

    Большинство моделей Vendaro будут наследоваться от этой.

    Пример использования:
    class Product(BaseModel):
        name = models.CharField(max_length=200)
        price = models.DecimalField(max_digits=10, decimal_places=2)

        class Meta:
            verbose_name = 'Товар'
            verbose_name_plural = 'Товары'

        def get_slug_source(self):
            return self.name

    Product автоматически получит:
    - store (связь с магазином)
    - created, updated (даты)
    - is_deleted, deleted_at (мягкое удаление)
    - slug (для URL)
    """

    # Используем кастомный менеджер для фильтрации удалённых записей
    objects = SoftDeleteManager()

    class Meta:
        abstract = True


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# В других приложениях импортируем и используем:
#
# from apps.core.models import BaseModel
#
# class Product(BaseModel):
#     name = models.CharField(max_length=200)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#
#     class Meta:
#         verbose_name = 'Товар'
#         verbose_name_plural = 'Товары'
#
#     def get_slug_source(self):
#         return self.name
#
# Теперь Product имеет:
# - product.store (магазин)
# - product.created (дата создания)
# - product.updated (дата изменения)
# - product.is_deleted (флаг удаления)
# - product.slug (URL slug)
# - Product.objects.all() (только не удалённые)
# - Product.objects.deleted() (только удалённые)
# - product.delete() (мягкое удаление)
# - product.hard_delete() (физическое удаление)
# - product.restore() (восстановление)

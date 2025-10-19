"""
apps/products/models.py — Модели товаров для каталога Vendaro

Включает:
- Category — категории товаров (с вложенностью)
- Product — товары с розничными и оптовыми ценами
- Size — справочник размеров (одежда, обувь, диапазоны)
- ProductVariant — варианты товара (товар + размер + stock)
- ProductImage — фотографии товаров
- ProductReview — отзывы покупателей
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel, TimeStampedModel
from decimal import Decimal

# ============================================
# КАТЕГОРИЯ ТОВАРОВ
# ============================================


class Category(BaseModel):
    """
    Категория товаров с поддержкой вложенности (дерево категорий).
    """

    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent category'),
    )
    image = models.ImageField(
        _('image'),
        upload_to='categories/%Y/%m/',
        blank=True,
        null=True,
    )
    order = models.PositiveIntegerField(_('display order'), default=0)
    is_active = models.BooleanField(_('active'), default=True)
    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['store', 'parent']),
        ]

    def __str__(self):
        return self.name

    def get_slug_source(self):
        return self.name

    def get_full_path(self):
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)


# ============================================
# СПРАВОЧНИК РАЗМЕРОВ
# ============================================

class Size(models.Model):
    """
    Универсальный справочник размеров.

    Типы размеров:
    - clothing: XXS, XS, S, M, L, XL, XXL, XXXL, XXXXL
    - footwear: 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46
    - range: 36-37, 38-39, 40-41, 42-43
    """

    SIZE_TYPES = [
        ('clothing', _('Одежда (XXS-XXXXL)')),
        ('footwear', _('Обувь (размеры)')),
        ('range', _('Диапазон размеров')),
    ]

    type = models.CharField(
        _('тип размера'),
        max_length=20,
        choices=SIZE_TYPES,
        help_text=_('Тип размерной сетки'),
    )

    value = models.CharField(
        _('значение'),
        max_length=20,
        help_text=_('Значение размера (XL, 42, 40-41)'),
    )

    order = models.PositiveIntegerField(
        _('порядок'),
        default=0,
        help_text=_('Порядок отображения (меньше = выше)'),
    )

    is_active = models.BooleanField(
        _('активен'),
        default=True,
    )

    class Meta:
        verbose_name = _('размер')
        verbose_name_plural = _('размеры')
        ordering = ['type', 'order', 'value']
        unique_together = ['type', 'value']
        indexes = [
            models.Index(fields=['type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"


# ============================================
# ТОВАР (PRODUCT)
# ============================================

class Product(BaseModel):
    """
    Товар с поддержкой розничных и оптовых цен.

    Может иметь варианты (размеры) через ProductVariant.
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name=_('category'),
    )

    name = models.CharField(_('name'), max_length=255, db_index=True)
    description = models.TextField(
        _('description'),
        help_text=_('Detailed product description'),
    )
    short_description = models.CharField(
        _('short description'),
        max_length=500,
        blank=True,
    )

    # ========================================
    # ЦЕНЫ
    # ========================================

    retail_price = models.DecimalField(
        _('retail price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Regular price for retail customers (B2C)'),
    )

    wholesale_price = models.DecimalField(
        _('wholesale price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Special price for wholesale customers (B2B, optional)'),
    )

    discount_price = models.DecimalField(
        _('discount price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Sale price (optional)'),
    )

    compare_at_price = models.DecimalField(
        _('compare at price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Original price to show discount'),
    )

    cost_price = models.DecimalField(
        _('cost price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Cost price for profit analysis (internal)'),
    )

    # ========================================
    # НАЛИЧИЕ И СКЛАД
    # ========================================

    stock = models.PositiveIntegerField(
        _('stock quantity'),
        default=0,
        help_text=_('Available quantity in stock (если нет вариантов)'),
    )

    available = models.BooleanField(
        _('available'), default=True, db_index=True)
    sku = models.CharField(
        _('SKU'),
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_('Stock Keeping Unit (article number)'),
    )
    barcode = models.CharField(_('barcode'), max_length=100, blank=True)
    track_stock = models.BooleanField(_('track stock'), default=True)

    # ========================================
    # ВАРИАНТЫ (РАЗМЕРЫ)
    # ========================================

    has_variants = models.BooleanField(
        _('имеет варианты'),
        default=False,
        help_text=_('Товар имеет варианты (размеры, цвета и т.д.)'),
    )

    # Связь many-to-many с размерами (через ProductVariant)
    # sizes = доступные размеры для этого товара
    sizes = models.ManyToManyField(
        Size,
        through='ProductVariant',
        related_name='products',
        verbose_name=_('размеры'),
        blank=True,
    )

    # ========================================
    # ХАРАКТЕРИСТИКИ
    # ========================================

    specifications = models.JSONField(
        _('specifications'),
        default=dict,
        blank=True,
        help_text=_('Product specifications as JSON'),
    )

    # ========================================
    # РЕЙТИНГ И СТАТИСТИКА
    # ========================================

    rating = models.DecimalField(
        _('rating'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    reviews_count = models.PositiveIntegerField(_('reviews count'), default=0)
    views_count = models.PositiveIntegerField(_('views'), default=0)
    sales_count = models.PositiveIntegerField(_('sales count'), default=0)

    # ========================================
    # SEO
    # ========================================

    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['available', '-created']),
            models.Index(fields=['-rating', '-reviews_count']),
            models.Index(fields=['store', 'category']),
            models.Index(fields=['has_variants']),
        ]

    def __str__(self):
        return self.name

    def get_slug_source(self):
        return self.name

    def get_retail_price(self):
        """Возвращает актуальную розничную цену"""
        if self.discount_price:
            return self.discount_price
        return self.retail_price

    def get_wholesale_price(self):
        """Возвращает оптовую цену для B2B клиентов"""
        if not self.store.enable_wholesale:
            return self.get_retail_price()

        return self.store.calculate_wholesale_price(
            retail_price=self.get_retail_price(),
            product_wholesale_price=self.wholesale_price
        )

    def get_price_for_user(self, user=None):
        """Возвращает цену товара для конкретного пользователя"""
        if user and user.is_authenticated and user.can_see_wholesale_prices():
            return (self.get_wholesale_price(), True)
        return (self.get_retail_price(), False)

    def has_discount(self):
        """Проверка наличия скидки"""
        return self.discount_price is not None and self.discount_price < self.retail_price

    def is_in_stock(self):
        """
        Проверка наличия на складе.

        Если товар имеет варианты - проверяем наличие хотя бы одного варианта.
        Если нет вариантов - проверяем stock товара.
        """
        if self.has_variants:
            return self.variants.filter(stock__gt=0, is_active=True).exists()

        if not self.track_stock:
            return True
        return self.stock > 0

    def get_total_stock(self):
        """
        Возвращает общее количество товара на складе.

        Если товар имеет варианты - суммируем stock всех вариантов.
        Если нет - возвращаем stock товара.
        """
        if self.has_variants:
            return sum(v.stock for v in self.variants.filter(is_active=True))
        return self.stock

    def get_available_sizes(self):
        """Возвращает список доступных размеров (с наличием на складе)"""
        if not self.has_variants:
            return []

        return self.variants.filter(
            stock__gt=0,
            is_active=True
        ).select_related('size').order_by('size__order')


# ============================================
# ВАРИАНТ ТОВАРА (PRODUCT VARIANT)
# ============================================

class ProductVariant(TimeStampedModel):
    """
    Вариант товара (торговое предложение).

    Например:
    - Гидрокостюм 5мм: размер M, stock: 5, цена: 15000₽
    - Гидрокостюм 5мм: размер L, stock: 3, цена: 15000₽
    - Ласты: размер 42-43, stock: 10, цена: 8000₽
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('товар'),
    )

    size = models.ForeignKey(
        Size,
        on_delete=models.PROTECT,
        related_name='variants',
        verbose_name=_('размер'),
    )

    # ========================================
    # СКЛАД
    # ========================================

    stock = models.PositiveIntegerField(
        _('остаток'),
        default=0,
        help_text=_('Количество на складе для этого размера'),
    )

    # ========================================
    # ЦЕНА (опционально)
    # ========================================

    price_override = models.DecimalField(
        _('переопределённая цена'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Если цена отличается от базовой цены товара'),
    )

    wholesale_price_override = models.DecimalField(
        _('переопределённая оптовая цена'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Оптовая цена для этого варианта'),
    )

    # ========================================
    # АРТИКУЛ
    # ========================================

    sku = models.CharField(
        _('артикул'),
        max_length=100,
        blank=True,
        help_text=_('Артикул варианта (например, WETSUIT-5MM-M)'),
    )

    barcode = models.CharField(
        _('штрих-код'),
        max_length=100,
        blank=True,
    )

    # ========================================
    # СТАТУС
    # ========================================

    is_active = models.BooleanField(
        _('активен'),
        default=True,
        help_text=_('Доступен ли вариант для заказа'),
    )

    # ========================================
    # ВЫЧИСЛЯЕМЫЕ ПОЛЯ
    # ========================================

    sales_count = models.PositiveIntegerField(
        _('продано'),
        default=0,
    )

    class Meta:
        verbose_name = _('вариант товара')
        verbose_name_plural = _('варианты товаров')
        ordering = ['product', 'size__order']
        unique_together = ['product', 'size']
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['stock']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.size.value}"

    def get_retail_price(self):
        """
        Возвращает розничную цену варианта.

        Если есть price_override - используем его, иначе цену товара.
        """
        if self.price_override:
            return self.price_override
        return self.product.get_retail_price()

    def get_wholesale_price(self):
        """Возвращает оптовую цену варианта"""
        if self.wholesale_price_override:
            return self.wholesale_price_override
        return self.product.get_wholesale_price()

    def get_price_for_user(self, user=None):
        """Возвращает цену для конкретного пользователя"""
        if user and user.is_authenticated and user.can_see_wholesale_prices():
            return (self.get_wholesale_price(), True)
        return (self.get_retail_price(), False)

    def is_in_stock(self):
        """Проверка наличия на складе"""
        return self.stock > 0 and self.is_active


# ============================================
# ИЗОБРАЖЕНИЕ ТОВАРА
# ============================================

class ProductImage(models.Model):
    """Фотография товара"""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product'),
    )
    image = models.ImageField(_('image'), upload_to='products/%Y/%m/')
    is_main = models.BooleanField(_('main image'), default=False)
    order = models.PositiveIntegerField(_('order'), default=0)
    alt_text = models.CharField(_('alt text'), max_length=200, blank=True)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.name}"


# ============================================
# ОТЗЫВ О ТОВАРЕ
# ============================================

class ProductReview(TimeStampedModel):
    """Отзыв покупателя о товаре"""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('product'),
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('user'),
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=[(i, i) for i in range(1, 6)],
        help_text=_('Rating from 1 to 5 stars'),
    )
    comment = models.TextField(_('comment'), help_text=_('Your review'))
    is_verified = models.BooleanField(_('verified purchase'), default=False)
    is_approved = models.BooleanField(_('approved'), default=True)

    class Meta:
        verbose_name = _('product review')
        verbose_name_plural = _('product reviews')
        ordering = ['-created']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.get_short_name()} - {self.product.name} ({self.rating}★)"

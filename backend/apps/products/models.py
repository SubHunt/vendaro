"""
apps/products/models.py — Модели товаров для каталога Vendaro

Включает:
- Category — категории товаров (с вложенностью)
- Product — товары с розничными и оптовыми ценами
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

    Примеры для DeepReef:
    - Дайвинг
      - Маски
      - Ласты
      - Гидрокостюмы
    - Подводная охота
      - Ружья
      - Аксессуары
    - Фридайвинг
    - Снорклинг
    """

    name = models.CharField(
        _('name'),
        max_length=200,
    )

    description = models.TextField(
        _('description'),
        blank=True,
    )

    # parent — родительская категория для вложенности
    # null=True — может быть корневой категорией (без родителя)
    # related_name='children' — parent.children.all() вернёт подкатегории
    #
    # Пример:
    # diving = Category(name='Дайвинг', parent=None)  # Корневая
    # masks = Category(name='Маски', parent=diving)   # Подкатегория
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent category'),
    )

    # image — изображение категории
    # Используется для баннеров, карточек категорий
    image = models.ImageField(
        _('image'),
        upload_to='categories/%Y/%m/',
        blank=True,
        null=True,
    )

    # order — порядок отображения
    # Чем меньше число, тем выше в списке
    order = models.PositiveIntegerField(
        _('display order'),
        default=0,
    )

    # is_active — активна ли категория
    # False = категория скрыта от покупателей
    is_active = models.BooleanField(
        _('active'),
        default=True,
    )

    # SEO поля
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
        """Slug генерируется из названия категории"""
        return self.name

    def get_full_path(self):
        """
        Возвращает полный путь категории.

        Пример: "Дайвинг > Маски > Полнолицевые"
        """
        path = [self.name]
        parent = self.parent

        while parent:
            path.insert(0, parent.name)
            parent = parent.parent

        return ' > '.join(path)


# ============================================
# ТОВАР (PRODUCT)
# ============================================

class Product(BaseModel):
    """
    Товар с поддержкой розничных и оптовых цен.

    Розничная цена (retail_price) — для обычных покупателей (B2C)
    Оптовая цена (wholesale_price) — для оптовиков (B2B)

    Если wholesale_price не указана, применяется скидка магазина.
    """

    # ========================================
    # ОСНОВНАЯ ИНФОРМАЦИЯ
    # ========================================

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name=_('category'),
    )

    name = models.CharField(
        _('name'),
        max_length=255,
        db_index=True,
    )

    description = models.TextField(
        _('description'),
        help_text=_('Detailed product description'),
    )

    # short_description — краткое описание
    # Показывается в карточке товара, списках
    short_description = models.CharField(
        _('short description'),
        max_length=500,
        blank=True,
    )

    # ========================================
    # ЦЕНЫ (РОЗНИЧНАЯ И ОПТОВАЯ)
    # ========================================

    # retail_price — РОЗНИЧНАЯ цена (для B2C)
    # Обычные покупатели видят эту цену
    retail_price = models.DecimalField(
        _('retail price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Regular price for retail customers (B2C)'),
    )

    # wholesale_price — ОПТОВАЯ цена (для B2B)
    # null=True — может отсутствовать
    # Если не указана, используется скидка магазина (wholesale_discount_percent)
    wholesale_price = models.DecimalField(
        _('wholesale price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Special price for wholesale customers (B2B, optional)'),
    )

    # discount_price — цена со скидкой (акции)
    # Применяется к РОЗНИЧНОЙ цене
    # Пример: было 10000₽, стало 8000₽ (акция)
    discount_price = models.DecimalField(
        _('discount price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Sale price (optional)'),
    )

    # compare_at_price — зачёркнутая цена
    # Для визуализации скидки: ~~10000₽~~ 8000₽
    compare_at_price = models.DecimalField(
        _('compare at price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Original price to show discount'),
    )

    # cost_price — себестоимость
    # Для расчёта рентабельности (не показывается клиентам!)
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

    # stock — количество на складе
    stock = models.PositiveIntegerField(
        _('stock quantity'),
        default=0,
        help_text=_('Available quantity in stock'),
    )

    # available — доступен ли товар для заказа
    # False = товар скрыт (снят с продажи, закончился)
    available = models.BooleanField(
        _('available'),
        default=True,
        db_index=True,
    )

    # sku — артикул товара (Stock Keeping Unit)
    # Уникальный идентификатор для учёта
    sku = models.CharField(
        _('SKU'),
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_('Stock Keeping Unit (article number)'),
    )

    # barcode — штрих-код
    barcode = models.CharField(
        _('barcode'),
        max_length=100,
        blank=True,
    )

    # track_stock — отслеживать остатки
    # True = уменьшать stock при продаже
    # False = бесконечный товар (услуги, цифровые товары)
    track_stock = models.BooleanField(
        _('track stock'),
        default=True,
    )

    # ========================================
    # ХАРАКТЕРИСТИКИ (JSON)
    # ========================================

    # specifications — технические характеристики
    # JSONField для гибкости (разные товары = разные характеристики)
    #
    # Пример для маски (DeepReef):
    # {
    #   "material": "Силикон",
    #   "color": "Черный",
    #   "size": "Взрослый",
    #   "lens_type": "Закаленное стекло",
    #   "volume": "120 мл"
    # }
    specifications = models.JSONField(
        _('specifications'),
        default=dict,
        blank=True,
        help_text=_('Product specifications as JSON'),
    )

    # ========================================
    # РЕЙТИНГ И ОТЗЫВЫ
    # ========================================

    # rating — средний рейтинг (0.00 - 5.00)
    # Вычисляется автоматически из отзывов
    rating = models.DecimalField(
        _('rating'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    # reviews_count — количество отзывов
    # Обновляется автоматически через signals
    reviews_count = models.PositiveIntegerField(
        _('reviews count'),
        default=0,
    )

    # ========================================
    # СТАТИСТИКА
    # ========================================

    # views_count — количество просмотров
    views_count = models.PositiveIntegerField(
        _('views'),
        default=0,
        help_text=_('Number of times product was viewed'),
    )

    # sales_count — количество продаж
    # Обновляется при оформлении заказа
    sales_count = models.PositiveIntegerField(
        _('sales count'),
        default=0,
    )

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
        ]

    def __str__(self):
        return self.name

    def get_slug_source(self):
        """Slug генерируется из названия товара"""
        return self.name

    def get_retail_price(self):
        """
        Возвращает актуальную розничную цену.

        Логика:
        - Если есть discount_price — возвращаем его (акция)
        - Иначе возвращаем retail_price

        Возвращает: Decimal
        """
        if self.discount_price:
            return self.discount_price
        return self.retail_price

    def get_wholesale_price(self):
        """
        Возвращает оптовую цену для B2B клиентов.

        Логика:
        - Если есть индивидуальная wholesale_price — используем её
        - Иначе применяем скидку магазина
        - Если магазин не разрешает опт — розничная цена

        Возвращает: Decimal
        """
        if not self.store.enable_wholesale:
            return self.get_retail_price()

        return self.store.calculate_wholesale_price(
            retail_price=self.get_retail_price(),
            product_wholesale_price=self.wholesale_price
        )

    def get_price_for_user(self, user=None):
        """
        Возвращает цену товара для конкретного пользователя.

        Параметры:
        - user: объект User (или None для анонимного)

        Возвращает:
        - tuple: (price, is_wholesale)
          price: Decimal — цена
          is_wholesale: bool — оптовая ли цена

        Примеры:
        # Анонимный пользователь
        price, is_wholesale = product.get_price_for_user()
        # (10000, False) — розничная цена

        # Оптовик
        price, is_wholesale = product.get_price_for_user(wholesale_user)
        # (8500, True) — оптовая цена
        """
        if user and user.is_authenticated and user.can_see_wholesale_prices():
            return (self.get_wholesale_price(), True)

        return (self.get_retail_price(), False)

    def has_discount(self):
        """Проверка наличия скидки"""
        return self.discount_price is not None and self.discount_price < self.retail_price

    def is_in_stock(self):
        """Проверка наличия на складе"""
        if not self.track_stock:
            return True
        return self.stock > 0


# ============================================
# ИЗОБРАЖЕНИЕ ТОВАРА
# ============================================

class ProductImage(models.Model):
    """
    Фотография товара.

    Один товар может иметь несколько фотографий.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product'),
    )

    image = models.ImageField(
        _('image'),
        upload_to='products/%Y/%m/',
    )

    # is_main — главное фото
    # Показывается первым в карточке товара
    is_main = models.BooleanField(
        _('main image'),
        default=False,
    )

    # order — порядок отображения
    order = models.PositiveIntegerField(
        _('order'),
        default=0,
    )

    # alt_text — альтернативный текст (для SEO и доступности)
    alt_text = models.CharField(
        _('alt text'),
        max_length=200,
        blank=True,
    )

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
    """
    Отзыв покупателя о товаре.

    Один пользователь может оставить один отзыв на товар.
    """

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

    # rating — оценка (1-5 звёзд)
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=[(i, i) for i in range(1, 6)],
        help_text=_('Rating from 1 to 5 stars'),
    )

    # comment — текст отзыва
    comment = models.TextField(
        _('comment'),
        help_text=_('Your review'),
    )

    # is_verified — проверенный отзыв
    # True = покупатель действительно купил этот товар
    is_verified = models.BooleanField(
        _('verified purchase'),
        default=False,
    )

    # is_approved — одобрен модератором
    # False = отзыв на модерации, не показывается
    is_approved = models.BooleanField(
        _('approved'),
        default=True,
    )

    class Meta:
        verbose_name = _('product review')
        verbose_name_plural = _('product reviews')
        ordering = ['-created']

        # unique_together — один пользователь = один отзыв на товар
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.get_short_name()} - {self.product.name} ({self.rating}★)"


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# Создание категории:
# diving = Category.objects.create(
#     store=deepreef_store,
#     name='Дайвинг',
#     slug='diving',
# )
# masks = Category.objects.create(
#     store=deepreef_store,
#     name='Маски',
#     parent=diving,
# )

# Создание товара:
# product = Product.objects.create(
#     store=deepreef_store,
#     category=masks,
#     name='Маска Cressi Big Eyes Evolution',
#     retail_price=Decimal('8900'),
#     wholesale_price=Decimal('7500'),  # Для B2B
#     stock=50,
#     specifications={
#         'material': 'Силикон',
#         'color': 'Черный',
#         'lens': 'Закаленное стекло'
#     }
# )

# Получение цены для пользователя:
# price, is_wholesale = product.get_price_for_user(user)
# if is_wholesale:
#     print(f"Оптовая цена: {price}₽")
# else:
#     print(f"Розничная цена: {price}₽")

# Добавление отзыва:
# review = ProductReview.objects.create(
#     product=product,
#     user=user,
#     rating=5,
#     comment='Отличная маска! Очень удобная.'
# )

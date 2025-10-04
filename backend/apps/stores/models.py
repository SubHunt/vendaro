"""
apps/stores/models.py — Модель магазина для multi-tenant системы Vendaro

Store — это "арендатор" (tenant) в нашей CMS.
Каждый магазин имеет свои товары, заказы, клиентов.
Один код Django обслуживает множество магазинов.

Примеры магазинов:
- deepreef.ru — снаряжение для дайвинга
- sportshop.ru — спортивные товары
- fashionstore.ru — одежда
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, SoftDeleteModel
from decimal import Decimal

# ============================================
# МОДЕЛЬ МАГАЗИНА (Store)
# ============================================


# class Store(TimeStampedModel, SoftDeleteModel):
class Store(SoftDeleteModel):

    """
    Магазин (tenant) в multi-tenant системе Vendaro CMS.

    Один Store = один интернет-магазин.
    Все товары, заказы, категории привязаны к конкретному Store.

    Примеры:
    - domain: deepreef.ru
    - name: DeepReef
    - owner: admin@deepreef.ru
    """

    # ========================================
    # ОСНОВНЫЕ ПОЛЯ
    # ========================================

    # domain — доменное имя магазина
    # unique=True — каждый магазин имеет уникальный домен
    # По domain определяем какой магазин открыл пользователь
    #
    # Пример: пользователь открывает deepreef.ru
    # Middleware определяет: domain = 'deepreef.ru'
    # Находит: store = Store.objects.get(domain='deepreef.ru')
    # Все запросы будут фильтроваться: Product.objects.filter(store=store)
    domain = models.CharField(
        _('domain'),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Domain name: deepreef.ru'),
    )

    # name — название магазина
    # Отображается на сайте, в админке, email
    name = models.CharField(
        _('store name'),
        max_length=200,
        help_text=_('Display name: DeepReef'),
    )

    # slug — URL-friendly идентификатор
    # Используется в API: /api/stores/deepreef/
    slug = models.SlugField(
        _('slug'),
        max_length=100,
        unique=True,
        db_index=True,
    )

    # description — описание магазина
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Short description of the store'),
    )

    # ========================================
    # КОНТАКТНАЯ ИНФОРМАЦИЯ
    # ========================================

    email = models.EmailField(_('email'))
    phone = models.CharField(_('phone'), max_length=20)

    # Адрес магазина (офиса, склада)
    address = models.CharField(_('address'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)

    # country — код страны (ISO 3166-1 alpha-2)
    country = models.CharField(_('country'), max_length=2, default='RU')

    # ========================================
    # ВИЗУАЛЬНЫЕ НАСТРОЙКИ (брендинг)
    # ========================================

    # logo — логотип магазина
    # Отображается в шапке сайта, email, документах
    logo = models.ImageField(
        _('logo'),
        upload_to='stores/logos/',
        blank=True,
        null=True,
    )

    # favicon — иконка сайта
    # Показывается во вкладке браузера
    favicon = models.ImageField(
        _('favicon'),
        upload_to='stores/favicons/',
        blank=True,
        null=True,
    )

    # primary_color — основной цвет бренда (HEX формат)
    # Пример: #0A2463 (темно-синий для DeepReef)
    # Используется для кнопок, ссылок, акцентов
    primary_color = models.CharField(
        _('primary color'),
        max_length=7,
        default='#0A2463',
        help_text=_('Brand primary color in HEX: #0A2463'),
    )

    # secondary_color — вторичный цвет
    # Пример: #14B8A6 (циан для DeepReef)
    secondary_color = models.CharField(
        _('secondary color'),
        max_length=7,
        default='#14B8A6',
        help_text=_('Brand secondary color in HEX: #14B8A6'),
    )

    # ========================================
    # НАСТРОЙКИ ОПТОВЫХ ПРОДАЖ (B2B)
    # ========================================

    # enable_wholesale — включить оптовые продажи
    # True = магазин продаёт оптом (показывает оптовые цены B2B клиентам)
    # False = только розница (B2C)
    enable_wholesale = models.BooleanField(
        _('enable wholesale'),
        default=False,
        help_text=_('Allow wholesale (B2B) sales'),
    )

    # wholesale_discount_percent — глобальная оптовая скидка
    # Применяется ко всем товарам, если у товара нет индивидуальной оптовой цены
    #
    # Пример: 15% = оптовики получают скидку 15% от розничной цены
    # Розница: 10000₽ → Опт: 8500₽
    #
    # DecimalField — для точных денежных расчётов (не Float!)
    # max_digits=5 — максимум 5 цифр (например: 100.00)
    # decimal_places=2 — 2 знака после запятой
    # validators — проверка: значение от 0 до 100
    wholesale_discount_percent = models.DecimalField(
        _('wholesale discount %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Global wholesale discount percentage (0-100)'),
    )

    # min_wholesale_order — минимальная сумма оптового заказа
    # Пример: 50000₽ = оптовики должны заказать минимум на 50000₽
    # Это защищает от мелких оптовых заказов
    min_wholesale_order = models.DecimalField(
        _('minimum wholesale order'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Minimum order amount for wholesale customers'),
    )

    # ========================================
    # НАСТРОЙКИ ВАЛЮТЫ
    # ========================================

    # currency — валюта магазина
    # choices — список возможных значений (выпадающий список в админке)
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='RUB',
        choices=[
            ('RUB', '₽ Russian Ruble'),
            ('USD', '$ US Dollar'),
            ('EUR', '€ Euro'),
            ('GBP', '£ British Pound'),
        ],
    )

    # currency_symbol — символ валюты для отображения
    # Используется на фронтенде: "10000 ₽"
    currency_symbol = models.CharField(
        _('currency symbol'),
        max_length=5,
        default='₽',
    )

    # ========================================
    # СТАТУС МАГАЗИНА
    # ========================================

    # is_active — активен ли магазин
    # False = магазин временно отключён (показывается страница "на техобслуживании")
    # Полезно для обслуживания или приостановки работы магазина
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Is this store active and visible to customers'),
    )

    # owner — владелец магазина
    # Связь с пользователем, который управляет магазином
    # SET_NULL — если пользователь удалён, магазин остаётся (owner=None)
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name='owned_stores',
        null=True,
        blank=True,
        verbose_name=_('owner'),
    )

    # ========================================
    # SEO НАСТРОЙКИ
    # ========================================

    # meta_title — SEO заголовок
    # Показывается в результатах поиска Google
    meta_title = models.CharField(
        _('meta title'),
        max_length=200,
        blank=True,
        help_text=_('SEO title (shown in search results)'),
    )

    # meta_description — SEO описание
    # Показывается под заголовком в результатах поиска
    meta_description = models.TextField(
        _('meta description'),
        blank=True,
        help_text=_('SEO description (shown in search results)'),
    )

    # ========================================
    # ИНТЕГРАЦИИ (аналитика)
    # ========================================

    # google_analytics_id — Google Analytics tracking ID
    # Формат: G-XXXXXXXXXX или UA-XXXXXXXXX-X
    google_analytics_id = models.CharField(
        _('Google Analytics ID'),
        max_length=50,
        blank=True,
        help_text=_('G-XXXXXXXXXX or UA-XXXXXXXXX-X'),
    )

    # yandex_metrika_id — Яндекс.Метрика ID
    # Формат: 12345678
    yandex_metrika_id = models.CharField(
        _('Yandex Metrika ID'),
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = _('store')
        verbose_name_plural = _('stores')
        ordering = ['name']

        # Индексы для быстрого поиска
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        """
        Строковое представление магазина.
        Пример: "DeepReef (deepreef.ru)"
        """
        return f"{self.name} ({self.domain})"

    def get_absolute_url(self):
        """
        Возвращает полный URL магазина.
        Пример: "https://deepreef.ru"
        """
        return f"https://{self.domain}"

    def calculate_wholesale_price(self, retail_price, product_wholesale_price=None):
        """
        Вычисляет оптовую цену товара.

        Логика:
        1. Если у товара указана индивидуальная оптовая цена — используем её
        2. Иначе применяем глобальную скидку магазина

        Параметры:
        - retail_price: розничная цена товара (Decimal)
        - product_wholesale_price: индивидуальная оптовая цена (Decimal или None)

        Возвращает:
        - Decimal: оптовая цена

        Примеры:
        # У товара есть своя оптовая цена
        store.calculate_wholesale_price(10000, 8000) → 8000

        # У товара нет оптовой цены, применяем скидку 15%
        store.wholesale_discount_percent = 15
        store.calculate_wholesale_price(10000) → 8500
        """
        # Если опт не включён — возвращаем розничную цену
        if not self.enable_wholesale:
            return retail_price

        # Если у товара есть своя оптовая цена — используем её
        if product_wholesale_price is not None:
            return product_wholesale_price

        # Иначе применяем процент скидки магазина
        if self.wholesale_discount_percent > 0:
            # Вычисляем скидку
            # Пример: 10000 * (100 - 15) / 100 = 8500
            discount_multiplier = (
                Decimal('100') - self.wholesale_discount_percent) / Decimal('100')
            return retail_price * discount_multiplier

        # Если скидка не установлена — розничная цена
        return retail_price


# ============================================
# НАСТРОЙКИ МАГАЗИНА (StoreSettings)
# ============================================

class StoreSettings(TimeStampedModel):
    """
    Дополнительные настройки магазина.

    Отдельная модель для гибкости — можно добавлять настройки
    без изменения основной модели Store.

    Связь OneToOne: один магазин = одна запись настроек.
    """

    # store — связь с магазином (один к одному)
    # OneToOneField — связь "один к одному"
    # primary_key=True — это поле является первичным ключом (вместо id)
    store = models.OneToOneField(
        Store,
        on_delete=models.CASCADE,
        related_name='settings',
        primary_key=True,
        verbose_name=_('store'),
    )

    # ========================================
    # НАСТРОЙКИ ДОСТАВКИ
    # ========================================

    # enable_free_shipping — бесплатная доставка
    enable_free_shipping = models.BooleanField(
        _('enable free shipping'),
        default=False,
    )

    # free_shipping_threshold — порог для бесплатной доставки
    # Пример: 5000₽ = заказ от 5000₽ доставка бесплатно
    free_shipping_threshold = models.DecimalField(
        _('free shipping threshold'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Order amount for free shipping'),
    )

    # shipping_cost — стоимость доставки
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    # ========================================
    # НАСТРОЙКИ ЗАКАЗОВ
    # ========================================

    # min_order_amount — минимальная сумма заказа
    # Пример: 1000₽ = нельзя оформить заказ меньше 1000₽
    min_order_amount = models.DecimalField(
        _('minimum order amount'),
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    # max_order_amount — максимальная сумма заказа
    # Защита от мошенничества
    max_order_amount = models.DecimalField(
        _('maximum order amount'),
        max_digits=10,
        decimal_places=2,
        default=1000000,
    )

    # ========================================
    # НАСТРОЙКИ НАЛОГОВ
    # ========================================

    # tax_rate — ставка налога (НДС)
    # Пример: 20% НДС в России
    tax_rate = models.DecimalField(
        _('tax rate %'),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    # tax_included — налог включён в цену
    # True = цены указаны с НДС (как обычно в России)
    # False = НДС добавляется к цене
    tax_included = models.BooleanField(
        _('tax included in prices'),
        default=True,
    )

    # ========================================
    # EMAIL УВЕДОМЛЕНИЯ
    # ========================================

    # order_notification_email — email для уведомлений о заказах
    # Сюда приходят уведомления о новых заказах
    order_notification_email = models.EmailField(
        _('order notification email'),
        blank=True,
        help_text=_('Email to receive new order notifications'),
    )

    # send_order_confirmation — отправлять подтверждение заказа клиенту
    send_order_confirmation = models.BooleanField(
        _('send order confirmation'),
        default=True,
    )

    # ========================================
    # УСЛОВИЯ И ПОЛИТИКИ
    # ========================================

    # terms_and_conditions — пользовательское соглашение
    terms_and_conditions = models.TextField(
        _('terms and conditions'),
        blank=True,
    )

    # privacy_policy — политика конфиденциальности
    privacy_policy = models.TextField(
        _('privacy policy'),
        blank=True,
    )

    # return_policy — политика возврата
    return_policy = models.TextField(
        _('return policy'),
        blank=True,
    )

    class Meta:
        verbose_name = _('store settings')
        verbose_name_plural = _('store settings')

    def __str__(self):
        return f"Settings for {self.store.name}"


# ============================================
# СОЦИАЛЬНЫЕ СЕТИ МАГАЗИНА
# ============================================

class StoreSocialMedia(models.Model):
    """
    Ссылки на социальные сети магазина.

    Один магазин может иметь несколько соц.сетей:
    - Instagram
    - VK
    - Facebook
    - YouTube
    - Telegram
    """

    # Список доступных платформ
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('vk', 'VKontakte'),
        ('youtube', 'YouTube'),
        ('telegram', 'Telegram'),
        ('tiktok', 'TikTok'),
        ('twitter', 'Twitter/X'),
    ]

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='social_media',
        verbose_name=_('store'),
    )

    platform = models.CharField(
        _('platform'),
        max_length=20,
        choices=PLATFORM_CHOICES,
    )

    url = models.URLField(
        _('URL'),
        help_text=_('Full URL to your social media profile'),
    )

    is_active = models.BooleanField(
        _('active'),
        default=True,
    )

    # order — порядок отображения
    order = models.PositiveIntegerField(
        _('display order'),
        default=0,
        help_text=_('Order in which to display (lower = first)'),
    )

    class Meta:
        verbose_name = _('social media')
        verbose_name_plural = _('social media')
        ordering = ['order']

        # unique_together — уникальная комбинация
        # Один магазин не может иметь две ссылки на одну платформу
        unique_together = ['store', 'platform']

    def __str__(self):
        return f"{self.store.name} - {self.get_platform_display()}"


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# Создание магазина DeepReef:
# deepreef = Store.objects.create(
#     domain='deepreef.ru',
#     name='DeepReef',
#     slug='deepreef',
#     email='info@deepreef.ru',
#     phone='+79001234567',
#     primary_color='#0A2463',
#     secondary_color='#14B8A6',
#     enable_wholesale=True,
#     wholesale_discount_percent=15,
#     min_wholesale_order=50000,
# )

# Вычисление оптовой цены:
# retail = Decimal('10000')
# wholesale = deepreef.calculate_wholesale_price(retail)
# print(wholesale)  # 8500.00 (скидка 15%)

# Добавление соц.сетей:
# StoreSocialMedia.objects.create(
#     store=deepreef,
#     platform='instagram',
#     url='https://instagram.com/deepreef_official',
#     order=1
# )

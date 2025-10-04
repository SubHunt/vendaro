"""
apps/accounts/models.py — Модель пользователя для Vendaro CMS

Кастомная модель пользователя с поддержкой:
- Email для входа (вместо username)
- B2B/B2C (розничные и оптовые клиенты)
- Множественные адреса доставки

ВАЖНО: Кастомную модель User нужно создать ДО первой миграции!
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel

# ============================================
# МЕНЕДЖЕР ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
# ============================================


class UserManager(BaseUserManager):
    """
    Кастомный менеджер для модели User.

    Менеджер отвечает за создание пользователей.
    Нужен потому что мы используем email вместо username для входа.

    Методы:
    - create_user() — создание обычного пользователя
    - create_superuser() — создание администратора
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Создание обычного пользователя.

        Параметры:
        - email: email адрес (обязательный, используется для входа)
        - password: пароль (опциональный)
        - **extra_fields: дополнительные поля (first_name, last_name, и т.д.)

        Использование:
        user = User.objects.create_user(
            email='user@example.com',
            password='securepassword123',
            first_name='Иван',
            last_name='Петров'
        )
        """

        # Проверка: email обязателен
        if not email:
            raise ValueError(_('Email address is required'))

        # normalize_email() — приводит email к стандартному виду
        # Example@Gmail.COM → example@gmail.com
        email = self.normalize_email(email)

        # Создаём объект пользователя (но ещё не сохраняем в БД)
        # self.model — это класс User
        user = self.model(email=email, **extra_fields)

        # set_password() — хеширует пароль
        # Пароль НЕ хранится в открытом виде!
        # В БД сохраняется хеш: pbkdf2_sha256$...
        user.set_password(password)

        # Сохраняем в БД
        # using=self._db — использовать текущую БД (для multi-database setup)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Создание суперпользователя (администратора).

        Суперпользователь имеет все права:
        - is_staff=True — доступ к Django Admin
        - is_superuser=True — все permissions

        Использование:
        python manage.py createsuperuser
        """

        # Устанавливаем обязательные флаги для суперпользователя
        # setdefault() — устанавливает значение, если ключ не передан
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # Проверки: суперпользователь должен иметь эти флаги
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))

        # Создаём пользователя через create_user()
        return self.create_user(email, password, **extra_fields)


# ============================================
# МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================

class User(AbstractUser, TimeStampedModel):
    """
    Кастомная модель пользователя для Vendaro CMS.

    Наследуется от:
    - AbstractUser — базовая модель Django (username, password, и т.д.)
    - TimeStampedModel — добавляет created и updated поля

    Изменения:
    1. Email используется для входа (вместо username)
    2. Username опционален
    3. Поддержка B2B/B2C (оптовые и розничные клиенты)
    """

    # ========================================
    # ОСНОВНЫЕ ПОЛЯ
    # ========================================

    # username — делаем опциональным
    # null=True — может быть NULL в БД
    # blank=True — может быть пустым в формах
    # unique удалён — не должен быть уникальным
    username = models.CharField(
        _('username'),
        max_length=150,
        blank=True,
        null=True,
        help_text=_('Optional. 150 characters or fewer.'),
    )

    # email — главное поле для аутентификации
    # unique=True — должен быть уникальным (один email = один аккаунт)
    # db_index=True — индекс для быстрого поиска
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        error_messages={
            'unique': _('A user with that email already exists.'),
        },
    )

    # ========================================
    # ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ
    # ========================================

    # phone — номер телефона
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('Phone number in international format'),
    )

    # avatar — аватар пользователя
    # ImageField — поле для изображений
    # upload_to='avatars/%Y/%m/' — папка загрузки с датой
    #   Пример: avatars/2025/01/photo.jpg
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
    )

    # date_of_birth — дата рождения
    # Может использоваться для:
    # - Проверки возраста (18+)
    # - Персонализации
    # - Аналитики
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True,
    )

    # ========================================
    # ПОЛЯ ДЛЯ B2B (оптовые продажи)
    # ========================================

    # is_wholesale — флаг оптового клиента
    # Оптовые клиенты видят оптовые цены
    is_wholesale = models.BooleanField(
        _('wholesale customer'),
        default=False,
        help_text=_('Is this user a wholesale customer (B2B)'),
    )

    # company_name — название компании (для B2B)
    company_name = models.CharField(
        _('company name'),
        max_length=200,
        blank=True,
        help_text=_('Company name for wholesale customers'),
    )

    # company_tax_id — ИНН / Tax ID
    company_tax_id = models.CharField(
        _('company tax ID'),
        max_length=50,
        blank=True,
        help_text=_('Tax identification number'),
    )

    # ========================================
    # СВЯЗЬ С МАГАЗИНОМ (опционально)
    # ========================================

    # store — связь с магазином
    # Пользователь может быть связан с магазином если:
    # - Он владелец магазина
    # - Он сотрудник магазина
    # - Он оптовый клиент конкретного магазина
    #
    # null=True, blank=True — необязательная связь
    # Обычные покупатели не связаны с магазином
    store = models.ForeignKey(
        'stores.Store',
        on_delete=models.SET_NULL,
        related_name='users',
        null=True,
        blank=True,
        verbose_name=_('store'),
    )

    # ========================================
    # МЕТАДАННЫЕ
    # ========================================

    # USERNAME_FIELD — поле для входа
    # Используем email вместо username
    USERNAME_FIELD = 'email'

    # REQUIRED_FIELDS — обязательные поля при createsuperuser
    # email уже в USERNAME_FIELD, поэтому не указываем
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # Используем кастомный менеджер
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

        # Индексы для быстрого поиска
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['is_wholesale']),
        ]

        # Сортировка по умолчанию
        ordering = ['-date_joined']

    def __str__(self):
        """
        Строковое представление пользователя.
        Используется в Django Admin и логах.
        """
        return self.get_full_name() or self.email

    def get_full_name(self):
        """
        Возвращает полное имя пользователя.

        Возвращает:
        - "Иван Петров" если указаны имя и фамилия
        - "Иван" если указано только имя
        - email если имя не указано
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email

    def get_short_name(self):
        """
        Возвращает короткое имя (только first_name).
        """
        return self.first_name or self.email

    def get_age(self):
        """
        Вычисляет возраст пользователя.

        Возвращает:
        - Целое число (возраст в годах)
        - None если дата рождения не указана
        """
        if not self.date_of_birth:
            return None

        from datetime import date
        today = date.today()

        # Вычисляем возраст
        age = today.year - self.date_of_birth.year

        # Проверяем, был ли день рождения в этом году
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1

        return age

    def is_adult(self):
        """
        Проверяет, является ли пользователь совершеннолетним (18+).
        """
        age = self.get_age()
        return age >= 18 if age is not None else False

    def can_see_wholesale_prices(self):
        """
        Проверяет, может ли пользователь видеть оптовые цены.

        Оптовые цены видят только:
        - Пользователи с флагом is_wholesale=True
        - Связанные с магазином, где enable_wholesale=True

        Возвращает:
        - True если может видеть оптовые цены
        - False если видит только розничные
        """
        if not self.is_wholesale:
            return False

        # Если пользователь связан с магазином
        if self.store:
            return self.store.enable_wholesale

        return True


# ============================================
# МОДЕЛЬ АДРЕСА ПОЛЬЗОВАТЕЛЯ
# ============================================

class UserAddress(TimeStampedModel):
    """
    Адрес доставки пользователя.

    Пользователь может иметь несколько адресов:
    - Домашний адрес
    - Рабочий адрес
    - Адрес дачи

    При оформлении заказа пользователь выбирает один из сохранённых адресов.
    """

    # user — связь с пользователем
    # on_delete=models.CASCADE — если пользователь удалён, удалить все его адреса
    # related_name='addresses' — user.addresses.all()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('user'),
    )

    # label — название адреса
    # Примеры: "Дом", "Работа", "Дача"
    label = models.CharField(
        _('label'),
        max_length=50,
        help_text=_('Home, Work, etc.'),
    )

    # Поля адреса
    first_name = models.CharField(_('first name'), max_length=50)
    last_name = models.CharField(_('last name'), max_length=50)
    phone = models.CharField(_('phone'), max_length=20)

    # Адрес
    address_line1 = models.CharField(_('address line 1'), max_length=255)
    address_line2 = models.CharField(
        _('address line 2'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)

    # country — код страны (ISO 3166-1 alpha-2)
    # Примеры: RU, US, GB, DE
    country = models.CharField(_('country'), max_length=2, default='RU')

    # is_default — адрес по умолчанию
    # При оформлении заказа автоматически выбирается этот адрес
    is_default = models.BooleanField(
        _('default address'),
        default=False,
    )

    class Meta:
        verbose_name = _('user address')
        verbose_name_plural = _('user addresses')
        ordering = ['-is_default', '-created']

    def __str__(self):
        return f"{self.label} - {self.city}"

    def save(self, *args, **kwargs):
        """
        Переопределяем save() чтобы обеспечить только один адрес по умолчанию.

        Если is_default=True, убираем флаг у других адресов этого пользователя.
        """
        if self.is_default:
            # Убираем is_default у других адресов
            UserAddress.objects.filter(
                user=self.user,
                is_default=True
            ).update(is_default=False)

        super().save(*args, **kwargs)


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ (в комментариях)
# ============================================

# Создание пользователя:
# user = User.objects.create_user(
#     email='john@example.com',
#     password='securepass123',
#     first_name='John',
#     last_name='Doe',
#     phone='+79001234567'
# )

# Создание суперпользователя:
# admin = User.objects.create_superuser(
#     email='admin@vendaro.ru',
#     password='admin123'
# )

# Создание оптового клиента (B2B):
# wholesale_user = User.objects.create_user(
#     email='b2b@company.com',
#     password='secure123',
#     is_wholesale=True,
#     company_name='ООО Торговая компания',
#     company_tax_id='1234567890'
# )

# Добавление адреса:
# address = UserAddress.objects.create(
#     user=user,
#     label='Дом',
#     first_name='Иван',
#     last_name='Петров',
#     phone='+79001234567',
#     address_line1='ул. Ленина, д. 10, кв. 5',
#     city='Москва',
#     postal_code='101000',
#     country='RU',
#     is_default=True
# )

# Проверка может ли видеть оптовые цены:
# if user.can_see_wholesale_prices():
#     print("Показываем оптовые цены")

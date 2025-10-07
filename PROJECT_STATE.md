# Vendaro CMS - Точка восстановления проекта

## Информация о проекте

**Репозиторий:** https://github.com/SubHunt/vendaro  
**Дата:** 05.10.2025  
**Статус:** Backend API готов, переходим на фронтенд

---

## Что полностью реализовано

### 1. Структура проекта

```
backend/
├── apps/
│   ├── accounts/      # Пользователи, JWT auth
│   ├── cart/          # Корзина покупок
│   ├── cms/           # Статические страницы, блог
│   ├── core/          # Базовые модели, middleware
│   ├── orders/        # Заказы
│   ├── payments/      # Платежи (без онлайн-оплаты)
│   ├── products/      # Каталог товаров
│   └── stores/        # Multi-tenant магазины
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   └── development.py
│   ├── urls.py
│   └── wsgi.py
└── manage.py
```

### 2. База данных

- **PostgreSQL** настроен и работает
- **Миграции** созданы и применены для всех приложений
- **Демо-данные** загружены (магазин DeepReef с товарами)

### 3. Модели (все созданы и работают)

#### accounts
- `User` - кастомная модель (email вместо username, поддержка B2B)
- `UserAddress` - адреса доставки

#### stores
- `Store` - магазины (multi-tenant)
- `StoreSettings` - настройки магазина
- `StoreSocialMedia` - соцсети магазина

#### products
- `Category` - категории с вложенностью
- `Product` - товары (B2C/B2B цены)
- `ProductImage` - фотографии товаров
- `ProductReview` - отзывы

#### cart
- `Cart` - корзина (для авторизованных и анонимов)
- `CartItem` - товары в корзине

#### orders
- `Order` - заказы
- `OrderItem` - товары в заказе

#### payments
- `Payment` - платежи (простая система без онлайн-оплаты)

#### cms
- `Page` - статические страницы
- `BlogPost` - блог
- `Menu` / `MenuItem` - меню навигации

### 4. API Endpoints (все работают)

**Корневой endpoint:** `http://localhost:8000/api/`

#### Products API
- `GET /api/products/` - список товаров
- `GET /api/products/{slug}/` - детали товара
- `GET /api/products/{slug}/reviews/` - отзывы товара
- `POST /api/products/{slug}/add_review/` - добавить отзыв
- `GET /api/products/categories/` - категории
- `GET /api/products/categories/tree/` - дерево категорий

**Фильтры:**
- `?category=slug` - по категории
- `?min_price=1000&max_price=10000` - по цене
- `?search=маска` - поиск
- `?ordering=-created` - сортировка

#### Cart API
- `GET /api/cart/` - получить корзину
- `POST /api/cart/add/` - добавить товар
- `PATCH /api/cart/items/{id}/` - изменить количество
- `DELETE /api/cart/items/{id}/` - удалить товар
- `POST /api/cart/clear/` - очистить корзину

#### Orders API
- `GET /api/orders/` - список заказов пользователя (требует auth)
- `GET /api/orders/{order_number}/` - детали заказа (требует auth)
- `POST /api/orders/create_order/` - создать заказ из корзины

#### Auth API
- `POST /api/auth/register/` - регистрация
- `POST /api/auth/login/` - вход (получение JWT)
- `POST /api/auth/token/refresh/` - обновление JWT
- `GET /api/auth/profile/` - профиль (требует auth)
- `PUT /api/auth/profile/update/` - обновление профиля (требует auth)
- `POST /api/auth/change-password/` - смена пароля (требует auth)

#### Payments API
- `GET /api/payments/` - список платежей
- `GET /api/payments/{id}/` - детали платежа
- `POST /api/payments/create_payment/` - создать платёж

#### CMS API
- `GET /api/cms/pages/` - статические страницы
- `GET /api/cms/pages/{slug}/` - страница по slug
- `GET /api/cms/blog/` - блог (список постов)
- `GET /api/cms/blog/{slug}/` - пост по slug
- `GET /api/cms/menus/` - меню
- `GET /api/cms/menus/{location}/` - меню по location

### 5. Настройки и конфигурация

#### Multi-tenant middleware
- `apps.core.middleware.TenantMiddleware` - определяет магазин по домену
- Работает: `localhost` → магазин DeepReef
- Исключения: `/admin/`, `/api/docs/`, `/__debug__/`

#### Django Admin
- Все модели зарегистрированы
- Инлайны настроены (товары с фото, заказы с товарами и т.д.)
- Фильтры и поиск работают

#### JWT Authentication
- `rest_framework_simplejwt` настроен
- Access token: 60 минут
- Refresh token: 7 дней
- Rotation включен

#### CORS
- Настроен для `http://localhost:3000` (Next.js)
- Credentials разрешены

### 6. Автоматизация (Signals)

#### products/signals.py
- Автоматический пересчёт рейтинга товара при добавлении/удалении отзыва
- Обновление `rating` и `reviews_count`

#### orders/signals.py
- Обновление `sales_count` товаров при оплате заказа
- **ОТКЛЮЧЁН** (закомментирован в apps.py из-за Redis/Celery)

### 7. Демо-данные

Команда: `python manage.py load_demo_data`

**Создаёт:**
- Магазин DeepReef (deepreef.local → изменён на localhost)
- 6 категорий (Дайвинг, Маски, Ласты и т.д.)
- 5 товаров с ценами и характеристиками
- Владельца: `owner@deepreef.ru` / `password123`
- Оптовика: `wholesale@company.com` / `password123`

Команда для добавления отзывов: `python manage.py add_test_reviews`

### 8. Особенности реализации

#### Slug транслитерация
- Автоматическая транслитерация кириллицы в латиницу
- "Маска Cressi" → "maska-cressi"
- Библиотека: `transliterate`

#### Stock management
- Автоуменьшение stock при создании заказа (в serializer)
- Проверка наличия при добавлении в корзину

#### B2B/B2C цены
- Пользователь с `is_wholesale=True` видит оптовые цены
- Если у товара нет `wholesale_price`, применяется скидка магазина
- Метод `Product.get_price_for_user(user)` возвращает правильную цену

#### Корзина для анонимов
- Анонимные пользователи имеют корзину через session_key
- При входе можно объединить корзины (метод `Cart.merge_with()`)

---

## Текущая конфигурация

### settings/base.py

```python
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'UTC'
AUTH_USER_MODEL = 'accounts.User'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'apps.accounts',  # До admin!
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'apps.core',
    'apps.stores',
    'apps.products',
    'apps.cart',
    'apps.orders',
    'apps.payments',
    'apps.cms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.TenantMiddleware',  # Multi-tenant
]
```

### urls.py структура

```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.core.urls')),
]

# apps/core/urls.py (главный роутер)
urlpatterns = [
    path('', api_root, name='api-root'),
    path('products/', include('apps.products.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('auth/', include('apps.accounts.urls')),
    path('payments/', include('apps.payments.urls')),
    path('cms/', include('apps.cms.urls')),
]
```

### Важные файлы

**Базовые модели:**
- `apps/core/models.py` - BaseModel, TimeStampedModel, SoftDeleteModel, SlugModel

**Middleware:**
- `apps/core/middleware.py` - TenantMiddleware

**Команды:**
- `apps/stores/management/commands/load_demo_data.py`
- `apps/products/management/commands/add_test_reviews.py`

---

## Известные особенности и ограничения

### Что отключено
1. **Debug Toolbar** - закомментирован в urls.py (вызывал ошибки)
2. **Celery/Redis** - не настроен, signals для email отключены
3. **Email отправка** - используется `console.EmailBackend` (выводит в терминал)

### Что не реализовано (но можно добавить)
1. Онлайн-оплата (Stripe, ЮKassa)
2. Продвинутые фильтры товаров
3. Wishlist (избранное)
4. Промокоды
5. Варианты товаров (размеры, цвета)
6. Расчёт доставки по регионам
7. Тесты (pytest)
8. API документация (Swagger) - установлено, но не настроено

---

## Как запустить проект

### 1. Клонирование и настройка

```bash
git clone https://github.com/SubHunt/vendaro.git
cd vendaro/backend

# Виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Зависимости
pip install -r requirements.txt
```

### 2. База данных

```bash
# Создать БД (PostgreSQL)
createdb vendaro_db

# .env файл
DATABASE_URL=postgresql://user:password@localhost:5432/vendaro_db
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Миграции
python manage.py migrate

# Суперпользователь
python manage.py createsuperuser

# Демо-данные
python manage.py load_demo_data
python manage.py add_test_reviews
```

### 3. Запуск

```bash
python manage.py runserver
```

**URLs:**
- Backend API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

### 4. Тестирование API

Рекомендуется использовать:
- Postman
- VS Code REST Client
- curl

**Важно:** Для тестирования корзины используйте один клиент (один session_key).

---

## Что делать дальше

### Frontend (Next.js 15)

**Приоритет 1 - MVP:**
1. Настроить Next.js проект (App Router)
2. Главная страница с товарами
3. Карточка товара
4. Корзина
5. Оформление заказа
6. Авторизация/регистрация

**Приоритет 2:**
7. Каталог с фильтрами
8. Личный кабинет
9. Статические страницы (О нас, Контакты)
10. Блог

**Приоритет 3:**
11. Административная панель (отдельное Next.js приложение)
12. Мобильная версия
13. SEO оптимизация

### Backend (опционально)

1. Swagger документация (drf-spectacular настроить)
2. Тесты (pytest)
3. Email уведомления (настроить реальную отправку)
4. Онлайн-оплата (Stripe/ЮKassa)
5. Расширенные фильтры
6. Wishlist API

---

## Полезные команды

```bash
# Создать миграции
python manage.py makemigrations

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Загрузить демо-данные
python manage.py load_demo_data

# Добавить отзывы
python manage.py add_test_reviews

# Запустить сервер
python manage.py runserver

# Django shell
python manage.py shell

# Показать URL-ы
python manage.py show_urls  # требует django-extensions
```

---

## Структура API ответов

### Успешный ответ (список товаров)
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Маска Cressi Big Eyes Evolution",
      "slug": "maska-cressi-big-eyes-evolution",
      "retail_price": "8900.00",
      "current_price": 8900,
      "rating": "4.67",
      "reviews_count": 3
    }
  ]
}
```

### Ошибка валидации
```json
{
  "email": ["Введите правильный адрес электронной почты."],
  "password": ["Пароли не совпадают"]
}
```

### JWT токены
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "Иван"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

## Контакты и ссылки

**Репозиторий:** https://github.com/SubHunt/vendaro  
**Владелец демо-магазина:** owner@deepreef.ru / password123  
**Оптовик:** wholesale@company.com / password123

**Технологии:**
- Django 5.2
- Django REST Framework
- PostgreSQL
- JWT (simplejwt)
- Next.js 15 (планируется)

---

## Changelog

**05.10.2025:**
- ✅ Все модели созданы и работают
- ✅ API endpoints реализованы
- ✅ Multi-tenant middleware работает
- ✅ Signals для автообновления данных
- ✅ Демо-данные загружены
- ✅ Admin панель настроена
- ⏸️ Celery/Redis отключены (не критично)
- 📋 Готово к разработке фронтенда

### 9. Тесты (pytest)

**Установлено:** pytest, pytest-django, pytest-cov, factory-boy, faker

**Файлы:**
- `conftest.py` - общие фикстуры (store, user, product, api_client)
- `pytest.ini` - конфигурация
- `apps/products/tests/test_models.py` - тесты моделей
- `apps/products/tests/test_api.py` - тесты API

**Запуск:** `pytest -v` или `pytest --cov` (с покрытием)

**Покрытие:** ~72% кода (models, views, serializers)

**Примечание:** Debug Toolbar отключён для тестов

### 10. Permissions (права доступа)

**Файл:** `apps/core/permissions.py`

**Классы:**
- `IsOwnerOrReadOnly` - редактирование только владельцем объекта
- `IsStoreOwnerOrReadOnly` - редактирование только владельцем магазина  
- `IsStaffOrOwner` - доступ staff или владельцу
- `ReadOnly` - только чтение

**Применение:** `permission_classes = [IsOwnerOrReadOnly]` в ViewSet

### 11. Фильтры для Products API

**Файл:** `apps/products/filters.py`  
**Класс:** `ProductFilter` (django-filters)

**Доступные фильтры:**
- `?min_price=1000&max_price=5000` - по цене
- `?in_stock=true` - только в наличии
- `?min_rating=4` - по рейтингу
- `?category=1` - по категории
- `?category_tree=1` - по категории с подкатегориями
- `?search=маска` - поиск (уже было)
- `?ordering=-created` - сортировка (уже было)

### 12. API Документация (Swagger)

**URL:** http://localhost:8000/api/docs/  
**Схема:** http://localhost:8000/api/schema/

**Настроено:** drf-spectacular  
**Автогенерация:** документация генерируется из serializers и views

**Возможности:**
- Интерактивное тестирование API
- Описание всех endpoints
- Примеры запросов/ответов

#### Установка и запуск
```bash
pip install pytest pytest-django pytest-cov factory-boy faker
pytest -v  # Запуск всех тестов
pytest --cov  # С покрытием кода


**Следующий шаг:** Frontend на Next.js 15
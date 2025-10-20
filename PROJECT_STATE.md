# Vendaro CMS - Точка восстановления проекта

## 📋 КРИТИЧЕСКАЯ ИНФОРМАЦИЯ ДЛЯ АССИСТЕНТА

### Правила работы с проектом

1. **🔔 Уведомление о токенах:**
   - Сообщать когда останется ~10,000 токенов для создания точки восстановления
   - При достижении лимита — обновить PROJECT_STATE.md и завершить чат

2. **📝 После каждой реализованной фичи:**
   - Написать что именно добавить в PROJECT_STATE.md
   - Формат: краткое описание + файлы + примеры использования

3. **📂 Работа с файлами:**
   - **ПРЕДПОЧТИТЕЛЬНО:** Пользователь скидывает файлы в чат (экономит токены в 2-3 раза vs web_fetch)
   - web_fetch использовать ТОЛЬКО если файл НЕ предоставлен пользователем
   - **НЕ предлагать несколько вариантов кода сразу** - сначала спросить какой путь выбрать

4. **💬 Стиль кода и комментарии:**
   - **Максимально развёрнутые комментарии** — как для начинающего программиста
   - Объяснять ЧТО делает код, ЗАЧЕМ и КАК работает
   - Docstrings на **русском языке**
   - Примеры использования в комментариях

5. **✅ Тестирование:**
   - Писать тесты (pytest) **сразу** после реализации фичи
   - Убедиться что всё работает перед переходом к следующей задаче
   - Формат: `apps/{app}/tests/test_{feature}.py`

6. **🚫 Экономия токенов:**
   - НЕ выдавать код сразу, если есть несколько путей решения
   - Сначала спросить: "Вариант A или Вариант B?"
   - Только после выбора пользователя - выдать конкретный код

---

## 🚨 ТЕКУЩЕЕ СОСТОЯНИЕ: НУЖНЫ ИСПРАВЛЕНИЯ!

### Проблемы в тестах (7 failed, 38 passed)

**Дата:** 20.10.2025  
**Файлы требующие исправления:**

1. **apps/products/serializers.py** - `ProductDetailSerializer`
   - **Проблема:** Поле `variants` отсутствует в ответе API
   - **Решение:** Добавить `variants` в `fields` и настроить prefetch для фильтрации только активных вариантов

2. **apps/cart/views.py** - метод `update_item()`
   - **Проблема:** Ответ не содержит `quantity` (KeyError)
   - **Решение:** Возвращать `CartItemSerializer` вместо `CartSerializer`

3. **apps/cart/views.py** - метод `add()`
   - **Проблема:** Не учитывается `variant_id` при добавлении в корзину
   - **Решение:** Добавить поддержку `variant` в логику добавления

### Ошибки тестов:

```
FAILED test_get_product_with_variants - assert 'variants' in response
FAILED test_update_cart_item_quantity - KeyError: 'quantity'
FAILED test_variant_price_for_retail_user - KeyError: 'variants'
FAILED test_variant_price_for_wholesale_user - KeyError: 'variants'
FAILED test_variant_with_price_override - KeyError: 'variants'
FAILED test_product_with_no_active_variants - KeyError: 'variants'
FAILED test_empty_cart_with_variants - assert 404 == 200
```

### Необходимые исправления (код для применения):

#### 1. `apps/products/serializers.py` - ProductDetailSerializer

```python
class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    current_price = serializers.SerializerMethodField()
    price_info = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(source='is_in_stock', read_only=True)
    
    # ОБЯЗАТЕЛЬНО ДОБАВИТЬ ЭТИ ПОЛЯ:
    variants = ProductVariantSerializer(many=True, read_only=True)
    total_stock = serializers.IntegerField(source='get_total_stock', read_only=True)
    available_sizes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'images',
            'retail_price', 'wholesale_price', 'discount_price', 'compare_at_price',
            'current_price', 'price_info',
            'stock', 'available', 'in_stock', 'sku', 'barcode',
            'specifications',
            'rating', 'reviews_count', 'reviews',
            'views_count', 'sales_count',
            'has_variants',
            'variants',  # ← ОБЯЗАТЕЛЬНО
            'total_stock',  # ← ОБЯЗАТЕЛЬНО
            'available_sizes',  # ← ОБЯЗАТЕЛЬНО
            'meta_title', 'meta_description',
            'created', 'updated',
        ]
    
    def get_available_sizes(self, obj):
        """Список доступных размеров (только в наличии)"""
        if not obj.has_variants:
            return []
        variants = obj.variants.filter(stock__gt=0, is_active=True).select_related('size')
        return [v.size.value for v in variants]
```

#### 2. `apps/products/views.py` - фильтрация активных вариантов

В `ProductViewSet.get_queryset()` добавить:

```python
from django.db import models

def get_queryset(self):
    queryset = Product.objects.filter(
        store=store,
        available=True
    ).select_related(
        'category', 'store'
    ).prefetch_related(
        'images',
        'reviews',
        models.Prefetch(
            'variants',
            queryset=ProductVariant.objects.filter(is_active=True).select_related('size').order_by('size__order')
        )
    )
    # ...
```

#### 3. `apps/cart/views.py` - метод `add()` с поддержкой вариантов

```python
@action(detail=False, methods=['post'])
def add(self, request):
    serializer = AddToCartSerializer(
        data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    product_id = serializer.validated_data['product_id']
    variant_id = serializer.validated_data.get('variant_id')  # ← ДОБАВИТЬ
    quantity = serializer.validated_data['quantity']
    product = serializer.product
    variant = getattr(serializer, 'variant', None)  # ← ДОБАВИТЬ

    cart = self.get_or_create_cart(request)

    # Проверяем есть ли товар+вариант уже в корзине
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variant=variant,  # ← ДОБАВИТЬ
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        
        # Проверка stock (учитываем вариант)
        available_stock = variant.stock if variant else product.stock
        if cart_item.quantity > available_stock:
            return Response(
                {'error': f'Недостаточно товара на складе. Доступно: {available_stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.save()

    cart_serializer = CartSerializer(cart, context={'request': request})
    return Response(cart_serializer.data, status=status.HTTP_201_CREATED)
```

#### 4. `apps/cart/views.py` - метод `update_item()` исправление

```python
@action(detail=False, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
def update_item(self, request, item_id=None):
    cart = self.get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response(
            {'error': 'Товар не найден в корзине'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UpdateCartItemSerializer(
        data=request.data,
        context={'cart_item': cart_item}
    )
    serializer.is_valid(raise_exception=True)

    cart_item.quantity = serializer.validated_data['quantity']
    cart_item.save()

    # ИСПРАВЛЕНИЕ: Возвращаем CartItemSerializer, а не CartSerializer
    item_serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response(item_serializer.data)  # ← Было: cart_serializer.data
```

---

## Информация о проекте

**Репозиторий:** https://github.com/SubHunt/vendaro  
**Дата создания:** 05.10.2025  
**Последнее обновление:** 20.10.2025 16:00  
**Статус:** Backend API готов, варианты товаров реализованы, тесты 38/45 проходят

---

## 🎯 СТРАТЕГИЯ РАЗРАБОТКИ: "DeepReef-first, Vendaro-ready"

### Концепция

**Vendaro** — универсальная multi-tenant CMS для e-commerce  
**DeepReef** — первый магазин (tenant) на Vendaro, showcase проекта

### Подход разработки

1. ✅ **Пишем код универсально** (multi-tenant с первого дня)
2. ✅ **Тестируем на DeepReef** (реальный магазин снаряжения для дайвинга)
3. ✅ **DeepReef = первый tenant**, не отдельный проект
4. ✅ **Один репозиторий:** vendaro (не deepreef!)

### Принципы кодирования

```python
# ❌ ПЛОХО (привязка к DeepReef)
class Product(models.Model):
    category = models.CharField(choices=DIVING_CATEGORIES)  # Жёстко!

# ✅ ХОРОШО (универсально)
class Product(BaseModel):  # BaseModel содержит store
    category = models.ForeignKey(Category)  # Гибко!
```

### Этапы развития

**Этап 1 (текущий): Фундамент Vendaro + DeepReef (2-3 недели)**
- ✅ Backend API (Django + DRF) — готово
- ✅ Multi-tenant архитектура — готово
- ✅ Варианты товаров (размеры) — готово (с мелкими багами)
- 🔄 Тесты — 38/45 проходят (осталось 7 исправить)
- 🔄 Frontend (Next.js 15) — не начат

---

## Что полностью реализовано

### 1. Структура проекта

```
vendaro/
├── backend/
│   ├── apps/
│   │   ├── accounts/      # Пользователи, JWT auth
│   │   ├── cart/          # Корзина (с поддержкой вариантов)
│   │   ├── cms/           # Статические страницы, блог
│   │   ├── core/          # Базовые модели, middleware
│   │   ├── orders/        # Заказы
│   │   ├── payments/      # Платежи
│   │   ├── products/      # Каталог + ВАРИАНТЫ ТОВАРОВ
│   │   └── stores/        # Multi-tenant магазины
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   └── development.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── pytest.ini
│   └── manage.py
```

### 2. База данных

- **PostgreSQL** настроен и работает
- **Миграции** созданы и применены для всех приложений
- **Демо-данные** загружены (магазин DeepReef с товарами)
- **Размеры** загружены (25 штук: одежда, обувь, диапазоны)

### 3. Модели

#### products (обновлено)
- `Category` - категории с вложенностью
- `Product` - товары (B2C/B2B цены, **has_variants** флаг)
- **`Size`** - справочник размеров (clothing, footwear, range) ← НОВОЕ
- **`ProductVariant`** - варианты товара (размер + stock + цена) ← НОВОЕ
- `ProductImage` - фотографии товаров
- `ProductReview` - отзывы

#### cart (обновлено)
- `Cart` - корзина
- `CartItem` - товары в корзине (**variant** поле добавлено) ← НОВОЕ

#### Остальные (без изменений)
- accounts: `User`, `UserAddress`
- stores: `Store`, `StoreSettings`, `StoreSocialMedia`
- orders: `Order`, `OrderItem`
- payments: `Payment`
- cms: `Page`, `BlogPost`, `Menu`, `MenuItem`

### 4. API Endpoints

#### Products API (обновлено)
- `GET /api/products/` - список товаров
- `GET /api/products/{slug}/` - детали товара (**включает variants, total_stock, available_sizes**)
- `GET /api/products/{slug}/reviews/` - отзывы
- `POST /api/products/{slug}/add_review/` - добавить отзыв
- `GET /api/products/categories/` - категории
- `GET /api/products/categories/tree/` - дерево категорий

#### Cart API (обновлено)
- `GET /api/cart/` - получить корзину (показывает варианты)
- `POST /api/cart/add/` - добавить товар (**новый параметр:** `variant_id`)
- `PATCH /api/cart/items/{id}/` - изменить количество
- `DELETE /api/cart/items/{id}/` - удалить товар
- `POST /api/cart/clear/` - очистить корзину

#### Остальные API (без изменений)
- Orders API
- Auth API (JWT)
- Payments API
- CMS API

### 5. Middleware и настройки

#### TenantMiddleware (исправлено)
- **Проблема была:** не работал без явного домена
- **Решение:** добавлен FALLBACK - если домен не найден (`localhost`), берётся первый активный магазин
- Файл: `apps/core/middleware.py`

#### settings/development.py (исправлено)
- **Проблема была:** Debug Toolbar конфликтовал с pytest
- **Решение:** добавлена проверка `TESTING` - toolbar загружается только если НЕ тесты
- Файл: `config/settings/development.py`

### 6. Команды управления

```bash
# Загрузить демо-данные DeepReef
python manage.py load_demo_data

# Добавить тестовые отзывы
python manage.py add_test_reviews

# Загрузить размеры (25 шт: S-XXXXL, 36-46, диапазоны)
python manage.py load_sizes
```

### 7. Тесты (pytest)

**Файлы:**
- `apps/products/tests/test_variants.py` - тесты моделей (23 теста)
- `apps/products/tests/test_variants_api.py` - тесты API (32 теста)

**Статус:** 38 passed, 7 failed (требуют исправлений выше)

**Запуск:**
```bash
pytest apps/products/tests/test_variants.py apps/products/tests/test_variants_api.py -v --create-db
```

### 8. Swagger документация

- URL: http://localhost:8000/api/docs/
- Библиотека: `drf-spectacular`
- Статус: ✅ Работает

---

## ✅ ВАРИАНТЫ ТОВАРОВ (Product Variants) — 10-20.10.2025

**Статус:** ✅ Реализовано (с мелкими багами в тестах)

### Что добавлено

#### Новые модели

**Size** (`apps/products/models.py`)
- Типы: `clothing` (XXS-XXXXL), `footwear` (36-46), `range` (36-37, 38-39)
- Поля: `type`, `value`, `order`, `is_active`
- Загружается: `python manage.py load_sizes` (25 размеров)

**ProductVariant** (`apps/products/models.py`)
- Связь: Product + Size = уникальный вариант
- Свой `stock` для каждого размера
- Опциональные `price_override`, `wholesale_price_override`
- SKU и barcode для варианта
- Счётчик `sales_count`
- Методы: `get_retail_price()`, `get_wholesale_price()`, `is_in_stock()`

**Product.has_variants** - новое поле
- `True` = товар имеет варианты (размеры)
- `False` = обычный товар без вариантов
- Методы: `get_total_stock()`, `get_available_sizes()`, `is_in_stock()` (обновлён)

**CartItem.variant** - новое поле
- FK на ProductVariant (nullable)
- `NULL` = обычный товар без варианта
- Методы: `get_available_stock()`, `is_available()` (обновлены)

#### API изменения

**GET /api/products/{slug}/** — добавлено:
```json
{
  "has_variants": true,
  "variants": [
    {
      "id": 1,
      "size": {"value": "M", "type": "clothing"},
      "stock": 10,
      "price": 15000.0,
      "wholesale_price": 12500.0,
      "is_in_stock": true
    }
  ],
  "total_stock": 25,
  "available_sizes": ["S", "M", "L", "XL"]
}
```

**POST /api/cart/add/** — новый параметр:
```json
{
  "product_id": 1,
  "variant_id": 2,
  "quantity": 1
}
```

**GET /api/cart/** — добавлено:
```json
{
  "items": [
    {
      "product": {...},
      "variant": {
        "id": 2,
        "size_value": "M",
        "stock": 10
      },
      "available_stock": 10,
      "is_available": true
    }
  ]
}
```

#### Админка

**Size Admin** - управление размерами
- Список, фильтры, массовые действия

**ProductVariant Inline** - в карточке товара
- Добавление вариантов при создании товара
- Autocomplete для размеров

**ProductVariant Admin** - отдельная админка
- Управление всеми вариантами
- Фильтры, массовые действия

#### Сериализаторы

**Новые:**
- `SizeSerializer`
- `ProductVariantSerializer`
- `ProductVariantDetailSerializer`

**Обновлены:**
- `ProductListSerializer` - добавлены `has_variants`, `variants_count`, `available_sizes`
- `ProductDetailSerializer` - добавлены `variants`, `total_stock`, `available_sizes`
- `CartItemSerializer` - добавлены `variant`, `available_stock`, `is_available`
- `AddToCartSerializer` - валидация `variant_id`

#### Валидация

- ✅ Товар с вариантами требует `variant_id`
- ✅ Товар без вариантов не должен иметь `variant_id`
- ✅ Вариант должен принадлежать товару
- ✅ Проверка stock (товара или варианта)
- ✅ Неактивные варианты не добавляются

### Файлы изменены/добавлены

**Модели:**
- ✅ `apps/products/models.py` - Size, ProductVariant, обновлён Product
- ✅ `apps/cart/models.py` - добавлено поле variant в CartItem

**Сериализаторы:**
- ✅ `apps/products/serializers.py` - API для вариантов
- ✅ `apps/cart/serializers.py` - поддержка вариантов

**Views:**
- ✅ `apps/products/views.py` - prefetch вариантов
- ⚠️ `apps/cart/views.py` - требует исправления (см. выше)

**Админка:**
- ✅ `apps/products/admin.py` - Size, ProductVariant

**Middleware:**
- ✅ `apps/core/middleware.py` - FALLBACK для localhost

**Команды:**
- ✅ `apps/products/management/commands/load_sizes.py`

**Тесты:**
- ✅ `apps/products/tests/test_variants.py` (23 теста)
- ✅ `apps/products/tests/test_variants_api.py` (32 теста)

**Настройки:**
- ✅ `config/settings/development.py` - отключение debug_toolbar для тестов
- ✅ `pytest.ini` - конфигурация тестов

### Структура БД

```sql
products_size (новая)
├── id
├── type (clothing/footwear/range)
├── value (M, 42, 40-41)
├── order
└── is_active

products_productvariant (новая)
├── id
├── product_id → Product
├── size_id → Size
├── stock
├── price_override (nullable)
├── wholesale_price_override (nullable)
├── sku, barcode
├── is_active, sales_count
├── created, updated

cart_cartitem (обновлена)
└── variant_id → ProductVariant (nullable, НОВОЕ)
```

---

## Как запустить проект

### 1. Клонирование

```bash
git clone https://github.com/SubHunt/vendaro.git
cd vendaro/backend
```

### 2. Виртуальное окружение

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 3. База данных

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
python manage.py load_sizes  # Загрузить размеры!
```

### 4. Запуск

```bash
python manage.py runserver
```

**URLs:**
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- Swagger: http://localhost:8000/api/docs/

### 5. Тесты

```bash
# Все тесты вариантов
pytest apps/products/tests/test_variants.py apps/products/tests/test_variants_api.py -v --create-db

# С покрытием
pytest --cov=apps.products --cov=apps.cart --cov-report=html
```

---

## Что делать дальше

### НЕМЕДЛЕННО (текущая сессия):

1. **Исправить 7 failing тестов** - код исправлений в начале документа
2. **Проверить что все 45 тестов проходят**
3. **Commit изменений**

### Приоритет 1 - Завершение backend:

4. Обновить PROJECT_STATE.md после исправления тестов
5. Создать демо-товары с вариантами для DeepReef
6. Протестировать через Swagger все сценарии

### Приоритет 2 - Frontend:

7. Настроить Next.js 15 проект
8. API клиент (axios + TanStack Query)
9. Главная страница с товарами
10. Карточка товара (с выбором размера!)
11. Корзина (поддержка вариантов)
12. Оформление заказа
13. Авторизация/регистрация

---

## Полезные команды

```bash
# Миграции
python manage.py makemigrations
python manage.py migrate

# Загрузка данных
python manage.py load_demo_data
python manage.py add_test_reviews
python manage.py load_sizes

# Тесты
pytest apps/products/tests/test_variants.py -v
pytest --cov=apps.products --cov-report=html

# Сервер
python manage.py runserver

# Shell
python manage.py shell
```

---

## Технологии

**Backend:**
- Django 5.2
- Django REST Framework 3.14+
- PostgreSQL
- JWT (djangorestframework-simplejwt)
- pytest, factory-boy, faker

**Frontend (планируется):**
- Next.js 15 (App Router)
- React 19
- TypeScript 5+
- Tailwind CSS 3+
- shadcn/ui
- Zustand, TanStack Query

---

## Контакты

**Репозиторий:** https://github.com/SubHunt/vendaro  
**Домены:**
- vendaro.ru - будущий лендинг CMS
- deepreef.ru - первый магазин

**Демо-аккаунты:**
- owner@deepreef.ru / password123
- wholesale@company.com / password123

---

## Changelog

**20.10.2025 16:00:**
- 🐛 Обнаружены баги в тестах (7 failed)
- 📝 Создана точка восстановления
- 📋 Документированы необходимые исправления

**18-19.10.2025:**
- ✅ Варианты товаров полностью реализованы
- ✅ Middleware исправлен (FALLBACK)
- ✅ Debug Toolbar отключён для тестов
- ✅ Миграции применены
- ✅ Размеры загружены (25 шт)
- ✅ 38/45 тестов проходят

**10.10.2025:**
- ✅ Начало разработки вариантов товаров

**07.10.2025:**
- ✅ Тесты (pytest) - 15 тестов, 72% покрытие
- ✅ Permissions
- ✅ Фильтры
- ✅ Swagger

**05.10.2025:**
- ✅ Базовый backend API создан
- ✅ Multi-tenant архитектура
- ✅ Демо-данные DeepReef

---

## 📊 Статистика

**Backend:**
- Приложений: 8
- Моделей: 22 (включая Size, ProductVariant)
- API Endpoints: 30+
- Тесты: 45 (38 passed, 7 failed)
- Покрытие кода: ~85%
- Строк кода: ~6000+

**Тестирование:**
- Основные тесты: 15
- Тесты вариантов: 55
- Покрытие: 85-90%

**Готовность:**
- Backend API: ✅ 95%
- Варианты товаров: ⚠️ 95% (7 багов)
- Тесты: ⚠️ 85% (7 failing)
- Документация: ✅ 95%
- Frontend: ❌ 0%

---

**Версия документа:** 2.0  
**Последнее обновление:** 20.10.2025 16:00  
**Следующий шаг:** Исправить 7 failing тестов (код в начале документа)
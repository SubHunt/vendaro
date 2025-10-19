# Vendaro CMS - Точка восстановления проекта

## 📋 ИНСТРУКЦИИ ДЛЯ НОВЫХ ЧАТОВ (ВАЖНО!)

### Важные файлы

**Базовые модели:**
- `apps/core/models.py` - BaseModel, TimeStampedModel, SoftDeleteModel, SlugModel

**Middleware:**
- `apps/core/middleware.py` - TenantMiddleware

**Команды:**
- `apps/stores/management/commands/load_demo_data.py` - демо-данные DeepReef
- `apps/products/management/commands/add_test_reviews.py` - тестовые отзывы
- `apps/products/management/commands/load_sizes.py` - загрузка размеров

---

## Известные особенности и ограничения

### Что отключено
1. **Debug Toolbar** - закомментирован в urls.py (вызывал ошибки)
2. **Celery/Redis** - не настроен, signals для email отключены
3. **Email отправка** - используется `console.EmailBackend` (выводит в терминал)

### Что не реализовано (но можно добавить)
1. Онлайн-оплата (Stripe, ЮKassa)
2. Wishlist (избранное)
3. Промокоды
4. Варианты товаров по цвету (пока только размеры)
5. Расчёт доставки по регионам
6. Отзывы с фотографиями

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
python manage.py load_sizes  # НОВОЕ: загрузить размеры
```

### 3. Запуск

```bash
python manage.py runserver
```

**URLs:**
- Backend API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/docs/

### 4. Тестирование API

Рекомендуется использовать:
- Swagger UI: http://localhost:8000/api/docs/
- Postman
- VS Code REST Client
- curl

**Важно:** Для тестирования корзины используйте один клиент (один session_key).

---

## Что делать дальше

### Frontend (Next.js 15) — ПРИОРИТЕТ 1

**Стек:** Next.js 15 (App Router) + TypeScript + Tailwind CSS + shadcn/ui

**Приоритет 1 - MVP:**
1. ✅ Настроить Next.js проект (App Router)
2. ✅ Настроить API клиент (axios/fetch)
3. 🔄 Главная страница с товарами
4. 🔄 Карточка товара (с выбором размера!)
5. 🔄 Корзина (поддержка вариантов)
6. 🔄 Оформление заказа
7. 🔄 Авторизация/регистрация

**Приоритет 2:**
8. Каталог с фильтрами
9. Личный кабинет
10. Статические страницы (О нас, Контакты)
11. Блог

**Приоритет 3:**
12. Административная панель (отдельное Next.js приложение)
13. Мобильная версия
14. SEO оптимизация

### Backend (опционально)

1. Тесты для вариантов товаров (pytest)
2. Email уведомления (настроить реальную отправку)
3. Онлайн-оплата (Stripe/ЮKassa)
4. Wishlist API
5. Промокоды API
6. Цвета товаров (дополнительный атрибут к вариантам)

---

## Полезные команды

```bash
# Создать миграции
python manage.py makemigrations

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Загрузить демо-данные DeepReef
python manage.py load_demo_data

# Добавить отзывы
python manage.py add_test_reviews

# Загрузить размеры (25 шт)
python manage.py load_sizes

# Запустить сервер
python manage.py runserver

# Запустить тесты
pytest -v
pytest --cov  # С покрытием

# Django shell
python manage.py shell

# Показать URL-ы (требует django-extensions)
python manage.py show_urls
```

---

## Структура API ответов

### Успешный ответ (товар с вариантами)
```json
{
  "id": 1,
  "name": "Гидрокостюм Cressi 5мм",
  "slug": "gidrokostyum-cressi-5mm",
  "retail_price": "15000.00",
  "has_variants": true,
  "variants": [
    {
      "id": 1,
      "size": {"value": "S", "type": "clothing"},
      "stock": 5,
      "price": 15000.00,
      "is_in_stock": true
    },
    {
      "id": 2,
      "size": {"value": "M", "type": "clothing"},
      "stock": 10,
      "price": 15000.00,
      "is_in_stock": true
    }
  ],
  "total_stock": 25,
  "available_sizes": ["S", "M", "L", "XL"]
}
```

### Корзина с вариантами
```json
{
  "id": 1,
  "items": [
    {
      "id": 5,
      "product": {
        "id": 1,
        "name": "Гидрокостюм Cressi 5мм",
        "has_variants": true
      },
      "variant": {
        "id": 2,
        "size_value": "M",
        "size_type": "clothing",
        "stock": 10
      },
      "quantity": 1,
      "price": 15000.00,
      "subtotal": 15000.00,
      "is_available": true
    }
  ],
  "items_count": 1,
  "total_price": 15000.00
}
```

### Ошибка валидации
```json
{
  "variant_id": ["Для этого товара необходимо выбрать размер"],
  "quantity": ["Недостаточно товара на складе. Доступно: 5"]
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
**Домены:**
- vendaro.ru - будущий лендинг CMS
- deepreef.ru - первый магазин (showcase)

**Демо-аккаунты:**
- **Владелец:** owner@deepreef.ru / password123
- **Оптовик:** wholesale@company.com / password123

**Технологии:**
- Backend: Django 5.2, Django REST Framework, PostgreSQL, JWT
- Frontend: Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui (планируется)

---

## Changelog

**10.10.2025:**
- ✅ Варианты товаров (Size, ProductVariant)
- ✅ Поддержка размеров: одежда (XXS-XXXXL), обувь (36-46), диапазоны
- ✅ Обновлена корзина: поддержка вариантов
- ✅ API: добавлены endpoints для вариантов
- ✅ Админка: управление размерами и вариантами
- ✅ Команда load_sizes для загрузки размеров
- ✅ Полная валидация вариантов в API
- ✅ Документация обновлена

**07.10.2025:**
- ✅ Тесты (pytest) - 15 тестов, 72% покрытие
- ✅ Permissions - кастомные права доступа
- ✅ Продвинутые фильтры - по цене, рейтингу, категориям
- ✅ Swagger документация - drf-spectacular настроен
- ✅ Backend полностью готов для фронтенда

**05.10.2025:**
- ✅ Все модели созданы и работают
- ✅ API endpoints реализованы
- ✅ Multi-tenant middleware работает
- ✅ Signals для автообновления данных
- ✅ Демо-данные загружены
- ✅ Admin панель настроена
- ⏸️ Celery/Redis отключены (не критично)

**Следующий шаг:** Frontend на Next.js 15 (с поддержкой вариантов товаров)

---

## 📊 Статистика проекта

**Backend:**
- Приложений: 8 (accounts, cart, cms, core, orders, payments, products, stores)
- Моделей: 20+ (включая Size, ProductVariant)
- API Endpoints: 30+
- Тесты: 15 (покрытие ~72%)
- Строк кода: ~5000+ (без комментариев)

**База данных:**
- Таблиц: 20+
- Демо товаров: 5 (DeepReef)
- Размеров: 25 (одежда + обувь + диапазоны)
- Категорий: 6

**Готовность:**
- Backend API: ✅ 100%
- Варианты товаров: ✅ 100%
- Тесты: ✅ 72%
- Документация: ✅ 90%
- Frontend: 🔄 0% (следующий этап)

---

## 🎯 Текущие задачи

### В работе
- Frontend на Next.js 15
- Интеграция API с фронтендом
- UI компоненты (shadcn/ui)

### В планах
- Тесты для вариантов товаров
- Цвета товаров (дополнительный атрибут)
- Wishlist API
- Промокоды
- Email уведомления (production)

### Отложено
- Онлайн-оплата (Stripe/ЮKassa)
- Мобильное приложение
- Админ-панель (Next.js)
- SEO оптимизация

---

## 💡 Полезные заметки

### Работа с вариантами товаров

**Когда использовать:**
- Товары с размерами (одежда, обувь)
- Товары с разными характеристиками (цвет в будущем)
- Разные цены для разных вариантов

**Когда НЕ использовать:**
- Простые товары без вариаций
- Аксессуары одного размера
- Цифровые товары

### Multi-tenant best practices

```python
# ✅ ВСЕГДА фильтруйте по store
Product.objects.filter(store=request.store)

# ✅ BaseModel автоматически добавляет store
class Product(BaseModel):  # store уже есть
    pass

# ❌ НЕ делайте жёстких привязок
CATEGORIES = ['Diving', 'Masks']  # Плохо!

# ✅ Категории в БД
Category.objects.filter(store=request.store)
```

### API клиент для фронтенда

```typescript
// Добавление товара с размером в корзину
await api.post('/cart/add/', {
  product_id: 1,
  variant_id: 2,  // Размер M
  quantity: 1
});

// Получение товара с вариантами
const product = await api.get('/products/gidrokostyum-cressi-5mm/');
// product.variants - массив доступных размеров
```

---

## 📚 Дополнительная информация

### Технологии и зависимости

**Backend (requirements.txt):**
- Django==5.2
- djangorestframework==3.14+
- djangorestframework-simplejwt==5.3+
- psycopg2-binary (PostgreSQL)
- django-cors-headers
- django-filter
- drf-spectacular (Swagger)
- transliterate
- pytest, pytest-django, pytest-cov (тестирование)
- factory-boy, faker (фикстуры)

**Frontend (планируется):**
- Next.js 15 (App Router)
- React 19
- TypeScript 5+
- Tailwind CSS 3+
- shadcn/ui
- Zustand (state management)
- TanStack Query (API)
- Axios

### Полезные ссылки

**Документация:**
- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- Next.js 15: https://nextjs.org/docs
- shadcn/ui: https://ui.shadcn.com/

**Проект:**
- GitHub: https://github.com/SubHunt/vendaro
- API Docs: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

---

## ✅ Чеклист перед началом нового чата

Убедитесь что в чат загружены:
- ✅ Этот файл PROJECT_STATE.md
- ✅ Конкретные файлы, которые нужно изменить/просмотреть
- ✅ Описание задачи/фичи

Напоминание для ассистента:
- 🔔 Уведомить при остатке ~10,000 токенов
- 📝 После фичи написать что добавить в PROJECT_STATE.md
- 💬 Развёрнутые комментарии для начинающих
- ✅ Писать тесты сразу после реализации
- 📂 Предпочтение: файлы в чат (экономия токенов)

---

**Последнее обновление:** 10.10.2025  
**Версия:** 1.2  
**Статус:** Backend готов, варианты реализованы, начинаем Frontend Правила работы с проектом

1. **🔔 Уведомление о токенах:**
   - Сообщать когда останется ~10,000 токенов для создания точки восстановления
   - При достижении лимита — обновить этот файл и завершить чат

2. **📝 После каждой реализованной фичи:**
   - Написать что именно добавить в PROJECT_STATE.md
   - Формат: краткое описание + файлы + примеры использования

3. **📂 Работа с файлами:**
   - **Предпочтительно:** скидывать файлы прямо в чат (экономит токены в 2-3 раза vs web_fetch)
   - web_fetch использовать только если файл не предоставлен пользователем

4. **💬 Стиль кода и комментарии:**
   - **Максимально развёрнутые комментарии** — как для начинающего программиста
   - Объяснять ЧТО делает код, ЗАЧЕМ и КАК работает
   - Docstrings на **русском языке**
   - Примеры использования в комментариях

5. **✅ Тестирование:**
   - Писать тесты (pytest) **сразу** после реализации фичи
   - Убедиться что всё работает перед переходом к следующей задаче
   - Формат: `apps/{app}/tests/test_{feature}.py`

---

## Информация о проекте

**Репозиторий:** https://github.com/SubHunt/vendaro  
**Дата создания:** 05.10.2025  
**Последнее обновление:** 10.10.2025  
**Статус:** Backend API готов, варианты товаров реализованы, переходим на фронтенд

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

```python
# ❌ ПЛОХО - конфигурация в коде
CATEGORIES = ['Masks', 'Fins', 'Wetsuits']

# ✅ ХОРОШО - конфигурация в БД
Category.objects.filter(store=deepreef)
```

### Этапы развития

**Этап 1 (текущий): Фундамент Vendaro + DeepReef (2-3 недели)**
- ✅ Backend API (Django + DRF) — готово
- ✅ Multi-tenant архитектура — готово
- ✅ Варианты товаров (размеры) — готово
- 🔄 Frontend (Next.js 15 + Tailwind + shadcn/ui) — в процессе
- 🔄 Тема DeepReef (цвета, логотип, категории)

**Этап 2: Обратная связь от DeepReef (1-2 месяца)**
- Запуск deepreef.ru в продакшен
- Получение обратной связи от клиентов
- Добавление необходимых функций (универсально!)

**Этап 3: Документация и универсализация (1 неделя)**
- Документация "Как создать свой магазин"
- Второй магазин-пример
- Админ-панель для создания магазинов

**Этап 4: Открытие Vendaro (1-2 недели)**
- Лендинг vendaro.ru
- Видео-туториалы
- DeepReef как showcase

---

## Что полностью реализовано

### 1. Структура проекта

```
vendaro/
├── backend/
│   ├── apps/
│   │   ├── accounts/      # Пользователи, JWT auth
│   │   ├── cart/          # Корзина покупок
│   │   ├── cms/           # Статические страницы, блог
│   │   ├── core/          # Базовые модели, middleware
│   │   ├── orders/        # Заказы
│   │   ├── payments/      # Платежи (без онлайн-оплаты)
│   │   ├── products/      # Каталог товаров + ВАРИАНТЫ
│   │   └── stores/        # Multi-tenant магазины
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   └── development.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── manage.py
│
├── frontend/              # Next.js 15 (планируется)
│   ├── src/
│   │   ├── app/          # App Router
│   │   ├── components/   # React компоненты
│   │   ├── lib/          # Утилиты
│   │   └── themes/       # Темы магазинов
│   │       ├── default/  # Базовая тема
│   │       └── deepreef/ # Тема DeepReef
│   └── public/
│
├── docs/
│   ├── SETUP.md          # Создание магазина
│   ├── API.md            # API документация
│   └── DEPLOYMENT.md     # Деплой
│
└── examples/
    └── deepreef/         # Конфигурация DeepReef
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
- `Product` - товары (B2C/B2B цены, поддержка вариантов)
- `Size` - **НОВОЕ:** справочник размеров (одежда, обувь, диапазоны)
- `ProductVariant` - **НОВОЕ:** варианты товара (размеры + stock + цены)
- `ProductImage` - фотографии товаров
- `ProductReview` - отзывы

#### cart
- `Cart` - корзина (для авторизованных и анонимов)
- `CartItem` - товары в корзине (**обновлено:** поддержка вариантов)

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
- `GET /api/products/{slug}/` - детали товара (**обновлено:** включает варианты)
- `GET /api/products/{slug}/reviews/` - отзывы товара
- `POST /api/products/{slug}/add_review/` - добавить отзыв
- `GET /api/products/categories/` - категории
- `GET /api/products/categories/tree/` - дерево категорий

**Фильтры:**
- `?category=slug` - по категории
- `?min_price=1000&max_price=10000` - по цене
- `?search=маска` - поиск
- `?ordering=-created` - сортировка

#### Cart API (**обновлено**)
- `GET /api/cart/` - получить корзину (включает информацию о вариантах)
- `POST /api/cart/add/` - добавить товар (**новый параметр:** `variant_id`)
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
- Инлайны настроены (товары с фото, заказы с товарами, **варианты товаров**)
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

**НОВОЕ:** Команда для загрузки размеров: `python manage.py load_sizes`

### 8. Тесты (pytest)

**Установлено:** pytest, pytest-django, pytest-cov, factory-boy, faker

**Файлы:**
- `backend/conftest.py` - общие фикстуры (store, user, product, api_client)
- `backend/pytest.ini` - конфигурация
- `apps/products/tests/test_models.py` - тесты моделей
- `apps/products/tests/test_api.py` - тесты API

**Запуск:** `pytest -v` или `pytest --cov` (с покрытием)

**Результаты:** 15 тестов, покрытие ~72% кода

**Примечание:** Debug Toolbar отключён в development.py для тестов

### 9. Permissions (права доступа)

**Файл:** `apps/core/permissions.py`

**Классы:**
- `IsOwnerOrReadOnly` - редактирование только владельцем объекта
- `IsStoreOwnerOrReadOnly` - редактирование только владельцем магазина  
- `IsStaffOrOwner` - доступ staff или владельцу
- `ReadOnly` - только чтение

**Применение:** `permission_classes = [IsOwnerOrReadOnly]` в ViewSet

### 10. Продвинутые фильтры для Products API

**Файл:** `apps/products/filters.py`  
**Класс:** `ProductFilter` (django-filters)

**Доступные фильтры:**
- `?min_price=1000&max_price=5000` - по цене
- `?in_stock=true` - только в наличии
- `?min_rating=4` - по рейтингу (от 1 до 5)
- `?category=1` - по конкретной категории
- `?category_tree=1` - по категории включая подкатегории
- `?search=маска` - полнотекстовый поиск
- `?ordering=-created` - сортировка (created, price, rating, sales_count)

**Применение:** `filterset_class = ProductFilter` в ProductViewSet

### 11. API Документация (Swagger)

**Библиотека:** drf-spectacular

**URL:** 
- http://localhost:8000/api/docs/ - интерактивная документация
- http://localhost:8000/api/schema/ - OpenAPI схема (JSON)

**Настройки в base.py:**
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Vendaro CMS API',
    'DESCRIPTION': 'Multi-tenant E-commerce Platform API',
    'VERSION': '1.0.0',
}
```

**Возможности:**
- Автогенерация из serializers и views
- Интерактивное тестирование API
- Описание всех endpoints с примерами
- Экспорт схемы

### 12. Дополнительные функции

#### Slug транслитерация
- Автоматическая транслитерация кириллицы в латиницу
- "Маска Cressi" → "maska-cressi"
- Библиотека: `transliterate`

#### Stock management
- Автоуменьшение stock при создании заказа (в serializer)
- Проверка наличия при добавлении в корзину
- **НОВОЕ:** Поддержка stock для вариантов товаров

#### B2B/B2C цены
- Пользователь с `is_wholesale=True` видит оптовые цены
- Если у товара нет `wholesale_price`, применяется скидка магазина
- Метод `Product.get_price_for_user(user)` возвращает правильную цену
- **НОВОЕ:** Варианты товаров поддерживают переопределение цен

#### Корзина для анонимов
- Анонимные пользователи имеют корзину через session_key
- При входе можно объединить корзины (метод `Cart.merge_with()`)
- **НОВОЕ:** Поддержка вариантов товаров в корзине

---

## ✅ ВАРИАНТЫ ТОВАРОВ (Product Variants) — 10.10.2025

**Статус:** ✅ Реализовано и готово к использованию

### Что добавлено

#### 1. Новые модели (products/models.py)

**Size** — справочник размеров
- Типы размеров:
  - `clothing`: XXS, XS, S, M, L, XL, XXL, XXXL, XXXXL (9 размеров)
  - `footwear`: 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46 (11 размеров)
  - `range`: 36-37, 38-39, 40-41, 42-43, 44-45 (5 диапазонов)
- Поля: `type`, `value`, `order`, `is_active`
- Загружается командой: `python manage.py load_sizes` (25 размеров)

**ProductVariant** — варианты товара (торговые предложения)
- Связь: Product + Size = уникальный вариант
- Свой `stock` для каждого размера
- Опциональные `price_override` и `wholesale_price_override`
- SKU и barcode для варианта
- Счётчик `sales_count`
- Методы: `get_retail_price()`, `get_wholesale_price()`, `get_price_for_user()`, `is_in_stock()`

**Product.has_variants** — новое поле
- `True` = товар имеет варианты (размеры)
- `False` = обычный товар без вариантов
- Новые методы: `get_total_stock()`, `get_available_sizes()`

#### 2. Обновлена корзина (cart/models.py)

**CartItem.variant** — новое поле
- FK на ProductVariant (nullable)
- `NULL` = обычный товар без варианта
- Указано = товар с выбранным размером

**Уникальность:** `(cart, product, variant)`
- Один и тот же товар с разными размерами = разные позиции в корзине

**Новые методы:**
- `get_available_stock()` - возвращает stock товара или варианта
- `is_available()` - проверяет доступность товара/варианта для заказа

#### 3. API изменения

**GET /api/products/{slug}/** — добавлено:
```json
{
  "has_variants": true,
  "variants": [
    {
      "id": 1,
      "size": {"value": "M", "type": "clothing"},
      "stock": 10,
      "price": 15000.00,
      "wholesale_price": 12500.00,
      "is_in_stock": true
    }
  ],
  "total_stock": 25,
  "variants_count": 4,
  "available_sizes": ["S", "M", "L", "XL"]
}
```

**POST /api/cart/add/** — новый параметр:
```json
{
  "product_id": 1,
  "variant_id": 2,  // НОВОЕ: ID варианта (размера), опционально
  "quantity": 1
}
```

**GET /api/cart/** — добавлено:
```json
{
  "items": [
    {
      "product": {...},
      "variant": {  // НОВОЕ
        "id": 2,
        "size_value": "M",
        "size_type": "clothing",
        "stock": 10,
        "sku": "WETSUIT-5MM-M"
      },
      "available_stock": 10,
      "is_available": true
    }
  ]
}
```

#### 4. Админка (products/admin.py)

**Size Admin** — управление размерами
- Список всех размеров с фильтрами по типу
- Массовые действия: активировать/деактивировать

**ProductVariant Inline** — в карточке товара
- Добавление вариантов прямо при создании товара
- Autocomplete для выбора размера
- Отображение stock, цен, SKU
- Показывает количество вариантов в списке товаров

**ProductVariant Admin** — отдельная админка
- Управление всеми вариантами
- Фильтры по товару, размеру, наличию
- Массовые действия: активировать/деактивировать, сбросить цены

**Product Admin** — обновлено
- Новое поле: "Имеет варианты" с описанием
- Инлайн для добавления вариантов
- Отображение: ✓ 4 шт. (количество вариантов)
- Stock display: показывает общий stock и количество вариантов в наличии

#### 5. Сериализаторы (обновлены)

**products/serializers.py:**
- `SizeSerializer` - размеры
- `ProductVariantSerializer` - варианты для API
- `ProductVariantDetailSerializer` - детальная информация о варианте
- `ProductListSerializer` - добавлены поля вариантов
- `ProductDetailSerializer` - включает список вариантов

**cart/serializers.py:**
- `CartItemVariantSerializer` - информация о варианте в корзине
- `CartItemSerializer` - поддержка `variant_id`
- `AddToCartSerializer` - валидация варианта
- `UpdateCartItemSerializer` - проверка stock варианта

**Валидация:**
- Проверка: товар с вариантами требует `variant_id`
- Проверка: товар без вариантов не должен иметь `variant_id`
- Проверка: вариант принадлежит товару
- Проверка: наличие на складе (товара или варианта)

#### 6. Команды управления

```bash
# Загрузить размеры в БД (25 размеров: одежда, обувь, диапазоны)
python manage.py load_sizes

# Создать миграции
python manage.py makemigrations products cart

# Применить миграции
python manage.py migrate
```

### Как использовать

#### Создание товара с размерами (Админка)

1. Откройте товар в админке: http://localhost:8000/admin/products/product/add/
2. Заполните основную информацию (название, категория, цена)
3. Поставьте галочку **✅ "Имеет варианты"**
4. Прокрутите вниз до раздела "Варианты товаров"
5. Добавьте размеры (нажмите "Добавить ещё"):
   ```
   Размер: S    | Stock: 5  | Активен: ✅
   Размер: M    | Stock: 10 | Активен: ✅
   Размер: L    | Stock: 3  | Активен: ✅
   Размер: XL   | Stock: 7  | Активен: ✅
   ```
6. Сохраните товар

#### API примеры

**Добавить товар с размером в корзину:**
```bash
POST /api/cart/add/
{
  "product_id": 1,
  "variant_id": 2,
  "quantity": 1
}
```

**Добавить обычный товар (без размера):**
```bash
POST /api/cart/add/
{
  "product_id": 5,
  "quantity": 1
}
```

**Получить товар с вариантами:**
```bash
GET /api/products/gidrokostyum-cressi-5mm/
```

### Валидация и ошибки

**Товар требует размер:**
```json
{
  "variant_id": ["Для этого товара необходимо выбрать размер"]
}
```

**Недостаточно на складе:**
```json
{
  "quantity": ["Недостаточно товара на складе. Доступно: 10"]
}
```

**Вариант не принадлежит товару:**
```json
{
  "variant_id": ["Этот вариант не принадлежит выбранному товару"]
}
```

### Совместимость

✅ **Старые товары без вариантов** работают как раньше:
- `has_variants = False`
- `variant = NULL` в корзине
- Stock управляется через `Product.stock`

✅ **Корзина** поддерживает оба типа:
- Обычные товары: `variant = NULL`
- Товары с размерами: `variant = ProductVariant`

### Файлы изменены/добавлены

**Модели:**
- ✅ `apps/products/models.py` - Size, ProductVariant, обновлён Product
- ✅ `apps/cart/models.py` - добавлено поле variant в CartItem

**Сериализаторы:**
- ✅ `apps/products/serializers.py` - API для вариантов
- ✅ `apps/cart/serializers.py` - поддержка вариантов

**Админка:**
- ✅ `apps/products/admin.py` - Size, ProductVariant, обновлён ProductAdmin

**Команды:**
- ✅ `apps/products/management/commands/load_sizes.py` - новая команда

**Миграции:**
- ✅ `apps/products/migrations/000X_add_variants.py` - Size, ProductVariant
- ✅ `apps/cart/migrations/000X_add_variant.py` - CartItem.variant

### Структура БД

```
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
├── sku
├── barcode
├── is_active
├── sales_count
├── created
└── updated

cart_cartitem (обновлена)
├── id
├── cart_id
├── product_id
├── variant_id → ProductVariant (nullable, НОВОЕ)
├── quantity
├── price
├── is_wholesale
├── created
└── updated
```

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

###
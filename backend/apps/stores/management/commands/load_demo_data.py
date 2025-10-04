"""
Management команда для загрузки демо-данных в Vendaro CMS

Использование:
python manage.py load_demo_data

Создаёт:
- Магазин DeepReef
- Категории товаров
- Товары для дайвинга
- Тестового пользователя
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.stores.models import Store, StoreSettings
from apps.products.models import Category, Product
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Загружает демо-данные для магазина DeepReef'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            'Начинаем загрузку демо-данных...'))

        # 1. Создаём владельца магазина
        owner = self.create_owner()

        # 2. Создаём магазин DeepReef
        store = self.create_store(owner)

        # 3. Создаём категории
        categories = self.create_categories(store)

        # 4. Создаём товары
        self.create_products(store, categories)

        # 5. Создаём тестового оптовика
        self.create_wholesale_user(store)

        self.stdout.write(self.style.SUCCESS(
            '✅ Демо-данные успешно загружены!'))
        self.stdout.write(self.style.SUCCESS(f'Магазин: {store.domain}'))
        self.stdout.write(self.style.SUCCESS(
            'Владелец: owner@deepreef.ru / password123'))
        self.stdout.write(self.style.SUCCESS(
            'Оптовик: wholesale@company.com / password123'))

    def create_owner(self):
        """Создаёт владельца магазина"""
        owner, created = User.objects.get_or_create(
            email='owner@deepreef.ru',
            defaults={
                'first_name': 'Владимир',
                'last_name': 'Морской',
                'is_staff': True,
            }
        )
        if created:
            owner.set_password('password123')
            owner.save()
            self.stdout.write(self.style.SUCCESS('✓ Владелец магазина создан'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Владелец уже существует'))
        return owner

    def create_store(self, owner):
        """Создаёт магазин DeepReef"""
        store, created = Store.objects.get_or_create(
            domain='deepreef.local',
            defaults={
                'name': 'DeepReef',
                'slug': 'deepreef',
                'description': 'Снаряжение для дайвинга, подводной охоты и фридайвинга',
                'email': 'info@deepreef.ru',
                'phone': '+7 (495) 123-45-67',
                'address': 'ул. Морская, д. 15',
                'city': 'Москва',
                'postal_code': '101000',
                'country': 'RU',
                'primary_color': '#0A2463',
                'secondary_color': '#14B8A6',
                'enable_wholesale': True,
                'wholesale_discount_percent': Decimal('15.00'),
                'min_wholesale_order': Decimal('50000.00'),
                'currency': 'RUB',
                'currency_symbol': '₽',
                'is_active': True,
                'owner': owner,
                'meta_title': 'DeepReef - Снаряжение для дайвинга',
                'meta_description': 'Магазин профессионального снаряжения для дайвинга, подводной охоты и фридайвинга',
            }
        )

        if created:
            # Создаём настройки магазина
            StoreSettings.objects.create(
                store=store,
                enable_free_shipping=True,
                free_shipping_threshold=Decimal('5000.00'),
                shipping_cost=Decimal('500.00'),
                min_order_amount=Decimal('1000.00'),
                tax_rate=Decimal('20.00'),
                tax_included=True,
                order_notification_email='orders@deepreef.ru',
            )
            self.stdout.write(self.style.SUCCESS('✓ Магазин DeepReef создан'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Магазин уже существует'))

        return store

    def create_categories(self, store):
        """Создаёт категории товаров"""
        categories = {}

        # Корневые категории
        diving, _ = Category.objects.get_or_create(
            store=store,
            slug='diving',
            defaults={
                'name': 'Дайвинг',
                'description': 'Снаряжение для дайвинга',
                'order': 1,
            }
        )
        categories['diving'] = diving

        spearfishing, _ = Category.objects.get_or_create(
            store=store,
            slug='spearfishing',
            defaults={
                'name': 'Подводная охота',
                'description': 'Снаряжение для подводной охоты',
                'order': 2,
            }
        )
        categories['spearfishing'] = spearfishing

        freediving, _ = Category.objects.get_or_create(
            store=store,
            slug='freediving',
            defaults={
                'name': 'Фридайвинг',
                'description': 'Снаряжение для фридайвинга',
                'order': 3,
            }
        )
        categories['freediving'] = freediving

        # Подкатегории дайвинга
        masks, _ = Category.objects.get_or_create(
            store=store,
            slug='diving-masks',
            defaults={
                'name': 'Маски',
                'parent': diving,
                'order': 1,
            }
        )
        categories['masks'] = masks

        fins, _ = Category.objects.get_or_create(
            store=store,
            slug='diving-fins',
            defaults={
                'name': 'Ласты',
                'parent': diving,
                'order': 2,
            }
        )
        categories['fins'] = fins

        wetsuits, _ = Category.objects.get_or_create(
            store=store,
            slug='wetsuits',
            defaults={
                'name': 'Гидрокостюмы',
                'parent': diving,
                'order': 3,
            }
        )
        categories['wetsuits'] = wetsuits

        self.stdout.write(self.style.SUCCESS('✓ Категории созданы'))
        return categories

    def create_products(self, store, categories):
        """Создаёт товары"""
        products_data = [
            # Маски
            {
                'name': 'Маска Cressi Big Eyes Evolution',
                'category': categories['masks'],
                'retail_price': Decimal('8900.00'),
                'wholesale_price': Decimal('7500.00'),
                'stock': 25,
                'description': 'Профессиональная маска для дайвинга с широким обзором. Закалённые стёкла, силиконовый обтюратор.',
                'short_description': 'Маска с широким обзором',
                'sku': 'MASK-001',
                'specifications': {
                    'Бренд': 'Cressi',
                    'Материал': 'Силикон',
                    'Цвет': 'Чёрный',
                    'Тип стекла': 'Закалённое',
                }
            },
            {
                'name': 'Маска Mares X-Vision Ultra',
                'category': categories['masks'],
                'retail_price': Decimal('12500.00'),
                'wholesale_price': Decimal('10500.00'),
                'stock': 15,
                'description': 'Топовая маска с технологией X-Vision для максимального обзора.',
                'short_description': 'Топовая маска с панорамным обзором',
                'sku': 'MASK-002',
            },

            # Ласты
            {
                'name': 'Ласты Mares Avanti Quattro Plus',
                'category': categories['fins'],
                'retail_price': Decimal('7900.00'),
                'wholesale_price': Decimal('6700.00'),
                'stock': 30,
                'description': 'Универсальные ласты для дайвинга. Технология четырёх каналов для эффективного движения.',
                'short_description': 'Универсальные ласты для дайвинга',
                'sku': 'FINS-001',
                'specifications': {
                    'Бренд': 'Mares',
                    'Размер': '40-41',
                    'Цвет': 'Синий',
                }
            },
            {
                'name': 'Ласты Cressi Frog Plus',
                'category': categories['fins'],
                'retail_price': Decimal('6500.00'),
                'stock': 20,
                'description': 'Лёгкие и эффективные ласты с открытой пяткой.',
                'short_description': 'Лёгкие ласты с открытой пяткой',
                'sku': 'FINS-002',
            },

            # Гидрокостюмы
            {
                'name': 'Гидрокостюм Mares Flexa 5.4.3',
                'category': categories['wetsuits'],
                'retail_price': Decimal('24900.00'),
                'wholesale_price': Decimal('21000.00'),
                'stock': 10,
                'description': 'Гидрокостюм 5мм для холодной воды. Технология Flexa для максимальной гибкости.',
                'short_description': 'Гидрокостюм 5мм для холодной воды',
                'sku': 'SUIT-001',
                'specifications': {
                    'Бренд': 'Mares',
                    'Толщина': '5мм',
                    'Размер': 'L',
                    'Пол': 'Унисекс',
                }
            },
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                store=store,
                sku=product_data['sku'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'  ✓ {product.name}')

        self.stdout.write(self.style.SUCCESS(
            f'✓ Создано {len(products_data)} товаров'))

    def create_wholesale_user(self, store):
        """Создаёт тестового оптовика"""
        wholesale_user, created = User.objects.get_or_create(
            email='wholesale@company.com',
            defaults={
                'first_name': 'Оптовый',
                'last_name': 'Клиент',
                'is_wholesale': True,
                'company_name': 'ООО "Морские товары"',
                'company_tax_id': '1234567890',
                'store': store,
            }
        )
        if created:
            wholesale_user.set_password('password123')
            wholesale_user.save()
            self.stdout.write(self.style.SUCCESS('✓ Оптовый клиент создан'))
        else:
            self.stdout.write(self.style.WARNING(
                '⚠ Оптовый клиент уже существует'))

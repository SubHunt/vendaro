"""
apps/products/management/commands/load_sizes.py

Команда для загрузки размеров в базу данных.

Использование:
python manage.py load_sizes
"""

from django.core.management.base import BaseCommand
from apps.products.models import Size


class Command(BaseCommand):
    help = 'Загружает размеры для товаров в базу данных'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка размеров...\n')

        # ========================================
        # РАЗМЕРЫ ОДЕЖДЫ (XXS - XXXXL)
        # ========================================

        clothing_sizes = [
            ('XXS', 10),
            ('XS', 20),
            ('S', 30),
            ('M', 40),
            ('L', 50),
            ('XL', 60),
            ('XXL', 70),
            ('XXXL', 80),
            ('XXXXL', 90),
        ]

        self.stdout.write('• Одежда (XXS-XXXXL)...')
        clothing_count = 0

        for value, order in clothing_sizes:
            size, created = Size.objects.get_or_create(
                type='clothing',
                value=value,
                defaults={'order': order, 'is_active': True}
            )
            if created:
                clothing_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Создано: {clothing_count}'))

        # ========================================
        # РАЗМЕРЫ ОБУВИ (36-46)
        # ========================================

        footwear_sizes = [
            ('36', 360),
            ('37', 370),
            ('38', 380),
            ('39', 390),
            ('40', 400),
            ('41', 410),
            ('42', 420),
            ('43', 430),
            ('44', 440),
            ('45', 450),
            ('46', 460),
        ]

        self.stdout.write('• Обувь (36-46)...')
        footwear_count = 0

        for value, order in footwear_sizes:
            size, created = Size.objects.get_or_create(
                type='footwear',
                value=value,
                defaults={'order': order, 'is_active': True}
            )
            if created:
                footwear_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Создано: {footwear_count}'))

        # ========================================
        # ДИАПАЗОНЫ РАЗМЕРОВ (36-37, 38-39, ...)
        # ========================================

        range_sizes = [
            ('36-37', 3637),
            ('38-39', 3839),
            ('40-41', 4041),
            ('42-43', 4243),
            ('44-45', 4445),
        ]

        self.stdout.write('• Диапазоны (36-37, 38-39, ...)...')
        range_count = 0

        for value, order in range_sizes:
            size, created = Size.objects.get_or_create(
                type='range',
                value=value,
                defaults={'order': order, 'is_active': True}
            )
            if created:
                range_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Создано: {range_count}'))

        # ========================================
        # ИТОГО
        # ========================================

        total_created = clothing_count + footwear_count + range_count
        total_sizes = Size.objects.count()

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'✓ Загрузка завершена!'))
        self.stdout.write(f'  Создано новых: {total_created}')
        self.stdout.write(f'  Всего в базе: {total_sizes}')
        self.stdout.write('='*50 + '\n')

        # Показываем примеры
        self.stdout.write('Примеры размеров:')
        self.stdout.write(
            '  Одежда: ' + ', '.join([s.value for s in Size.objects.filter(type='clothing')[:5]]))
        self.stdout.write(
            '  Обувь: ' + ', '.join([s.value for s in Size.objects.filter(type='footwear')[:5]]))
        self.stdout.write(
            '  Диапазоны: ' + ', '.join([s.value for s in Size.objects.filter(type='range')[:5]]))

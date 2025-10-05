"""
apps/products/signals.py — Сигналы для автоматического обновления данных товаров

Сигналы в Django - это события которые срабатывают автоматически.
Например: после создания отзыва -> пересчитать рейтинг товара.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ProductReview


@receiver(post_save, sender=ProductReview)
def update_product_rating_on_review_save(sender, instance, created, **kwargs):
    """
    Обновляет рейтинг товара после добавления/изменения отзыва.

    Срабатывает:
    - После создания нового отзыва
    - После изменения существующего отзыва

    Что делает:
    1. Считает средний рейтинг из всех одобренных отзывов
    2. Обновляет поля rating и reviews_count у товара
    """
    product = instance.product

    # Получаем только одобренные отзывы
    approved_reviews = product.reviews.filter(is_approved=True)

    # Подсчитываем количество отзывов
    reviews_count = approved_reviews.count()

    if reviews_count > 0:
        # Вычисляем средний рейтинг
        # Sum всех оценок / количество отзывов
        from django.db.models import Avg
        avg_rating = approved_reviews.aggregate(Avg('rating'))['rating__avg']

        # Обновляем товар
        product.rating = round(avg_rating, 2)
        product.reviews_count = reviews_count
    else:
        # Нет отзывов - сбрасываем рейтинг
        product.rating = 0
        product.reviews_count = 0

    product.save(update_fields=['rating', 'reviews_count'])


@receiver(post_delete, sender=ProductReview)
def update_product_rating_on_review_delete(sender, instance, **kwargs):
    """
    Обновляет рейтинг товара после удаления отзыва.

    Срабатывает:
    - После удаления отзыва
    """
    product = instance.product

    # Получаем оставшиеся одобренные отзывы
    approved_reviews = product.reviews.filter(is_approved=True)
    reviews_count = approved_reviews.count()

    if reviews_count > 0:
        from django.db.models import Avg
        avg_rating = approved_reviews.aggregate(Avg('rating'))['rating__avg']
        product.rating = round(avg_rating, 2)
        product.reviews_count = reviews_count
    else:
        product.rating = 0
        product.reviews_count = 0

    product.save(update_fields=['rating', 'reviews_count'])

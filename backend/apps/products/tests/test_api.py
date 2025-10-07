"""
apps/products/tests/test_api.py — Тесты для Products API
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestProductsAPI:
    """Тесты Products API endpoints"""

    def test_get_products_list(self, api_client, store, product):
        """Тест получения списка товаров"""
        # Устанавливаем store в request через middleware simulation
        api_client.defaults['HTTP_HOST'] = store.domain

        response = api_client.get('/api/products/')

        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Product'

    def test_get_product_detail(self, api_client, store, product):
        """Тест получения детальной информации о товаре"""
        api_client.defaults['HTTP_HOST'] = store.domain

        response = api_client.get(f'/api/products/{product.slug}/')

        assert response.status_code == 200
        assert response.data['name'] == 'Test Product'
        assert response.data['retail_price'] == '1000.00'

    def test_filter_products_by_category(self, api_client, store, product, category):
        """Тест фильтрации товаров по категории"""
        api_client.defaults['HTTP_HOST'] = store.domain

        response = api_client.get(f'/api/products/?category={category.id}')

        assert response.status_code == 200
        assert len(response.data['results']) == 1

    def test_search_products(self, api_client, store, product):
        """Тест поиска товаров"""
        api_client.defaults['HTTP_HOST'] = store.domain

        response = api_client.get('/api/products/?search=Test')

        assert response.status_code == 200
        assert len(response.data['results']) == 1


@pytest.mark.django_db
class TestCategoriesAPI:
    """Тесты Categories API"""

    def test_get_categories(self, api_client, store, category):
        """Тест получения списка категорий"""
        api_client.defaults['HTTP_HOST'] = store.domain

        response = api_client.get('/api/products/categories/')

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        # assert len(response.data) == 1
        # assert response.data[0]['name'] == 'Test Category'

    def test_get_categories_tree(self, api_client, store, category):
        """Тест получения дерева категорий"""
        api_client.defaults['HTTP_HOST'] = store.domain

        response = api_client.get('/api/products/categories/tree/')

        assert response.status_code == 200
        assert len(response.data) == 1

# apps/core/urls.py
"""
Главный роутер для всех API endpoints
"""
from django.urls import path, include
from django.http import JsonResponse

app_name = 'api'


def api_root(request):
    """Корневой endpoint API"""
    return JsonResponse({
        'message': 'Vendaro CMS API',
        'store': request.store.name if hasattr(request, 'store') and request.store else None,
        'version': '1.0.0',
        'endpoints': {
            'products': '/api/products/',
            'categories': '/api/products/categories/',
            'cart': '/api/cart/',
            'orders': '/api/orders/',
            'auth': '/api/auth/',
            'payments': '/api/payments/',
            'cms': '/api/cms/',
        }
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('products/', include('apps.products.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('auth/', include('apps.accounts.urls')),
    path('payments/', include('apps.payments.urls')),
    path('cms/', include('apps.cms.urls')),
]

# def api_root(request):
#     """Корневой endpoint API"""
#     return JsonResponse({
#         'message': 'Vendaro CMS API',
#         'store': request.store.name if hasattr(request, 'store') and request.store else None,
#         'version': '1.0.0',
#         'endpoints': {
#             'products': '/api/products/',
#             'categories': '/api/products/categories/',
#             'cart': '/api/cart/',
#             'orders': '/api/orders/',
#             'auth': '/api/auth/',
#         }
#     })


# urlpatterns = [
#     path('', api_root, name='api-root'),
#     path('products/', include('apps.products.urls')),
#     path('cart/', include('apps.cart.urls')),
#     path('orders/', include('apps.orders.urls')),
#     path('auth/', include('apps.accounts.urls')),
# ]
# # apps/core/urls.py
# """
# Главный роутер для всех API endpoints
# """
# from django.urls import path, include
# from django.http import JsonResponse

# app_name = 'api'


# def api_root(request):
#     """Корневой endpoint API - показывает список доступных endpoints"""
#     return JsonResponse({
#         'message': 'Vendaro CMS API',
#         'store': request.store.name if hasattr(request, 'store') and request.store else None,
#         'version': '1.0.0',
#         'endpoints': {
#             'products': '/api/products/',
#             'categories': '/api/products/categories/',
#             # Добавим позже:
#             # 'cart': '/api/cart/',
#             # 'orders': '/api/orders/',
#             # 'auth': '/api/auth/',
#         }
#     })


# urlpatterns = [
#     # Корневой endpoint
#     path('', api_root, name='api-root'),

#     # Products API
#     path('products/', include('apps.products.urls')),

#     # Когда создадите другие urls.py, раскомментируйте:
#     # path('cart/', include('apps.cart.urls')),
#     # path('orders/', include('apps.orders.urls')),
#     # path('accounts/', include('apps.accounts.urls')),
# ]

"""
apps/accounts/urls.py — URL маршруты для Auth API
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Регистрация и вход
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),

    # JWT токены
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Профиль
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update-profile'),

    # Смена пароля
    path('change-password/', views.change_password, name='change-password'),
]

"""
apps/accounts/admin.py — Регистрация моделей пользователей в Django Admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserAddress


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для кастомной модели User"""

    # Колонки в списке пользователей
    list_display = ['email', 'first_name', 'last_name',
                    'is_wholesale', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser',
                   'is_active', 'is_wholesale', 'date_joined']
    search_fields = ['email', 'first_name',
                     'last_name', 'company_name', 'phone']
    ordering = ['-date_joined']

    # Поля в форме редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name',
         'last_name', 'phone', 'avatar', 'date_of_birth')}),
        (_('B2B Info'), {'fields': ('is_wholesale',
         'company_name', 'company_tax_id', 'store')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Поля при создании нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    """Админка для адресов пользователей"""

    list_display = ['user', 'label', 'city', 'is_default', 'created']
    list_filter = ['is_default', 'country', 'created']
    search_fields = ['user__email', 'city', 'address_line1', 'phone']
    ordering = ['-created']

    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Address Info'), {
         'fields': ('label', 'first_name', 'last_name', 'phone')}),
        (_('Address'), {'fields': ('address_line1',
         'address_line2', 'city', 'postal_code', 'country')}),
        (_('Settings'), {'fields': ('is_default',)}),
    )

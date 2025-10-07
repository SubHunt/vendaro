"""
apps/core/permissions.py — Кастомные permissions для Vendaro CMS
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только владельцу объекта.

    Использование:
    class MyViewSet(viewsets.ModelViewSet):
        permission_classes = [IsOwnerOrReadOnly]
    """

    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Редактирование только владельцу
        return obj.user == request.user


class IsStoreOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только владельцу магазина.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для объектов с полем store
        if hasattr(obj, 'store'):
            return obj.store.owner == request.user

        # Для самого Store
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False


class IsStaffOrOwner(permissions.BasePermission):
    """
    Разрешает доступ staff пользователям или владельцу объекта.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff может всё
        if request.user.is_staff:
            return True

        # Владелец объекта
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class ReadOnly(permissions.BasePermission):
    """
    Разрешает только чтение.
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

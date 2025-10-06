"""
apps/accounts/views.py — Views для Auth API
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Регистрация нового пользователя.

    POST /api/auth/register/
    Body: {
        "email": "user@example.com",
        "password": "securepass123",
        "password2": "securepass123",
        "first_name": "Иван",
        "last_name": "Петров",
        "phone": "+79001234567"
    }

    Возвращает:
    - Данные пользователя
    - JWT токены (access и refresh)
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()

    # Генерируем JWT токены
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Вход пользователя (получение JWT токенов).

    POST /api/auth/login/
    Body: {
        "email": "user@example.com",
        "password": "securepass123"
    }

    Возвращает:
    - Данные пользователя
    - JWT токены (access и refresh)
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    # Проверяем email и пароль
    user = authenticate(request, username=email, password=password)

    if user is None:
        return Response(
            {'error': 'Неверный email или пароль'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Аккаунт деактивирован'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Генерируем JWT токены
    refresh = RefreshToken.for_user(user)

    return Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Получение профиля текущего пользователя.

    GET /api/auth/profile/
    Headers: Authorization: Bearer <access_token>

    Возвращает данные пользователя.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Обновление профиля текущего пользователя.

    PUT/PATCH /api/auth/profile/update/
    Headers: Authorization: Bearer <access_token>
    Body: {
        "first_name": "Новое имя",
        "phone": "+79009999999"
    }
    """
    serializer = UserSerializer(
        request.user,
        data=request.data,
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Смена пароля.

    POST /api/auth/change-password/
    Headers: Authorization: Bearer <access_token>
    Body: {
        "old_password": "oldpass123",
        "new_password": "newpass123",
        "new_password2": "newpass123"
    }
    """
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({
        'message': 'Пароль успешно изменён'
    })

import re

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import SlugRelatedField
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from reviews.models import (
    EMAIL_LENGTH, USERNAME_LENGTH, Category,
    Genre, Review, ReviewComment, Title, User,
)
from api_yamdb.settings import DEFAULT_FROM_EMAIL
from django.db import IntegrityError


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователей."""

    username = serializers.CharField(
        required=True,
        max_length=USERNAME_LENGTH,
    )
    email = serializers.EmailField(required=True, max_length=EMAIL_LENGTH)

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя должно содержать только',
                'буквы, цифры и подчеркивания.'
            )
        return value

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Пользователь с таким именем пользователя уже существует.'
            )

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует.'
            )
        return data

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )


class UserDisplaySerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role'
        )


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, max_length=USERNAME_LENGTH)
    email = serializers.EmailField(required=True, max_length=EMAIL_LENGTH)
    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя должно содержать только буквы, цифры и подчеркивания.'
            )
        if value == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" недопустимо.'
            )
        return value

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        try:
            user, _ = User.objects.get_or_create(username=username, email=email)
        except IntegrityError:
            raise serializers.ValidationError(
                'Имя пользователя или email уже используются.'
            )
        confirmation_code = default_token_generator.make_token(user)
        send_mail(
            subject='Код подтверждения',
            message=f'Ваш код подтверждения: {confirmation_code}',
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[user.email]
        )
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        try:
            instance.save()
        except IntegrityError:
            raise serializers.ValidationError(
                'Имя пользователя или email уже используются.'
            )
        return instance


class TokenSerializer(serializers.Serializer):
    """Сериализатор для получения токена."""

    username = serializers.CharField(required=True, max_length=USERNAME_LENGTH)
    confirmation_code = serializers.CharField(required=True)

    def validate_code(self, data):
        user = get_object_or_404(User, username=data['username'])
        if user.confirmation_code != data['confirmation_code']:
            raise serializers.ValidationError('Неверный код подтерждения')
        return RefreshToken.for_user(user).access_token

    class Meta:
        model = User
        fields = (
            'username',
            'confirmation_code'
        )

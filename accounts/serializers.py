from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from providers.models import ProviderProfile

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'role')
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    # Admins are never self-registered, so only these two roles are allowed here.
    role = serializers.ChoiceField(
        choices=[(User.Role.CUSTOMER, 'Customer'), (User.Role.PROVIDER, 'Service Provider')],
        default=User.Role.CUSTOMER,
    )

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'role')

    def validate(self, attrs):
        candidate = User(name=attrs.get('name', ''), email=attrs.get('email', ''))
        validate_password(attrs['password'], user=candidate)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        if user.role == User.Role.PROVIDER:
            ProviderProfile.objects.create(user=user)
        return user


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

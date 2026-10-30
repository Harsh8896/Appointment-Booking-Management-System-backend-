from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import User


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == User.Role.CUSTOMER)


class IsProvider(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == User.Role.PROVIDER)


class IsProviderOrReadOnly(BasePermission):
    """Anyone can read; only providers can write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.role == User.Role.PROVIDER)

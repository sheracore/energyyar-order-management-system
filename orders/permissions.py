from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin to access it.

    - Admin users have full access to all orders
    - Customer users can only access their own orders
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_admin:
            return True

        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True

        return obj.user == request.user

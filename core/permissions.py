from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):


    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsAdminOrReadOnly(permissions.BasePermission):


    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
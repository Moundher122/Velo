import rest_framework.permissions as permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read access to anyone, write access to admin/staff only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
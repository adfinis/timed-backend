from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated


class IsUnverified(BasePermission):
    """Allows access only to verified objects."""

    def has_object_permission(self, request, view, obj):
        return obj.verified_by_id is None


class IsReadOnly(BasePermission):
    """Allows read only methods."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsDeleteOnly(BasePermission):
    """Allows only delete method."""

    def has_permission(self, request, view):
        return request.method == "DELETE"

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsNotDelete(BasePermission):
    """Disallow delete method."""

    def has_permission(self, request, view):
        return request.method != "DELETE"

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsCreateOnly(BasePermission):
    """Allows only create method."""

    def has_permission(self, request, view):
        return request.method == "POST"

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsUpdateOnly(BasePermission):
    """Allows only update method."""

    def has_permission(self, request, view):
        return request.method in ["PATCH", "PUT"]

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsAuthenticated(IsAuthenticated):
    """
    Support mixing permission IsAuthenticated with object permission.

    This is needed to use IsAuthenticated with rest condition and or
    operator.
    """

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwner(IsAuthenticated):
    """Allows access to object only to owners."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class IsSupervisor(IsAuthenticated):
    """Allows access to object only to supervisors."""

    def has_object_permission(self, request, view, obj):
        return request.user.supervisees.filter(id=obj.user_id).exists()


class IsReviewer(IsAuthenticated):
    """Allows access to object only to reviewers."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.task.project.reviewers.filter(id=user.id).exists()


class IsSuperUser(BasePermission):
    """Allows access only to superuser."""

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsNotTransferred(BasePermission):
    """Allows access only to not transferred objects."""

    def has_object_permission(self, request, view, obj):
        return not obj.transferred

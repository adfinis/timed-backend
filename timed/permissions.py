# from django.utils import timezone
from datetime import date

from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated

from timed.employment import models as employment_models
from timed.projects import models as projects_models
from timed.tracking import models as tracking_models


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
        if not super().has_object_permission(request, view, obj):  # pragma: no cover
            return False

        return obj.user_id == request.user.id


class IsSupervisor(IsAuthenticated):
    """Allows access to object only to supervisors."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):  # pragma: no cover
            return False

        return request.user.supervisees.exists()

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):  # pragma: no cover
            return False

        return request.user.supervisees.filter(id=obj.user_id).exists()


class IsReviewer(IsAuthenticated):
    """Allows access to object only to reviewers."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):  # pragma: no cover
            return False

        return True

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):  # pragma: no cover
            return False

        user = request.user

        if isinstance(obj, tracking_models.Report):
            task = obj.task
        else:  # pragma: no cover
            raise RuntimeError("IsReviewer permission called on unsupported model")
        return (
            projects_models.Task.objects.filter(pk=task.pk)
            .filter(
                Q(task_assignees__user=user, task_assignees__is_reviewer=True)
                | Q(
                    project__project_assignees__user=user,
                    project__project_assignees__is_reviewer=True,
                )
                | Q(
                    project__customer__customer_assignees__user=user,
                    project__customer__customer_assignees__is_reviewer=True,
                )
            )
            .exists()
        )


class IsSuperUser(IsAuthenticated):
    """Allows access only to superuser."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):  # pragma: no cover
            return False

        return request.user.is_superuser

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsNotTransferred(BasePermission):
    """Allows access only to not transferred objects."""

    def has_object_permission(self, request, view, obj):
        return not obj.transferred


class IsNotBilledAndVerfied(BasePermission):
    """Allows access only to not billed and not verfied objects."""

    def has_object_permission(self, request, view, obj):
        return not obj.billed or obj.verified_by_id is None


class IsInternal(IsAuthenticated):
    """Allows access only to internal employees."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):  # pragma: no cover
            return False

        try:
            employment = employment_models.Employment.objects.get_at(
                user=request.user, date=date.today()
            )
            return not employment.is_external
        except employment_models.Employment.DoesNotExist:
            raise PermissionDenied("User has no employment")

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):  # pragma: no cover
            return False

        employment = employment_models.Employment.objects.get_at(
            user=request.user, date=date.today()
        )
        if employment:
            return not employment.is_external
        return False  # pragma: no cover


class IsExternal(IsAuthenticated):
    """Allows access only to external employees."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):  # pragma: no cover
            return False

        try:
            employment = employment_models.Employment.objects.get_at(
                user=request.user, date=date.today()
            )
            return employment.is_external
        except employment_models.Employment.DoesNotExist:  # pragma: no cover
            raise PermissionDenied("User has no employment")

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):  # pragma: no cover
            return False

        employment = employment_models.Employment.objects.get_at(
            user=request.user, date=date.today()
        )
        if employment:
            return employment.is_external
        return False  # pragma: no cover


class IsManager(IsAuthenticated):
    """Allows access only to assignees with manager role."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):  # pragma: no cover
            return False

        if (
            request.user.customer_assignees.filter(is_manager=True).exists()
            or request.user.project_assignees.filter(is_manager=True).exists()
            or request.user.task_assignees.filter(is_manager=True).exists()
        ):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):  # pragma: no cover
            return False

        user = request.user

        if isinstance(obj, projects_models.Task):
            return (
                projects_models.Task.objects.filter(pk=obj.pk)
                .filter(
                    Q(task_assignees__user=user, task_assignees__is_manager=True)
                    | Q(
                        project__project_assignees__user=user,
                        project__project_assignees__is_manager=True,
                    )
                    | Q(
                        project__customer__customer_assignees__user=user,
                        project__customer__customer_assignees__is_manager=True,
                    )
                )
                .exists()
            )
        else:  # pragma: no cover
            raise RuntimeError("IsManager permission called on unsupported model")


class IsResource(IsAuthenticated):
    """Allows access only to assignees with resource role."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):  # pragma: no cover
            return False

        if (
            request.user.customer_assignees.filter(is_resource=True).exists()
            or request.user.project_assignees.filter(is_resource=True).exists()
            or request.user.task_assignees.filter(is_resource=True).exists()
        ):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):  # pragma: no cover
            return False

        user = request.user

        if isinstance(obj, tracking_models.Activity) or isinstance(
            obj, tracking_models.Report
        ):
            task = obj.task
            task = obj.task
        else:  # pragma: no cover
            raise RuntimeError("IsResource permission called on unsupported model")

        return (
            projects_models.Task.objects.filter(pk=task.pk)
            .filter(
                Q(task_assignees__user=user, task_assignees__is_resource=True)
                | Q(
                    project__project_assignees__user=user,
                    project__project_assignees__is_resource=True,
                )
                | Q(
                    project__customer__customer_assignees__user=user,
                    project__customer__customer_assignees__is_resource=True,
                )
            )
            .exists()
        )

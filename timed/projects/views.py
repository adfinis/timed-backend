"""Viewsets for the projects app."""

from datetime import date

from django.db.models import Q
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_json_api.views import PreloadIncludesMixin

from timed.employment.models import Employment
from timed.permissions import (
    IsAuthenticated,
    IsInternal,
    IsManager,
    IsReadOnly,
    IsSuperUser,
)
from timed.projects import filters, models, serializers


class CustomerViewSet(ReadOnlyModelViewSet):
    """Customer view set."""

    serializer_class = serializers.CustomerSerializer
    filterset_class = filters.CustomerFilterSet
    ordering = "name"

    def get_queryset(self):
        """Prefetch related data.

        If an employee is external, get only assigned customers.

        :return: The customers
        :rtype:  QuerySet
        """
        user = self.request.user
        current_employment = Employment.objects.get_at(user=user, date=date.today())
        queryset = models.Customer.objects.prefetch_related("projects")

        if not current_employment.is_external:  # pragma: no cover
            return queryset
        else:
            return queryset.filter(
                Q(assignees=user)
                | Q(projects__assignees=user)
                | Q(projects__tasks__assignees=user)
            )


class BillingTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.BillingTypeSerializer
    ordering = "name"
    permission_classes = [
        # superuser may edit all billing types
        IsSuperUser
        # internal employees may read all billing types
        | IsAuthenticated & IsInternal & IsReadOnly
    ]

    def get_queryset(self):
        return models.BillingType.objects.all()


class CostCenterViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.CostCenterSerializer
    ordering = "name"
    permission_classes = [
        # superuser may edit all cost centers
        IsSuperUser
        # internal employees may read all cost centers
        | IsAuthenticated & IsInternal & IsReadOnly
    ]

    def get_queryset(self):
        return models.CostCenter.objects.all()


class ProjectViewSet(PreloadIncludesMixin, ReadOnlyModelViewSet):
    """Project view set."""

    serializer_class = serializers.ProjectSerializer
    filterset_class = filters.ProjectFilterSet
    ordering_fields = ("customer__name", "name")
    ordering = "name"
    queryset = models.Project.objects.all()

    prefetch_for_includes = {
        "__all__": ["reviewers"],
        "reviewers": ["reviewers__supervisors"],
    }

    def get_queryset(self):
        """Get only assigned projects, if an employee is external."""
        user = self.request.user
        current_employment = Employment.objects.get_at(user=user, date=date.today())
        queryset = (
            super()
            .get_queryset()
            .select_related("customer", "billing_type", "cost_center")
        )

        if not current_employment.is_external:  # pragma: no cover
            return queryset
        else:
            return queryset.filter(
                Q(assignees=user)
                | Q(tasks__assignees=user)
                | Q(customer__assignees=user)
            )


class TaskViewSet(ModelViewSet):
    """Task view set."""

    serializer_class = serializers.TaskSerializer
    filterset_class = filters.TaskFilterSet
    queryset = models.Task.objects.select_related("project", "cost_center")
    permission_classes = [
        # superuser may edit all tasks
        IsSuperUser
        # managers may edit all tasks
        | IsManager
        # all authenticated users may read all tasks
        | IsAuthenticated & IsReadOnly
    ]
    ordering = "name"

    def filter_queryset(self, queryset):
        """Specific filter queryset options."""
        # my most frequent filter uses LIMIT so default ordering
        # needs to be disabled to avoid exception
        # see TODO filters.MyMostFrequentTaskFilter to avoid this
        if "my_most_frequent" in self.request.query_params:
            self.ordering = None

        return super().filter_queryset(queryset)

    def get_queryset(self):
        """Get only assigned tasks, if an employee is external."""
        user = self.request.user
        current_employment = Employment.objects.get_at(user=user, date=date.today())
        queryset = super().get_queryset().select_related("project", "cost_center")

        if not current_employment.is_external:  # pragma: no cover
            return queryset
        else:
            return queryset.filter(
                Q(assignees=user)
                | Q(project__assignees=user)
                | Q(project__customer__assignees=user)
            )

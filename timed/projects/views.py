"""Viewsets for the projects app."""

from django.db.models import Q
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from timed.permissions import (
    IsAccountant,
    IsAuthenticated,
    IsCustomer,
    IsInternal,
    IsManager,
    IsReadOnly,
    IsSuperUser,
    IsUpdateOnly,
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
        queryset = models.Customer.objects.prefetch_related("projects")
        current_employment = user.get_active_employment()

        if current_employment is None:
            if models.CustomerAssignee.objects.filter(
                user=user, is_customer=True
            ).exists():
                return queryset.filter(assignees=user)
        elif not current_employment.is_external:  # pragma: no cover
            return queryset
        elif current_employment.is_external:
            return queryset.filter(
                Q(assignees=user)
                | Q(projects__assignees=user)
                | Q(projects__tasks__assignees=user)
            )
        return queryset.none()


class BillingTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.BillingTypeSerializer
    ordering = "name"
    permission_classes = [
        # superuser may edit all billing types
        IsSuperUser
        # internal employees may read all billing types
        | IsAuthenticated & (IsInternal | IsCustomer) & IsReadOnly
    ]

    def get_queryset(self):
        """Get billing types depending on the user's role.

        Internal employees should see all billing types.
        Customers should only see billing types that are used in customer visible projects.
        """
        user = self.request.user
        queryset = models.BillingType.objects.all()

        current_employment = user.get_active_employment()

        if current_employment:
            if (
                current_employment.is_external
                and models.CustomerAssignee.objects.filter(
                    user=user, is_customer=True
                ).exists()
            ):
                return queryset.filter(
                    projects__customer_visible=True,
                    projects__customer__customer_assignees__user=user,
                    projects__customer__customer_assignees__is_customer=True,
                )
            return queryset
        else:
            if models.CustomerAssignee.objects.filter(
                user=user, is_customer=True
            ).exists():
                return queryset.filter(
                    projects__customer_visible=True,
                    projects__customer__customer_assignees__user=user,
                    projects__customer__customer_assignees__is_customer=True,
                )


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


class ProjectViewSet(ModelViewSet):
    """Project view set."""

    serializer_class = serializers.ProjectSerializer
    filterset_class = filters.ProjectFilterSet
    ordering_fields = ("customer__name", "name")
    ordering = "name"
    queryset = models.Project.objects.all()
    permission_classes = [
        # superuser may edit all projects
        IsSuperUser
        # accountants may edit all projects
        | IsAccountant
        # managers may edit only assigned projects
        | IsManager & IsUpdateOnly
        # all authenticated users may read all tasks
        | IsAuthenticated & IsReadOnly
    ]

    def get_queryset(self):
        """Get only assigned projects, if an employee is external."""
        user = self.request.user
        queryset = (
            super()
            .get_queryset()
            .select_related("customer", "billing_type", "cost_center")
        )
        current_employment = user.get_active_employment()

        if current_employment is None:
            if models.CustomerAssignee.objects.filter(
                user=user, is_customer=True
            ).exists():
                return queryset.filter(customer__assignees=user, customer_visible=True)
        elif not current_employment.is_external:  # pragma: no cover
            return queryset
        elif current_employment.is_external:
            return queryset.filter(
                Q(assignees=user)
                | Q(tasks__assignees=user)
                | Q(customer__assignees=user)
            )
        return queryset.none()


class TaskViewSet(ModelViewSet):
    """Task view set."""

    serializer_class = serializers.TaskSerializer
    filterset_class = filters.TaskFilterSet
    queryset = models.Task.objects.select_related("project", "cost_center")
    ordering = "name"
    permission_classes = [
        # superuser may edit all tasks
        IsSuperUser
        # managers may edit all tasks
        | IsManager
        # all authenticated users may read all tasks
        | IsAuthenticated & IsReadOnly
    ]

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
        queryset = super().get_queryset().select_related("project", "cost_center")
        current_employment = user.get_active_employment()

        if current_employment is None:
            if models.CustomerAssignee.objects.filter(
                user=user, is_customer=True
            ).exists():
                return queryset.filter(
                    project__customer__assignees=user, project__customer_visible=True
                )
        elif not current_employment.is_external:
            return queryset
        elif current_employment.is_external:
            return queryset.filter(
                Q(assignees=user)
                | Q(project__assignees=user)
                | Q(project__customer__assignees=user)
            )
        return queryset.none()


class TaskAsssigneeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TaskAssigneeSerializer
    filterset_class = filters.TaskAssigneeFilterSet

    def get_queryset(self):
        """Don't show task assignees to customers."""
        user = self.request.user

        queryset = models.TaskAssignee.objects.select_related("task", "user")

        current_employment = user.get_active_employment()
        if current_employment is None or current_employment.is_external:
            return queryset.none()
        return queryset


class ProjectAsssigneeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.ProjectAssigneeSerializer
    filterset_class = filters.ProjectAssigneeFilterSet

    def get_queryset(self):
        """Don't show project assignees to customers."""
        user = self.request.user

        queryset = models.ProjectAssignee.objects.select_related("project", "user")

        current_employment = user.get_active_employment()
        if current_employment is None or current_employment.is_external:
            return queryset.none()
        return queryset


class CustomerAsssigneeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.CustomerAssigneeSerializer
    filterset_class = filters.CustomerAssigneeFilterSet

    def get_queryset(self):
        """Don't show customer assignees to customers."""
        user = self.request.user

        queryset = models.CustomerAssignee.objects.select_related("customer", "user")

        current_employment = user.get_active_employment()
        if current_employment is None or current_employment.is_external:
            return queryset.none()
        return queryset

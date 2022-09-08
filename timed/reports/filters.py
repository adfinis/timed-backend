from django.db.models import Q
from django_filters.rest_framework import (
    BaseInFilter,
    DateFilter,
    FilterSet,
    NumberFilter,
)

from timed.projects.models import CustomerAssignee, ProjectAssignee, Task, TaskAssignee


class MultiQSFilterMixin:
    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        return qs._finalize()


class TaskStatisticFilterSet(MultiQSFilterMixin, FilterSet):
    """Filter set for the customer, project and task statistic endpoint."""

    id = BaseInFilter()
    from_date = DateFilter(field_name="reports__date", lookup_expr="gte")
    to_date = DateFilter(field_name="reports__date", lookup_expr="lte")
    project = NumberFilter(field_name="project")
    customer = NumberFilter(field_name="project__customer")
    review = NumberFilter(field_name="reports__review")
    editable = NumberFilter(method="filter_editable")
    not_billable = NumberFilter(field_name="reports__not_billable")
    billed = NumberFilter(field_name="reports__billed")
    verified = NumberFilter(
        field_name="reports__verified_by_id", lookup_expr="isnull", exclude=True
    )
    reviewer = NumberFilter(method="filter_has_reviewer")
    verifier = NumberFilter(field_name="reports__verified_by")
    billing_type = NumberFilter(field_name="project__billing_type")
    user = NumberFilter(field_name="reports__user_id")
    cost_center = NumberFilter(method="filter_cost_center")
    rejected = NumberFilter(field_name="reports__rejected")

    def filter_has_reviewer(self, queryset, name, value):
        if not value:  # pragma: no cover
            return queryset

        return queryset.filter(
            Q(
                project__customer_id__in=CustomerAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("customer_id")
            )
            | Q(
                project_id__in=ProjectAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("project_id")
            )
            | Q(
                id__in=TaskAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("task_id")
            )
        )

    def filter_cost_center(self, queryset, name, value):
        """
        Filter report by cost center.

        Cost center on task has higher priority over project cost
        center.
        """
        return queryset.filter(
            Q(cost_center=value)
            | Q(project__cost_center=value) & Q(cost_center__isnull=True)
        )

    class Meta:
        """Meta information for the task statistic filter set."""

        model = Task
        fields = ["most_recent_remaining_effort"]

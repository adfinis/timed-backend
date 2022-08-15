from django.db.models import Q
from django_filters.rest_framework import DateFilter, FilterSet, NumberFilter, BaseInFilter

from timed.projects.models import CustomerAssignee, ProjectAssignee, TaskAssignee
from timed.projects.models import Task


class TaskStatisticFilterSet(FilterSet):
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

        # reports in which user is customer assignee and responsible reviewer
        reports_customer_assignee_is_reviewer = queryset.filter(
            Q(
                project__customer_id__in=CustomerAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("customer_id")
            )
        ).exclude(
            Q(
                project_id__in=ProjectAssignee.objects.filter(
                    is_reviewer=True
                ).values("project_id")
            )
            | Q(
                id__in=TaskAssignee.objects.filter(is_reviewer=True).values(
                    "task_id"
                )
            )
        )

        # reports in which user is project assignee and responsible reviewer
        reports_project_assignee_is_reviewer = queryset.filter(
            Q(
                project_id__in=ProjectAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("project_id")
            )
        ).exclude(
            Q(
                id__in=TaskAssignee.objects.filter(is_reviewer=True).values(
                    "task_id"
                )
            )
        )

        # reports in which user task assignee and responsible reviewer
        reports_task_assignee_is_reviewer = queryset.filter(
            Q(
                id__in=TaskAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("task_id")
            )
        )

        return (
            reports_customer_assignee_is_reviewer
            | reports_project_assignee_is_reviewer
            | reports_task_assignee_is_reviewer
        )

    def filter_editable(self, queryset, name, value):
        """Filter reports whether they are editable by current user.

        When set to `1` filter all results to what is editable by current
        user. If set to `0` to not editable.
        """
        user = self.request.user
        assignee_filter = (
            # avoid duplicates by using subqueries instead of joins
            Q(reports__user__in=user.supervisees.values("id"))
            | Q(
                task_assignees__user=user,
                task_assignees__is_reviewer=True,
            )
            | Q(
                project__project_assignees__user=user,
                project__project_assignees__is_reviewer=True,
            )
            | Q(
                project__customer__customer_assignees__user=user,
                project__customer__customer_assignees__is_reviewer=True,
            )
            | Q(reports__user=user)
        )
        unfinished_filter = Q(reports__verified_by__isnull=True)
        editable_filter = assignee_filter & unfinished_filter

        if value:  # editable
            if user.is_superuser:
                # superuser may edit all reports
                return queryset
            elif user.is_accountant:
                return queryset.filter(unfinished_filter)
            # only owner, reviewer or supervisor may change unverified reports
            queryset = queryset.filter(editable_filter).distinct()

            return queryset
        else:  # not editable
            if user.is_superuser:
                # no reports which are not editable
                return queryset.none()
            elif user.is_accountant:
                return queryset.exclude(unfinished_filter)

            queryset = queryset.exclude(editable_filter)
            return queryset

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
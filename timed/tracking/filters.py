"""Filters for filtering the data of the tracking app endpoints."""

from functools import wraps

from django.db.models import Q
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import (
    BaseInFilter,
    DateFilter,
    Filter,
    FilterSet,
    NumberFilter,
)

from timed.projects.models import CustomerAssignee, ProjectAssignee, TaskAssignee
from timed.tracking import models


def boolean_filter(func):
    """Cast the passed query parameter into a boolean.

    :param function func: The function to decorate
    :return:              The function called with a boolean
    :rtype:               function
    """

    @wraps(func)
    def wrapper(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        value = value.lower() not in ("1", "true", "yes")

        return func(self, qs, value)

    return wrapper


class ActivityActiveFilter(Filter):
    """Filter to filter activities by being currently active or not.

    An activity is active, as soon as they have at least on activity
    block which does not have to_time.
    """

    @boolean_filter
    def filter(self, qs, value):
        """Filter the queryset.

        :param QuerySet qs: The queryset to filter
        :param bool  value: Whether the activities should be active
        :return:            The filtered queryset
        :rtype:             QuerySet
        """
        return qs.filter(to_time__exact=None).distinct()


class ActivityFilterSet(FilterSet):
    """Filter set for the activities endpoint."""

    active = ActivityActiveFilter()
    day = DateFilter(field_name="date")

    class Meta:
        """Meta information for the activity filter set."""

        model = models.Activity
        fields = ["active", "day"]


class AttendanceFilterSet(FilterSet):
    """Filter set for the attendance endpoint."""

    class Meta:
        """Meta information for the attendance filter set."""

        model = models.Attendance
        fields = ["date"]


class ReportFilterSet(FilterSet):
    """Filter set for the reports endpoint."""

    id = BaseInFilter()
    from_date = DateFilter(field_name="date", lookup_expr="gte")
    to_date = DateFilter(field_name="date", lookup_expr="lte")
    project = NumberFilter(field_name="task__project")
    customer = NumberFilter(field_name="task__project__customer")
    review = NumberFilter(field_name="review")
    editable = NumberFilter(method="filter_editable")
    not_billable = NumberFilter(field_name="not_billable")
    billed = NumberFilter(field_name="billed")
    verified = NumberFilter(
        field_name="verified_by_id", lookup_expr="isnull", exclude=True
    )
    reviewer = NumberFilter(method="filter_has_reviewer")
    verifier = NumberFilter(field_name="verified_by")
    billing_type = NumberFilter(field_name="task__project__billing_type")
    user = NumberFilter(field_name="user_id")
    cost_center = NumberFilter(method="filter_cost_center")

    def filter_has_reviewer(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(
                task_id__in=TaskAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("task_id"),
            )
            | Q(
                task__project_id__in=ProjectAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("project_id"),
            )
            | Q(
                task__project__customer_id__in=CustomerAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("customer_id"),
            )
        )

    def filter_editable(self, queryset, name, value):
        """Filter reports whether they are editable by current user.

        When set to `1` filter all results to what is editable by current
        user. If set to `0` to not editable.
        """
        user = self.request.user

        editable_filter = (
            # avoid duplicates by using subqueries instead of joins
            Q(user__in=user.supervisees.values("id"))
            | Q(
                task__task_assignees__user=user,
                task__task_assignees__is_reviewer=True,
            )
            | Q(
                task__project__project_assignees__user=user,
                task__project__project_assignees__is_reviewer=True,
            )
            | Q(
                task__project__customer__customer_assignees__user=user,
                task__project__customer__customer_assignees__is_reviewer=True,
            )
            | Q(user=user)
        ) & ~(Q(verified_by__isnull=False) & Q(billed=True))

        if value:  # editable
            if user.is_superuser:
                # superuser may edit all reports
                return queryset

            # only owner, reviewer or supervisor may change unverified reports
            queryset = queryset.filter(editable_filter).distinct()

            return queryset
        else:  # not editable
            if user.is_superuser:
                # no reports which are not editable
                return queryset.none()

            queryset = queryset.exclude(editable_filter)
            return queryset

    def filter_cost_center(self, queryset, name, value):
        """
        Filter report by cost center.

        Cost center on task has higher priority over project cost
        center.
        """
        return queryset.filter(
            Q(task__cost_center=value)
            | Q(task__project__cost_center=value) & Q(task__cost_center__isnull=True)
        )

    class Meta:
        """Meta information for the report filter set."""

        model = models.Report
        fields = (
            "date",
            "from_date",
            "to_date",
            "user",
            "task",
            "project",
            "verified",
            "not_billable",
            "review",
            "reviewer",
            "billing_type",
        )


class AbsenceFilterSet(FilterSet):
    """Filter set for the absences endpoint."""

    from_date = DateFilter(field_name="date", lookup_expr="gte")
    to_date = DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        """Meta information for the absence filter set."""

        model = models.Absence
        fields = ["date", "from_date", "to_date", "user"]

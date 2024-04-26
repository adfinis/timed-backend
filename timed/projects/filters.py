"""Filters for filtering the data of the projects app endpoints."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from django.db.models import Count, Q
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import BaseInFilter, Filter, FilterSet, NumberFilter

from timed.projects import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class CustomerFilterSet(FilterSet):
    """Filter set for the customers endpoint."""

    archived = NumberFilter(field_name="archived")

    class Meta:
        """Meta information for the customer filter set."""

        model = models.Customer
        fields = (
            "archived",
            "reference",
        )


class ProjectFilterSet(FilterSet):
    """Filter set for the projects endpoint."""

    archived = NumberFilter(field_name="archived")
    has_manager = NumberFilter(method="filter_has_manager")
    has_reviewer = NumberFilter(method="filter_has_reviewer")
    customer = NumberInFilter(field_name="customer")

    def filter_has_manager(
        self, queryset: QuerySet[models.Project], _name: str, value: int
    ) -> QuerySet[models.Project]:
        if not value:  # pragma: no cover
            return queryset
        return queryset.filter(
            Q(
                pk__in=models.ProjectAssignee.objects.filter(
                    is_manager=True, user_id=value
                ).values("project_id"),
            )
            | Q(
                customer_id__in=models.CustomerAssignee.objects.filter(
                    is_manager=True, user_id=value
                ).values("customer_id"),
            )
        )

    def filter_has_reviewer(
        self, queryset: QuerySet[models.Project], _name: str, value: int
    ) -> QuerySet[models.Project]:
        if not value:  # pragma: no cover
            return queryset
        return queryset.filter(
            Q(
                pk__in=models.ProjectAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("project_id"),
            )
            | Q(
                customer_id__in=models.CustomerAssignee.objects.filter(
                    is_reviewer=True, user_id=value
                ).values("customer_id"),
            )
        )

    class Meta:
        """Meta information for the project filter set."""

        model = models.Project
        fields = (
            "archived",
            "customer",
            "billing_type",
            "cost_center",
            "reference",
        )


class MyMostFrequentTaskFilter(Filter):
    """Filter most frequently used tasks."""

    # TODO: From an api and framework standpoint instead of an additional filter it
    # would be more desirable to assign an ordering field frecency and to
    # limit by use paging.  This is way harder to implement therefore on hold.

    def filter(
        self, qs: QuerySet[models.Task], value: int | str | tuple | list | None
    ) -> QuerySet[models.Task]:
        """Filter for given most frequently used tasks.

        Most frequently used tasks are only counted within last
        few months as older tasks are not relevant anymore
        for today's usage.
        """
        if value in EMPTY_VALUES:
            return qs

        user = self.parent.request.user
        from_date = date.today() - timedelta(days=60)

        qs = qs.filter(
            reports__user=user,
            reports__date__gt=from_date,
            archived=False,
            project__archived=False,
        )
        qs = qs.annotate(frequency=Count("reports")).order_by("-frequency")
        # limit number of results to given value
        return qs[: int(value)]


class TaskFilterSet(FilterSet):
    """Filter set for the tasks endpoint."""

    my_most_frequent = MyMostFrequentTaskFilter()
    archived = NumberFilter(field_name="archived")
    project = NumberInFilter(field_name="project")

    class Meta:
        """Meta information for the task filter set."""

        model = models.Task
        fields = (
            "archived",
            "project",
            "my_most_frequent",
            "reference",
            "cost_center",
        )


class TaskAssigneeFilterSet(FilterSet):
    """Filter set for the task assignees endpoint."""

    task = NumberFilter(field_name="task")
    tasks = NumberInFilter(field_name="task")
    user = NumberFilter(field_name="user")

    class Meta:
        """Meta information for the task assignee filter set."""

        model = models.TaskAssignee
        fields = (
            "task",
            "user",
            "is_reviewer",
            "is_manager",
            "is_resource",
        )


class ProjectAssigneeFilterSet(FilterSet):
    """Filter set for the project assignees endpoint."""

    project = NumberFilter(field_name="project")
    projects = NumberInFilter(field_name="project")
    user = NumberFilter(field_name="user")

    class Meta:
        """Meta information for the project assignee filter set."""

        model = models.ProjectAssignee
        fields = (
            "project",
            "user",
            "is_reviewer",
            "is_manager",
            "is_resource",
        )


class CustomerAssigneeFilterSet(FilterSet):
    """Filter set for the customer assignees endpoint."""

    customer = NumberFilter(field_name="customer")
    customers = NumberInFilter(field_name="customer")
    user = NumberFilter(field_name="user")

    class Meta:
        """Meta information for the customer assignee filter set."""

        model = models.CustomerAssignee
        fields = (
            "customer",
            "user",
            "is_reviewer",
            "is_manager",
            "is_resource",
        )

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import DurationField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import (
    BaseInFilter,
    DateFilter,
    FilterSet,
    NumberFilter,
)

from timed.projects.models import CustomerAssignee, ProjectAssignee, TaskAssignee

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from timed.tracking.models import Report


class StatisticFiltersetBase:
    def filter_has_reviewer(
        self, queryset: QuerySet[Report], _name: str, value: int
    ) -> QuerySet[Report]:
        if not value:  # pragma: no cover
            return queryset

        task_prefix = self._refs["task_prefix"]
        project_prefix = self._refs["project_prefix"]
        customer_prefix = self._refs["customer_prefix"]

        customer_assignees = CustomerAssignee.objects.filter(
            is_reviewer=True, user_id=value
        ).values("customer_id")

        project_assignees = ProjectAssignee.objects.filter(
            is_reviewer=True, user_id=value
        ).values("project_id")
        task_assignees = TaskAssignee.objects.filter(
            is_reviewer=True, user_id=value
        ).values("task_id")

        the_filter = (
            Q(**{f"{customer_prefix}pk__in": customer_assignees})
            | Q(**{f"{project_prefix}pk__in": project_assignees})
            | Q(**{f"{task_prefix}id__in": task_assignees})
        )
        return queryset.filter_aggregate(the_filter).filter_base(the_filter)

    def filter_cost_center(
        self, queryset: QuerySet[Report], _name: str, value: int
    ) -> QuerySet[Report]:
        """Filter report by cost center.

        The filter behaves slightly different depending on what the
        statistic summarizes:
        * When viewing the statistic over customers, the work durations are
          filtered (either project or task)
        * When viewing the statistic over project, only the projects
          are filtered
        * When viewing the statistic over tasks, only the tasks
          are filtered
        """
        # TODO: Discuss Is this the desired behaviour by our users?

        if not value:  # pragma: no cover
            return queryset

        is_customer = not self._refs["customer_prefix"]

        task_prefix = self._refs["task_prefix"]
        project_prefix = self._refs["project_prefix"]

        filter_q = Q(**{f"{task_prefix}cost_center": value}) | Q(
            **{
                f"{project_prefix}cost_center": value,
                f"{task_prefix}cost_center__isnull": True,
            }
        )

        if is_customer:
            # Customer mode: We only need to filter aggregates,
            # as the customer has no cost center
            return queryset.filter_aggregate(filter_q)
        # Project or task: Filter both to get the correct result
        return queryset.filter_base(filter_q).filter_aggregate(filter_q)

    def filter_queryset(self, queryset: QuerySet[Report]) -> QuerySet[Report]:
        qs = super().filter_queryset(queryset)

        duration_ref = self._refs["reports_ref"] + "__duration"

        full_qs = qs._base.annotate(  # noqa: SLF001
            duration=Coalesce(
                Sum(duration_ref, filter=qs._agg_filters),  # noqa: SLF001
                Value("00:00:00", DurationField(null=False)),
            ),
            pk=F("id"),
        )
        return full_qs.values()


def statistic_filterset_builder(
    name: str, reports_ref: str, project_ref: str, customer_ref: str, task_ref: str
) -> type[StatisticFiltersetBase, FilterSet]:
    reports_prefix = f"{reports_ref}__" if reports_ref else ""
    project_prefix = f"{project_ref}__" if project_ref else ""
    customer_prefix = f"{customer_ref}__" if customer_ref else ""
    task_prefix = f"{task_ref}__" if task_ref else ""

    return type(
        name,
        (StatisticFiltersetBase, FilterSet),
        {
            "_refs": {
                "reports_prefix": reports_prefix,
                "project_prefix": project_prefix,
                "customer_prefix": customer_prefix,
                "task_prefix": task_prefix,
                "reports_ref": reports_ref,
                "project_ref": project_ref,
                "customer_ref": customer_ref,
                "task_ref": task_ref,
            },
            "from_date": DateFilter(
                field_name=f"{reports_prefix}date", lookup_expr="gte"
            ),
            "to_date": DateFilter(
                field_name=f"{reports_prefix}date", lookup_expr="lte"
            ),
            "project": NumberFilter(field_name=f"{project_prefix}pk"),
            "customer": NumberFilter(field_name=f"{customer_prefix}pk"),
            "review": NumberFilter(field_name=f"{reports_prefix}review"),
            "not_billable": NumberFilter(field_name=f"{reports_prefix}not_billable"),
            "billed": NumberFilter(field_name=f"{reports_prefix}billed"),
            "verified": NumberFilter(
                field_name=f"{reports_prefix}verified_by_id",
                lookup_expr="isnull",
                exclude=True,
            ),
            "verifier": NumberFilter(field_name=f"{reports_prefix}verified_by"),
            "billing_type": NumberFilter(field_name=f"{project_prefix}billing_type"),
            "user": NumberFilter(field_name=f"{reports_prefix}user_id"),
            "rejected": NumberFilter(field_name=f"{reports_prefix}rejected"),
            "id": BaseInFilter(),
            "cost_center": NumberFilter(method="filter_cost_center"),
            "reviewer": NumberFilter(method="filter_has_reviewer"),
        },
    )


CustomerStatisticFilterSet = statistic_filterset_builder(
    "CustomerStatisticFilterSet",
    reports_ref="projects__tasks__reports",
    project_ref="projects",
    task_ref="projects__tasks",
    customer_ref="",
)

ProjectStatisticFilterSet = statistic_filterset_builder(
    "ProjectStatisticFilterSet",
    reports_ref="tasks__reports",
    project_ref="",
    task_ref="tasks",
    customer_ref="customer",
)

TaskStatisticFilterSet = statistic_filterset_builder(
    "TaskStatisticFilterSet",
    reports_ref="reports",
    project_ref="project",
    task_ref="",
    customer_ref="project__customer",
)

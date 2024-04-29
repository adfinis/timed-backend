from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import DateFilter, Filter, FilterSet, NumberFilter

from timed.employment import models
from timed.employment.models import User

if TYPE_CHECKING:
    from typing import TypeVar

    from django.db.models import QuerySet

    T = TypeVar("T", QuerySet)


class YearFilter(Filter):
    """Filter to filter a queryset by year."""

    def filter(self, qs: T, value: int) -> T:
        if value in EMPTY_VALUES:
            return qs

        return qs.filter(**{f"{self.field_name}__year": value})


class PublicHolidayFilterSet(FilterSet):
    """Filter set for the public holidays endpoint."""

    year = YearFilter(field_name="date")
    from_date = DateFilter(field_name="date", lookup_expr="gte")
    to_date = DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        """Meta information for the public holiday filter set."""

        model = models.PublicHoliday
        fields = (
            "year",
            "location",
            "date",
            "from_date",
            "to_date",
        )


class AbsenceTypeFilterSet(FilterSet):
    fill_worktime = NumberFilter(field_name="fill_worktime")

    class Meta:
        """Meta information for the public holiday filter set."""

        model = models.AbsenceType
        fields = ("fill_worktime",)


class UserFilterSet(FilterSet):
    active = NumberFilter(field_name="is_active")
    supervisor = NumberFilter(field_name="supervisors")
    is_reviewer = NumberFilter(method="filter_is_reviewer")
    is_supervisor = NumberFilter(method="filter_is_supervisor")
    is_accountant = NumberFilter(field_name="is_accountant")
    is_external = NumberFilter(method="filter_is_external")

    def filter_is_external(
        self, queryset: QuerySet[models.User], _name: str, value: int
    ) -> QuerySet[models.User]:
        return queryset.filter(employments__is_external=value)

    def filter_is_reviewer(
        self, queryset: QuerySet[models.User], _name: str, value: int
    ) -> QuerySet[models.User]:
        if value:
            return queryset.filter(pk__in=User.objects.all_reviewers())
        return queryset.exclude(pk__in=User.objects.all_reviewers())

    def filter_is_supervisor(
        self, queryset: QuerySet[models.User], _name: str, value: int
    ) -> QuerySet[models.User]:
        if value:
            return queryset.filter(pk__in=User.objects.all_supervisors())
        return queryset.exclude(pk__in=User.objects.all_supervisors())

    class Meta:
        model = models.User
        fields = (
            "active",
            "supervisor",
            "is_reviewer",
            "is_supervisor",
            "is_accountant",
        )


class EmploymentFilterSet(FilterSet):
    date = DateFilter(method="filter_date")

    def filter_date(
        self, queryset: QuerySet[models.Employment], _name: str, value: int
    ) -> QuerySet[models.Employment]:
        return queryset.filter(
            Q(start_date__lte=value)
            & Q(Q(end_date__gte=value) | Q(end_date__isnull=True))
        )

    class Meta:
        model = models.Employment
        fields = (
            "user",
            "location",
        )


class OvertimeCreditFilterSet(FilterSet):
    year = YearFilter(field_name="date")
    from_date = DateFilter(field_name="date", lookup_expr="gte")
    to_date = DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = models.OvertimeCredit
        fields = (
            "year",
            "user",
            "date",
            "from_date",
            "to_date",
        )


class AbsenceCreditFilterSet(FilterSet):
    year = YearFilter(field_name="date")
    from_date = DateFilter(field_name="date", lookup_expr="gte")
    to_date = DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = models.AbsenceCredit
        fields = (
            "year",
            "user",
            "date",
            "from_date",
            "to_date",
            "absence_type",
        )


class WorktimeBalanceFilterSet(FilterSet):
    user = NumberFilter(field_name="id")
    supervisor = NumberFilter(field_name="supervisors")

    class Meta:
        model = models.User
        fields = ("user",)


class AbsenceBalanceFilterSet(FilterSet):
    absence_type = NumberFilter(field_name="id")

    class Meta:
        model = models.AbsenceType
        fields = ("absence_type",)

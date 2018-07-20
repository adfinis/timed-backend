from datetime import date

from django.db.models import Value
from django.db.models.functions import Coalesce
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import (DateFilter, Filter, FilterSet,
                                           NumberFilter)

from timed.employment import models
from timed.employment.models import User


class YearFilter(Filter):
    """Filter to filter a queryset by year."""

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        return qs.filter(**{
            '%s__year' % self.field_name: value
        })


class PublicHolidayFilterSet(FilterSet):
    """Filter set for the public holidays endpoint."""

    year      = YearFilter(field_name='date')
    from_date = DateFilter(field_name='date', lookup_expr='gte')
    to_date   = DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        """Meta information for the public holiday filter set."""

        model  = models.PublicHoliday
        fields = ['year', 'location', 'date', 'from_date', 'to_date']


class AbsenceTypeFilterSet(FilterSet):
    fill_worktime = NumberFilter(field_name='fill_worktime')

    class Meta:
        """Meta information for the public holiday filter set."""

        model  = models.AbsenceType
        fields = ['fill_worktime']


class UserFilterSet(FilterSet):
    active      = NumberFilter(field_name='is_active')
    supervisor  = NumberFilter(field_name='supervisors')
    is_reviewer = NumberFilter(method='filter_is_reviewer')
    is_supervisor = NumberFilter(method='filter_is_supervisor')

    def filter_is_reviewer(self, queryset, name, value):
        if value:
            return queryset.filter(pk__in=User.objects.all_reviewers())
        return queryset.exclude(pk__in=User.objects.all_reviewers())

    def filter_is_supervisor(self, queryset, name, value):
        if value:
            return queryset.filter(pk__in=User.objects.all_supervisors())
        return queryset.exclude(pk__in=User.objects.all_supervisors())

    class Meta:
        model  = models.User
        fields = ['active', 'supervisor', 'is_reviewer', 'is_supervisor']


class EmploymentFilterSet(FilterSet):
    date = DateFilter(method='filter_date')

    def filter_date(self, queryset, name, value):
        queryset = queryset.annotate(
            end=Coalesce('end_date', Value(date.today()))
        )

        queryset = queryset.filter(
            start_date__lte=value,
            end__gte=value
        )

        return queryset

    class Meta:
        model  = models.Employment
        fields = ['user', 'location']


class OvertimeCreditFilterSet(FilterSet):
    year      = YearFilter(field_name='date')
    from_date = DateFilter(field_name='date', lookup_expr='gte')
    to_date   = DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model  = models.OvertimeCredit
        fields = ['year', 'user', 'date', 'from_date', 'to_date']


class AbsenceCreditFilterSet(FilterSet):
    year      = YearFilter(field_name='date')
    from_date = DateFilter(field_name='date', lookup_expr='gte')
    to_date   = DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model  = models.AbsenceCredit
        fields = [
            'year', 'user', 'date', 'from_date', 'to_date', 'absence_type'
        ]


class WorktimeBalanceFilterSet(FilterSet):
    user = NumberFilter(field_name='id')
    supervisor = NumberFilter(field_name='supervisors')
    # additional filters analyzed in WorktimeBalanceView
    # date = DateFilter()
    # last_reported_date = NumberFilter()

    class Meta:
        model  = models.User
        fields = ['user']


class AbsenceBalanceFilterSet(FilterSet):
    absence_type = NumberFilter(field_name='id')

    class Meta:
        model  = models.AbsenceType
        fields = ['absence_type']

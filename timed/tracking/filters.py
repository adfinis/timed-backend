"""Filters for filtering the data of the tracking app endpoints."""

import datetime
from functools import wraps

from django_filters import DateFilter, Filter, FilterSet

from timed.tracking import models


def boolean_filter(func):
    """Cast the passed query parameter into a boolean.

    :param function func: The function to decorate
    :return:              The function called with a boolean
    :rtype:               function
    """
    @wraps(func)
    def wrapper(self, qs, value):
        """Wrap the initial function.

        :param QuerySet qs: The queryset to filter
        :param str   value: The value to cast
        :return:            The original function
        :rtype:             function
        """
        value = value.lower() not in ('1', 'true', 'yes')

        return func(self, qs, value)

    return wrapper


class DayFilter(Filter):
    """Filter to filter a queryset by day."""

    def filter(self, qs, value):
        """Filter the queryset.

        :param QuerySet qs: The queryset to filter
        :param str   value: The day to filter to
        :return:            The filtered queryset
        :rtype:             QuerySet
        """
        date = datetime.datetime.strptime(value, '%Y-%m-%d').date()

        return qs.filter(**{
            '%s__date' % self.name: date
        })


class ActivityActiveFilter(Filter):
    """Filter to filter activities by being currently active or not.

    An activity is active, as soon as they have at least on activity
    block which does not have to_datetime.
    """

    @boolean_filter
    def filter(self, qs, value):
        """Filter the queryset.

        :param QuerySet qs: The queryset to filter
        :param bool  value: Whether the activities should be active
        :return:            The filtered queryset
        :rtype:             QuerySet
        """
        return qs.filter(
            blocks__isnull=False,
            blocks__to_datetime__exact=None
        ).distinct()


class RecentActivityFilter(Filter):
    """Filter to get recent activities."""

    @boolean_filter
    def filter(self, qs, value):
        """Filter the queryset.

        :param QuerySet qs: The queryset to filter
        :param bool  value: Whether to get only recent activities
        :return:            The filtered queryset
        :rtype:             QuerySet
        """
        return qs.order_by('task', '-start_datetime').distinct('task')[:10]


class ActivityFilterSet(FilterSet):
    """Filter set for the activities endpoint."""

    active = ActivityActiveFilter()
    recent = RecentActivityFilter()
    day    = DayFilter(name='start_datetime')

    class Meta:
        """Meta information for the activity filter set."""

        model  = models.Activity
        fields = ['active', 'recent', 'day']


class ActivityBlockFilterSet(FilterSet):
    """Filter set for the activity blocks endpoint."""

    class Meta:
        """Meta information for the activity block filter set."""

        model  = models.ActivityBlock
        fields = ['activity']


class AttendanceFilterSet(FilterSet):
    """Filter set for the attendance endpoint."""

    day = DayFilter(name='from_datetime')

    class Meta:
        """Meta information for the attendance filter set."""

        model  = models.Attendance
        fields = ['day']


class RecentReportFilter(Filter):
    """Filter to get recent reports."""

    @boolean_filter
    def filter(self, qs, value):
        """Filter the queryset.

        :param QuerySet qs: The queryset to filter
        :param bool  value: Whether to get only recent reports
        :return:            The filtered queryset
        :rtype:             QuerySet
        """
        return qs.order_by('task', '-date').distinct('task')[:10]


class ReportFilterSet(FilterSet):
    """Filter set for the reports endpoint."""

    from_date = DateFilter(name='date', lookup_expr='gte')
    to_date   = DateFilter(name='date', lookup_expr='lte')
    recent    = RecentReportFilter()

    class Meta:
        """Meta information for the report filter set."""

        model  = models.Report
        fields = ['date', 'from_date', 'to_date', 'recent']


class AbsenceFilterSet(FilterSet):
    """Filter set for the absences endpoint."""

    from_date = DateFilter(name='date', lookup_expr='gte')
    to_date   = DateFilter(name='date', lookup_expr='lte')

    class Meta:
        """Meta information for the absence filter set."""

        model  = models.Absence
        fields = ['date', 'from_date', 'to_date']
